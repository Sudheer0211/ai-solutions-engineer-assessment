"""T1-002: shared validation and advertised JSON Schema."""

from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

CustomerId = Annotated[str, Field(pattern=r"^CUST-[0-9]{5}$", min_length=10, max_length=10)]


def require_json_number(value: object) -> int | float:
    if type(value) not in (int, float):
        raise ValueError("amount must be a JSON number")
    return value


JsonAmount = Annotated[
    Annotated[int, Field(gt=0)] | Annotated[float, Field(gt=0, allow_inf_nan=False)],
    BeforeValidator(require_json_number),
]


class StrictArguments(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")


class GetCustomerArguments(StrictArguments):
    customer_id: CustomerId


class RefundArguments(StrictArguments):
    customer_id: CustomerId
    amount: JsonAmount
    reason: Annotated[str, Field(min_length=10, pattern=r"\S")]
