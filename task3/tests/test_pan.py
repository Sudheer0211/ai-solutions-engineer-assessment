"""T3-007: synthetic PANs, no Luhn filter, whole-stream reference/privacy checks."""

import random

import pytest

from task3_streaming.models import ErrorCode, Event, Kind, StreamError
from task3_streaming.redaction import PII, Processor, Redactor, classify_candidate
from tests.support import output, reference, run, stream, text_output, wire

pytestmark = pytest.mark.task3


def pan(length=16, separator=""):
    digits = ("4111111111111111111")[:length]
    return separator.join(digits[i : i + 4] for i in range(0, length, 4))


@pytest.mark.parametrize("length", range(13, 20))
@pytest.mark.parametrize("separator", ["", "-", " "])
def test_pan_all_lengths_formats_every_byte_and_delta_cut(length, separator, caplog):
    value = pan(length, separator)
    raw = stream("Before (" + value + ") after")
    for cut in range(len(raw) + 1):
        frames = run(raw, [cut, len(raw) - cut])
        assert text_output(frames) == "Before ([REDACTED]) after"
        assert value not in str(output(frames)) + caplog.text
    for cut in range(len(value) + 1):
        p = Processor()
        assert list(p.feed(wire("delta", {"channel": 0, "text": value[:cut]}))) == []
        assert list(p.feed(wire("delta", {"channel": 0, "text": value[cut:]}))) == []
        assert text_output(list(p.feed(wire("done", {"channel": 0}) + wire("end", {})))) == (
            "[REDACTED]"
        )


@pytest.mark.parametrize(
    "text,expected",
    [
        ("0000000000000000", "[REDACTED]"),  # Deliberately not Luhn-gated.
        ("1111111111111", "[REDACTED]"),
        ("id:4111 1111-1111 1111!", "id:[REDACTED]!"),
        ("4111 1111 1111 1111.", "[REDACTED]"),  # Whole compound K-candidate.
        ("x4111111111111111y", "[REDACTED]"),
        ("4111 1111 1111 1111@invalid", "[REDACTED]"),
        ("4111 1111 1111 1111+12025550123", "[REDACTED]"),
        ("123,4111111111111111;456", "123,[REDACTED];456"),
        ("\u26034111 1111 1111 1111\U0001f600", "\u2603[REDACTED]\U0001f600"),
        ("411111111111", "411111111111"),
        ("41111111111111111111", "41111111111111111111"),
        ("4111  1111  1111  1111", "4111  1111  1111  1111"),
        ("4111\t1111\t1111\t1111", "4111\t1111\t1111\t1111"),
        ("4111--1111-1111-1111", "4111--1111-1111-1111"),
        ("word4111 1111 1111 1111", "word4111 1111 1111 1111"),
        ("\uff14\uff11\uff11\uff11" * 4, "\uff14\uff11\uff11\uff11" * 4),
    ],
)
def test_pan_boundaries_overlaps_false_positives_and_out_of_scope(text, expected):
    assert text_output(run(stream(text))) == reference(text) == expected
    assert PII.PAN in classify_candidate("0000000000000000")


@pytest.mark.parametrize("seed", range(24))
def test_pan_random_fragmentation_interleaved_channels_and_reference(seed):
    rng = random.Random(seed)
    values = {
        c: "start \u2603 (" + pan(13 + c * 2, ["", " ", "-", " "][c]) + ") tail" for c in range(4)
    }
    rest = dict(values)
    p, frames = Processor(), []
    while rest:
        c = rng.choice(list(rest))
        n = rng.randint(1, 5)
        part, rest[c] = rest[c][:n], rest[c][n:]
        raw = wire("delta", {"channel": c, "text": part}, ascii_json=bool(seed % 2))
        for i in range(0, len(raw), 3):
            frames.extend(p.feed(raw[i : i + 3]))
        if not rest[c]:
            frames.extend(p.feed(wire("done", {"channel": c})))
            del rest[c]
    frames.extend(p.feed(wire("end", {})))
    assert output(frames)[-1] == ("end", {})
    for c in values:
        assert text_output(frames, c) == reference(values[c]) == "start \u2603 ([REDACTED]) tail"


@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"])
def test_pan_json_escapes_multibyte_unicode_and_one_byte_sse(newline):
    raw = wire("delta", {"channel": 0, "text": "\u2603 "}, newline, ascii_json=False)
    for char in pan(19, " "):
        part = wire("delta", {"channel": 0, "text": char}, newline)
        if "0" <= char <= "9":
            part = part.replace(char.encode(), f"\\u{ord(char):04x}".encode())
        raw += part
    raw += wire("done", {"channel": 0}, newline) + wire("end", {}, newline)
    assert text_output(run(raw, [1] * len(raw))) == "\u2603 [REDACTED]"


@pytest.mark.parametrize("suffix", [b"", b"\xff", b"event: end\ndata: {}\n\n"])
def test_pan_unsafe_eof_malformed_termination_never_flushes(suffix, caplog):
    p = Processor()
    assert list(p.feed(wire("delta", {"channel": 0, "text": "4111 1111 1111 "}))) == []
    with pytest.raises(StreamError) as caught:
        list(p.feed(suffix))
        list(p.finish())
    assert "4111" not in str(caught.value) + repr(caught.value) + caplog.text
    assert p.redactor.stats.held_chars == 0 and not p.redactor.success


@pytest.mark.parametrize("value", ["1 " * 20, "1" * 257, "4111 " + "2" + "a" * 256])
def test_pan_overflow_fails_closed_without_retention_threshold_release(value):
    p, emitted = Processor(), []
    with pytest.raises(StreamError) as caught:
        for char in value:
            emitted.extend(p.feed(wire("delta", {"channel": 0, "text": char})))
    assert caught.value.code is ErrorCode.LIMIT
    assert text_output(emitted) == ""
    assert p.redactor.stats.held_chars == 0


def test_pan_additive_bridge_state_bounded_without_expanding_generic_candidate_cap():
    p = Processor()
    text = "1 " * 18 + "2" + "a" * 255
    for c in range(4):
        assert list(p.feed(wire("delta", {"channel": c, "text": text}))) == []
    assert p.redactor.stats.held_chars == 1168
    assert p.redactor.stats.peak_candidate_chars == 256
    for c in range(4):
        assert text_output(list(p.feed(wire("done", {"channel": c}))), c) == "[REDACTED]"
    assert output(list(p.feed(wire("end", {})))) == [("end", {})]


def test_pan_abandoned_iterator_clears_bridge_and_channel_state():
    redactor = Redactor()
    assert list(redactor.process(Event(Kind.DELTA, 0, "4111 1111 "))) == []
    iterator = redactor.process(Event(Kind.DELTA, 0, "1111 1111!"))
    next(iterator)
    iterator.close()
    assert redactor.stats.held_chars == 0 and not redactor.success
    assert redactor._spaces == set()


def test_pan_long_stream_retains_no_unbounded_numeric_or_prose_history():
    p = Processor()
    for _ in range(3000):
        frames = list(p.feed(wire("delta", {"channel": 0, "text": "card 4111 1111 1111 1111! "})))
        assert text_output(frames) == "card [REDACTED]! "
        assert p.redactor.stats.held_chars == 0
    assert p.redactor.stats.peak_held_chars <= 38
    assert p.redactor.stats.peak_pending_chars <= 256
    frames = list(p.feed(wire("done", {"channel": 0}) + wire("end", {})))
    assert text_output(frames) == ""
