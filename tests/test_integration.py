"""T1-003/T1-005: real SDK integration in-process (not wire tests)."""

from decimal import Decimal

import pytest
from mcp import Client, MCPError

from task1.repository import MockRepository
from task1.server import ARGUMENT_MODELS, create_server

pytestmark = pytest.mark.task1


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_lifecycle_schemas_and_both_tools(mode):
    async with Client(create_server(), mode=mode) as client:
        assert client.protocol_version == ("2026-07-28" if mode == "auto" else "2025-11-25")
        tools = (await client.list_tools()).tools
        assert {tool.name for tool in tools} == set(ARGUMENT_MODELS)
        assert len(tools) == 2
        for tool in tools:
            assert tool.input_schema == ARGUMENT_MODELS[tool.name].model_json_schema()
            assert tool.input_schema["additionalProperties"] is False
        customer = await client.call_tool("get_customer_record", {"customer_id": "CUST-00001"})
        assert not customer.is_error
        assert customer.structured_content["refundable_balance"] == "100.00"
        result = await client.call_tool(
            "trigger_refund",
            {"customer_id": "CUST-00001", "amount": 10.25, "reason": "Synthetic refund request"},
        )
        assert not result.is_error
        assert result.structured_content["refund_id"] == "REF-000001"


@pytest.mark.parametrize(
    "name,args",
    [
        ("unknown", {}),
        ("get_customer_record", {}),
        ("get_customer_record", {"customer_id": "CUST-00001", "extra": True}),
        ("trigger_refund", {"customer_id": "CUST-00001", "amount": "10", "reason": "Valid reason"}),
        ("trigger_refund", {"customer_id": "CUST-00001", "amount": True, "reason": "Valid reason"}),
    ],
)
async def test_invalid_args_are_protocol_errors_without_mutation(name, args):
    repo = MockRepository()
    async with Client(create_server(repo)) as client:
        with pytest.raises(MCPError) as error:
            await client.call_tool(name, args)
        assert error.value.code == -32602
        assert repo.get_customer("CUST-00001").refundable_balance == Decimal("100.00")
        assert repo.refunds == ()


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_business_errors(mode):
    async with Client(create_server(), mode=mode) as client:
        missing = await client.call_tool("get_customer_record", {"customer_id": "CUST-99999"})
        assert missing.is_error
        assert missing.structured_content == {"error": "Customer not found"}
        excessive = await client.call_tool(
            "trigger_refund", {"customer_id": "CUST-00001", "amount": 101, "reason": "Valid reason"}
        )
        assert excessive.is_error


class FailingRepository(MockRepository):
    def get_customer(self, customer_id):
        raise RuntimeError("PRIVATE_IMPLEMENTATION_DETAILS")


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_internal_exception_is_safe_protocol_error(mode):
    async with Client(create_server(FailingRepository()), mode=mode) as client:
        with pytest.raises(MCPError) as error:
            await client.call_tool("get_customer_record", {"customer_id": "CUST-00001"})
        assert error.value.code == -32603
        assert error.value.message == "Internal server error"
        assert "PRIVATE" not in str(error.value)
