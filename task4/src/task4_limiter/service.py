"""T4-004 / Q6-Q10: single-owner routing over the accepted durable store APIs."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from typing import Protocol, TypeVar
from uuid import UUID, uuid4

from task4_limiter.models import ModelTokenBounds, ReservationPlan, _integer
from task4_limiter.providers import PreparedAttempt, Provider, ProviderResult, ProviderStatus
from task4_limiter.storage import SQLiteStore

PRIMARY_MS = 3000
CLEANUP_MS = 500
_T = TypeVar("_T")
_MESSAGES = {
    "invalid_request": "Invalid request",
    "invalid_credentials": "Invalid credentials",
    "tenant_quota_exceeded": "Tenant quota exceeded",
    "provider_rate_limited": "Model capacity unavailable",
    "model_timeout": "Model request timed out",
    "model_unavailable": "Model unavailable",
    "service_unavailable": "Service unavailable",
}


class MonotonicClock(Protocol):
    def now_ms(self) -> float: ...

    async def wait_until(self, deadline_ms: float) -> None: ...


class LoopClock:
    def now_ms(self) -> float:
        return asyncio.get_running_loop().time() * 1000

    async def wait_until(self, deadline_ms: float) -> None:
        await asyncio.sleep(max(0, deadline_ms - self.now_ms()) / 1000)


@dataclass(frozen=True, slots=True)
class RoutingPolicy:
    """Explicit operator choices, not unspecified assessment timeout defaults.

    Reservation lifetime includes both attempts and both cleanup budgets, plus
    operator-supplied DB/scheduling margin. No default backup/overall timeout.
    """

    backup_timeout_ms: int
    reservation_ms: int

    def __post_init__(self) -> None:
        _integer(self.backup_timeout_ms, minimum=1)
        _integer(self.reservation_ms, minimum=1)
        if self.reservation_ms <= PRIMARY_MS + 2 * CLEANUP_MS + self.backup_timeout_ms:
            raise ValueError("Insufficient reservation lifetime")


@dataclass(frozen=True, slots=True)
class ServiceOutcome:
    request_id: UUID
    code: str | None = None
    text: str | None = field(default=None, repr=False)
    used_backup: bool = False

    @property
    def message(self) -> str | None:
        return _MESSAGES[self.code] if self.code is not None else None


@dataclass(frozen=True, slots=True)
class _Exchange:
    result: ProviderResult | None
    timed_out: bool
    cleaned: bool
    dispatched: bool


class LLMService:
    """Trusted in-process API: validated tenant key bytes, prompt, internal UUID.

    No public key authentication/HTTP boundary is invented. The external owner
    must stop submissions and await aclose BEFORE closing the store/event loop.
    Caller cancellation signals an owned workflow; it never cancels a DB thread
    or implies rollback. Strong references retain workflows and uncertain cleanup.
    """

    def __init__(
        self,
        store: SQLiteStore,
        primary: Provider,
        backup: Provider,
        policy: RoutingPolicy,
        *,
        clock: MonotonicClock | None = None,
    ) -> None:
        if type(policy) is not RoutingPolicy:
            raise ValueError("Invalid routing policy")
        self._store, self._primary, self._backup = store, primary, backup
        self._policy, self._clock = policy, clock or LoopClock()
        # A bounded offload lane, not the quota lock: SQLite remains authoritative.
        self._lane = asyncio.Semaphore(1)
        self._work: set[asyncio.Task[ServiceOutcome]] = set()
        self._cleanup: set[asyncio.Task[bool]] = set()
        self._closed = False
        self._healthy = True
        self._failed_handles: list[PreparedAttempt] = []

    @property
    def pending_cleanup(self) -> int:
        return len(self._cleanup)

    async def _offload(self, function: Callable[..., _T], *args: object, **kw: object) -> _T:
        async with self._lane:
            return await asyncio.to_thread(partial(function, *args, **kw))

    @staticmethod
    def _retain(task: asyncio.Task[_T], collection: set[asyncio.Task[_T]]) -> None:
        collection.add(task)

        def done(finished: asyncio.Task[_T]) -> None:
            collection.discard(finished)
            if not finished.cancelled():
                finished.exception()  # Consume failures; never log adapter/SQL details.

        task.add_done_callback(done)

    async def generate(
        self, api_key: bytes, text: str, *, request_id: UUID | None = None
    ) -> ServiceOutcome:
        rid = uuid4() if request_id is None else request_id
        if type(rid) is not UUID:
            return ServiceOutcome(uuid4(), "invalid_request")
        if type(api_key) is not bytes or not 1 <= len(api_key) <= 4096:
            return ServiceOutcome(rid, "invalid_credentials")
        if type(text) is not str or not text:
            return ServiceOutcome(rid, "invalid_request")
        if self._closed or not self._healthy:
            return ServiceOutcome(rid, "service_unavailable")
        cancelled = asyncio.Event()
        task = asyncio.create_task(self._run(api_key, text, rid, cancelled))
        self._retain(task, self._work)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    async def drain(self) -> None:
        """Discover actual worker outcomes after cancellation; no provider replay."""
        while self._work:
            await asyncio.shield(asyncio.gather(*tuple(self._work)))

    async def aclose(self) -> bool:
        """Drain DB/workflows, then bounded wait for quarantined local cleanup.

        False means a trusted adapter did not terminate/close: the owner must not
        claim graceful shutdown or discard the service's remaining task references.
        asyncio cannot forcibly terminate an arbitrary cancellation-resistant task.
        """
        self._closed = True
        await self.drain()
        if self._cleanup:
            await self._wait(
                asyncio.gather(*tuple(self._cleanup)), self._clock.now_ms() + CLEANUP_MS
            )
        return not self._cleanup and not self._failed_handles

    async def _wait(
        self, task: asyncio.Future[_T], deadline: float, cancelled: asyncio.Event | None = None
    ) -> bool:
        timer = asyncio.create_task(self._clock.wait_until(deadline))
        signal = asyncio.create_task(cancelled.wait()) if cancelled is not None else None
        try:
            watched = {task, timer} | ({signal} if signal is not None else set())
            await asyncio.wait(watched, return_when=asyncio.FIRST_COMPLETED)
            return (
                task.done()
                and self._clock.now_ms() < deadline
                and (cancelled is None or not cancelled.is_set())
            )
        finally:
            for waiter in (timer, signal):
                if waiter is not None:
                    waiter.cancel()
            await asyncio.gather(
                *(w for w in (timer, signal) if w is not None), return_exceptions=True
            )

    async def _exchange(
        self, attempt: PreparedAttempt, timeout_ms: int, cancelled: asyncio.Event, expires: float
    ) -> _Exchange:
        deadline = self._clock.now_ms() + timeout_ms
        dispatched = False

        async def invoke() -> ProviderResult | None:
            nonlocal dispatched
            if (
                cancelled.is_set()
                or not self._healthy
                or self._clock.now_ms() >= deadline
                or self._clock.now_ms() + timeout_ms + CLEANUP_MS >= expires
            ):
                return None
            dispatched = True
            return await attempt.execute()

        task = asyncio.create_task(invoke())
        timely = await self._wait(task, deadline, cancelled)
        result = None
        if timely:
            try:
                candidate = task.result()
                if type(candidate) is ProviderResult:
                    result = candidate
            except (Exception, asyncio.CancelledError):
                pass

        async def cleanup() -> bool:
            if not task.done():
                task.cancel()
            try:
                await task
            except (Exception, asyncio.CancelledError):
                pass
            try:
                await attempt.aclose()
                return True
            except (Exception, asyncio.CancelledError):
                # Keep ownership even when close itself fails and its task is done.
                self._failed_handles.append(attempt)
                return False

        closer = asyncio.create_task(cleanup())
        self._retain(closer, self._cleanup)
        # Scheduling delay after the timeout cannot renew the cleanup allowance.
        grace_end = min(self._clock.now_ms(), deadline) + CLEANUP_MS
        finished = await self._wait(closer, grace_end)
        cleaned = finished and closer.result()
        if not cleaned:
            self._healthy = False  # Quarantine: no further sends in this service instance.
        elif result is None and task.done() and not task.cancelled():
            # Late content never wins the timeout race, but reliable usage is useful.
            try:
                candidate = task.result()
                if type(candidate) is ProviderResult:
                    result = candidate
            except Exception:
                pass
        return _Exchange(result, not timely and not cancelled.is_set(), cleaned, dispatched)

    async def _prepare(self, provider: Provider, text: str) -> PreparedAttempt:
        attempt = await self._offload(provider.prepare, text)
        bounds = attempt.bounds
        if (
            type(bounds) is not ModelTokenBounds
            or bounds.model_id != provider.model_id
            or bounds.counter_id != provider.counter_id
        ):
            raise ValueError("Reliable model bounds unavailable")
        return attempt

    async def _run(
        self, key: bytes, text: str, rid: UUID, cancelled: asyncio.Event
    ) -> ServiceOutcome:
        used_backup = False
        try:
            primary = await self._prepare(self._primary, text)
            backup = await self._prepare(self._backup, text)
            plan = ReservationPlan(primary.bounds, backup.bounds)
            if cancelled.is_set() or not self._healthy:
                return ServiceOutcome(rid, "service_unavailable")
            # Starting before admission is conservative for monotonic expiry.
            expires = self._clock.now_ms() + self._policy.reservation_ms
            admitted = await self._offload(
                self._store.admit, key, rid, plan, reservation_ms=self._policy.reservation_ms
            )
            if not admitted.admitted:
                return ServiceOutcome(rid, "tenant_quota_exceeded")
            for ordinal, attempt, bound, budget in (
                (1, primary, plan.primary, PRIMARY_MS),
                (2, backup, plan.backup, self._policy.backup_timeout_ms),
            ):
                # Check before intent AND again after DB completion, without an await
                # between the last check and creating the owned execution task.
                if (
                    cancelled.is_set()
                    or not self._healthy
                    or self._clock.now_ms() + budget + CLEANUP_MS >= expires
                ):
                    await self._offload(self._store.release_unused, key, rid, ordinal)
                    if ordinal == 1:
                        await self._offload(self._store.release_unused, key, rid, 2)
                    return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
                await self._offload(self._store.start_attempt, key, rid, ordinal)
                if (
                    cancelled.is_set()
                    or not self._healthy
                    or self._clock.now_ms() + budget + CLEANUP_MS >= expires
                ):
                    # Durable intent committed but this owner provably never sent.
                    await self._offload(self._store.settle, key, rid, ordinal, actual_tokens=0)
                    if ordinal == 1:
                        await self._offload(self._store.release_unused, key, rid, 2)
                    return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
                exchange = await self._exchange(attempt, budget, cancelled, expires)
                used_backup = ordinal == 2 and exchange.dispatched
                if not exchange.cleaned:
                    # Keep ALL holds for deadline-anchored recovery; no guessed release.
                    return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
                result = exchange.result
                usage = result.usage if result is not None else None
                invalid_usage = usage is not None and (
                    usage.input_tokens > bound.input_tokens
                    or usage.output_tokens > bound.output_tokens
                )
                actual = usage.total_tokens if usage is not None else None
                if invalid_usage and actual <= bound.total_tokens:
                    actual = None  # Broken category/cap contract: never refund uncertainty.
                    self._healthy = False
                if not exchange.dispatched:
                    actual = 0  # Intent persisted, but this owner provably did not send.
                await self._offload(self._store.settle, key, rid, ordinal, actual_tokens=actual)
                if ordinal == 1 and (
                    cancelled.is_set()
                    or invalid_usage
                    or not self._healthy
                    or not (
                        exchange.timed_out
                        or (result is not None and result.status == ProviderStatus.RATE_LIMITED)
                    )
                ):
                    await self._offload(self._store.release_unused, key, rid, 2)
                if cancelled.is_set() or invalid_usage:
                    return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
                if (
                    result is not None
                    and result.status == ProviderStatus.SUCCESS
                    and not exchange.timed_out
                ):
                    return ServiceOutcome(rid, text=result.text, used_backup=used_backup)
                timeout = exchange.timed_out or (
                    result is not None and result.status == ProviderStatus.TIMEOUT
                )
                rate_limited = result is not None and result.status == ProviderStatus.RATE_LIMITED
                if ordinal == 1 and (exchange.timed_out or rate_limited):
                    continue
                code = (
                    "model_timeout"
                    if timeout
                    else "provider_rate_limited"
                    if rate_limited
                    else "model_unavailable"
                )
                return ServiceOutcome(rid, code, used_backup=used_backup)
        except Exception:
            # An ambiguous DB commit is NOT retried/refunded. Existing durable holds
            # remain recoverable; raw adapter/SQL exception text is never returned.
            return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
        return ServiceOutcome(rid, "service_unavailable", used_backup=used_backup)
