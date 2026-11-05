"""Bounded SSE bytes/framing and safe serialization, not an HTTP transport."""

import codecs
import json
from collections.abc import Iterator
from itertools import chain

from task3_streaming.models import (
    DEFAULT_LIMITS,
    MESSAGES,
    ErrorCode,
    Event,
    Kind,
    Limits,
    ParserStats,
    RawEvent,
    StreamError,
)


class SSEParser:
    """Consume each iterator fully or close it; abandoned iteration fails closed.

    Counters include raw BOM/terminators. A CR is deferred to distinguish CRLF
    before dispatch or limit accounting. No chunk/event queue is retained.
    """

    def __init__(self, limits: Limits = DEFAULT_LIMITS) -> None:
        self.limits = limits
        self._decoder = codecs.getincrementaldecoder("utf-8-sig")("strict")
        self._line: list[str] = []
        self._data: list[str] = []
        self._name: str | None = None
        self._cr = self._busy = self._failed = self._finished = False
        self._line_bytes = self._event_bytes = 0
        self._peak_line = self._peak_event = self._peak_decoder = 0

    @property
    def stats(self) -> ParserStats:
        return ParserStats(
            self._line_bytes,
            self._event_bytes,
            len(self._decoder.getstate()[0]),
            self._peak_line,
            self._peak_event,
            self._peak_decoder,
        )

    def abort(self) -> None:
        self._line.clear()
        self._data.clear()
        self._name = None
        self._decoder.reset()
        self._line_bytes = self._event_bytes = 0
        self._cr = False
        self._failed = True

    def _count(self) -> None:
        if self._failed:
            raise StreamError()
        if (
            self._line_bytes >= self.limits.line_bytes
            or self._event_bytes >= self.limits.event_bytes
        ):
            raise StreamError(ErrorCode.LIMIT)
        self._line_bytes += 1
        self._event_bytes += 1
        self._peak_line = max(self._peak_line, self._line_bytes)
        self._peak_event = max(self._peak_event, self._event_bytes)

    def _decode(self, data: bytes, *, final: bool = False) -> str:
        text = None
        try:
            text = self._decoder.decode(data, final=final)
        except UnicodeError:
            pass
        if text is None:  # Outside except: no raw UnicodeDecodeError context.
            raise StreamError()
        self._peak_decoder = max(self._peak_decoder, len(self._decoder.getstate()[0]))
        return text

    def _end_line(self) -> RawEvent | None:
        line = "".join(self._line)
        self._line.clear()
        self._line_bytes = 0
        if not line:
            result = None
            if self._name is not None or self._data:
                if self._name is None or not self._data:
                    raise StreamError()
                result = RawEvent(self._name, "\n".join(self._data))
            self._name = None
            self._data.clear()
            self._event_bytes = 0
            return result
        if line.startswith(":"):
            return None
        name, separator, value = line.partition(":")
        if not separator:
            value = ""
        elif value.startswith(" "):
            value = value[1:]
        if name == "event":
            if self._name is not None:
                raise StreamError()
            self._name = value
        elif name == "data":
            self._data.append(value)
        # id/retry/unknown fields never become an output or retained authority.
        return None

    def feed(self, chunk: bytes) -> Iterator[RawEvent]:
        if self._failed or self._finished or self._busy or type(chunk) is not bytes:
            self.abort()
            raise StreamError()
        if len(chunk) > self.limits.chunk_bytes:
            self.abort()
            raise StreamError(ErrorCode.LIMIT)
        self._busy = True
        complete = False
        try:
            for byte in chunk:
                if self._cr:
                    self._cr = False
                    if byte == 10:
                        self._count()
                        self._decode(bytes((byte,)))
                        result = self._end_line()
                        if result is not None:
                            yield result
                        continue
                    result = self._end_line()
                    if result is not None:
                        yield result
                self._count()
                text = self._decode(bytes((byte,)))
                if byte == 13:
                    self._cr = True
                elif byte == 10:
                    result = self._end_line()
                    if result is not None:
                        yield result
                elif text:
                    self._line.append(text)
            complete = True
        finally:
            self._busy = False
            if not complete:
                self.abort()

    def finish(self) -> Iterator[RawEvent]:
        if self._failed or self._finished or self._busy:
            self.abort()
            raise StreamError()
        self._busy = True
        complete = False
        try:
            self._decode(b"", final=True)
            if self._cr:
                self._cr = False
                result = self._end_line()
                if result is not None:
                    yield result
            if self._event_bytes:
                raise StreamError()  # Even ignored metadata must be fully framed.
            self._finished = True
            complete = True
        finally:
            self._busy = False
            if not complete:
                self.abort()


def encode_event(event: Event, limits: Limits = DEFAULT_LIMITS) -> bytes:
    """Encode ONLY redactor output. This shape encoder is not a redaction boundary."""
    if type(event) is not Event:
        raise StreamError()
    if event.kind is Kind.DELTA:
        if len(event.text) > limits.fragment_chars or len(event.text) > limits.pending_chars:
            raise StreamError(ErrorCode.LIMIT)
        data = {"channel": event.channel, "text": event.text}
    elif event.kind is Kind.DONE:
        data = {"channel": event.channel}
    elif event.kind is Kind.END:
        data = {}
    else:
        data = {"code": event.code, "message": MESSAGES[event.code]}
    encoded = bytearray()
    encoder = json.JSONEncoder(ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    for part in chain((f"event: {event.kind}\ndata: ",), encoder.iterencode(data), ("\n\n",)):
        chunk = part.encode("utf-8")
        if len(encoded) + len(chunk) > limits.output_bytes:
            raise StreamError(ErrorCode.LIMIT)
        encoded.extend(chunk)
    return bytes(encoded)
