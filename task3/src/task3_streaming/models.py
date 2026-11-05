"""T3-001/002 immutable, bounded records; never reflect untrusted values in errors."""

from dataclasses import dataclass, field, fields
from enum import StrEnum


class ErrorCode(StrEnum):
    INVALID = "invalid_stream"
    UPSTREAM = "upstream_error"
    LIMIT = "stream_limit_exceeded"
    TIMEOUT = "stream_timeout"
    UNAVAILABLE = "service_unavailable"


MESSAGES = {
    ErrorCode.INVALID: "Invalid upstream stream",
    ErrorCode.UPSTREAM: "Upstream service failed",
    ErrorCode.LIMIT: "Stream limit exceeded",
    ErrorCode.TIMEOUT: "Stream timed out",
    ErrorCode.UNAVAILABLE: "Service unavailable",
}


class StreamError(Exception):
    def __init__(self, code: ErrorCode = ErrorCode.INVALID) -> None:
        if type(code) is not ErrorCode:
            code = ErrorCode.INVALID
        self.code = code
        super().__init__(MESSAGES[code])


def scalar_text(value: object, maximum: int) -> str:
    if type(value) is not str:
        raise StreamError()
    if len(value) > maximum:
        raise StreamError(ErrorCode.LIMIT)
    if any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        raise StreamError()
    return value


class Kind(StrEnum):
    DELTA = "delta"
    DONE = "done"
    END = "end"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class Limits:
    """Approved maxima; trusted callers may tighten, never enlarge, individual caps."""

    chunk_bytes: int = 4096
    line_bytes: int = 8192
    event_bytes: int = 16384
    delta_chars: int = 4096
    candidate_chars: int = 256
    channels: int = 4
    pending_chars: int = 1024
    output_bytes: int = 8192
    fragment_chars: int = 256
    json_depth: int = 8
    number_bytes: int = 16
    object_members: int = 8

    def __post_init__(self) -> None:
        for f in fields(self):
            value = getattr(self, f.name)
            if type(value) is not int or not 1 <= value <= f.default:
                raise StreamError()


DEFAULT_LIMITS = Limits()


@dataclass(frozen=True, slots=True)
class RawEvent:
    name: str = field(repr=False)
    data: str = field(repr=False)

    def __post_init__(self) -> None:
        scalar_text(self.name, 8192)
        scalar_text(self.data, 16384)


@dataclass(frozen=True, slots=True)
class Event:
    kind: Kind
    channel: int | None = None
    text: str = field(default="", repr=False)
    code: ErrorCode | None = None

    def __post_init__(self) -> None:
        if type(self.kind) is not Kind:
            raise StreamError()
        scalar_text(self.text, 4096)
        if self.kind in (Kind.DELTA, Kind.DONE):
            if type(self.channel) is not int or not 0 <= self.channel <= 3 or self.code:
                raise StreamError()
            if self.kind is Kind.DONE and self.text:
                raise StreamError()
        elif self.channel is not None or self.text:
            raise StreamError()
        if self.kind is Kind.ERROR:
            if type(self.code) is not ErrorCode:
                raise StreamError()
        elif self.code is not None:
            raise StreamError()


@dataclass(frozen=True, slots=True)
class ParserStats:
    line_bytes: int
    event_bytes: int
    decoder_bytes: int
    peak_line_bytes: int
    peak_event_bytes: int
    peak_decoder_bytes: int


@dataclass(frozen=True, slots=True)
class RedactionStats:
    held_chars: int
    pending_chars: int
    pending_bytes: int
    peak_candidate_chars: int
    peak_held_chars: int
    peak_pending_chars: int
    peak_pending_bytes: int
    channels: int
