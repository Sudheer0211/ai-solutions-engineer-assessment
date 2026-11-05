import pytest

from task3_streaming.models import (
    DEFAULT_LIMITS,
    ErrorCode,
    Event,
    Kind,
    Limits,
    RawEvent,
    StreamError,
)
from task3_streaming.sse import SSEParser, encode_event
from tests.support import output

pytestmark = pytest.mark.task3


def parsed(raw, step=4096, limits=DEFAULT_LIMITS):
    parser = SSEParser(limits)
    events = []
    for start in range(0, len(raw), step):
        events.extend(parser.feed(raw[start : start + step]))
    events.extend(parser.finish())
    return events, parser


@pytest.mark.parametrize("newline", [b"\n", b"\r", b"\r\n"])
@pytest.mark.parametrize("step", [1, 2, 3, 7, 4096])
def test_line_endings_bom_metadata_and_multiline_data(newline, step):
    lines = [
        b"\xef\xbb\xbf: private-comment",
        b"id: private-id",
        b"retry: 123",
        b"unknown: private",
        b"event: delta",
        b'data: {"channel":0,',
        b'data: "text":"\xe2\x98\x83"}',
        b"",
        b"",
    ]
    events, parser = parsed(newline.join(lines), step)
    assert events == [RawEvent("delta", '{"channel":0,\n"text":"\u2603"}')]
    assert parser.stats.decoder_bytes == 0 and parser.stats.peak_decoder_bytes <= 3
    assert parser.stats.event_bytes == parser.stats.line_bytes == 0


@pytest.mark.parametrize(
    "raw", [b"", b"\n\n", b":comment\n\n", b"id: x\nretry: nope\nx\n\n", b" \n\n"]
)
def test_empty_and_metadata_only_blocks_not_dispatched(raw):
    assert parsed(raw)[0] == []


@pytest.mark.parametrize(
    "raw",
    [
        b"event: end\nevent: end\ndata: {}\n\n",
        b"event: end\n\n",
        b"data: {}\n\n",
        b"event: end\ndata: {}",
        b"event: end\ndata: {}\n",
        b":unterminated",
        b"\xff",
        b"\xc0\xaf",
        b"\xed\xa0\x80",
        b"\xf4\x90\x80\x80",
        b"\xe2\x82",
        b"\xe2\r\n",
    ],
)
def test_malformed_or_incomplete_input_latches_failure_without_raw_details(raw):
    parser = SSEParser()
    with pytest.raises(StreamError) as caught:
        list(parser.feed(raw))
        list(parser.finish())
    assert caught.value.code is ErrorCode.INVALID
    assert caught.value.__context__ is None
    assert parser.stats.decoder_bytes == parser.stats.line_bytes == parser.stats.event_bytes == 0
    with pytest.raises(StreamError):
        list(parser.feed(b"event: end\ndata: {}\n\n"))


@pytest.mark.parametrize("newline", [b"\n", b"\r", b"\r\n"])
def test_line_byte_limit_includes_complete_terminator(newline):
    cap = 32
    raw = b":" + b"x" * (cap - 1 - len(newline)) + newline + newline
    _, parser = parsed(raw, 1, Limits(line_bytes=cap))
    assert parser.stats.peak_line_bytes == cap
    with pytest.raises(StreamError) as caught:
        parsed(b":" + b"x" * (cap - len(newline)) + newline + newline, 1, Limits(line_bytes=cap))
    assert caught.value.code is ErrorCode.LIMIT


def test_line_limit_is_raw_bytes_not_unicode_characters_and_bom_counts():
    parsed(b":" + "\u2603".encode() * 10 + b"\n\n", 1, Limits(line_bytes=32))
    with pytest.raises(StreamError):
        parsed(b":" + "\u2603".encode() * 11 + b"\n\n", 1, Limits(line_bytes=32))
    with pytest.raises(StreamError):
        parsed(b"\xef\xbb\xbf:" + b"x" * 28 + b"\n\n", 1, Limits(line_bytes=32))


def test_event_limit_cannot_be_bypassed_with_comments_or_metadata():
    raw = b":123\nid:ab\n\n"
    _, parser = parsed(raw, 1, Limits(event_bytes=len(raw)))
    assert parser.stats.peak_event_bytes == len(raw)
    with pytest.raises(StreamError) as caught:
        parsed(raw, 1, Limits(event_bytes=len(raw) - 1))
    assert caught.value.code is ErrorCode.LIMIT
    with pytest.raises(StreamError):
        parsed(b":x\n" * 6000 + b"\n", 4096)


def test_chunk_limit_empty_feed_and_single_use_finish():
    parser = SSEParser()
    assert list(parser.feed(b"")) == []
    assert list(parser.feed(b":" + b"x" * 4095)) == []
    with pytest.raises(StreamError):
        list(SSEParser().feed(b"x" * 4097))
    assert list(SSEParser().finish()) == []
    parser = SSEParser()
    list(parser.finish())
    with pytest.raises(StreamError):
        list(parser.finish())


@pytest.mark.parametrize(
    "text", ["\n\r\x00\t", '"\\', "\u2603\U0001f600", "event: end\ndata: {}\n\n", "x" * 256]
)
def test_encoder_escapes_text_without_sse_injection(text):
    encoded = encode_event(Event(Kind.DELTA, 0, text))
    assert output([encoded]) == [("delta", {"channel": 0, "text": text})]


def test_serialized_byte_limit_separate_from_scalar_limit():
    event = Event(Kind.DELTA, 0, "\x00" * 20)
    encoded = encode_event(event)
    assert encode_event(event, Limits(output_bytes=len(encoded))) == encoded
    with pytest.raises(StreamError) as caught:
        encode_event(event, Limits(output_bytes=len(encoded) - 1))
    assert caught.value.code is ErrorCode.LIMIT
    with pytest.raises(StreamError):
        encode_event(Event(Kind.DELTA, 0, "x" * 257))
    with pytest.raises(StreamError):
        encode_event(Event(Kind.DELTA, 0, "xx"), Limits(pending_chars=1))


@pytest.mark.parametrize("code", list(ErrorCode))
def test_error_encoder_uses_fixed_code_and_message(code):
    event = output([encode_event(Event(Kind.ERROR, code=code))])[0]
    assert event[0] == "error" and set(event[1]) == {"code", "message"}
    assert event[1]["code"] == code


def test_abandoned_iterator_clears_retained_parser_state():
    parser = SSEParser()
    iterator = parser.feed(b"event: end\ndata: {}\n\nprivate")
    assert next(iterator) == RawEvent("end", "{}")
    iterator.close()
    assert parser.stats.event_bytes == 0
    with pytest.raises(StreamError):
        list(parser.feed(b"\n\n"))


def test_default_8192_line_and_16384_event_exact_boundaries():
    line = b":" + b"x" * 8190 + b"\n"
    raw = line + b":" + b"x" * 8189 + b"\n\n"
    assert len(line) == 8192 and len(raw) == 16384
    events, parser = parsed(raw)
    assert events == []
    assert parser.stats.peak_line_bytes == 8192 and parser.stats.peak_event_bytes == 16384
    with pytest.raises(StreamError) as caught:
        parsed(line + line + b"\n")
    assert caught.value.code is ErrorCode.LIMIT
    with pytest.raises(StreamError):
        parsed(b":" + b"x" * 8191 + b"\n\n")


def test_tightened_raw_chunk_limit_is_independent_of_event_capacity():
    parser = SSEParser(Limits(chunk_bytes=3))
    assert list(parser.feed(b":xx")) == []
    with pytest.raises(StreamError) as caught:
        list(parser.feed(b"xxxx"))
    assert caught.value.code is ErrorCode.LIMIT


def test_decoder_holds_at_most_three_bytes_of_incomplete_four_byte_scalar():
    parser = SSEParser()
    assert list(parser.feed(b"data: \xf0\x9f\x98")) == []
    assert parser.stats.decoder_bytes == parser.stats.peak_decoder_bytes == 3
    assert list(parser.feed(b"\x80\nevent: delta\n\n")) == [RawEvent("delta", "\U0001f600")]
    assert parser.stats.decoder_bytes == 0
