"""T4-005: authenticated nonstreaming HTTP boundary around accepted orchestration."""

import asyncio
import json
import re
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

from task4_limiter.models import BoundsUnavailable
from task4_limiter.providers import Provider
from task4_limiter.service import LLMService, MonotonicClock
from task4_limiter.settings import (
    AuthenticationError,
    ConfigurationError,
    HTTPSettings,
    load_settings,
)
from task4_limiter.storage import SQLiteStore

ProviderResources = Callable[[], AbstractAsyncContextManager[tuple[Provider, Provider]]]
_JSON = re.compile(r'application/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?', re.I)
_SAFE = {"cache-control": "no-store", "x-content-type-options": "nosniff"}
_STATUS = {
    "invalid_request": 400,
    "invalid_credentials": 401,
    "tenant_quota_exceeded": 429,
    "provider_rate_limited": 429,
    "model_timeout": 504,
    "model_unavailable": 502,
    "service_unavailable": 503,
}


class GenerateRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", hide_input_in_errors=True)
    prompt: str = Field(min_length=1, max_length=16_000, repr=False)


class _Rejected(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message


@dataclass
class _UTC:
    def now_ms(self) -> int:
        return time.time_ns() // 1_000_000


class _UnconfiguredProvider:
    model_id = "unconfigured"
    counter_id = "unconfigured"

    def prepare(self, text: str):
        raise BoundsUnavailable()


@asynccontextmanager
async def _unconfigured() -> AsyncIterator[tuple[Provider, Provider]]:
    # Safe launch without pretending to support a vendor/tokenizer/output cap.
    yield _UnconfiguredProvider(), _UnconfiguredProvider()


def _error(rid: UUID, status: int, code: str, message: str, **extra: str) -> JSONResponse:
    headers = {**_SAFE, "x-request-id": str(rid), **extra}
    if status == 401:
        headers["www-authenticate"] = 'Bearer realm="task4"'
    return JSONResponse(
        {"error": {"code": code, "message": message, "request_id": str(rid)}},
        status_code=status,
        headers=headers,
    )


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for name, value in items:
        if name in result:
            raise ValueError
        result[name] = value
    return result


def _constant(value: str) -> None:
    raise ValueError


async def _body(request: Request, settings: HTTPSettings) -> bytes:
    types = request.headers.getlist("content-type")
    encodings = request.headers.getlist("content-encoding")
    lengths = request.headers.getlist("content-length")
    transfers = request.headers.getlist("transfer-encoding")
    if len(types) != 1 or not _JSON.fullmatch(types[0]):
        raise _Rejected(415, "unsupported_media_type", "Unsupported media type")
    if encodings:
        raise _Rejected(415, "unsupported_content_encoding", "Unsupported content encoding")
    if (
        len(lengths) > 1
        or len(transfers) > 1
        or (lengths and transfers)
        or (transfers and transfers[0].lower() != "chunked")
    ):
        raise _Rejected(400, "invalid_request", "Invalid request")
    declared = None
    if lengths:
        if not re.fullmatch(r"[0-9]{1,10}", lengths[0]):
            raise _Rejected(400, "invalid_request", "Invalid request")
        declared = int(lengths[0])
        if declared > settings.max_body_bytes:
            raise _Rejected(413, "request_too_large", "Request body too large")
    result = bytearray()
    try:
        async with asyncio.timeout(settings.body_timeout_ms / 1000):
            async for chunk in request.stream():
                if len(result) + len(chunk) > settings.max_body_bytes:
                    raise _Rejected(413, "request_too_large", "Request body too large")
                result.extend(chunk)
    except TimeoutError:
        raise _Rejected(408, "request_timeout", "Request body timed out") from None
    if declared is not None and len(result) != declared:
        raise _Rejected(400, "invalid_request", "Invalid request")
    return bytes(result)


async def _disconnect(request: Request) -> None:
    # Body reader is finished before this single receive consumer starts.
    while True:
        if (await request.receive())["type"] == "http.disconnect":
            return


async def _generate(request: Request, service: LLMService, key: bytes, prompt: str, rid: UUID):
    call = asyncio.create_task(service.generate(key, prompt, request_id=rid))
    gone = asyncio.create_task(_disconnect(request))
    try:
        await asyncio.wait({call, gone}, return_when=asyncio.FIRST_COMPLETED)
        if gone.done():
            raise ClientDisconnect()
        return call.result()
    finally:
        call.cancel()
        gone.cancel()
        await asyncio.gather(call, gone, return_exceptions=True)


async def _open_store(settings: HTTPSettings, clock) -> SQLiteStore:
    worker = asyncio.create_task(asyncio.to_thread(SQLiteStore, settings.storage, clock=clock))
    try:
        return await asyncio.shield(worker)
    except asyncio.CancelledError:
        # Cancellation cannot tell whether initialization committed. Discover and
        # close the actual result, including repeated startup cancellation.
        while not worker.done():
            try:
                await asyncio.shield(worker)
            except asyncio.CancelledError:
                pass
        if not worker.cancelled() and worker.exception() is None:
            worker.result().close()
        raise


def create_app(
    settings: HTTPSettings | None = None,
    *,
    provider_resources: ProviderResources | None = None,
    accounting_clock=None,
    monotonic_clock: MonotonicClock | None = None,
) -> FastAPI:
    """Only trusted Python deployment code injects adapters; no URL/client override."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        stack = AsyncExitStack()
        store = None
        service = None
        try:
            current = settings if settings is not None else load_settings()
            store = await _open_store(current, accounting_clock or _UTC())
            primary, backup = await stack.enter_async_context(
                (provider_resources or _unconfigured)()
            )
            service = LLMService(store, primary, backup, current.routing, clock=monotonic_clock)
            app.state.settings, app.state.store, app.state.service = current, store, service
            app.state.accepting = True
            yield
        except asyncio.CancelledError:
            raise
        except Exception:
            raise ConfigurationError() from None
        finally:
            app.state.accepting = False

            async def cleanup():
                clean = service is None or await service.aclose()
                if clean:
                    try:
                        await stack.aclose()
                    except Exception:
                        raise ConfigurationError() from None
                    finally:
                        if store is not None:
                            store.close()  # Flag only; all DB work is already drained.
                else:
                    # Keep ownership; never close a pool under an owned attempt.
                    app.state.quarantined_resources = (stack, store, service)
                    raise RuntimeError("Task 4 shutdown incomplete") from None

            app.state.shutdown_task = asyncio.create_task(cleanup())
            try:
                await asyncio.shield(app.state.shutdown_task)
            except asyncio.CancelledError:
                while not app.state.shutdown_task.done():
                    try:
                        await asyncio.shield(app.state.shutdown_task)
                    except asyncio.CancelledError:
                        pass
                app.state.shutdown_task.result()
                raise

    app = FastAPI(
        lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None, redirect_slashes=False
    )
    app.state.accepting = False

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        message = "Method not allowed" if exc.status_code == 405 else "Not found"
        extra = {"allow": "POST"} if exc.status_code == 405 else {}
        return _error(uuid4(), exc.status_code, "invalid_request", message, **extra)

    @app.post("/generate")
    async def generate(request: Request):
        rid = uuid4()
        try:
            if not app.state.accepting:
                return _error(rid, 503, "service_unavailable", "Service unavailable")
            current = app.state.settings
            try:
                key = current.credentials.authenticate(request.headers.getlist("authorization"))
            except AuthenticationError:
                return _error(rid, 401, "invalid_credentials", "Invalid credentials")
            raw = await _body(request, current)
            try:
                data = json.loads(
                    raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant
                )
                value = GenerateRequest.model_validate(data)
                value.prompt.encode("utf-8")  # Reject unpaired surrogate input before accounting.
            except (ValueError, UnicodeError, ValidationError, RecursionError):
                return _error(rid, 400, "invalid_request", "Invalid request")
            outcome = await _generate(request, app.state.service, key, value.prompt, rid)
            if outcome.code is not None:
                return _error(rid, _STATUS[outcome.code], outcome.code, outcome.message)
            return JSONResponse(
                {
                    "request_id": str(rid),
                    "result": {"text": outcome.text, "used_backup": outcome.used_backup},
                },
                headers={**_SAFE, "x-request-id": str(rid)},
            )
        except _Rejected as exc:
            return _error(rid, exc.status, exc.code, exc.message, connection="close")
        except ClientDisconnect:
            return _error(rid, 499, "client_disconnected", "Client disconnected")
        except Exception:
            return _error(rid, 503, "service_unavailable", "Service unavailable")

    return app
