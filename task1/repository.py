"""T1-002: deterministic synthetic state; lifetime is one server process."""

from dataclasses import dataclass, replace
from decimal import Decimal, localcontext


class BusinessError(Exception):
    """An expected execution failure with a safe client-facing message."""


@dataclass(frozen=True)
class Customer:
    customer_id: str
    customer_name: str
    account_status: str
    refundable_balance: Decimal

    def as_json(self) -> dict[str, str]:
        return {
            "customer_id": self.customer_id,
            "customer_name": self.customer_name,
            "account_status": self.account_status,
            "refundable_balance": str(self.refundable_balance),
        }


@dataclass(frozen=True)
class Refund:
    refund_id: str
    customer_id: str
    amount: Decimal
    reason: str
    status: str = "completed"


class MockRepository:
    def __init__(self) -> None:
        self._customers = {
            f"CUST-{index:05d}": Customer(
                f"CUST-{index:05d}", f"Demo Customer {index}", "active", Decimal(balance)
            )
            for index, balance in enumerate(("100.00", "250.00", "50.00"), start=1)
        }
        self._refunds: list[Refund] = []

    @property
    def refunds(self) -> tuple[Refund, ...]:
        return tuple(self._refunds)

    def get_customer(self, customer_id: str) -> Customer:
        try:
            return self._customers[customer_id]
        except KeyError:
            raise BusinessError("Customer not found") from None

    def refund(self, customer_id: str, amount: Decimal, reason: str) -> tuple[Refund, Customer]:
        customer = self.get_customer(customer_id)
        if amount > customer.refundable_balance:
            raise BusinessError("Refund exceeds available refundable balance")
        # Preserve even the smallest positive finite float, without quantizing.
        balance = customer.refundable_balance
        with localcontext() as context:
            context.prec = (
                max(balance.adjusted(), amount.adjusted())
                - min(balance.as_tuple().exponent, amount.as_tuple().exponent)
                + 2
            )
            updated = replace(customer, refundable_balance=balance - amount)
        transaction = Refund(f"REF-{len(self._refunds) + 1:06d}", customer_id, amount, reason)
        # No awaits: this event loop cannot interleave check and commit.
        self._customers[customer_id] = updated
        self._refunds.append(transaction)
        return transaction, updated
