"""T1-002/T1-005: strict boundaries and schema/validation agreement."""

import math
from decimal import Decimal

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from task1.schemas import GetCustomerArguments, RefundArguments

pytestmark = pytest.mark.task1
VALID = {"customer_id": "CUST-00001", "amount": 10.25, "reason": "1234567890"}
INVALID_IDS = [
    None,
    1,
    True,
    "cust-00001",
    "CUST-0001",
    "CUST-000001",
    "CUST-１２３４５",
    "CUST-١٢٣٤٥",
    "CUST-00001\n",
    " CUST-00001",
    "CUST-0000x",
    "",
]
INVALID_AMOUNTS = [None, True, False, "10", "10.5", 0, -1, -0.1, [], {}]
INVALID_REASONS = [None, 10, True, "", "123456789", " " * 10, "\t\n " * 5]


@pytest.mark.parametrize("customer_id", INVALID_IDS)
@pytest.mark.parametrize("model", [GetCustomerArguments, RefundArguments])
def test_customer_id_rejections(model, customer_id):
    args = dict(VALID) if model is RefundArguments else {}
    args["customer_id"] = customer_id
    with pytest.raises(ValidationError):
        model.model_validate(args)


@pytest.mark.parametrize("customer_id", ["CUST-00000", "CUST-00001", "CUST-99999"])
def test_customer_id_boundaries(customer_id):
    assert GetCustomerArguments(customer_id=customer_id).customer_id == customer_id


@pytest.mark.parametrize("amount", INVALID_AMOUNTS + [math.nan, math.inf, -math.inf, Decimal("10")])
def test_amount_rejections(amount):
    with pytest.raises(ValidationError):
        RefundArguments.model_validate({**VALID, "amount": amount})


@pytest.mark.parametrize("amount", [10, 10.5, 10.25, 0.001, 5e-324, 1e308, 10**100])
def test_amount_acceptance_without_cent_restriction(amount):
    result = RefundArguments.model_validate({**VALID, "amount": amount})
    assert result.amount == amount
    assert type(result.amount) is type(amount)


@pytest.mark.parametrize("reason", INVALID_REASONS)
def test_reason_rejections(reason):
    with pytest.raises(ValidationError):
        RefundArguments.model_validate({**VALID, "reason": reason})


@pytest.mark.parametrize("reason", ["1234567890", "Valid refund reason", "         x"])
def test_reason_boundary(reason):
    assert RefundArguments.model_validate({**VALID, "reason": reason}).reason == reason


@pytest.mark.parametrize(
    "model,base", [(GetCustomerArguments, {"customer_id": "CUST-00001"}), (RefundArguments, VALID)]
)
def test_missing_and_unknown_fields(model, base):
    for field in base:
        with pytest.raises(ValidationError):
            model.model_validate({k: v for k, v in base.items() if k != field})
    with pytest.raises(ValidationError):
        model.model_validate({**base, "unexpected": 1})
    for invalid in (None, [], "arguments"):
        with pytest.raises(ValidationError):
            model.model_validate(invalid)


def test_advertised_refund_schema_agrees_with_validation():
    schema = RefundArguments.model_json_schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    samples = [VALID, {**VALID, "amount": 10}, {**VALID, "amount": 0.001}]
    samples += [{**VALID, "customer_id": value} for value in INVALID_IDS]
    samples += [{**VALID, "amount": value} for value in INVALID_AMOUNTS]
    samples += [{**VALID, "reason": value} for value in INVALID_REASONS]
    samples += [{k: v for k, v in VALID.items() if k != field} for field in VALID]
    samples += [{**VALID, "unexpected": 1}]
    for sample in samples:
        try:
            RefundArguments.model_validate(sample)
            accepted = True
        except ValidationError:
            accepted = False
        assert validator.is_valid(sample) == accepted, sample
