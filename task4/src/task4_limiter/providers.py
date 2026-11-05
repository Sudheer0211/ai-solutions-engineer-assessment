"""T4-004: trusted injectable adapters, without an invented vendor/tokenizer API."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol

from task4_limiter.models import ModelTokenBounds, _integer


@dataclass(frozen=True, slots=True)
class TokenUsage:
    """Reliable adapter measurements; None at the result level means unknown."""

    input_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        _integer(self.input_tokens)
        _integer(self.output_tokens)
        _integer(self.total_tokens)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class ProviderStatus(StrEnum):
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    TRANSPORT_FAILURE = "transport_failure"


@dataclass(frozen=True, slots=True)
class ProviderResult:
    status: ProviderStatus
    usage: TokenUsage | None = None
    text: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if (
            type(self.status) is not ProviderStatus
            or (self.usage is not None and type(self.usage) is not TokenUsage)
            or (self.status == ProviderStatus.SUCCESS and type(self.text) is not str)
            or (self.status != ProviderStatus.SUCCESS and self.text is not None)
        ):
            raise ValueError("Invalid provider result")


class PreparedAttempt(Protocol):
    """One request-scoped, one-shot handle produced by a TRUSTED adapter.

    Preparation performs no network/resource acquisition. It establishes complete
    model-specific bounds and installs the matching enforced output cap. execute
    uses exactly that prepared input/cap; no hidden retries/redirects/hedging.
    aclose must close all local exchange resources, including after cancellation.
    Returning from execute alone is not evidence of cleanup or remote termination.
    Adapters must be cooperative async code; CPU-blocking code cannot be timed out
    safely by asyncio. This protocol does not certify a real provider/tokenizer.
    """

    @property
    def bounds(self) -> ModelTokenBounds: ...

    async def execute(self) -> ProviderResult: ...

    async def aclose(self) -> None: ...


class Provider(Protocol):
    model_id: str
    counter_id: str

    def prepare(self, text: str) -> PreparedAttempt:
        """Pure trusted counting/cap preparation, offloaded by the service.

        Raise BoundsUnavailable when reliable bounds/caps cannot be established.
        Never accept caller estimates or acquire resources that need async cleanup.
        Credentials remain private to a future operator-configured adapter.
        """
        ...
