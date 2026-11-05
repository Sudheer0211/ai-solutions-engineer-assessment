"""T4-002 / P1-P2: immutable internal accounting records, never caller attestations."""

from dataclasses import dataclass, field
from enum import StrEnum

QUOTA_TOKENS = 50_000
WINDOW_MS = 60_000
MAX_INTEGER = 2**63 - 1


class AccountingValidationError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid accounting value")


class BoundsUnavailable(ValueError):
    def __init__(self) -> None:
        super().__init__("Reliable model bounds unavailable")


class InvalidSnapshot(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid accounting snapshot")


def _integer(value: int, *, minimum: int = 0) -> None:
    if type(value) is not int or not minimum <= value <= MAX_INTEGER:
        raise AccountingValidationError()


def _identifier(value: str) -> None:
    # Opaque internal identifiers: never normalize/case-fold or echo invalid values.
    if type(value) is not str or not value:
        raise AccountingValidationError()


@dataclass(frozen=True, slots=True)
class ModelTokenBounds:
    """Trusted model adapter output; construction does not certify tokenizer accuracy.

    Future adapters must establish/enforce the bounds before constructing this
    record. No HTTP/caller estimate or `verified` flag is supported by this API.
    counter_id identifies the trusted model-specific counting policy/version.
    """

    model_id: str
    input_tokens: int
    output_tokens: int
    counter_id: str

    def __post_init__(self) -> None:
        if any(type(value) is not str or not value for value in (self.model_id, self.counter_id)):
            raise BoundsUnavailable()
        _integer(self.input_tokens)
        _integer(self.output_tokens)
        if self.total_tokens == 0:
            raise BoundsUnavailable()
        _integer(self.total_tokens)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True, slots=True)
class ReservationPlan:
    primary: ModelTokenBounds
    backup: ModelTokenBounds

    def __post_init__(self) -> None:
        if type(self.primary) is not ModelTokenBounds or type(self.backup) is not ModelTokenBounds:
            raise BoundsUnavailable()
        _integer(self.total_tokens, minimum=1)

    @property
    def total_tokens(self) -> int:
        return self.primary.total_tokens + self.backup.total_tokens


@dataclass(frozen=True, slots=True)
class SettledUsage:
    tenant_id: str = field(repr=False)
    entry_id: str = field(repr=False)
    admission_ms: int
    tokens: int

    def __post_init__(self) -> None:
        _identifier(self.tenant_id)
        _identifier(self.entry_id)
        _integer(self.admission_ms)
        _integer(self.tokens)


@dataclass(frozen=True, slots=True)
class OutstandingReservation:
    tenant_id: str = field(repr=False)
    entry_id: str = field(repr=False)
    admission_ms: int
    tokens: int

    def __post_init__(self) -> None:
        _identifier(self.tenant_id)
        _identifier(self.entry_id)
        _integer(self.admission_ms)
        _integer(self.tokens, minimum=1)


@dataclass(frozen=True, slots=True)
class UsageSnapshot:
    tenant_id: str = field(repr=False)
    as_of_ms: int
    settled_tokens: int
    reserved_tokens: int

    def __post_init__(self) -> None:
        _identifier(self.tenant_id)
        for value in (self.as_of_ms, self.settled_tokens, self.reserved_tokens):
            _integer(value)
        _integer(self.total_tokens)

    @property
    def total_tokens(self) -> int:
        return self.settled_tokens + self.reserved_tokens

    @property
    def remaining_tokens(self) -> int:
        return max(0, QUOTA_TOKENS - self.total_tokens)


class AdmissionReason(StrEnum):
    ALLOWED = "allowed"
    QUOTA_EXCEEDED = "quota_exceeded"
    EXISTING_OVERAGE = "existing_overage"


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """An arithmetic result, not a mutable reservation or concurrent admission permit."""

    usage: UsageSnapshot
    plan: ReservationPlan

    def __post_init__(self) -> None:
        if type(self.usage) is not UsageSnapshot:
            raise InvalidSnapshot()
        if type(self.plan) is not ReservationPlan:
            raise BoundsUnavailable()

    @property
    def allowed(self) -> bool:
        return self.usage.total_tokens + self.plan.total_tokens <= QUOTA_TOKENS

    @property
    def reason(self) -> AdmissionReason:
        if self.usage.total_tokens > QUOTA_TOKENS:
            return AdmissionReason.EXISTING_OVERAGE
        return AdmissionReason.ALLOWED if self.allowed else AdmissionReason.QUOTA_EXCEEDED

    @property
    def remaining_tokens(self) -> int:
        """Capacity after admission, or unchanged capacity when admission is denied."""
        return self.usage.remaining_tokens - (self.plan.total_tokens if self.allowed else 0)
