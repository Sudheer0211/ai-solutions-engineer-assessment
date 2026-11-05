"""T4-002 K2/K5, T4-Q1/Q9: strict internal records and fail-closed bounds."""

from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from task4_limiter.models import (
    MAX_INTEGER,
    AccountingValidationError,
    AdmissionDecision,
    BoundsUnavailable,
    InvalidSnapshot,
    ModelTokenBounds,
    OutstandingReservation,
    ReservationPlan,
    SettledUsage,
    UsageSnapshot,
)

pytestmark = pytest.mark.task4
BAD_COUNTS = [
    -1,
    True,
    False,
    1.0,
    "1",
    None,
    Decimal(1),
    float("inf"),
    float("nan"),
    MAX_INTEGER + 1,
]


def model(**changes):
    return ModelTokenBounds(
        **{
            "model_id": "primary",
            "input_tokens": 1000,
            "output_tokens": 1000,
            "counter_id": "fixture-counter-v1",
            **changes,
        }
    )


@pytest.mark.parametrize("value", BAD_COUNTS)
@pytest.mark.parametrize("field", ["input_tokens", "output_tokens"])
def test_model_bound_counts_are_exact_storage_safe_integers(field, value):
    with pytest.raises(AccountingValidationError, match="^Invalid accounting value$"):
        model(**{field: value})


@pytest.mark.parametrize("value", ["", None, True, 12])
@pytest.mark.parametrize("field", ["model_id", "counter_id"])
def test_model_specific_counting_metadata_is_required(field, value):
    with pytest.raises(BoundsUnavailable):
        model(**{field: value})


def test_zero_or_overflowing_bounds_cannot_authorize_work():
    with pytest.raises(BoundsUnavailable):
        model(input_tokens=0, output_tokens=0)
    with pytest.raises(AccountingValidationError):
        model(input_tokens=MAX_INTEGER, output_tokens=1)
    with pytest.raises(AccountingValidationError):
        ReservationPlan(model(input_tokens=MAX_INTEGER, output_tokens=0), model())


@pytest.mark.parametrize(
    "primary,backup",
    [(None, None), (None, "bound"), (1000, 2000), ({"input_tokens": 10, "verified": True}, None)],
)
def test_caller_estimates_and_flags_are_not_bound_records(primary, backup):
    with pytest.raises(BoundsUnavailable):
        ReservationPlan(primary, backup)


def test_each_model_is_required_and_counts_may_differ():
    primary = model(input_tokens=123, output_tokens=456)
    backup = model(
        model_id="backup", input_tokens=321, output_tokens=654, counter_id="other-model-counter-v2"
    )
    assert ReservationPlan(primary, backup).total_tokens == 1554
    for missing in [(primary, None), (None, backup)]:
        with pytest.raises(BoundsUnavailable):
            ReservationPlan(*missing)
    assert model(input_tokens=0, output_tokens=1).total_tokens == 1
    assert model(input_tokens=1, output_tokens=0).total_tokens == 1


@pytest.mark.parametrize("record", [SettledUsage, OutstandingReservation])
@pytest.mark.parametrize("field", ["tokens", "admission_ms"])
@pytest.mark.parametrize("value", BAD_COUNTS)
def test_ledger_records_validate_counts_and_timestamps(record, field, value):
    values = {"tenant_id": "a", "entry_id": "entry", "admission_ms": 0, "tokens": 1, field: value}
    with pytest.raises(AccountingValidationError):
        record(**values)


@pytest.mark.parametrize("record", [SettledUsage, OutstandingReservation])
@pytest.mark.parametrize("field", ["tenant_id", "entry_id"])
@pytest.mark.parametrize("value", ["", None, True, 1])
def test_ledger_records_require_opaque_nonempty_identifiers(record, field, value):
    values = {"tenant_id": "a", "entry_id": "entry", "admission_ms": 0, "tokens": 1, field: value}
    with pytest.raises(AccountingValidationError):
        record(**values)


def test_known_zero_usage_is_distinct_from_an_outstanding_bound():
    assert SettledUsage("a", "entry", 0, 0).tokens == 0
    with pytest.raises(AccountingValidationError):
        OutstandingReservation("a", "entry", 0, 0)


@pytest.mark.parametrize("field", ["as_of_ms", "settled_tokens", "reserved_tokens"])
@pytest.mark.parametrize("value", BAD_COUNTS)
def test_snapshot_direct_construction_cannot_bypass_integer_validation(field, value):
    with pytest.raises(AccountingValidationError):
        UsageSnapshot(
            **{
                "tenant_id": "a",
                "as_of_ms": 0,
                "settled_tokens": 0,
                "reserved_tokens": 0,
                field: value,
            }
        )


def test_aggregate_snapshot_overflow_fails_closed():
    with pytest.raises(AccountingValidationError):
        UsageSnapshot("a", 0, MAX_INTEGER, 1)


def test_records_and_decisions_are_immutable_and_do_not_echo_identifiers():
    bound = model()
    records = [
        bound,
        ReservationPlan(bound, bound),
        SettledUsage("private-key", "private-id", 0, 1),
        OutstandingReservation("private-key", "private-id", 0, 1),
        UsageSnapshot("private-key", 0, 1, 1),
    ]
    records.append(AdmissionDecision(records[-1], records[1]))
    for record in records:
        attribute = next(iter(record.__dataclass_fields__))
        with pytest.raises(FrozenInstanceError):
            setattr(record, attribute, None)
        assert "private-key" not in repr(record)
        assert "private-id" not in repr(record)


def test_errors_are_generic_and_decisions_require_typed_inputs():
    with pytest.raises(AccountingValidationError) as caught:
        model(input_tokens="sensitive-canary")
    assert "sensitive-canary" not in str(caught.value)
    with pytest.raises(InvalidSnapshot):
        AdmissionDecision({}, ReservationPlan(model(), model()))
    with pytest.raises(BoundsUnavailable):
        AdmissionDecision(UsageSnapshot("a", 0, 0, 0), {})
