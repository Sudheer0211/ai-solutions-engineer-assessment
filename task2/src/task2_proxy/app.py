"""T2-004: bounded HTTP policy around the accepted guards and upstream adapter."""

import asyncio
import json
import math
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse, Response

from task2_proxy.rpc import UNAUTHORIZED_TOOL_CALL, RpcError
from task2_proxy.security import AuthenticationError, authenticate, guard_request
from task2_proxy.settings import ConfigurationError, SecuritySettings, load_settings
from task2_proxy.upstream import (
    FailureKind,
    UpstreamAdapter,
    UpstreamError,
    UpstreamSettings,
    load_upstream_settings,
)

_JSON_TYPE = re.compile(r'application/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?', re.I)
_SAFE_HEADERS = {"cache-control": "no-store", "x-content-type-options": "nosniff"}


class _HttpRejection(Exception):
    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


@dataclass(frozen=True, slots=True)
class _Runtime:
    security: SecuritySettings
    upstream: UpstreamSettings
    adapter: UpstreamAdapter


def _http_error(status: int, detail: str, *, headers: dict[str, str] | None = None) -> Response:
    return JSONResponse({"detail": detail}, status, headers={**_SAFE_HEADERS, **(headers or {})})


def _rpc_error(error: RpcError, status: int) -> Response:
    value = error.to_response()
    if value is None:
        return Response(status_code=status, headers=_SAFE_HEADERS)
    # ASCII escaping also preserves accepted string IDs containing surrogate escapes.
    return Response(
        json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii"),
        status_code=status,
        media_type="application/json",
        headers=_SAFE_HEADERS,
    )


def _http_metadata(request: Request, limit: int) -> int | None:
    types = request.headers.getlist("content-type")
    encodings = request.headers.getlist("content-encoding")
    lengths = request.headers.getlist("content-length")
    transfers = request.headers.getlist("transfer-encoding")
    if any(len(values) > 1 for values in (types, encodings, lengths, transfers)):
        raise _HttpRejection(400, "Ambiguous HTTP headers")
    if len(types) != 1 or _JSON_TYPE.fullmatch(types[0].strip()) is None:
        raise _HttpRejection(415, "Unsupported media type")
    if encodings and encodings[0].strip().lower() != "identity":
        raise _HttpRejection(415, "Unsupported content encoding")
    if transfers and (lengths or transfers[0].strip().lower() != "chunked"):
        raise _HttpRejection(400, "Invalid HTTP framing")
    if not lengths:
        return None
    length = lengths[0].strip(" \t")
    if re.fullmatch(r"[0-9]+", length) is None:
        raise _HttpRejection(400, "Invalid Content-Length")
    normalized = length.lstrip("0") or "0"
    maximum = str(limit)
    if len(normalized) > len(maximum) or (len(normalized) == len(maximum) and normalized > maximum):
        raise _HttpRejection(413, "Request body too large")
    return int(normalized)


async def _read_body(request: Request, limit: int, declared: int | None, timeout: float) -> bytes:
    body = bytearray()
    try:
        async with asyncio.timeout(timeout):
            async for chunk in request.stream():
                if len(body) + len(chunk) > limit:
                    raise _HttpRejection(413, "Request body too large")
                body.extend(chunk)
    except TimeoutError:
        raise _HttpRejection(408, "Request body timeout") from None
    except ClientDisconnect:
        raise _HttpRejection(400, "Incomplete request body") from None
    if declared is not None and len(body) != declared:
        raise _HttpRejection(400, "Content-Length mismatch")
    return bytes(body)


def create_app(
    security_settings: SecuritySettings | None = None,
    upstream_settings: UpstreamSettings | None = None,
    *,
    upstream_transport: httpx.AsyncBaseTransport | None = None,
    body_timeout: float = 10.0,
) -> FastAPI:
    """Create an app without loading secrets or opening a client until lifespan startup."""
    try:
        if (
            type(body_timeout) not in (int, float)
            or not math.isfinite(body_timeout)
            or body_timeout <= 0
            or (security_settings is not None and type(security_settings) is not SecuritySettings)
            or (upstream_settings is not None and type(upstream_settings) is not UpstreamSettings)
        ):
            raise ValueError
    except (ValueError, OverflowError):
        raise ConfigurationError("Invalid HTTP application configuration") from None
    runtime: _Runtime | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        nonlocal runtime
        if runtime is not None:
            raise ConfigurationError("Application lifespan already started")
        security = security_settings if security_settings is not None else load_settings()
        upstream = upstream_settings if upstream_settings is not None else load_upstream_settings()
        async with UpstreamAdapter(upstream, transport=upstream_transport) as adapter:
            runtime = _Runtime(security, upstream, adapter)
            try:
                yield
            finally:
                runtime = None

    app = FastAPI(
        lifespan=lifespan,
        debug=False,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
    )

    @app.exception_handler(HTTPException)
    async def http_exception(request: Request, exc: HTTPException) -> Response:
        if exc.status_code == 405:
            return _http_error(405, "Method Not Allowed", headers={"allow": "POST"})
        return _http_error(404, "Not Found")

    @app.post("/mcp")
    async def mcp(request: Request) -> Response:
        current = runtime
        if current is None:
            return _http_error(503, "Service unavailable")
        permit = None
        try:
            declared = _http_metadata(request, current.upstream.max_request_bytes)
            header_values = request.headers.getlist("authorization")
            try:
                authenticate(header_values, current.security)
            except AuthenticationError:
                return _http_error(
                    401,
                    "Invalid Bearer credentials",
                    headers={"www-authenticate": 'Bearer realm="mcp"'},
                )
            raw = await _read_body(
                request, current.upstream.max_request_bytes, declared, body_timeout
            )
            try:
                # The accepted guard rechecks the same immutable credentials and issues the permit.
                permit = guard_request(header_values, raw, current.security)
            except AuthenticationError:
                return _http_error(
                    401,
                    "Invalid Bearer credentials",
                    headers={"www-authenticate": 'Bearer realm="mcp"'},
                )
            except RpcError as exc:
                return _rpc_error(exc, 403 if exc.code == UNAUTHORIZED_TOOL_CALL else 400)
            try:
                upstream = await current.adapter.forward(permit)
            except UpstreamError as exc:
                if exc.kind is FailureKind.TIMEOUT:
                    status, message = 504, "Upstream timeout"
                elif exc.kind is FailureKind.CLOSED:
                    status, message = 503, "Upstream unavailable"
                elif exc.kind is FailureKind.REQUEST_TOO_LARGE:
                    status, message = 413, "Request body too large"
                else:
                    status, message = 502, "Upstream request failed"
                return _rpc_error(RpcError(-32603, message, permit.request.request_id), status)
            return Response(
                upstream.body,
                upstream.status_code,
                headers={**dict(upstream.headers), "x-content-type-options": "nosniff"},
            )
        except _HttpRejection as exc:
            return _http_error(exc.status, exc.detail)
        except Exception:
            # Deliberately do not log exception text/tracebacks or raw request material.
            if permit is not None:
                return _rpc_error(
                    RpcError(-32603, "Internal error", permit.request.request_id), 500
                )
            return _http_error(500, "Internal Server Error")

    return app
