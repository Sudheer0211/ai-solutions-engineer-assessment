"""T2-C6/T2-C7: unambiguous JSON, request IDs and explicit shape handling."""

import json
from dataclasses import FrozenInstanceError
from decimal import InvalidOperation, localcontext

import pytest

from task2_proxy.rpc import RpcError, inspect_request

pytestmark = pytest.mark.task2


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"{",
        b'{"id":42,',
        b"not-json",
        b"\xff",
        b'{"jsonrpc":"2.0","id":1,"method":"x","params":[NaN]}',
        b'{"jsonrpc":"2.0","id":1,"method":"x","params":[Infinity]}',
        b'{"jsonrpc":"2.0","id":1,"method":"x","params":[-Infinity]}',
    ],
)
def test_parse_errors_never_recover_partial_id(raw):
    with pytest.raises(RpcError) as caught:
        inspect_request(raw)
    assert caught.value.to_response() == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32700, "message": "Parse error"},
    }


@pytest.mark.parametrize(
    "value", [None, True, 5, "request", [], [{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}]]
)
def test_scalars_and_batches_have_no_partial_permits(value):
    with pytest.raises(RpcError) as caught:
        inspect_request(json.dumps(value).encode())
    assert caught.value.code == -32600
    assert caught.value.request_id is None


@pytest.mark.parametrize(
    "changes",
    [
        {"jsonrpc": "1.0"},
        {"jsonrpc": 2},
        {"jsonrpc": None},
        {"method": 7},
        {"method": None},
        {"result": {}},
        {"error": {"code": 0, "message": "x"}},
    ],
)
def test_malformed_envelope_preserves_unique_top_level_id(changes):
    body = {"jsonrpc": "2.0", "id": "top-id", "method": "tools/list", **changes}
    with pytest.raises(RpcError) as caught:
        inspect_request(json.dumps(body).encode())
    assert caught.value.code == -32600
    assert caught.value.request_id == "top-id"


@pytest.mark.parametrize("request_id", [True, False, 1.5, 1.0, [], {}])
def test_invalid_id_is_not_coerced(request_id, rpc_body):
    with pytest.raises(RpcError) as caught:
        inspect_request(rpc_body(request_id=request_id))
    assert caught.value.code == -32600
    assert caught.value.request_id is None


@pytest.mark.parametrize("request_id", [0, -7, 2**100, "", "x", None])
def test_supported_ids_are_preserved_with_explicit_null_distinct_from_missing(request_id, rpc_body):
    request = inspect_request(rpc_body(request_id=request_id))
    assert request.request_id == request_id
    assert type(request.request_id) is type(request_id)
    assert request.has_id
    assert not request.is_notification


@pytest.mark.parametrize(
    "raw,expected_id",
    [
        (b'{"jsonrpc":"2.0","id":1,"id":2,"method":"tools/list"}', None),
        (b'{"jsonrpc":"2.0","id":0,"method":"tools/list","method":"tools/call"}', 0),
        (
            b'{"jsonrpc":"2.0","id":"outer","method":"tools/call","params":{"name":"x","name":"admin_x"}}',
            "outer",
        ),
        (
            b'{"jsonrpc":"2.0","id":"outer","method":"tools/call","params":{"name":"x","na\\u006de":"admin_x"}}',
            "outer",
        ),
        (
            b'{"jsonrpc":"2.0","id":"outer","method":"x","params":{"nested":[{"id":"inner","a":1,"a":2}]}}',
            "outer",
        ),
        (b'{"jsonrpc":"2.0","id":"outer","method":"x","params":{"id":1,"id":2}}', "outer"),
    ],
)
def test_duplicate_keys_anywhere_rejected_without_using_nested_id(raw, expected_id):
    with pytest.raises(RpcError) as caught:
        inspect_request(raw)
    assert caught.value.code == -32600
    assert caught.value.request_id == expected_id


@pytest.mark.parametrize(
    "params",
    [
        None,
        [],
        {},
        {"name": None},
        {"name": 1},
        {"name": True},
        {"name": ""},
        {"arguments": {"name": "read_record"}},
    ],
)
def test_invalid_tool_parameters(params):
    body = {"jsonrpc": "2.0", "id": 0, "method": "tools/call", "params": params}
    with pytest.raises(RpcError) as caught:
        inspect_request(json.dumps(body).encode())
    assert caught.value.code == -32602
    assert caught.value.request_id == 0


def test_missing_tool_parameters_and_required_envelope_fields():
    for field, code in [("params", -32602), ("method", -32600), ("jsonrpc", -32600)]:
        body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "x"}}
        del body[field]
        with pytest.raises(RpcError) as caught:
            inspect_request(json.dumps(body).encode())
        assert caught.value.code == code


@pytest.mark.parametrize(
    "method,params",
    [
        ("tools/list", {}),
        ("tools/list", {"cursor": "next"}),
        ("vendor/extension", []),
        ("vendor/extension", {"x": 1}),
    ],
)
def test_discovery_and_other_methods_preserve_original_bytes(method, params):
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
            "_meta": {"extension": True},
        },
        indent=2,
    ).encode()
    assert inspect_request(raw).raw_body is raw


def test_large_numeric_arguments_and_extensions_remain_opaque():
    raw = (
        b'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":'
        b'{"name":"read","arguments":{"large":1e9999,"exact":0.1234567890123456789}},'
        b'"vendor_extension":{"value":true}}'
    )
    request = inspect_request(raw)
    assert request.raw_body is raw
    with pytest.raises(FrozenInstanceError):
        request.tool_name = "admin_reset"


@pytest.mark.parametrize(
    "number",
    [
        b"1e999999999999999999999999999999999999999",
        b"1e-999999999999999999999999999999999999999",
        b"-1e999999999999999999999999999999999999999",
        b"0e999999999999999999999999999999999999999",
    ],
)
@pytest.mark.parametrize("location", ["extension", "arguments", "id"])
@pytest.mark.parametrize("trap_invalid", [True, False])
def test_unrepresentable_exponents_are_parse_errors(number, location, trap_invalid):
    if location == "extension":
        raw = b'{"jsonrpc":"2.0","id":1,"method":"tools/list","extra":' + number + b"}"
    elif location == "arguments":
        raw = (
            b'{"jsonrpc":"2.0","id":1,"method":"tools/call",'
            b'"params":{"name":"read","arguments":{"value":' + number + b"}}}"
        )
    else:
        raw = b'{"jsonrpc":"2.0","method":"tools/list","id":' + number + b"}"
    with localcontext() as context:
        context.traps[InvalidOperation] = trap_invalid
        with pytest.raises(RpcError) as caught:
            inspect_request(raw)
    assert caught.value.to_response() == {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": -32700, "message": "Parse error"},
    }


@pytest.mark.parametrize("number", [b"1e9999", b"1e-9999", b"0.1234567890123456789"])
@pytest.mark.parametrize("location", ["extension", "arguments"])
def test_representable_numbers_preserve_raw_body(number, location):
    if location == "extension":
        raw = b'{"jsonrpc":"2.0","id":1,"method":"tools/list","extra":' + number + b"}"
    else:
        raw = (
            b'{"jsonrpc":"2.0","id":1,"method":"tools/call",'
            b'"params":{"name":"read","arguments":{"value":' + number + b"}}}"
        )
    request = inspect_request(raw)
    assert request.raw_body is raw
    assert request.request_id == 1
    assert request.tool_name == ("read" if location == "arguments" else None)


def test_error_construction_is_fresh_and_suppresses_notification_replies():
    error = RpcError(-32602, "Invalid params", "original")
    response = error.to_response()
    response["id"] = "mutated"
    response["error"]["message"] = "mutated"
    assert error.to_response()["id"] == "original"
    assert error.to_response()["error"]["message"] == "Invalid params"
    assert RpcError(-32600, "Invalid Request", respond=False).to_response() is None


@pytest.mark.parametrize("fields", [(True, "x", 1), (-32600, 5, 1), (-32600, "x", True)])
def test_error_builder_rejects_invalid_field_types(fields):
    with pytest.raises(TypeError):
        RpcError(*fields)
