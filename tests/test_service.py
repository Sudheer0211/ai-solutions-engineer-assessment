"""T1-002/T1-005: refund behavior, exact arithmetic and state lifecycle."""

from dataclasses import FrozenInstanceError
from decimal import Decimal, localcontext

import pytest

from task1.repository import BusinessError, MockRepository
from task1.schemas import GetCustomerArguments, RefundArguments
from task1.service import CustomerService

pytestmark = pytest.mark.task1


@pytest.fixture
def repository():
    return MockRepository()


def refund(service, amount=10.25, customer_id="CUST-00001"):
    return service.trigger_refund(
        RefundArguments(customer_id=customer_id, amount=amount, reason="Synthetic refund request")
    )


def test_seed_records_and_immutable_views(repository):
    service = CustomerService(repository)
    for index in range(1, 4):
        result = service.get_customer_record(GetCustomerArguments(customer_id=f"CUST-{index:05d}"))
        assert result["customer_name"] == f"Demo Customer {index}"
        result["refundable_balance"] = "0"
        assert repository.get_customer(result["customer_id"]).refundable_balance > 0
    with pytest.raises(FrozenInstanceError):
        repository.get_customer("CUST-00001").refundable_balance = Decimal(0)


def test_successful_refunds_and_sequential_ids(repository):
    service = CustomerService(repository)
    first = refund(service)
    second = refund(service, 0.001)
    assert first["refund_id"] == "REF-000001"
    assert first["status"] == "completed"
    assert second["refund_id"] == "REF-000002"
    assert second["refundable_balance"] == "89.749"
    assert len(repository.refunds) == 2
    assert repository.refunds[0].amount == Decimal("10.25")
    assert repository.refunds[0].reason == "Synthetic refund request"


@pytest.mark.parametrize("customer_id,amount", [("CUST-99999", 1), ("CUST-00001", 100.01)])
def test_failed_execution_is_atomic(repository, customer_id, amount):
    service = CustomerService(repository)
    before = repository.get_customer("CUST-00001")
    with pytest.raises(BusinessError):
        refund(service, amount, customer_id)
    assert repository.get_customer("CUST-00001") == before
    assert repository.refunds == ()
    assert refund(service, 1)["refund_id"] == "REF-000001"


def test_exact_balance_boundary_and_no_float_drift(repository):
    service = CustomerService(repository)
    refund(service, 0.1)
    refund(service, 0.2)
    assert repository.get_customer("CUST-00001").refundable_balance == Decimal("99.70")
    assert refund(service, 99.7)["refundable_balance"] == "0.00"
    with pytest.raises(BusinessError):
        refund(service, 5e-324)
    assert len(repository.refunds) == 3


def test_tiny_amount_changes_balance_exactly(repository):
    refund(CustomerService(repository), 5e-324)
    with localcontext() as context:
        context.prec = 400
        difference = Decimal("100.00") - repository.get_customer("CUST-00001").refundable_balance
    assert difference == Decimal("5e-324")


def test_fresh_repository_resets_state(repository):
    refund(CustomerService(repository))
    fresh = MockRepository()
    assert fresh.get_customer("CUST-00001").refundable_balance == Decimal("100.00")
    assert fresh.refunds == ()
