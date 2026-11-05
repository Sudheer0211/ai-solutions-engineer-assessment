"""Strict synthetic payload validation; no provider-specific shapes or coercion."""

import json

from task3_streaming.models import (
    DEFAULT_LIMITS,
    ErrorCode,
    Event,
    Kind,
    Limits,
    RawEvent,
    StreamError,
)


def _bounded_lexical_check(text: str, limits: Limits) -> None:
    """Resource precheck only; stdlib JSON remains the syntax/escape parser."""
    stack: list[list[object]] = []
    quoted = escaped = False
    index = 0
    while index < len(text):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            if len(stack) >= limits.json_depth:
                raise StreamError(ErrorCode.LIMIT)
            stack.append([char, 0])
        elif char in "]}":
            if not stack or stack[-1][0] != ("[" if char == "]" else "{"):
                raise StreamError()
            stack.pop()
        elif char == ":" and stack and stack[-1][0] == "{":
            stack[-1][1] += 1
            if stack[-1][1] > limits.object_members:
                raise StreamError(ErrorCode.LIMIT)
        elif char in "-0123456789":
            start = index
            while index < len(text) and text[index] in "0123456789eE+.-":
                index += 1
                if index - start > limits.number_bytes:
                    raise StreamError(ErrorCode.LIMIT)
            continue
        index += 1


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in items:
        if key in result:
            raise StreamError()
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise StreamError()


def inspect_event(raw: RawEvent, limits: Limits = DEFAULT_LIMITS) -> Event:
    if type(raw) is not RawEvent:
        raise StreamError()
    if len(raw.data.encode("utf-8")) > limits.event_bytes:
        raise StreamError(ErrorCode.LIMIT)
    _bounded_lexical_check(raw.data, limits)
    value = None
    failed = False
    try:
        value = json.loads(raw.data, object_pairs_hook=_pairs, parse_constant=_constant)
    except (ValueError, RecursionError, StreamError):
        failed = True
    if failed or type(value) is not dict:
        raise StreamError()  # No raw JSONDecodeError retained as context.
    if raw.name == "delta" and set(value) == {"channel", "text"}:
        event = Event(Kind.DELTA, value["channel"], value["text"])
        if len(event.text) > limits.delta_chars:
            raise StreamError(ErrorCode.LIMIT)
        return event
    if raw.name == "done" and set(value) == {"channel"}:
        return Event(Kind.DONE, value["channel"])
    if raw.name == "end" and not value:
        return Event(Kind.END)
    if raw.name == "error" and value == {"code": "upstream_error"}:
        return Event(Kind.ERROR, code=ErrorCode.UPSTREAM)
    raise StreamError()
