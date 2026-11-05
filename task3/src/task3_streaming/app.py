"""T3-004 strict synthetic HTTP boundary and owned, deadline-bound ASGI sends."""

import asyncio
import json
import re
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, Response
from starlette.types import Message, Receive, Scope, Send

from task3_streaming.models import MESSAGES, ErrorCode, StreamError
from task3_streaming.service import Capacity, CapacityExceeded, Clock, LoopClock, StreamService
from task3_streaming.settings import HTTPSettings, authenticated, load_settings
from task3_streaming.upstream import UpstreamAdapter, UpstreamRequest

_HTTP_CAPACITY = Capacity()  # Includes blocked terminal sends after upstream releases its slot.
_SAFE = {"cache-control": "no-store", "x-content-type-options": "nosniff"}
_JSON_TYPE = re.compile(rb'application/json(?:\s*;\s*charset\s*=\s*(?:utf-8|"utf-8"))?', re.I)
_STATUS = {
    ErrorCode.INVALID: 502,
    ErrorCode.UPSTREAM: 502,
    ErrorCode.LIMIT: 502,
    ErrorCode.TIMEOUT: 504,
    ErrorCode.UNAVAILABLE: 503,
}


class _Reject(Exception):
    def __init__(self, status: int, code: str, message: str) -> None:
        self.status, self.code, self.message = status, code, message


class _Gone(Exception):
    pass


class _Stopped(Exception):
    pass


class _SendFailed(Exception):
    pass


def _json(status: int, code: str, message: str) -> JSONResponse:
    headers = dict(_SAFE)
    if status == 401:
        headers["www-authenticate"] = 'Bearer realm="task3"'
    return JSONResponse({"error": {"code": code, "message": message}}, status, headers)


def _headers(scope: Scope, name: bytes) -> list[bytes]:
    return [v for k, v in scope["headers"] if k.lower() == name]


def _metadata(scope: Scope) -> int | None:
    if scope.get("query_string"):
        raise _Reject(400, "invalid_request", "Invalid request")
    media, enc, lengths, transfers = (
        _headers(scope, k)
        for k in (b"content-type", b"content-encoding", b"content-length", b"transfer-encoding")
    )
    if any(len(v) > 1 for v in (media, enc, lengths, transfers)):
        raise _Reject(400, "invalid_request", "Invalid request")
    if len(media) != 1 or _JSON_TYPE.fullmatch(media[0].strip()) is None or enc:
        raise _Reject(415, "unsupported_media", "Unsupported media type or encoding")
    if transfers and (lengths or transfers[0].lower() != b"chunked"):
        raise _Reject(400, "invalid_request", "Invalid request")
    if not lengths:
        return None
    if re.fullmatch(rb"[0-9]{1,10}", lengths[0]) is None:
        raise _Reject(400, "invalid_request", "Invalid request")
    size = int(lengths[0])
    if size > 16384:
        raise _Reject(413, "request_too_large", "Request body too large")
    return size


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError
        result[key] = value
    return result


def _number(value):
    raise ValueError  # No numeric value occurs in the exact prompt-only schema.


def _inspect(raw: bytes) -> UpstreamRequest:
    value, invalid = None, False
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_number,
            parse_int=_number,
            parse_float=_number,
        )
    except (ValueError, RecursionError):
        invalid = True
    if (
        invalid
        or type(value) is not dict
        or set(value) != {"prompt"}
        or type(value["prompt"]) is not str
        or not 1 <= len(value["prompt"]) <= 4096
        or any(0xD800 <= ord(c) <= 0xDFFF for c in value["prompt"])
    ):
        raise _Reject(400, "invalid_request", "Invalid request")
    return UpstreamRequest(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def _consume(task: asyncio.Task) -> None:
    if not task.cancelled():
        task.exception()  # Never emit unhandled task exceptions with private diagnostics.


async def _within(task: asyncio.Task, deadline: float, clock: Clock) -> bool:
    timer = asyncio.create_task(clock.wait_until(deadline))
    try:
        await asyncio.wait({task, timer}, return_when=asyncio.FIRST_COMPLETED)
        return task.done() and clock.now() <= deadline
    finally:
        timer.cancel()
        await asyncio.gather(timer, return_exceptions=True)


async def _body(request: Request, declared: int | None, clock: Clock) -> bytes:
    data = bytearray()
    deadline = clock.now() + 10
    while True:
        task = asyncio.create_task(request.receive())
        try:
            # ASGI receive is the server-owned, cancellation-cooperative body interface.
            if not await _within(task, deadline, clock) or clock.now() >= deadline:
                raise _Reject(408, "request_timeout", "Request body timed out")
            message = task.result()
        finally:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        if message["type"] == "http.disconnect":
            raise _Gone()
        if message["type"] != "http.request" or type(message.get("body", b"")) is not bytes:
            raise _Reject(400, "invalid_request", "Invalid request")
        chunk = message.get("body", b"")
        if len(data) + len(chunk) > 16384:
            raise _Reject(413, "request_too_large", "Request body too large")
        data.extend(chunk)
        if not message.get("more_body", False):
            break
        await asyncio.sleep(0)
    if declared is not None and len(data) != declared:
        raise _Reject(400, "invalid_request", "Invalid request")
    return bytes(data)


class _Runtime:
    def __init__(self, settings: HTTPSettings, service: StreamService) -> None:
        self.settings, self.service, self.clock = settings, service, service.clock
        self.stopped = asyncio.Event()
        self.owners: set[_Exchange] = set()
        self.shutdown: asyncio.Task[bool] | None = None

    async def aclose(self) -> bool:
        self.stopped.set()  # Synchronous admission barrier before first await.
        if self.shutdown is None or self.shutdown.done():
            self.shutdown = asyncio.create_task(self._close())
            self.shutdown.add_done_callback(_consume)
        return await asyncio.shield(self.shutdown)

    async def _close(self) -> bool:
        if self.owners:
            await asyncio.gather(*(o.aclose() for o in tuple(self.owners)))
        if self.owners:
            return False  # Retain both HTTP and service owners; no shared-pool close.
        return await self.service.aclose()


class _Exchange:
    """One ASGI reader, one operation/send, retained worker for uncertain cleanup."""

    def __init__(self, runtime: _Runtime, request: UpstreamRequest, receive: Receive, send: Send):
        self.runtime, self.clock, self.send = runtime, runtime.clock, send
        self.session = runtime.service.stream(request)
        self.gone = asyncio.create_task(self._listen(receive))
        self.stop = asyncio.create_task(runtime.stopped.wait())
        self.gone.add_done_callback(_consume)
        self.stop.add_done_callback(_consume)
        self.operation: asyncio.Task | None = None
        self.cleanup: asyncio.Task[bool] | None = None
        self.work: asyncio.Task | None = None
        self.session_close: asyncio.Task | None = None
        self.cleanup_deadline = self.send_deadline = 0.0
        self.started = self.disconnected = self.send_failed = self.success = False
        self.released = False

    async def _listen(self, receive: Receive) -> None:
        # Called only AFTER the final http.request; never races the request reader.
        while True:
            message = await receive()
            if message["type"] != "http.request" or message.get("body"):
                return  # Disconnect/invalid extra body: fail closed.
            await asyncio.sleep(0)

    async def _call(self, operation: Awaitable, deadline: float | None = None):
        self.operation = asyncio.create_task(operation)
        self.operation.add_done_callback(_consume)
        timer = None if deadline is None else asyncio.create_task(self.clock.wait_until(deadline))
        waits = {self.operation, self.gone, self.stop}
        if timer is not None:
            waits.add(timer)
        try:
            await asyncio.wait(waits, return_when=asyncio.FIRST_COMPLETED)
            if self.gone.done():
                self.disconnected = True
                raise _Gone()
            if self.stop.done():
                raise _Stopped()
            if deadline is not None and self.clock.now() >= deadline:
                raise _SendFailed()
            if not self.operation.done():
                raise _SendFailed()
            return self.operation.result()
        finally:
            if timer is not None:
                timer.cancel()
                await asyncio.gather(timer, return_exceptions=True)

    async def _send(self, message: Message, *, renew: bool = True) -> None:
        if renew:
            overall = self.session.deadline or (self.clock.now() + 120)
            self.send_deadline = min(self.clock.now() + 10, overall)
        if self.disconnected or self.send_failed or self.clock.now() >= self.send_deadline:
            raise _SendFailed()
        try:
            await self._call(self.send(message), self.send_deadline)
        except (_Gone, _Stopped, asyncio.CancelledError):
            raise
        except Exception:
            self.send_failed = True
            raise _SendFailed() from None

    async def _report(self, code: ErrorCode, *, capacity: bool = False) -> None:
        try:
            if self.started:
                # No new error-send allowance or locally encoded event bypass.
                await self._send({"type": "http.response.body", "body": b""}, renew=False)
            else:
                response = (
                    _json(429, "stream_capacity_exceeded", "Stream capacity exceeded")
                    if capacity
                    else _json(_STATUS[code], code.value, MESSAGES[code])
                )
                self.started = True  # A failed/uncertain response.start is never retried.
                await self._send(
                    {
                        "type": "http.response.start",
                        "status": response.status_code,
                        "headers": response.raw_headers,
                    }
                )
                await self._send({"type": "http.response.body", "body": response.body})
        except (_Gone, _Stopped, _SendFailed):
            pass

    async def run(self) -> None:
        delivered = False
        try:
            # Give the sole post-body receiver a chance to observe a queued disconnect.
            await asyncio.sleep(0)
            if self.gone.done():
                self.disconnected = True
                raise _Gone()
            if self.stop.done():
                raise _Stopped()
            await self._call(self.session.__aenter__())  # Admission/header preflight only.
            self.started = True
            await self._send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"text/event-stream; charset=utf-8"),
                        (b"cache-control", b"no-store"),
                        (b"x-content-type-options", b"nosniff"),
                    ],
                }
            )
            while True:
                try:
                    frame = await self._call(anext(self.session))
                except StopAsyncIteration:
                    break
                await self._send({"type": "http.response.body", "body": frame, "more_body": True})
            await self._send({"type": "http.response.body", "body": b""})
            delivered = self.session.completed
        except asyncio.CancelledError:
            raise
        except (_Gone, _Stopped, _SendFailed):
            pass  # Never write to an absent/stalled peer or resume after shutdown.
        except CapacityExceeded:
            await self._report(ErrorCode.UNAVAILABLE, capacity=True)
        except StreamError as exc:
            await self._report(exc.code)
        except Exception:
            await self._report(ErrorCode.UNAVAILABLE)
        finally:
            clean = await self.aclose()
            self.success = delivered and clean

    def _confirmed(self) -> bool:
        close = self.session_close
        return (
            self.work is not None
            and self.work.done()
            and all(t.done() for t in (self.gone, self.stop, self.operation) if t is not None)
            and close is not None
            and close.done()
            and not close.cancelled()
            and close.exception() is None
            and (close.result() or self.session.cleaned)
        )

    def _release(self) -> None:
        if not self.released and self._confirmed():
            self.released = True
            self.runtime.owners.discard(self)
            _HTTP_CAPACITY.release()

    async def aclose(self) -> bool:
        if self._confirmed():
            self._release()
            return True
        if self.cleanup is None:
            self.cleanup_deadline = (
                min(self.clock.now() + 1, self.session.deadline + 1)
                if self.session.deadline
                else self.clock.now() + 1
            )
            self.session_close = asyncio.create_task(self.session.aclose())
            self.session_close.add_done_callback(_consume)
            self.work = asyncio.create_task(self._close_work())
            self.work.add_done_callback(lambda task: (self._release(), _consume(task)))
            self.cleanup = asyncio.create_task(self._guard())
            self.cleanup.add_done_callback(_consume)
        return await asyncio.shield(self.cleanup)

    async def _close_work(self) -> None:
        tasks = [t for t in (self.operation, self.gone, self.stop) if t is not None]
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, self.session_close, return_exceptions=True)

    async def _guard(self) -> bool:
        finished = await _within(self.work, self.cleanup_deadline, self.clock)
        self._release()
        if not finished or not self.released:
            self.runtime.service.adapter.quarantined = True
            return False
        return True


class _StreamResponse(Response):
    def __init__(self, runtime: _Runtime, request: UpstreamRequest) -> None:
        super().__init__()
        self.runtime, self.upstream_request = runtime, request

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        rt = self.runtime
        if rt.stopped.is_set() or not rt.service.adapter.healthy:
            await _json(503, "service_unavailable", "Service unavailable")(scope, receive, send)
            return
        try:
            _HTTP_CAPACITY.acquire()
        except CapacityExceeded:
            await _json(429, "stream_capacity_exceeded", "Stream capacity exceeded")(
                scope, receive, send
            )
            return
        owner = _Exchange(rt, self.upstream_request, receive, send)
        self.upstream_request = None
        rt.owners.add(owner)
        await owner.run()


def create_app(
    settings: HTTPSettings | None = None,
    *,
    upstream_transport: httpx.AsyncBaseTransport | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    """No secret loading/client creation until startup. Injected transports are trusted."""
    if settings is not None and type(settings) is not HTTPSettings:
        raise ValueError("Invalid HTTP configuration")
    http_clock = clock or LoopClock()
    runtime: _Runtime | None = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        nonlocal runtime
        if runtime is not None:
            raise ValueError("Application lifespan already started")
        configured = settings if settings is not None else load_settings()
        adapter = UpstreamAdapter(configured.upstream, transport=upstream_transport)
        runtime = _Runtime(configured, StreamService(adapter, clock=http_clock))
        app.state.runtime = runtime  # Retained even when shutdown/caller cleanup is uncertain.
        try:
            yield
        finally:
            # Remain explicitly unclean if the lifespan waiter is cancelled mid-close.
            app.state.unclean_shutdown = True
            app.state.unclean_shutdown = not await runtime.aclose()
            if app.state.unclean_shutdown:
                raise RuntimeError("Unclean streaming shutdown")

    app = FastAPI(
        lifespan=lifespan,
        debug=False,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        redirect_slashes=False,
    )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> Response:
        if exc.status_code == 405:
            response = _json(405, "method_not_allowed", "Method not allowed")
            response.headers["allow"] = "POST"
            return response
        return _json(404, "not_found", "Not found")

    @app.post("/stream")
    async def stream(request: Request) -> Response:
        rt = runtime
        if rt is None or rt.stopped.is_set() or not rt.service.adapter.healthy:
            return _json(503, "service_unavailable", "Service unavailable")
        if not authenticated(_headers(request.scope, b"authorization"), rt.settings):
            return _json(401, "invalid_credentials", "Invalid credentials")
        try:
            declared = _metadata(request.scope)
            raw = await _body(request, declared, rt.clock)
            return _StreamResponse(rt, _inspect(raw))
        except _Reject as exc:
            return _json(exc.status, exc.code, exc.message)
        except _Gone:
            return _SilentResponse()
        except Exception:
            return _json(400, "invalid_request", "Invalid request")

    return app


class _SilentResponse(Response):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        pass  # Confirmed disconnect while receiving the request: no response writes.
