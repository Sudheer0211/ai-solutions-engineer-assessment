"""T3-003 fixed-destination HTTPX streaming. StreamService owns bounded cleanup."""

import asyncio
import logging
import re
from collections.abc import AsyncIterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from http.cookiejar import CookieJar, DefaultCookiePolicy
from ipaddress import ip_address
from urllib.parse import urlsplit

import httpx

from task3_streaming.models import ErrorCode, StreamError

_PRIVATE_IO = ContextVar("task3_private_io", default=False)
_FILTER_INSTALLED = False
_CONTENT_TYPE = re.compile(r'text/event-stream(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?', re.I)


class _PrivateFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return not _PRIVATE_IO.get()


@contextmanager
def _private_io():
    token = _PRIVATE_IO.set(True)
    try:
        yield
    finally:
        _PRIVATE_IO.reset(token)


class _NoCookies(DefaultCookiePolicy):
    def set_ok(self, cookie, request) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class UpstreamSettings:
    url: str = field(repr=False)
    bearer_token: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        invalid = False
        try:
            if type(self.url) is not str or any(
                ord(c) <= 32 or ord(c) == 127 or c == "\\" for c in self.url
            ):
                raise ValueError
            url = httpx.URL(self.url)
            if (
                not url.is_absolute_url
                or not url.host
                or url.scheme not in {"http", "https"}
                or url.username
                or url.password
                or "@" in urlsplit(self.url).netloc
                or "?" in self.url
                or "#" in self.url
                or (url.port is not None and not 1 <= url.port <= 65535)
            ):
                raise ValueError
            if url.scheme == "http" and not ip_address(url.host).is_loopback:
                raise ValueError
            if self.bearer_token is not None and (
                type(self.bearer_token) is not str
                or not 1 <= len(self.bearer_token) <= 4096
                or not re.fullmatch(r"[A-Za-z0-9._~+/-]+=*", self.bearer_token)
            ):
                raise ValueError
        except (ValueError, TypeError, httpx.InvalidURL):
            invalid = True
        if invalid:
            raise ValueError("Invalid upstream configuration")


@dataclass(frozen=True, slots=True)
class UpstreamRequest:
    """Trusted caller's already formed request; no vendor/request schema is inferred."""

    body: bytes = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.body) is not bytes or not 1 <= len(self.body) <= 65536:
            raise StreamError(ErrorCode.LIMIT)


class UpstreamAdapter:
    def __init__(
        self, settings: UpstreamSettings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        if type(settings) is not UpstreamSettings:
            raise ValueError("Invalid upstream configuration")
        global _FILTER_INSTALLED
        if not _FILTER_INSTALLED:
            # HTTPX's INFO record includes an untrusted HTTP reason phrase. Scope
            # suppression to owned I/O; unrelated requests keep their logging.
            for name in ("httpx", "httpcore.connection", "httpcore.http11"):
                logging.getLogger(name).addFilter(_PrivateFilter())
            _FILTER_INSTALLED = True
        self._settings = settings
        self.quarantined = self.closed = self._closing = False
        limits = httpx.Limits(max_connections=16, max_keepalive_connections=16)
        self._client = httpx.AsyncClient(
            transport=transport
            or httpx.AsyncHTTPTransport(
                retries=0, http2=False, limits=limits, trust_env=False, verify=True
            ),
            timeout=httpx.Timeout(connect=5, pool=5, write=5, read=15),
            limits=limits,
            follow_redirects=False,
            trust_env=False,
            http2=False,
            cookies=CookieJar(policy=_NoCookies()),
        )

    @property
    def healthy(self) -> bool:
        return not (self.quarantined or self.closed or self._closing)

    def lease(self, request: UpstreamRequest) -> "UpstreamLease":
        if not self.healthy or type(request) is not UpstreamRequest:
            raise StreamError(ErrorCode.UNAVAILABLE)
        return UpstreamLease(self, request)

    async def aclose(self) -> None:
        self._closing = True
        with _private_io():
            await self._client.aclose()
        self.closed = True  # Only after actual asynchronous close succeeds.


class UpstreamLease:
    """One response/reader. Caller must retain this lease until aclose confirms."""

    def __init__(self, adapter: UpstreamAdapter, request: UpstreamRequest) -> None:
        self._adapter = adapter
        self._request = request
        self._response: httpx.Response | None = None
        self._iterator: AsyncIterator[bytes] | None = None
        self._buffer = b""
        self._offset = 0
        self.opened = self.closed = False
        self.raw_reads = self.raw_chunks = self.processing_chunks = self.peak_raw_bytes = 0

    async def open(self) -> None:
        if self.opened or self.closed:
            raise StreamError(ErrorCode.UNAVAILABLE)
        self.opened = True
        headers = {
            "accept": "text/event-stream",
            "accept-encoding": "identity",
            "content-type": "application/json",
        }
        if self._adapter._settings.bearer_token is not None:
            headers["authorization"] = "Bearer " + self._adapter._settings.bearer_token
        with _private_io():
            request = self._adapter._client.build_request(
                "POST", self._adapter._settings.url, headers=headers, content=self._request.body
            )
            self._response = await self._adapter._client.send(request, stream=True)
        self._request = None  # No replay/request-body retention after headers.
        response = self._response
        if response.status_code != 200:
            raise StreamError(ErrorCode.UPSTREAM)
        values = response.headers.get_list("content-type")
        if (
            len(values) != 1
            or len(values[0]) > 256
            or _CONTENT_TYPE.fullmatch(values[0].strip()) is None
            or "content-encoding" in response.headers
            or not isinstance(response.stream, httpx.AsyncByteStream)
        ):
            raise StreamError()
        # Public AsyncByteStream is raw and does not auto-close at EOF. Owning
        # response.aclose separately avoids an interrupted aiter_raw EOF close
        # falsely relying on HTTPX's early is_closed flag. No SDK monkeypatch.
        self._iterator = response.stream.__aiter__()

    async def read(self) -> bytes | None:
        if self.closed or self._iterator is None:
            raise StreamError(ErrorCode.UNAVAILABLE)
        while self._offset >= len(self._buffer):
            self._buffer = b""
            self._offset = 0
            self.raw_reads += 1
            with _private_io():
                try:
                    chunk = await anext(self._iterator)
                except StopAsyncIteration:
                    return None
            if type(chunk) is not bytes:
                raise StreamError()
            # Native pinned HTTP/1.1 httpcore reads <=64 KiB. Never coalesce
            # small events to 4 KiB (that can destroy progressive delivery).
            if len(chunk) > 65536:
                raise StreamError(ErrorCode.LIMIT)
            self.raw_chunks += 1
            self.peak_raw_bytes = max(self.peak_raw_bytes, len(chunk))
            self._buffer = chunk
            if not chunk:
                await asyncio.sleep(0)
        end = min(self._offset + 4096, len(self._buffer))
        piece = self._buffer[self._offset : end]
        self._offset = end
        self.processing_chunks += 1
        return piece

    async def aclose(self) -> None:
        self._buffer = b""
        self._offset = 0
        self._request = None
        with _private_io():
            if self._iterator is not None:
                closer = getattr(self._iterator, "aclose", None)
                if closer is not None:
                    await closer()
            if self._response is not None:
                await self._response.aclose()
        self.closed = True
        self._iterator = None
        self._response = None
