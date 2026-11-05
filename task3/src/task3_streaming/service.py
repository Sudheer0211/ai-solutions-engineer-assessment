"""T3-003 owned async pull sessions; no HTTP endpoint or downstream socket claim."""

import asyncio
import threading
from collections.abc import Awaitable, Iterator
from typing import Protocol

import httpx

from task3_streaming.models import ErrorCode, StreamError
from task3_streaming.redaction import Processor
from task3_streaming.upstream import UpstreamAdapter, UpstreamRequest


class Clock(Protocol):
    def now(self) -> float: ...

    async def wait_until(self, deadline: float) -> None: ...


class LoopClock:
    def now(self) -> float:
        return asyncio.get_running_loop().time()

    async def wait_until(self, deadline: float) -> None:
        await asyncio.sleep(max(0, deadline - self.now()))


class CapacityExceeded(Exception):
    code = "stream_capacity_exceeded"

    def __init__(self) -> None:
        super().__init__("Stream capacity exceeded")


class Capacity:
    """No admission queue; default instance is shared across services/event loops."""

    def __init__(self, maximum: int = 16) -> None:
        if type(maximum) is not int or not 1 <= maximum <= 16:
            raise ValueError("Invalid stream capacity")
        self._maximum = maximum
        self._active = 0
        self._lock = threading.Lock()

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    def acquire(self) -> None:
        with self._lock:
            if self._active >= self._maximum:
                raise CapacityExceeded()
            self._active += 1

    def release(self) -> None:
        with self._lock:
            self._active -= 1


_PROCESS_CAPACITY = Capacity()


def _consume_failure(task: asyncio.Task) -> None:
    if not task.cancelled():
        task.exception()  # No raw exceptions in unhandled-task diagnostics.


async def _before[T](
    task: asyncio.Task[T], deadline: float, clock: Clock, *, inclusive: bool = False
) -> bool:
    timer = asyncio.create_task(clock.wait_until(deadline))
    try:
        await asyncio.wait({task, timer}, return_when=asyncio.FIRST_COMPLETED)
        now = clock.now()
        return task.done() and (now <= deadline if inclusive else now < deadline)
    finally:
        timer.cancel()
        await asyncio.gather(timer, return_exceptions=True)


class StreamService:
    def __init__(
        self,
        adapter: UpstreamAdapter,
        *,
        clock: Clock | None = None,
    ) -> None:
        self.adapter = adapter
        self.clock = clock or LoopClock()
        self.capacity = _PROCESS_CAPACITY
        self._owners: set[StreamSession] = set()
        self._closing = False
        self._shutdown: asyncio.Task[bool] | None = None
        self._pool_close: asyncio.Task | None = None
        self._pool_deadline = 0.0

    @property
    def active(self) -> int:
        return len(self._owners)

    def stream(self, request: UpstreamRequest) -> "StreamSession":
        if type(request) is not UpstreamRequest:
            raise StreamError()
        return StreamSession(self, request)

    async def aclose(self) -> bool:
        self._closing = True
        if self.adapter.closed and not self._owners:
            return True
        if self._shutdown is None or (
            self._shutdown.done() and not self._owners and self._pool_close is None
        ):
            self._shutdown = asyncio.create_task(self._close())
            self._shutdown.add_done_callback(_consume_failure)
        return await asyncio.shield(self._shutdown)

    async def _close(self) -> bool:
        if self._owners:
            await asyncio.gather(*(s.aclose() for s in tuple(self._owners)))
        if self._owners:
            return False  # Never close shared pool beneath uncertain response ownership.
        if self._pool_close is None:
            self._pool_deadline = self.clock.now() + 1
            self._pool_close = asyncio.create_task(self.adapter.aclose())
            self._pool_close.add_done_callback(_consume_failure)
        if not await _before(self._pool_close, self._pool_deadline, self.clock, inclusive=True):
            self.adapter.quarantined = True
            return False
        try:
            self._pool_close.result()
        except (Exception, asyncio.CancelledError):
            self.adapter.quarantined = True
            return False
        return self.adapter.closed


class StreamSession:
    """Use async with; one anext at a time. aclose never discards its owned worker."""

    def __init__(self, service: StreamService, request: UpstreamRequest) -> None:
        self.service = service
        self._request = request
        self.processor = Processor()
        self.lease = None
        self.deadline = self._first_deadline = 0.0
        self._entered = self._pulling = self._stopping = False
        self._first_seen = self.completed = self.cleaned = False
        self._first_event = asyncio.Event()
        self.failure: ErrorCode | None = None
        self._pending: Iterator[bytes] | None = None
        self._operation: asyncio.Task | None = None
        self._watchdog: asyncio.Task | None = None
        self._cleanup: asyncio.Task[bool] | None = None
        self._cleanup_work: asyncio.Task | None = None
        self._cleanup_deadline = 0.0

    async def __aenter__(self) -> "StreamSession":
        if self._entered or self.service._closing or not self.service.adapter.healthy:
            raise StreamError(ErrorCode.UNAVAILABLE)
        self.service.capacity.acquire()  # Synchronous/atomic, before any await/send.
        self._entered = True
        self.service._owners.add(self)
        self.deadline = self.service.clock.now() + 120
        self._first_deadline = self.service.clock.now() + 15
        self._watchdog = asyncio.create_task(self._watch())
        self._watchdog.add_done_callback(_consume_failure)
        try:
            self.lease = self.service.adapter.lease(self._request)
            self._request = None
            await self._run(self.lease.open(), min(self.deadline, self._first_deadline))
            return self
        except asyncio.CancelledError:
            self._start_close()
            await asyncio.shield(self._cleanup)
            raise
        except Exception as exc:
            code = self._code(exc)
            self.failure = code
            await self.aclose()
        raise StreamError(self.failure)

    async def __aexit__(self, kind, value, traceback) -> None:
        if not await self.aclose() and kind is None:
            raise StreamError(ErrorCode.UNAVAILABLE)

    def __aiter__(self) -> "StreamSession":
        return self

    @staticmethod
    def _code(exc: Exception) -> ErrorCode:
        if isinstance(exc, StreamError):
            return exc.code
        if isinstance(exc, httpx.TimeoutException):
            return ErrorCode.TIMEOUT
        return ErrorCode.UPSTREAM

    async def _run[T](self, operation: Awaitable[T], deadline: float) -> T:
        self._operation = asyncio.create_task(operation)
        self._operation.add_done_callback(_consume_failure)
        if not await _before(self._operation, deadline, self.service.clock):
            raise StreamError(ErrorCode.TIMEOUT)
        if self._operation.cancelled() and not asyncio.current_task().cancelling():
            raise StreamError(self.failure or ErrorCode.UNAVAILABLE)
        return self._operation.result()

    def _check(self) -> None:
        if self.failure is not None:
            raise StreamError(self.failure)
        now = self.service.clock.now()
        if now >= self.deadline or (not self._first_seen and now >= self._first_deadline):
            raise StreamError(ErrorCode.TIMEOUT)
        if self._stopping:
            raise StreamError(ErrorCode.UNAVAILABLE)

    def _observe(self) -> None:
        if self.processor.redactor.stats.channels or self.processor.redactor.terminal:
            self._first_seen = True
            self._first_event.set()

    async def __anext__(self) -> bytes:
        if not self._entered or self._pulling:
            raise StreamError(ErrorCode.UNAVAILABLE)
        if self.failure is not None:
            raise StreamError(self.failure)
        if self._stopping:
            raise StopAsyncIteration
        self._pulling = True
        error = None
        try:
            while True:
                await asyncio.sleep(0)  # Bounded cooperative redaction checkpoint.
                self._check()
                if self._pending is not None:
                    try:
                        frame = next(self._pending)
                    except StopIteration:
                        self._pending = None
                        self._check()
                        self._observe()
                        continue
                    self._check()
                    self._observe()
                    if self.processor.redactor.terminal:
                        # Exhaust the accepted terminal iterator normally; closing it
                        # mid-yield intentionally revokes pure success (T3-002).
                        try:
                            next(self._pending)
                        except StopIteration:
                            self._pending = None
                        else:
                            raise StreamError()
                        success = self.processor.redactor.success
                        if not await self.aclose():
                            raise StreamError(ErrorCode.UNAVAILABLE)
                        self.completed = success
                    return frame
                now = self.service.clock.now()
                deadline = min(self.deadline, now + 15)
                if not self._first_seen:
                    deadline = min(deadline, self._first_deadline)
                chunk = await self._run(self.lease.read(), deadline)
                self._pending = (
                    self.processor.finish() if chunk is None else self.processor.feed(chunk)
                )
        except asyncio.CancelledError:
            self._start_close()
            await asyncio.shield(self._cleanup)
            raise
        except Exception as exc:
            error = self._code(exc)
            self.failure = error
            await self.aclose()
        finally:
            self._pulling = False
        raise StreamError(error)

    async def _watch(self) -> None:
        signal = asyncio.create_task(self._first_event.wait())
        try:
            await _before(signal, self._first_deadline, self.service.clock)
        finally:
            signal.cancel()
            await asyncio.gather(signal, return_exceptions=True)
        # _observe already checked the deadline synchronously. A delayed timer
        # observer must not reclassify an event accepted before that deadline.
        if not self._first_seen and not self._stopping:
            self.failure = ErrorCode.TIMEOUT
            self._start_close()
            return
        await self.service.clock.wait_until(self.deadline)
        if not self._stopping:
            self.failure = ErrorCode.TIMEOUT
            self._start_close()

    def _start_close(self) -> None:
        if self._cleanup is not None:
            return
        self._stopping = True
        self.completed = False
        if self._pending is not None:
            self._pending.close()
            self._pending = None
        self.processor.abort()  # Never flush sensitive candidates on a failure/close.
        self._request = None
        self._cleanup_deadline = self.service.clock.now() + 1
        self._cleanup = asyncio.create_task(self._guard_cleanup())
        self._cleanup.add_done_callback(_consume_failure)

    async def aclose(self) -> bool:
        if not self._entered:
            return True
        self._start_close()
        return await asyncio.shield(self._cleanup)

    async def _guard_cleanup(self) -> bool:
        deadline = self._cleanup_deadline
        self._cleanup_work = asyncio.create_task(self._close_owned())
        self._cleanup_work.add_done_callback(_consume_failure)
        if not await _before(self._cleanup_work, deadline, self.service.clock, inclusive=True):
            self.service.adapter.quarantined = True
            return False  # Worker/resource remains strongly owned; never cancel/drop.
        try:
            self._cleanup_work.result()
        except (Exception, asyncio.CancelledError):
            self.service.adapter.quarantined = True
            return False
        return self.cleaned

    async def _close_owned(self) -> None:
        if self._watchdog is not None:
            self._watchdog.cancel()
            await asyncio.gather(self._watchdog, return_exceptions=True)
        if self._operation is not None:
            if not self._operation.done():
                self._operation.cancel()
            try:
                await self._operation
            except (Exception, asyncio.CancelledError):
                pass
        if self.lease is not None:
            await self.lease.aclose()
        self.cleaned = True
        self.service._owners.discard(self)
        self.service.capacity.release()
