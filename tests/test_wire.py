"""T1-004/T1-005: actual STDIO subprocess tests, separate from SDK integration."""

import json
import sys

import pytest
from mcp import Client, StdioServerParameters

from task1.server import ARGUMENT_MODELS
from tests.wire_support import ROOT, WireServer

pytestmark = [pytest.mark.task1, pytest.mark.wire]
VALID_REFUND = {"customer_id": "CUST-00001", "amount": 10.25, "reason": "Synthetic request"}


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_wire_lifecycle_tools_mutation_and_stream_isolation(mode):
    with WireServer(mode) as server:
        discovered = server.request("tools/list", request_id=1)["result"]["tools"]
        assert len(discovered) == 2
        assert {tool["name"] for tool in discovered} == set(ARGUMENT_MODELS)
        for tool in discovered:
            assert tool["inputSchema"] == ARGUMENT_MODELS[tool["name"]].model_json_schema()
        before = server.request(
            "tools/call",
            {"name": "get_customer_record", "arguments": {"customer_id": "CUST-00001"}},
            "before",
        )["result"]
        assert before["structuredContent"]["refundable_balance"] == "100.00"
        assert not before.get("isError", False)
        refund = server.request(
            "tools/call", {"name": "trigger_refund", "arguments": VALID_REFUND}, "refund"
        )["result"]
        assert refund["structuredContent"]["refund_id"] == "REF-000001"
        assert refund["structuredContent"]["refundable_balance"] == "89.75"
        failed = server.request(
            "tools/call",
            {"name": "trigger_refund", "arguments": {**VALID_REFUND, "amount": 1000}},
            "excessive",
        )["result"]
        assert failed["isError"] is True
        invalid = server.request(
            "tools/call",
            {"name": "trigger_refund", "arguments": {**VALID_REFUND, "amount": True}},
            "invalid",
        )
        assert invalid["error"]["code"] == -32602
        after = server.request(
            "tools/call",
            {"name": "get_customer_record", "arguments": {"customer_id": "CUST-00001"}},
            "after",
        )["result"]
        assert after["structuredContent"]["refundable_balance"] == "89.75"
        missing = server.request(
            "tools/call",
            {"name": "get_customer_record", "arguments": {"customer_id": "CUST-99999"}},
            "missing",
        )["result"]
        assert missing["isError"] is True
    logs = "".join(server.errors)
    for expected in (
        "server starting",
        "server stopped",
        "Tool execution",
        "Validation failed",
        "Business operation failed",
    ):
        assert expected in logs
    assert "Synthetic request" not in logs
    assert "Demo Customer" not in logs


@pytest.mark.parametrize("mode", ["legacy", "modern"])
@pytest.mark.parametrize("request_id", [42, "client-request-42"])
def test_wire_protocol_error_matrix_and_ids(mode, request_id):
    with WireServer(mode) as server:
        for method, params, expected in [
            ("unknown/method", {}, -32601),
            ("tools/call", {"name": "unknown", "arguments": {}}, -32602),
            ("tools/call", {"name": "get_customer_record", "arguments": {}}, -32602),
            ("tools/call", {"name": "get_customer_record", "arguments": None}, -32602),
            (
                "tools/call",
                {"name": "trigger_refund", "arguments": {**VALID_REFUND, "extra": 1}},
                -32602,
            ),
            (
                "tools/call",
                {"name": "trigger_refund", "arguments": {**VALID_REFUND, "amount": "10"}},
                -32602,
            ),
            (
                "tools/call",
                {"name": "trigger_refund", "arguments": {**VALID_REFUND, "reason": " " * 10}},
                -32602,
            ),
            ("tools/call", {}, -32602),
        ]:
            message = server.request(method, params, request_id)
            assert message["id"] == request_id
            assert message["error"]["code"] == expected
            assert "result" not in message
            assert "Traceback" not in json.dumps(message)


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_wire_internal_error_is_sanitized_and_preserves_id(mode):
    with WireServer(mode, fault=True) as server:
        response = server.request(
            "tools/call",
            {"name": "get_customer_record", "arguments": {"customer_id": "CUST-00001"}},
            "internal-7",
        )
        assert response["id"] == "internal-7"
        assert response["error"] == {"code": -32603, "message": "Internal server error"}
        assert "PRIVATE" not in json.dumps(response)
    assert "Unexpected tool exception" in "".join(server.errors)
    assert "PRIVATE" not in "".join(server.errors)


@pytest.mark.sdk_limitation
@pytest.mark.xfail(strict=True, reason="MCP 2.3.0 STDIO drops malformed transport exceptions (B3)")
@pytest.mark.parametrize("mode", ["legacy", "modern"])
@pytest.mark.parametrize(
    "raw,code,request_id",
    [
        ('{"jsonrpc":\n', -32700, None),
        ('{"jsonrpc":"2.0","id":"invalid-8","method":7}\n', -32600, "invalid-8"),
    ],
)
def test_required_malformed_transport_error(mode, raw, code, request_id):
    with WireServer(mode) as server:
        server.send_raw(raw)
        # A subsequent response proves the bad frame was consumed and the
        # connection remains live; no arbitrary sleep/timeout asserts absence.
        server.request("tools/list", request_id="after-bad-frame")
        errors = [message for message in server.messages if "error" in message]
        assert any(
            message["error"]["code"] == code and message["id"] == request_id for message in errors
        ), f"Required {code} response absent; observed {errors!r}"


@pytest.mark.parametrize("mode", ["auto", "legacy"])
async def test_official_sdk_client_over_actual_subprocess(mode):
    params = StdioServerParameters(command=sys.executable, args=["-m", "task1"], cwd=str(ROOT))
    async with Client(params, mode=mode) as client:
        assert len((await client.list_tools()).tools) == 2
        result = await client.call_tool("trigger_refund", VALID_REFUND)
        assert result.structured_content["refundable_balance"] == "89.75"


def test_console_entry_point_and_process_restart_resets_state():
    with WireServer(console=True) as server:
        server.request("tools/call", {"name": "trigger_refund", "arguments": VALID_REFUND})
    with WireServer(console=True) as server:
        result = server.request(
            "tools/call", {"name": "trigger_refund", "arguments": VALID_REFUND}
        )["result"]["structuredContent"]
        assert result["refund_id"] == "REF-000001"
        assert result["refundable_balance"] == "89.75"


@pytest.mark.parametrize("token", ["NaN", "Infinity", "-Infinity", "1e309"])
def test_nonfinite_wire_amount_is_rejected_without_mutation(token):
    with WireServer() as server:
        server.send_raw(
            '{"jsonrpc":"2.0","id":"nonfinite","method":"tools/call",'
            '"params":{"name":"trigger_refund","arguments":'
            '{"customer_id":"CUST-00001","amount":' + token + ',"reason":"Synthetic request"}}}\n'
        )
        response = server.receive("nonfinite")
        assert response["error"]["code"] == -32602
        result = server.request(
            "tools/call", {"name": "trigger_refund", "arguments": VALID_REFUND}
        )["result"]["structuredContent"]
        assert result["refund_id"] == "REF-000001"
        assert result["refundable_balance"] == "89.75"
