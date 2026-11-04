"""T2-003: bounded, byte-preserving JSON-RPC forwarding to one trusted destination."""

import asyncio
import json
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from http.cookiejar import Cookie, CookieJar, DefaultCookiePolicy
from ipaddress import ip_address
from typing import Any
from urllib.parse import urlsplit
from urllib.request import Request as CookieRequest

import httpx

from task2_proxy.rpc import RequestId
from task2_proxy.security import AuthorizedRequest, require_authorized_request
from task2_proxy.settings import TOKEN_PATTERN


class UpstreamConfigurationError(ValueError):
    """Configuration failures never echo URLs or credentials."""


@dataclass(frozen=True, slots=True)
class UpstreamSettings:
    url: str = field(repr=False)
    bearer_token: str | None = field(default=None, repr=False)
    connect_timeout: float = 5.0
    read_timeout: float = 15.0
    write_timeout: float = 15.0
    pool_timeout: float = 5.0
    total_timeout: float = 30.0
    max_request_bytes: int = 1_048_576
    max_response_bytes: int = 2_097_152

    def __post_init__(self) -> None:
        try:
            if type(self.url) is not str or any(
                char.isspace() or ord(char) <= 32 or ord(char) == 127 or char == "\\"
                for char in self.url
            ):
                raise ValueError
            url = httpx.URL(self.url)
            if (
                not url.is_absolute_url
                or not url.host
                or url.username
                or url.password
                or "@" in urlsplit(self.url).netloc
                or (url.port is not None and not 1 <= url.port <= 65535)
                or "?" in self.url
                or "#" in self.url
                or url.scheme not in {"http", "https"}
            ):
                raise ValueError
            if url.scheme == "http" and not ip_address(url.host).is_loopback:
                raise ValueError
            if self.bearer_token is not None and (
                type(self.bearer_token) is not str or not TOKEN_PATTERN.fullmatch(self.bearer_token)
            ):
                raise ValueError
            for value in (
                self.connect_timeout,
                self.read_timeout,
                self.write_timeout,
                self.pool_timeout,
                self.total_timeout,
            ):
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    raise ValueError
            for value in (self.max_request_bytes, self.max_response_bytes):
                if type(value) is not int or value <= 0:
                    raise ValueError
        except (ValueError, TypeError, OverflowError, httpx.InvalidURL):
            raise UpstreamConfigurationError("Invalid upstream configuration") from None


def load_upstream_settings(environment: Mapping[str, str] | None = None) -> UpstreamSettings:
    """Trusted startup configuration only; no inbound header/query/body fallback."""
    source = os.environ if environment is None else environment
    url = source.get("TASK2_UPSTREAM_URL")
    if type(url) is not str:
        raise UpstreamConfigurationError("Invalid upstream configuration")
    return UpstreamSettings(url, source.get("TASK2_UPSTREAM_BEARER_TOKEN"))


class FailureKind(StrEnum):
    TIMEOUT = "timeout"
    TRANSPORT = "transport"
    REDIRECT = "redirect"
    INVALID_RESPONSE = "invalid_response"
    ID_MISMATCH = "id_mismatch"
    REQUEST_TOO_LARGE = "request_too_large"
    RESPONSE_TOO_LARGE = "response_too_large"
    CLOSED = "closed"


class UpstreamError(Exception):
    def __init__(self, kind: FailureKind) -> None:
        super().__init__(f"Upstream request failed ({kind.value})")
        self.kind = kind


@dataclass(frozen=True, slots=True)
class UpstreamResponse:
    status_code: int
    body: bytes = field(repr=False)
    # Entire upstream header set is discarded; only local safe metadata is returned.
    headers: tuple[tuple[str, str], ...] = (
        ("content-type", "application/json"),
        ("cache-control", "no-store"),
    )


class _NoCookies(DefaultCookiePolicy):
    def set_ok(self, cookie: Cookie, request: CookieRequest) -> bool:
        return False


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ValueError


def _validate_response(body: bytes, request_id: RequestId) -> None:
    # Opaque fractional/exponent numbers need no conversion: raw bytes are relayed.
    # A marker keeps them distinct from the exact int/string/null ID/code types.
    noninteger = object()
    try:
        value = json.loads(
            body.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_float=lambda _: noninteger,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError):
        raise UpstreamError(FailureKind.INVALID_RESPONSE) from None
    if (
        type(value) is not dict
        or value.get("jsonrpc") != "2.0"
        or "id" not in value
        or type(value["id"]) not in (str, int, type(None))
        or ("result" in value) == ("error" in value)
        or "method" in value
    ):
        raise UpstreamError(FailureKind.INVALID_RESPONSE)
    if "error" in value:
        error = value["error"]
        if (
            type(error) is not dict
            or type(error.get("code")) is not int
            or type(error.get("message")) is not str
        ):
            raise UpstreamError(FailureKind.INVALID_RESPONSE)
    if type(value["id"]) is not type(request_id) or value["id"] != request_id:
        raise UpstreamError(FailureKind.ID_MISMATCH)


class UpstreamAdapter:
    """One adapter per trusted upstream/lifespan; injected transport is for tests."""

    def __init__(
        self, settings: UpstreamSettings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        if type(settings) is not UpstreamSettings:
            raise UpstreamConfigurationError("Invalid upstream configuration")
        self._settings = settings
        self._url = httpx.URL(settings.url)
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        self._client = httpx.AsyncClient(
            transport=transport
            if transport is not None
            else httpx.AsyncHTTPTransport(retries=0, trust_env=False, limits=limits),
            timeout=httpx.Timeout(
                connect=settings.connect_timeout,
                read=settings.read_timeout,
                write=settings.write_timeout,
                pool=settings.pool_timeout,
            ),
            limits=limits,
            trust_env=False,
            follow_redirects=False,
            cookies=CookieJar(policy=_NoCookies()),
        )

    async def __aenter__(self) -> "UpstreamAdapter":
        if self._client.is_closed:
            raise UpstreamError(FailureKind.CLOSED)
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """The lifespan owner must finish/cancel active work before closing."""
        await self._client.aclose()

    async def forward(self, permit: AuthorizedRequest) -> UpstreamResponse:
        inspected = require_authorized_request(permit)
        if len(inspected.raw_body) > self._settings.max_request_bytes:
            raise UpstreamError(FailureKind.REQUEST_TOO_LARGE)
        if self._client.is_closed:
            raise UpstreamError(FailureKind.CLOSED)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "identity",
        }
        if self._settings.bearer_token is not None:
            headers["Authorization"] = f"Bearer {self._settings.bearer_token}"
        request = httpx.Request("POST", self._url, content=inspected.raw_body, headers=headers)
        try:
            async with asyncio.timeout(self._settings.total_timeout):
                response = await self._client.send(
                    request, stream=True, auth=None, follow_redirects=False
                )
                try:
                    return await self._receive(response, inspected.request_id)
                finally:
                    await response.aclose()
        except (TimeoutError, httpx.TimeoutException):
            raise UpstreamError(FailureKind.TIMEOUT) from None
        except httpx.RequestError:
            raise UpstreamError(FailureKind.TRANSPORT) from None

    async def _receive(self, response: httpx.Response, request_id: RequestId) -> UpstreamResponse:
        if 300 <= response.status_code < 400:
            raise UpstreamError(FailureKind.REDIRECT)
        if not 200 <= response.status_code < 600:
            raise UpstreamError(FailureKind.INVALID_RESPONSE)
        types = response.headers.get_list("content-type")
        encodings = response.headers.get_list("content-encoding")
        if (
            len(types) != 1
            or types[0].split(";", 1)[0].strip().lower() != "application/json"
            or (encodings and (len(encodings) != 1 or encodings[0].strip().lower() != "identity"))
        ):
            raise UpstreamError(FailureKind.INVALID_RESPONSE)
        body = bytearray()
        if response.is_stream_consumed:
            if len(response.content) > self._settings.max_response_bytes:
                raise UpstreamError(FailureKind.RESPONSE_TOO_LARGE)
            body.extend(response.content)
        else:
            async for chunk in response.aiter_raw():
                if len(body) + len(chunk) > self._settings.max_response_bytes:
                    raise UpstreamError(FailureKind.RESPONSE_TOO_LARGE)
                body.extend(chunk)
        raw = bytes(body)
        _validate_response(raw, request_id)
        return UpstreamResponse(response.status_code, raw)
