"""T4-002 K3-K5 / T4-Q1-Q3,Q9: deterministic accounting, not concurrent admission."""

from dataclasses import dataclass

import pytest

from task4_limiter.accounting import assess_admission, calculate_usage
from task4_limiter.models import (
    MAX_INTEGER,
    QUOTA_TOKENS,
    WINDOW_MS,
    AccountingValidationError,
    AdmissionReason,
    BoundsUnavailable,
    InvalidSnapshot,
    ModelTokenBounds,
    OutstandingReservation,
    ReservationPlan,
    SettledUsage,
)

pytestmark = pytest.mark.task4


@dataclass
class Clock:
    value: int
    calls: int = 0

    def now_ms(self):
        self.calls += 1
        return self.value


def plan(primary=2000, backup=2000):
    return ReservationPlan(
        ModelTokenBounds("primary", primary, 0, "fixture-v1"),
        ModelTokenBounds("backup", backup, 0, "fixture-v2"),
    )


@pytest.mark.parametrize(
    "held,allowed,remaining", [(999, True, 1), (1000, True, 0), (1001, False, 3999)]
)
def test_combined_reservation_obeys_exact_49999_50000_50001_boundary(held, allowed, remaining):
    decision = assess_admission(
        "a",
        plan(),
        [SettledUsage("a", "paid", 99_000, 45_000)],
        [OutstandingReservation("a", "held", 0, held)],
        clock=Clock(100_000),
    )
    assert decision.allowed is allowed
    assert decision.remaining_tokens == remaining
    assert decision.plan.total_tokens == 4000
    assert decision.reason == (
        AdmissionReason.ALLOWED if allowed else AdmissionReason.QUOTA_EXCEEDED
    )


@pytest.mark.parametrize(
    "now,expected",
    [
        (59_999, 48_000),
        (60_000, 41_000),
        (60_001, 41_000),
        (69_999, 41_000),
        (70_000, 30_000),
        (89_999, 30_000),
        (90_000, 17_000),
        (119_998, 17_000),
        (119_999, 0),
    ],
)
def test_weighted_sliding_expiration_keeps_old_holds(now, expected):
    entries = [
        SettledUsage("a", str(i), stamp, tokens)
        for i, (stamp, tokens) in enumerate(
            [(0, 7000), (10_000, 11_000), (30_000, 13_000), (59_999, 17_000)]
        )
    ]
    usage = calculate_usage("a", now, entries, [OutstandingReservation("a", "old-hold", 0, 2000)])
    assert usage.settled_tokens == expected
    assert usage.reserved_tokens == 2000
    assert usage.total_tokens == expected + 2000


def test_exact_lower_boundary_excluded_upper_boundary_included():
    usage = calculate_usage(
        "a",
        100_000,
        [
            SettledUsage("a", "expired", 40_000, 7000),
            SettledUsage("a", "inside", 40_001, 11_000),
            SettledUsage("a", "now", 100_000, 13_000),
        ],
        [],
    )
    assert usage.settled_tokens == 24_000
    assert QUOTA_TOKENS == 50_000 and WINDOW_MS == 60_000


def test_minute_boundary_does_not_reset_usage():
    entry = SettledUsage("a", "last-minute", 59_999, 48_000)
    assert not assess_admission("a", plan(), [entry], [], clock=Clock(60_000)).allowed


def test_tenants_are_exact_and_do_not_share_usage_or_entry_names():
    entries = [
        SettledUsage("a", "same", 99_000, 45_000),
        SettledUsage("A", "same", 99_000, 50_000),
        SettledUsage("a ", "same", MAX_INTEGER, MAX_INTEGER),
    ]
    holds = [OutstandingReservation("other", "same", MAX_INTEGER, MAX_INTEGER)]
    assert assess_admission("a", plan(), entries, holds, clock=Clock(100_000)).allowed
    assert not assess_admission("A", plan(), entries, holds, clock=Clock(100_000)).allowed
    assert calculate_usage("unseen", 100_000, entries, holds).total_tokens == 0


@pytest.mark.parametrize("now", [60_000, 60_001, 1_000_000_000])
def test_unresolved_reservations_never_expire_implicitly(now):
    hold = OutstandingReservation("a", "uncertain", 0, 48_000)
    decision = assess_admission("a", plan(), [], [hold], clock=Clock(now))
    assert decision.usage.reserved_tokens == 48_000
    assert not decision.allowed


@pytest.mark.parametrize("paid", [50_000, 50_001])
def test_full_or_already_overdrawn_snapshot_never_admits(paid):
    decision = assess_admission(
        "a", plan(), [SettledUsage("a", "paid", 0, paid)], [], clock=Clock(1)
    )
    assert not decision.allowed
    assert decision.remaining_tokens == 0
    assert decision.reason == (
        AdmissionReason.EXISTING_OVERAGE if paid > 50_000 else AdmissionReason.QUOTA_EXCEEDED
    )


def test_request_can_be_denied_even_when_primary_alone_would_fit():
    decision = assess_admission(
        "a",
        plan(primary=3000, backup=3000),
        [SettledUsage("a", "paid", 0, 45_000)],
        [],
        clock=Clock(1),
    )
    assert decision.usage.remaining_tokens == 5000
    assert not decision.allowed
    assert not assess_admission("a", plan(30_000, 30_000), [], [], clock=Clock(0)).allowed


@pytest.mark.parametrize("kind", ["settled", "held", "mixed", "expired-mixed"])
def test_duplicate_or_both_state_identities_are_rejected(kind):
    entry = SettledUsage("a", "same", 0, 1000)
    hold = OutstandingReservation("a", "same", 0, 2000)
    settled, held = (
        ([entry, entry], [])
        if kind == "settled"
        else (([], [hold, hold]) if kind == "held" else ([entry], [hold]))
    )
    with pytest.raises(InvalidSnapshot):
        calculate_usage("a", 100_000 if kind == "expired-mixed" else 0, settled, held)


@pytest.mark.parametrize(
    "entry", [SettledUsage("a", "future", 101, 1), OutstandingReservation("a", "future", 101, 1)]
)
def test_future_target_entries_are_not_silently_dropped(entry):
    settled = [entry] if type(entry) is SettledUsage else []
    held = [entry] if type(entry) is OutstandingReservation else []
    with pytest.raises(InvalidSnapshot):
        calculate_usage("a", 100, settled, held)


def test_clock_is_sampled_once_and_regression_fails_closed():
    clock = Clock(100)
    assess_admission("a", plan(), [], [], clock=clock, last_observed_ms=100)
    assert clock.calls == 1
    with pytest.raises(InvalidSnapshot):
        assess_admission("a", plan(), [], [], clock=Clock(99), last_observed_ms=100)


@pytest.mark.parametrize("value", [-1, True, 1.5, "100", None, MAX_INTEGER + 1])
def test_injected_clock_values_are_validated(value):
    with pytest.raises(AccountingValidationError):
        assess_admission("a", plan(), [], [], clock=Clock(value))


@pytest.mark.parametrize(
    "field,value",
    [("tenant_id", ""), ("tenant_id", None), ("last_observed_ms", True), ("last_observed_ms", -1)],
)
def test_snapshot_context_is_validated(field, value):
    with pytest.raises(AccountingValidationError):
        calculate_usage(
            **{"tenant_id": "a", "now_ms": 100, "settled": [], "outstanding": [], field: value}
        )


@pytest.mark.parametrize(
    "settled,held",
    [
        ([None], []),
        ([], [{}]),
        ([OutstandingReservation("a", "hold", 0, 1)], []),
        ([], [SettledUsage("a", "paid", 0, 1)]),
    ],
)
def test_untyped_or_wrong_state_records_fail_closed(settled, held):
    with pytest.raises(InvalidSnapshot):
        calculate_usage("a", 0, settled, held)


def test_missing_plan_fails_before_sampling_clock():
    clock = Clock(0)
    with pytest.raises(BoundsUnavailable):
        assess_admission("a", None, [], [], clock=clock)
    assert clock.calls == 0


def test_permutation_generators_and_repeated_decisions_do_not_mutate_state():
    entries = [SettledUsage("a", "one", 40_000, 5000), SettledUsage("a", "two", 50_000, 6000)]
    holds = [OutstandingReservation("a", "hold", 0, 7000)]
    original = entries[:], holds[:]
    first = assess_admission("a", plan(), entries, holds, clock=Clock(100_000))
    second = assess_admission("a", plan(), reversed(entries), iter(holds), clock=Clock(100_000))
    assert first == second and first.allowed
    assert first.usage.total_tokens == 13_000
    assert (entries, holds) == original
    # Pure evaluation does not reserve tokens. Atomic concurrent admission is T4-003.
    assert assess_admission("a", plan(), entries, holds, clock=Clock(100_000)) == first


def test_settlement_projection_uses_one_original_timestamp_without_refunding_uncertainty():
    # These are externally supplied snapshots, not settlement/recovery operations.
    pending = [
        OutstandingReservation("a", "primary", 0, 2000),
        OutstandingReservation("a", "backup", 0, 2000),
    ]
    assert calculate_usage("a", 60_000, [], pending).total_tokens == 4000
    known = [SettledUsage("a", "primary", 0, 1000)]
    assert calculate_usage("a", 59_999, known, []).total_tokens == 1000
    assert calculate_usage("a", 60_000, known, []).total_tokens == 0
    conservative = [SettledUsage("a", "primary", 0, 2000), SettledUsage("a", "backup", 0, 1000)]
    assert calculate_usage("a", 59_999, conservative, []).total_tokens == 3000
