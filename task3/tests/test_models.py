from dataclasses import FrozenInstanceError, fields

import pytest

from task3_streaming.models import ErrorCode, Event, Kind, Limits, RawEvent, StreamError

pytestmark = pytest.mark.task3


@pytest.mark.parametrize("field", [f.name for f in fields(Limits)])
@pytest.mark.parametrize("value", [True, False, 0, -1, 1.0, "1", None, 100000])
def test_limits_are_exact_positive_integers_and_cannot_enlarge_contract(field, value):
    with pytest.raises(StreamError):
        Limits(**{field: value})


@pytest.mark.parametrize("channel", [True, False, -1, 4, 0.0, "0", None])
@pytest.mark.parametrize("kind", [Kind.DELTA, Kind.DONE])
def test_channel_types_and_range(channel, kind):
    with pytest.raises(StreamError):
        Event(kind, channel)


@pytest.mark.parametrize(
    "kind,channel,text,code",
    [
        ("delta", 0, "", None),
        (Kind.END, 0, "", None),
        (Kind.END, None, "x", None),
        (Kind.DONE, 0, "x", None),
        (Kind.DELTA, 0, "", ErrorCode.INVALID),
        (Kind.ERROR, None, "", None),
        (Kind.ERROR, None, "", "private-diagnostic"),
        (Kind.DELTA, 0, 1, None),
        (Kind.DELTA, 0, "\ud800", None),
    ],
)
def test_invalid_event_records_do_not_reflect_values(kind, channel, text, code):
    with pytest.raises(StreamError) as caught:
        Event(kind, channel, text, code)
    assert "private-diagnostic" not in str(caught.value)


def test_records_immutable_and_payload_representations_private():
    event = Event(Kind.DELTA, 0, "private-marker@example.test")
    raw = RawEvent("private-event-name", "private-data")
    for obj, field, value in [
        (event, "text", "changed"),
        (raw, "data", "changed"),
        (Limits(), "channels", 2),
    ]:
        with pytest.raises(FrozenInstanceError):
            setattr(obj, field, value)
    assert "private-marker" not in repr(event)
    assert "private" not in repr(raw)


@pytest.mark.parametrize("code", list(ErrorCode))
def test_only_fixed_error_messages(code):
    error = StreamError(code)
    assert error.code is code and error.__context__ is None
    assert error.args == (str(error),)
