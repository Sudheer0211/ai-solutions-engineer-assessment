"""T2-C3/T2-C4/T2-C5: pure Bearer and exact role policy behavior."""

import secrets

import pytest

from task2_proxy import security
from task2_proxy.rpc import RpcError, inspect_request
from task2_proxy.security import AuthenticationError, authenticate, authorize
from task2_proxy.settings import Role

pytestmark = pytest.mark.task2


@pytest.mark.parametrize("scheme", ["Bearer", "bearer", "BEARER", "bEaReR"])
@pytest.mark.parametrize("role", [Role.ADMIN, Role.VIEWER])
def test_known_tokens_resolve_to_trusted_roles(credentials, scheme, role):
    token = credentials.admin if role is Role.ADMIN else credentials.viewer
    assert authenticate([f"{scheme} {token}"], credentials.settings) is role


def test_allowed_http_whitespace(credentials):
    assert authenticate([f" \tBearer   {credentials.admin}\t "], credentials.settings) is Role.ADMIN


@pytest.mark.parametrize(
    "headers",
    [
        None,
        [],
        [""],
        ["Bearer"],
        ["Bearer "],
        ["Basic opaque"],
        ["Bearer wrong-token"],
        ["Bearer x y"],
        ["Bearer x,y"],
        ["Bearer\tx"],
        ["Bearer é"],
        ["Bearer %61dmin"],
        ["Bearer x\r\nRole: admin"],
        [None],
        [True],
        "Bearer x",
        b"Bearer x",
    ],
)
def test_bad_credentials_are_generic_auth_failures(credentials, headers):
    with pytest.raises(AuthenticationError) as caught:
        authenticate(headers, credentials.settings)
    assert str(caught.value) == "Invalid Bearer credentials"


def test_duplicate_headers_are_rejected_even_when_both_valid(credentials):
    for headers in (
        [f"Bearer {credentials.admin}", f"Bearer {credentials.viewer}"],
        [f"Bearer {credentials.admin}", f"Bearer {credentials.admin}"],
    ):
        with pytest.raises(AuthenticationError):
            authenticate(headers, credentials.settings)


def test_token_comparison_is_case_sensitive(credentials):
    with pytest.raises(AuthenticationError):
        authenticate([f"Bearer {credentials.admin.swapcase()}"], credentials.settings)


@pytest.mark.parametrize("match_role", [Role.ADMIN, Role.VIEWER, None])
def test_every_candidate_is_compared(credentials, monkeypatch, match_role):
    original = secrets.compare_digest
    count = 0

    def compare(left, right):
        nonlocal count
        count += 1
        return original(left, right)

    monkeypatch.setattr(security.secrets, "compare_digest", compare)
    token = (
        credentials.admin
        if match_role is Role.ADMIN
        else credentials.viewer
        if match_role is Role.VIEWER
        else secrets.token_urlsafe(32)
    )
    if match_role is None:
        with pytest.raises(AuthenticationError):
            authenticate([f"Bearer {token}"], credentials.settings)
    else:
        assert authenticate([f"Bearer {token}"], credentials.settings) is match_role
    assert count == len(credentials.settings.bindings)


@pytest.mark.parametrize("request_id", [0, 42, "", "request-17", None, 2**100])
def test_viewer_denial_has_exact_contract_and_id(rpc_body, request_id):
    request = inspect_request(rpc_body(name="admin_reset", request_id=request_id))
    with pytest.raises(RpcError) as caught:
        authorize(Role.VIEWER, request)
    assert caught.value.to_response() == {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32001, "message": "Unauthorized Tool Call"},
    }
    assert type(caught.value.request_id) is type(request_id)


@pytest.mark.parametrize("name", ["admin_", "admin_reset", "admin_世界", "admin_\noperation"])
def test_admin_can_authorize_protected_tools(rpc_body, name):
    authorize(Role.ADMIN, inspect_request(rpc_body(name=name)))


@pytest.mark.parametrize(
    "name",
    [
        "read_record",
        "trigger_refund",
        "admin",
        "Admin_reset",
        "ADMIN_reset",
        "xadmin_reset",
        " admin_reset",
        "аdmin_reset",
    ],
)
def test_literal_prefix_does_not_expand_to_other_names(rpc_body, name):
    authorize(Role.VIEWER, inspect_request(rpc_body(name=name)))


@pytest.mark.parametrize("role", [None, True, "admin", "viewer", "owner"])
def test_untrusted_role_strings_cannot_authorize(rpc_body, role):
    with pytest.raises(AuthenticationError):
        authorize(role, inspect_request(rpc_body(name="admin_reset")))
