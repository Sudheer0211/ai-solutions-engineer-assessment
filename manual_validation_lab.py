
from tests.wire_support import WireServer

CUSTOMER = "CUST-00001"

invalid_cases = [
    ("invalid-customer-id", {
        "customer_id": "CUST-001",
        "amount": 10,
        "reason": "Duplicate payment",
    }),
    ("boolean-amount", {
        "customer_id": CUSTOMER,
        "amount": True,
        "reason": "Duplicate payment",
    }),
    ("string-amount", {
        "customer_id": CUSTOMER,
        "amount": "25.50",
        "reason": "Duplicate payment",
    }),
    ("negative-amount", {
        "customer_id": CUSTOMER,
        "amount": -10,
        "reason": "Duplicate payment",
    }),
    ("short-reason", {
        "customer_id": CUSTOMER,
        "amount": 10,
        "reason": "Short",
    }),
    ("unknown-field", {
        "customer_id": CUSTOMER,
        "amount": 10,
        "reason": "Duplicate payment",
        "extra": 123,
    }),
]

with WireServer("legacy") as server:
    for request_id, arguments in invalid_cases:
        response = server.request(
            "tools/call",
            {"name": "trigger_refund", "arguments": arguments},
            request_id,
        )

        assert response["id"] == request_id
        assert response["error"]["code"] == -32602
        assert "result" not in response

        print(f"PASS: {request_id} -> -32602")

    balance_response = server.request(
        "tools/call",
        {
            "name": "get_customer_record",
            "arguments": {"customer_id": CUSTOMER},
        },
        "verify-balance",
    )

    balance = balance_response["result"]["structuredContent"][
        "refundable_balance"
    ]

    assert balance == "100.00"

    print(f"Final balance: {balance}")
    print("ALL MCP VALIDATION CHECKS PASSED")
