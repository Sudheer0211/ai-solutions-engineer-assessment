"""T2-002: strict JSON inspection without coercing or reserializing opaque arguments."""

import json
from dataclasses import dataclass, field
from decimal import Decimal, DecimalException
from typing import Any

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
INVALID_PARAMS = -32602
UNAUTHORIZED_TOOL_CALL = -32001
RequestId = str | int | None


class RpcError(Exception):
    def __init__(
        self,
        code: int,
        message: str,
        request_id: RequestId = None,
        *,
        respond: bool = True,
    ) -> None:
        if (
            type(code) is not int
            or type(message) is not str
            or type(request_id) not in (str, int, type(None))
            or type(respond) is not bool
        ):
            raise TypeError("Invalid JSON-RPC error fields")
        super().__init__(message)
        self.code = code
        self.message = message
        self.request_id = request_id
        self.respond = respond

    def to_response(self) -> dict[str, Any] | None:
        """Construct a fresh error envelope, never an ordinary reply to a notification."""
        if not self.respond:
            return None
        return {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "error": {"code": self.code, "message": self.message},
        }


@dataclass(frozen=True, slots=True)
class InspectedRequest:
    method: str
    request_id: RequestId
    has_id: bool
    tool_name: str | None
    raw_body: bytes = field(repr=False)

    @property
    def is_notification(self) -> bool:
        return not self.has_id


class _JSONObject(dict[str, Any]):
    """Retain which ROOT keys were duplicated, independently of nested duplicates."""

    def __init__(self, pairs: list[tuple[str, Any]]) -> None:
        super().__init__()
        self.duplicate_keys: set[str] = set()
        for key, value in pairs:
            if key in self:
                self.duplicate_keys.add(key)
            self[key] = value


def _reject_constant(value: str) -> Any:
    raise ValueError("Nonstandard JSON numeric constant")


def _parse_decimal(value: str) -> Decimal:
    number = Decimal(value)
    # A disabled InvalidOperation trap can return NaN for an unsupported exponent.
    if not number.is_finite():
        raise ValueError("Unrepresentable JSON number")
    return number


def inspect_request(raw_body: bytes) -> InspectedRequest:
    if type(raw_body) is not bytes:
        raise TypeError("raw_body must be bytes")
    duplicates_found = False

    def object_hook(pairs: list[tuple[str, Any]]) -> _JSONObject:
        nonlocal duplicates_found
        result = _JSONObject(pairs)
        duplicates_found |= bool(result.duplicate_keys)
        return result

    try:
        envelope = json.loads(
            raw_body.decode("utf-8"),
            object_pairs_hook=object_hook,
            parse_float=_parse_decimal,
            parse_constant=_reject_constant,
        )
    except (ValueError, RecursionError, DecimalException):
        raise RpcError(PARSE_ERROR, "Parse error") from None

    if not isinstance(envelope, _JSONObject):
        # Includes batches: never produce partial permits from an array.
        raise RpcError(INVALID_REQUEST, "Invalid Request")
    candidate_id = envelope.get("id")
    valid_id = type(candidate_id) in (str, int, type(None))
    request_id = candidate_id if valid_id and "id" not in envelope.duplicate_keys else None
    notification = (
        "id" not in envelope
        and envelope.get("jsonrpc") == "2.0"
        and type(envelope.get("method")) is str
        and not {"jsonrpc", "method"}.intersection(envelope.duplicate_keys)
        and "result" not in envelope
        and "error" not in envelope
    )
    respond = not notification
    if (
        duplicates_found
        or envelope.get("jsonrpc") != "2.0"
        or type(envelope.get("method")) is not str
        or not valid_id
        or "result" in envelope
        or "error" in envelope
    ):
        raise RpcError(INVALID_REQUEST, "Invalid Request", request_id, respond=respond)

    method = envelope["method"]
    params = envelope.get("params")
    tool_name = None
    if "params" in envelope and not isinstance(params, dict | list):
        raise RpcError(INVALID_PARAMS, "Invalid params", request_id, respond=respond)
    if method == "tools/call":
        if (
            not isinstance(params, dict)
            or type(params.get("name")) is not str
            or not params["name"]
        ):
            raise RpcError(INVALID_PARAMS, "Invalid params", request_id, respond=respond)
        tool_name = params["name"]
    if method == "tools/list" and "params" in envelope and not isinstance(params, dict):
        raise RpcError(INVALID_PARAMS, "Invalid params", request_id, respond=respond)
    return InspectedRequest(method, request_id, "id" in envelope, tool_name, raw_body)
