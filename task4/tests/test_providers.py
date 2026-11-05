"""T4-004 typed adapter and finite operator-budget contract."""

import pytest

from task4_limiter.models import MAX_INTEGER
from task4_limiter.providers import ProviderResult, ProviderStatus, TokenUsage
from task4_limiter.service import RoutingPolicy


@pytest.mark.parametrize("bad", [True, -1, 0.5, "1", None, MAX_INTEGER + 1])
@pytest.mark.parametrize("position", [0, 1])
def test_usage_requires_exact_nonnegative_bounded_integers(bad, position):
    args = [0, 0]
    args[position] = bad
    with pytest.raises(ValueError):
        TokenUsage(*args)


def test_usage_combined_overflow_and_zero():
    assert TokenUsage(0, 0).total_tokens == 0
    with pytest.raises(ValueError):
        TokenUsage(MAX_INTEGER, 1)


@pytest.mark.parametrize(
    "status,usage,text",
    [
        ("success", None, "x"),
        (ProviderStatus.SUCCESS, None, None),
        (ProviderStatus.SUCCESS, 3, "x"),
        (ProviderStatus.RATE_LIMITED, None, "private payload"),
        (ProviderStatus.TRANSPORT_FAILURE, None, {}),
        (ProviderStatus.SUCCESS, None, 123),
    ],
)
def test_invalid_result_contract(status, usage, text):
    with pytest.raises(ValueError, match="Invalid provider result"):
        ProviderResult(status, usage, text)


@pytest.mark.parametrize(
    "backup,reservation",
    [
        (True, 10_000),
        (0, 10_000),
        (-1, 10_000),
        (1.1, 10_000),
        ("2000", 10_000),
        (2000, 6000),
        (2000, 5999),
        (2000, True),
        (2000, MAX_INTEGER + 1),
        (MAX_INTEGER, MAX_INTEGER),
    ],
)
def test_policy_requires_explicit_sufficient_finite_budgets(backup, reservation):
    with pytest.raises(ValueError):
        RoutingPolicy(backup, reservation)


def test_policy_valid_exact_margin():
    assert RoutingPolicy(2000, 6001).backup_timeout_ms == 2000
