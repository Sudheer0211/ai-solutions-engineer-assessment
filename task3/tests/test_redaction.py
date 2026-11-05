import random
import string

import pytest

from task3_streaming.models import ErrorCode, Event, Kind, Limits, StreamError
from task3_streaming.redaction import (
    CANDIDATE_ALPHABET,
    PII,
    Processor,
    Redactor,
    classify_candidate,
    is_canonical_email,
)
from tests.support import output, reference, run, stream, text_output, wire

pytestmark = pytest.mark.task3
VALUES = ["alpha.beta+tag@example.test", "+12025550123", "202-555-0123", "000-12-3456"]


@pytest.mark.parametrize(
    "value,kind",
    [
        (VALUES[0], PII.EMAIL),
        (VALUES[1], PII.PHONE),
        (VALUES[2], PII.PHONE),
        (VALUES[3], PII.SSN),
        ("@", PII.EMAIL_LIKE),
        ("decorator@invalid", PII.EMAIL_LIKE),
        ("prefix000-12-3456suffix", PII.SSN),
        ("000-12-3456+12025550123", PII.SSN),
    ],
)
def test_all_categories_and_conservative_whole_candidate_masking(value, kind):
    assert set(value) <= CANDIDATE_ALPHABET
    assert kind in classify_candidate(value)
    assert text_output(run(stream("Before " + value + " After"))) == "Before [REDACTED] After"


@pytest.mark.parametrize(
    "value,expected",
    [
        ("a@b.co", True),
        ("a.b_%+-@sub.example.test", True),
        ("a" * 64 + "@example.test", True),
        ("a" * 65 + "@example.test", False),
        ("a..b@example.test", False),
        (".a@example.test", False),
        ("a.@example.test", False),
        ("a@-example.test", False),
        ("a@example-.test", False),
        ("a@example.1t", False),
        ("a@example.t", False),
        ("a@localhost", False),
        ("\u00e9@example.test", False),
        ('"a"@example.test', False),
        ("a@" + "b" * 63 + ".test", True),
        ("a@" + "b" * 64 + ".test", False),
        ("a@" + ".".join(["b" * 63] * 3 + ["c" * 60]), True),
        ("a@" + ".".join(["b" * 63] * 3 + ["c" * 61]), False),
    ],
)
def test_canonical_email_grammar_and_exact_lengths(value, expected):
    assert is_canonical_email(value) is expected


@pytest.mark.parametrize(
    "text",
    [
        "ordinary prose 1234567",
        "+1234567",
        "+012345678",
        "+1234567890123456",
        "1202-555-01234",
        "1000-12-34567",
        "202 555 0123",
        "(202) 555 0123",
        "\uff11\uff12\uff13\uff14",
        "user%40example.test",
        "card 0000000000000000",
        "\u2603 e\u0301 \U0001f600",
        "literal\\u0040example.test",
    ],
)
def test_out_of_scope_forms_and_unmatched_unicode_are_not_normalized(text):
    assert text_output(run(stream(text))) == reference(text) == text


@pytest.mark.parametrize("value", VALUES)
def test_every_transport_byte_split_and_every_model_delta_split(value):
    raw = stream("start " + value + " end", ascii_json=False)
    for cut in range(len(raw) + 1):
        assert text_output(run(raw, [cut, len(raw) - cut])) == "start [REDACTED] end"
    for cut in range(len(value) + 1):
        raw = (
            wire("delta", {"channel": 0, "text": value[:cut]})
            + wire("delta", {"channel": 0, "text": value[cut:]})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
        assert text_output(run(raw)) == "[REDACTED]"


def test_all_short_candidate_partitions_and_no_prefix_before_done():
    value = "a@b.co"
    for mask in range(1 << (len(value) - 1)):
        parts = []
        start = 0
        for cut in range(1, len(value)):
            if mask & (1 << (cut - 1)):
                parts.append(value[start:cut])
                start = cut
        parts.append(value[start:])
        processor = Processor()
        for part in parts:
            assert list(processor.feed(wire("delta", {"channel": 0, "text": part}))) == []
        frames = list(processor.feed(wire("done", {"channel": 0}) + wire("end", {})))
        assert text_output(frames) == "[REDACTED]"


@pytest.mark.parametrize("size", [255, 256, 257])
@pytest.mark.parametrize("sensitive", [False, True])
def test_candidate_255_256_257_never_release_at_retention_threshold(size, sensitive):
    value = ("@" if sensitive else "a") + "x" * (size - 1)
    processor = Processor()
    if size > 256:
        with pytest.raises(StreamError) as caught:
            list(processor.feed(wire("delta", {"channel": 0, "text": value})))
        assert caught.value.code is ErrorCode.LIMIT
        assert processor.redactor.stats.held_chars == 0
    else:
        assert list(processor.feed(wire("delta", {"channel": 0, "text": value}))) == []
        assert processor.redactor.stats.held_chars == size
        frames = list(processor.feed(wire("done", {"channel": 0}) + wire("end", {})))
        assert text_output(frames) == ("[REDACTED]" if sensitive else value)


def test_four_channels_independent_shared_delta_state_and_no_cross_channel_join():
    processor = Processor()
    frames = []
    for channel, text in [
        (0, "a@"),
        (1, "not-an-"),
        (2, "000-"),
        (3, "\u2603 "),
        (0, "b.co"),
        (1, "email"),
        (2, "12-3456"),
    ]:
        frames.extend(processor.feed(wire("delta", {"channel": channel, "text": text})))
    for channel in [3, 1, 2, 0]:
        frames.extend(processor.feed(wire("done", {"channel": channel})))
    frames.extend(processor.feed(wire("end", {})))
    assert [text_output(frames, c) for c in range(4)] == [
        "[REDACTED]",
        "not-an-email",
        "[REDACTED]",
        "\u2603 ",
    ]
    other = run(
        wire("delta", {"channel": 0, "text": "a"})
        + wire("delta", {"channel": 1, "text": "@b.co"})
        + wire("done", {"channel": 0})
        + wire("done", {"channel": 1})
        + wire("end", {})
    )
    assert text_output(other, 0) == "a" and text_output(other, 1) == "[REDACTED]"


@pytest.mark.parametrize(
    "sequence",
    [
        [("done", {"channel": 0})],
        [("delta", {"channel": 0, "text": "a@"}), ("end", {})],
        [
            ("delta", {"channel": 0, "text": "x"}),
            ("done", {"channel": 0}),
            ("done", {"channel": 0}),
        ],
        [
            ("delta", {"channel": 0, "text": "x"}),
            ("done", {"channel": 0}),
            ("delta", {"channel": 0, "text": "x"}),
        ],
        [("delta", {"channel": True, "text": "x"})],
        [("delta", {"channel": 4, "text": "x"})],
    ],
)
def test_invalid_channel_transitions(sequence):
    processor = Processor()
    with pytest.raises(StreamError):
        for name, value in sequence:
            list(processor.feed(wire(name, value)))
    assert not processor.redactor.success and processor.redactor.stats.held_chars == 0


@pytest.mark.parametrize("suffix", [b"", b"event: end\ndata: {}", b"\xe2\x82", b"data: {}\n\n"])
def test_unexpected_eof_never_flushes_unresolved_text(suffix):
    processor = Processor()
    assert list(processor.feed(wire("delta", {"channel": 0, "text": "private@pending"}))) == []
    with pytest.raises(StreamError) as caught:
        list(processor.feed(suffix))
        list(processor.finish())
    assert "private" not in str(caught.value) + repr(caught.value)
    assert processor.redactor.stats.held_chars == 0


def test_only_valid_done_finalizes_tail_error_clears_every_channel():
    processor = Processor()
    assert list(processor.feed(wire("delta", {"channel": 0, "text": "private@pending"}))) == []
    frames = list(processor.feed(wire("error", {"code": "upstream_error"}) + wire("end", {})))
    assert output(frames) == [
        ("error", {"code": "upstream_error", "message": "Upstream service failed"})
    ]
    assert processor.redactor.terminal and not processor.redactor.success
    assert processor.redactor.stats.held_chars == 0 and list(processor.finish()) == []


def test_empty_stream_terminal_stops_before_untrusted_trailing_bytes():
    assert output(run(wire("end", {}) + b"\xffprivate")) == [("end", {})]


@pytest.mark.parametrize("seed", range(32))
def test_random_chunk_and_delta_partitions_match_independent_reference(seed):
    rng = random.Random(seed)
    text = "\u2603 ordinary " + " | ".join(VALUES) + " \U0001f600 @decorator tail"
    payloads = []
    start = 0
    while start < len(text):
        end = min(len(text), start + rng.randint(1, 13))
        payloads.append(wire("delta", {"channel": 0, "text": text[start:end]}, ascii_json=False))
        start = end
    raw = b"".join(payloads) + wire("done", {"channel": 0}) + wire("end", {})
    sizes = []
    total = 0
    while total < len(raw):
        sizes.append(rng.randint(1, 37))
        total += sizes[-1]
    frames = run(raw, sizes)
    assert text_output(frames) == reference(text)
    for value in VALUES:
        assert value not in text_output(frames)


def test_multibyte_unicode_and_decoded_ascii_escapes_across_every_byte_boundary():
    for ascii_json in [False, True]:
        raw = stream("\u2603\U0001f600 a@b.test \u00e9 e\u0301", ascii_json=ascii_json)
        for cut in range(len(raw) + 1):
            assert (
                text_output(run(raw, [cut, len(raw) - cut]))
                == "\u2603\U0001f600 [REDACTED] \u00e9 e\u0301"
            )
    raw = (
        b'event: delta\ndata: {"channel":0,"text":"a\\u0040b.test"}\n\n'
        + wire("done", {"channel": 0})
        + wire("end", {})
    )
    assert text_output(run(raw, [1] * len(raw))) == "[REDACTED]"


def test_long_stream_retained_state_independent_of_event_count():
    processor = Processor()
    count = 0
    for _ in range(5000):
        for frame in processor.feed(wire("delta", {"channel": 0, "text": "ordinary "})):
            count += len(output([frame])[0][1]["text"])
        assert processor.parser.stats.event_bytes == 0
        assert processor.redactor.stats.pending_chars == processor.redactor.stats.held_chars == 0
    assert count == 5000 * 9
    list(processor.feed(wire("done", {"channel": 0}) + wire("end", {})))
    assert processor.redactor.stats.peak_candidate_chars == 8
    assert processor.redactor.stats.peak_pending_chars <= 256
    assert processor.peak_encoded_bytes <= 8192


def test_four_maximum_holds_do_not_accumulate_event_envelopes():
    processor = Processor()
    for channel in range(4):
        assert list(processor.feed(wire("delta", {"channel": channel, "text": "a" * 256}))) == []
    for _ in range(1000):
        assert list(processor.feed(wire("delta", {"channel": 0, "text": ""}))) == []
    assert processor.redactor.stats.held_chars == processor.redactor.stats.peak_held_chars == 1024
    assert processor.parser.stats.event_bytes == 0
    processor.abort()
    assert processor.redactor.stats.held_chars == 0


def test_tightened_pending_scalar_byte_and_channel_caps_independent():
    redactor = Redactor(Limits(pending_chars=1))
    with pytest.raises(StreamError) as caught:
        list(redactor.process(Event(Kind.DELTA, 0, "ab ")))
    assert caught.value.code is ErrorCode.LIMIT
    redactor = Redactor(Limits(output_bytes=1))
    with pytest.raises(StreamError):
        list(redactor.process(Event(Kind.DELTA, 0, "\u2603")))
    redactor = Redactor(Limits(channels=1))
    list(redactor.process(Event(Kind.DELTA, 0, "")))
    with pytest.raises(StreamError):
        list(redactor.process(Event(Kind.DELTA, 1, "")))


def test_safe_prefix_is_delivered_without_consuming_complete_stream():
    processor = Processor()
    frames = list(processor.feed(wire("delta", {"channel": 0, "text": "safe text private@"})))
    assert text_output(frames) == "safe text "
    assert processor.redactor.stats.held_chars == len("private@")
    assert not processor.redactor.terminal


def test_no_sensitive_output_or_error_details_logs_or_abandoned_state(caplog, capsys):
    processor = Processor()
    raw = wire("delta", {"channel": 0, "text": "private@example.test " + "x" * 257})
    frames = []
    with pytest.raises(StreamError) as caught:
        for frame in processor.feed(raw):
            frames.append(frame)
    assert "private@example.test" not in text_output(frames) + str(caught.value) + repr(
        caught.value
    )
    assert processor.redactor.stats.held_chars == 0
    assert caplog.text == "" and capsys.readouterr() == ("", "")
    processor = Processor()
    iterator = processor.feed(stream("safe private@example.test " * 20))
    next(iterator)
    iterator.close()
    assert processor.redactor.stats.held_chars == processor.parser.stats.event_bytes == 0
    with pytest.raises(StreamError):
        list(processor.finish())


def test_candidate_alphabet_is_exact_and_detector_has_no_extra_pattern_characters():
    assert CANDIDATE_ALPHABET == frozenset(string.ascii_letters + string.digits + "._%+@-")
    for value in VALUES + ["@", "alpha+tag@example.test"]:
        assert set(value) <= CANDIDATE_ALPHABET and classify_candidate(value)
    for value in ["", "x y", "\u00e9", "x" * 257]:
        with pytest.raises(StreamError):
            classify_candidate(value)


@pytest.mark.parametrize("newline", [b"\n", b"\r", b"\r\n"])
@pytest.mark.parametrize("step", [1, 2, 11])
def test_composed_multiline_sse_and_cr_at_eof_terminal(newline, step):
    raw = (
        newline.join(
            [
                b": private-comment",
                b"id: private-id",
                b"event: delta",
                b'data: {"channel":0,',
                b'data: "text":"a@b.test"}',
                b"",
                b"",
            ]
        )
        + wire("done", {"channel": 0}, newline)
        + wire("end", {}, newline)
    )
    frames = run(raw, [step] * (len(raw) // step + 1))
    assert text_output(frames) == "[REDACTED]"
    assert [kind for kind, _ in output(frames)] == ["delta", "done", "end"]
    assert b"private" not in b"".join(frames)


def test_composition_rejects_encoded_output_overflow_without_success_or_raw_tail():
    processor = Processor(Limits(output_bytes=128))
    with pytest.raises(StreamError) as caught:
        list(processor.feed(wire("delta", {"channel": 0, "text": "\x00" * 30})))
    assert caught.value.code is ErrorCode.LIMIT
    assert processor.peak_encoded_bytes == 0 and not processor.redactor.success
    assert processor.redactor.stats.pending_chars == processor.redactor.stats.held_chars == 0


def test_missing_global_end_is_failure_even_after_valid_channel_done():
    processor = Processor()
    frames = list(
        processor.feed(
            wire("delta", {"channel": 0, "text": "a@b.test"}) + wire("done", {"channel": 0})
        )
    )
    assert text_output(frames) == "[REDACTED]"
    with pytest.raises(StreamError):
        list(processor.finish())
    assert not processor.redactor.success


def test_four_closed_channel_ids_still_cannot_be_reused():
    processor = Processor()
    for channel in range(4):
        list(
            processor.feed(
                wire("delta", {"channel": channel, "text": ""}) + wire("done", {"channel": channel})
            )
        )
    with pytest.raises(StreamError):
        list(processor.feed(wire("delta", {"channel": 0, "text": "private"})))


def test_interleaved_processors_have_no_shared_candidate_or_terminal_state():
    first, second = Processor(), Processor()
    assert list(first.feed(wire("delta", {"channel": 0, "text": "first@"}))) == []
    frames = list(second.feed(stream("ordinary ")))
    assert text_output(frames) == "ordinary "
    assert not first.redactor.terminal and first.redactor.stats.held_chars == 6
    frames = list(
        first.feed(
            wire("delta", {"channel": 0, "text": "example.test"})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
    )
    assert text_output(frames) == "[REDACTED]"


def test_terminal_encoder_failure_and_abandoned_terminal_cannot_claim_success():
    processor = Processor(Limits(output_bytes=1))
    with pytest.raises(StreamError) as caught:
        list(processor.feed(wire("end", {})))
    assert caught.value.code is ErrorCode.LIMIT and not processor.redactor.success
    processor = Processor()
    iterator = processor.feed(wire("end", {}))
    next(iterator)
    iterator.close()
    assert not processor.redactor.success


@pytest.mark.parametrize(
    "value,masked",
    [
        ("+12345678", True),
        ("+123456789012345", True),
        ("+1234567", False),
        ("+1234567890123456", False),
        ("+02345678", False),
        ("000-000-0000", True),
        ("000-00-0000", True),
        ("1000-00-00001", False),
        ("x+12345678y", True),
        ("1+12345678", False),
    ],
)
def test_phone_ssn_numeric_boundaries_exactly_match_approved_syntax(value, masked):
    expected = "[REDACTED]" if masked else value
    assert text_output(run(stream(value))) == reference(value) == expected


@pytest.mark.parametrize("seed", range(16))
def test_bounded_adversarial_candidates_differential_reference(seed):
    rng = random.Random(seed)
    alphabet = string.ascii_letters + string.digits + "._%+-"
    values = ["".join(rng.choices(alphabet, k=rng.randint(1, 256))) for _ in range(40)]
    values += ["a." * 128, "1-" * 128, "+" + "1" * 255]
    values += ["prefix" + value + "suffix" for value in VALUES]
    text = " ".join(values)
    assert text_output(run(stream(text[:4096]))) == reference(text[:4096])
    # Full random content is emitted as bounded deltas, never one oversized payload.
    raw = b"".join(
        wire("delta", {"channel": 0, "text": text[i : i + 97]}) for i in range(0, len(text), 97)
    )
    raw += wire("done", {"channel": 0}) + wire("end", {})
    assert text_output(run(raw)) == reference(text)
