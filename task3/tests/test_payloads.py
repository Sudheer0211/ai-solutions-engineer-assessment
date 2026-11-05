import json

import pytest

from task3_streaming.models import ErrorCode, Event, Kind, Limits, RawEvent, StreamError
from task3_streaming.payloads import inspect_event

pytestmark = pytest.mark.task3


@pytest.mark.parametrize(
    "name,data,expected",
    [
        ("delta", '{"channel":0,"text":"a\\u0040b.test"}', Event(Kind.DELTA, 0, "a@b.test")),
        ("delta", '{"channel":3,"text":"\\ud83d\\ude00"}', Event(Kind.DELTA, 3, "\U0001f600")),
        ("delta", '{"channel":0,"text":""}', Event(Kind.DELTA, 0)),
        ("done", '{"channel":0}', Event(Kind.DONE, 0)),
        ("end", "{}", Event(Kind.END)),
        ("error", '{"code":"upstream_error"}', Event(Kind.ERROR, code=ErrorCode.UPSTREAM)),
    ],
)
def test_exact_supported_payloads_and_decoded_json_escapes(name, data, expected):
    assert inspect_event(RawEvent(name, data)) == expected


@pytest.mark.parametrize(
    "name,data",
    [
        ("delta", '{"channel":0,"channel":1,"text":"x"}'),
        ("delta", '{"channel":0,"chann\\u0065l":1,"text":"x"}'),
        ("delta", '{"channel":0,"text":"private","text":"other"}'),
        ("delta", '{"channel":true,"text":"x"}'),
        ("delta", '{"channel":0.0,"text":"x"}'),
        ("delta", '{"channel":"0","text":"x"}'),
        ("delta", '{"channel":4,"text":"x"}'),
        ("delta", '{"channel":0,"text":null}'),
        ("delta", '{"channel":0,"text":"\\ud800"}'),
        ("delta", '{"channel":0,"text":"\\udfff"}'),
        ("delta", '{"channel":0,"text":"x","extra":1}'),
        ("delta", '{"channel":0,"text":"x","extra":{"x":1,"x":2}}'),
        ("delta", '{"channel":0}'),
        ("delta", "[]"),
        ("delta", "null"),
        ("delta", "1"),
        ("delta", '{"channel":NaN,"text":"x"}'),
        ("delta", '{"channel":Infinity,"text":"x"}'),
        ("delta", '{"channel":1e99999999999999,"text":"x"}'),
        ("delta", '{"channel":0,"text":"unterminated'),
        ("delta", '{"channel":0,"text":"x"} {}'),
        ("delta", '{"channel":0,"text":"\\x41"}'),
        ("done", '{"channel":0,"text":"x"}'),
        ("done", "{}"),
        ("end", '{"channel":0}'),
        ("message", "{}"),
        ("error", '{"code":"private-provider-error"}'),
        ("error", '{"code":"upstream_error","message":"private-diagnostic"}'),
    ],
)
def test_ambiguous_invalid_and_unknown_shapes_reject_without_raw_context(name, data):
    with pytest.raises(StreamError) as caught:
        inspect_event(RawEvent(name, data))
    assert "private" not in str(caught.value) + repr(caught.value)
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    "text,limits",
    [
        ("[" * 9 + "0" + "]" * 9, Limits()),
        ('{"x":' + "[" * 8 + "0" + "]" * 8 + "}", Limits()),
        ('{"x":12345678901234567}', Limits()),
        ('{"x":1e999999999999999999999999999999999999999999}', Limits()),
        ("{" + ",".join(f'"k{i}":0' for i in range(9)) + "}", Limits()),
        ('{"channel":0,"text":"x"}', Limits(json_depth=1, object_members=1)),
    ],
)
def test_json_resource_prechecks_fail_before_decoding_large_structures(text, limits):
    with pytest.raises(StreamError) as caught:
        inspect_event(RawEvent("delta", text), limits)
    assert caught.value.code is ErrorCode.LIMIT


def test_lexical_resource_scan_respects_quotes_escapes_and_delimiter_characters():
    text = 'braces {[[[]]]} : \\" numbers 12345678901234567890'
    assert inspect_event(RawEvent("delta", json.dumps({"channel": 0, "text": text}))).text == text


def test_payload_scalar_and_byte_limits_are_independent():
    assert (
        len(inspect_event(RawEvent("delta", json.dumps({"channel": 0, "text": "x" * 4096}))).text)
        == 4096
    )
    with pytest.raises(StreamError) as caught:
        inspect_event(RawEvent("delta", json.dumps({"channel": 0, "text": "x" * 4097})))
    assert caught.value.code is ErrorCode.LIMIT
    data = json.dumps({"channel": 0, "text": "\u2603" * 20}, ensure_ascii=False)
    assert inspect_event(RawEvent("delta", data), Limits(event_bytes=len(data.encode())))
    with pytest.raises(StreamError):
        inspect_event(RawEvent("delta", data), Limits(event_bytes=len(data.encode()) - 1))
    with pytest.raises(StreamError):
        inspect_event(RawEvent("delta", '{"channel":0,"text":"ab"}'), Limits(delta_chars=1))
