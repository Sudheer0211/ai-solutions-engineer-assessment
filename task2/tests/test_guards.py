"""T2-002: the pure guard cannot return permits for denied/unsupported input."""

import json

import pytest

from task2_proxy.rpc import RpcError
from task2_proxy.security import AuthenticationError, guard_request
from task2_proxy.settings import Role

pytestmark = pytest.mark.task2


@pytest.mark.parametrize(
    "raw",
    [
        b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"\\u0061dmin_reset"}}',
        b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"admin\\u005freset"}}',
        b'{"jsonrpc":"2.0","id":7,"method":"tools/call","par\\u0061ms":{"na\\u006de":"admin_reset"}}',
        b'{"jsonrpc":"2.0","id":7,"method":"tools\\u002fcall","params":{"name":"admin_reset"}}',
    ],
)
def test_encoded_names_and_selectors_cannot_bypass_viewer_policy(credentials, raw):
    with pytest.raises(RpcError) as caught:
        guard_request([f"Bearer {credentials.viewer}"], raw, credentials.settings)
    assert caught.value.to_response() == {
        "jsonrpc": "2.0",
        "id": 7,
        "error": {"code": -32001, "message": "Unauthorized Tool Call"},
    }


def test_authentication_precedes_json_inspection(credentials):
    with pytest.raises(AuthenticationError):
        guard_request([], b"{", credentials.settings)


def test_body_claims_and_nested_names_cannot_override_policy(credentials):
    raw = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "role": "admin",
            "params": {"name": "admin_reset", "arguments": {"name": "safe", "role": "admin"}},
        }
    ).encode()
    with pytest.raises(RpcError) as caught:
        guard_request([f"Bearer {credentials.viewer}"], raw, credentials.settings)
    assert caught.value.code == -32001


@pytest.mark.parametrize(
    "role,name",
    [(Role.ADMIN, "admin_reset"), (Role.VIEWER, "read_record"), (Role.VIEWER, "trigger_refund")],
)
def test_supported_authorized_request_yields_immutable_raw_permit(
    credentials, rpc_body, role, name
):
    token = credentials.admin if role is Role.ADMIN else credentials.viewer
    raw = rpc_body(name=name)
    permit = guard_request([f"Bearer {token}"], raw, credentials.settings)
    assert permit.role is role
    assert permit.request.raw_body is raw
    assert permit.request.tool_name == name


@pytest.mark.parametrize("role", [Role.ADMIN, Role.VIEWER])
def test_discovery_is_authorized_without_a_tool_filter(credentials, role):
    token = credentials.admin if role is Role.ADMIN else credentials.viewer
    raw = b'{"jsonrpc":"2.0","id":0,"method":"tools/list"}'
    permit = guard_request([f"Bearer {token}"], raw, credentials.settings)
    assert permit.request.method == "tools/list"
    assert permit.request.raw_body is raw


@pytest.mark.parametrize(
    "role,name,code",
    [
        (Role.ADMIN, "admin_reset", -32600),
        (Role.VIEWER, "read_record", -32600),
        (Role.VIEWER, "admin_reset", -32001),
    ],
)
def test_notifications_are_inspected_authorized_and_never_permitted(credentials, role, name, code):
    token = credentials.admin if role is Role.ADMIN else credentials.viewer
    raw = json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name}}).encode()
    with pytest.raises(RpcError) as caught:
        guard_request([f"Bearer {token}"], raw, credentials.settings)
    assert caught.value.code == code
    assert caught.value.to_response() is None
    if code == -32001:
        assert caught.value.message == "Unauthorized Tool Call"


def test_mixed_batch_is_rejected_wholly(credentials):
    raw = json.dumps(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "admin_reset"}},
        ]
    ).encode()
    with pytest.raises(RpcError) as caught:
        guard_request([f"Bearer {credentials.viewer}"], raw, credentials.settings)
    assert caught.value.code == -32600
    assert caught.value.request_id is None


def test_guard_library_emits_no_logs_or_credentials(credentials, rpc_body, capsys):
    with pytest.raises(RpcError):
        guard_request(
            [f"Bearer {credentials.viewer}"], rpc_body(name="admin_reset"), credentials.settings
        )
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
