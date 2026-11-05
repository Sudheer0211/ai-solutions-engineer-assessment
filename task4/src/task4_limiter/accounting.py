"""T4-002 / T4-Q1-Q3,Q9: tenant-scoped snapshot math with no state or I/O."""

from collections.abc import Iterable
from typing import Protocol

from task4_limiter.models import (
    WINDOW_MS,
    AdmissionDecision,
    BoundsUnavailable,
    InvalidSnapshot,
    OutstandingReservation,
    ReservationPlan,
    SettledUsage,
    UsageSnapshot,
    _identifier,
    _integer,
)


class AccountingClock(Protocol):
    def now_ms(self) -> int:
        """Return UTC accounting milliseconds; elapsed provider timing is separate."""
        ...


def calculate_usage(
    tenant_id: str,
    now_ms: int,
    settled: Iterable[SettledUsage],
    outstanding: Iterable[OutstandingReservation],
    *,
    last_observed_ms: int | None = None,
) -> UsageSnapshot:
    """Count settled (now-60s,now] plus ALL holds, including old/expired-deadline holds.

    Settlement/recovery must replace entries transactionally in T4-003; this
    function neither expires holds nor mutates caller-owned collections.
    """
    _identifier(tenant_id)
    _integer(now_ms)
    if last_observed_ms is not None:
        _integer(last_observed_ms)
        if now_ms < last_observed_ms:
            raise InvalidSnapshot()
    seen: set[str] = set()

    def include(entry: SettledUsage | OutstandingReservation) -> bool:
        if entry.tenant_id != tenant_id:
            return False
        if entry.admission_ms > now_ms or entry.entry_id in seen:
            raise InvalidSnapshot()
        seen.add(entry.entry_id)
        return True

    settled_total = 0
    for entry in settled:
        if type(entry) is not SettledUsage:
            raise InvalidSnapshot()
        if include(entry) and entry.admission_ms > now_ms - WINDOW_MS:
            settled_total += entry.tokens
    reserved_total = 0
    for hold in outstanding:
        if type(hold) is not OutstandingReservation:
            raise InvalidSnapshot()
        if include(hold):
            reserved_total += hold.tokens
    return UsageSnapshot(tenant_id, now_ms, settled_total, reserved_total)


def assess_admission(
    tenant_id: str,
    plan: ReservationPlan,
    settled: Iterable[SettledUsage],
    outstanding: Iterable[OutstandingReservation],
    *,
    clock: AccountingClock,
    last_observed_ms: int | None = None,
) -> AdmissionDecision:
    """Sample the injected clock once; no reservation is written or permit issued."""
    if type(plan) is not ReservationPlan:
        raise BoundsUnavailable()
    usage = calculate_usage(
        tenant_id,
        clock.now_ms(),
        settled,
        outstanding,
        last_observed_ms=last_observed_ms,
    )
    return AdmissionDecision(usage, plan)
