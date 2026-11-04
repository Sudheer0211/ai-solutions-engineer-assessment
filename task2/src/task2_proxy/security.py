"""T2-002: pure authentication/authorization; no endpoint or forwarding side effects."""

import re
import secrets
from collections.abc import Sequence
from dataclasses import dataclass

from task2_proxy.rpc import (
    INVALID_PARAMS,
    INVALID_REQUEST,
    UNAUTHORIZED_TOOL_CALL,
    InspectedRequest,
    RpcError,
    inspect_request,
)
from task2_proxy.settings import Role, SecuritySettings

_BEARER = re.compile(r"(?i:Bearer) +([A-Za-z0-9._~+/-]+=*)")


class AuthenticationError(Exception):
    def __init__(self) -> None:
        super().__init__("Invalid Bearer credentials")


@dataclass(frozen=True, slots=True)
class AuthorizedRequest:
    role: Role
    request: InspectedRequest


def authenticate(header_values: Sequence[str], settings: SecuritySettings) -> Role:
    """Require a single header, compare all candidates, never trust client role claims."""
    if (
        not isinstance(header_values, Sequence)
        or isinstance(header_values, str | bytes)
        or len(header_values) != 1
    ):
        raise AuthenticationError()
    value = header_values[0]
    if type(value) is not str:
        raise AuthenticationError()
    match = _BEARER.fullmatch(value.strip(" \t"))
    if match is None:
        raise AuthenticationError()
    credential = match[1]
    role = None
    for binding in settings.bindings:
        if secrets.compare_digest(credential, binding.token):
            role = binding.role
    if role is None:
        raise AuthenticationError()
    return role


def authorize(role: Role, request: InspectedRequest) -> None:
    if type(role) is not Role:
        raise AuthenticationError()
    if request.method == "tools/call":
        if type(request.tool_name) is not str or not request.tool_name:
            raise RpcError(
                INVALID_PARAMS, "Invalid params", request.request_id, respond=request.has_id
            )
        if request.tool_name.startswith("admin_") and role is not Role.ADMIN:
            raise RpcError(
                UNAUTHORIZED_TOOL_CALL,
                "Unauthorized Tool Call",
                request.request_id,
                respond=request.has_id,
            )


def guard_request(
    header_values: Sequence[str], raw_body: bytes, settings: SecuritySettings
) -> AuthorizedRequest:
    role = authenticate(header_values, settings)
    request = inspect_request(raw_body)
    authorize(role, request)
    if request.is_notification:
        raise RpcError(INVALID_REQUEST, "Notifications are not supported", respond=False)
    return AuthorizedRequest(role, request)
