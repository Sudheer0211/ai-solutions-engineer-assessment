
from tests.wire_support import WireServer

CUSTOMER_ID = "CUST-00001"


def call_tool(server, name, arguments, request_id):
    return server.request(
        "tools/call",
        {"name": name, "arguments": arguments},
        request_id,
    )


def get_balance(server, request_id):
    response = call_tool(
        server,
        "get_customer_record",
        {"customer_id": CUSTOMER_ID},
        request_id,
    )
    assert response["result"]["isError"] is False
    return response["result"]["structuredContent"]["refundable_balance"]


with WireServer("legacy") as server:

    # 1. Check initial state
    initial = get_balance(server, "lookup-1")
    print("Initial balance:", initial)
    assert initial == "100.00"

    # 2. First refund
    first = call_tool(
        server,
        "trigger_refund",
        {
            "customer_id": CUSTOMER_ID,
            "amount": 25.50,
            "reason": "Duplicate payment",
        },
        "refund-1",
    )
    assert first["result"]["isError"] is False
    print("First refund:", first["result"]["structuredContent"])

    balance_1 = get_balance(server, "lookup-2")
    assert balance_1 == "74.50"

    # 3. Second refund
    second = call_tool(
        server,
        "trigger_refund",
        {
            "customer_id": CUSTOMER_ID,
            "amount": 10.00,
            "reason": "Customer adjustment",
        },
        "refund-2",
    )
    assert second["result"]["isError"] is False
    print("Second refund:", second["result"]["structuredContent"])

    balance_2 = get_balance(server, "lookup-3")
    assert balance_2 == "64.50"

    # 4. Attempt an excessive refund
    failed = call_tool(
        server,
        "trigger_refund",
        {
            "customer_id": CUSTOMER_ID,
            "amount": 100.00,
            "reason": "Excessive refund test",
        },
        "refund-3",
    )
    assert failed["result"]["isError"] is True
    print("Failed refund:", failed["result"]["structuredContent"])

    # 5. Verify failed refund changed nothing
    final_balance = get_balance(server, "lookup-4")
    assert final_balance == "64.50"

    print("Final balance:", final_balance)
    print("ALL MANUAL REFUND CHECKS PASSED")
