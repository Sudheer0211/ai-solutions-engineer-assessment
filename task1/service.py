"""T1-002: business operations consume validated Pydantic models."""

from decimal import Decimal

from task1.repository import MockRepository
from task1.schemas import GetCustomerArguments, RefundArguments


class CustomerService:
    def __init__(self, repository: MockRepository) -> None:
        self.repository = repository

    def get_customer_record(self, arguments: GetCustomerArguments) -> dict[str, str]:
        return self.repository.get_customer(arguments.customer_id).as_json()

    def trigger_refund(self, arguments: RefundArguments) -> dict[str, str]:
        transaction, customer = self.repository.refund(
            arguments.customer_id, Decimal(str(arguments.amount)), arguments.reason
        )
        return {
            "refund_id": transaction.refund_id,
            "status": transaction.status,
            "customer_id": transaction.customer_id,
            "amount": str(transaction.amount),
            "refundable_balance": str(customer.refundable_balance),
        }
