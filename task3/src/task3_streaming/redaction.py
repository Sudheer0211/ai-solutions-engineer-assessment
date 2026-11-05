"""T3-P1/P3 candidate proof and pure, pull-driven composition. No network I/O."""

import re
import string
from collections.abc import Iterator
from contextlib import closing
from enum import StrEnum

from task3_streaming.models import (
    DEFAULT_LIMITS,
    ErrorCode,
    Event,
    Kind,
    Limits,
    RedactionStats,
    StreamError,
)
from task3_streaming.payloads import inspect_event
from task3_streaming.sse import SSEParser, encode_event

CANDIDATE_ALPHABET = frozenset(string.ascii_letters + string.digits + "._%+@-")
REPLACEMENT = "[REDACTED]"
_ATOM = re.compile(r"[A-Za-z0-9_%+-]+")
_LABEL = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?")
_TLD = re.compile(r"[A-Za-z]{2,63}")
_PHONE = re.compile(r"(?<![0-9])(?:\+[1-9][0-9]{7,14}|[0-9]{3}-[0-9]{3}-[0-9]{4})(?![0-9])")
_SSN = re.compile(r"(?<![0-9])[0-9]{3}-[0-9]{2}-[0-9]{4}(?![0-9])")


class PII(StrEnum):
    EMAIL = "email"
    EMAIL_LIKE = "email_like"
    PHONE = "phone"
    SSN = "ssn"


def is_canonical_email(candidate: str) -> bool:
    if type(candidate) is not str or len(candidate) > 254 or candidate.count("@") != 1:
        return False
    local, domain = candidate.split("@")
    if not 1 <= len(local) <= 64 or not 1 <= len(domain) <= 253:
        return False
    atoms, labels = local.split("."), domain.split(".")
    return (
        all(_ATOM.fullmatch(atom) is not None for atom in atoms)
        and len(labels) >= 2
        and all(_LABEL.fullmatch(label) is not None for label in labels)
        and _TLD.fullmatch(labels[-1]) is not None
    )


def classify_candidate(candidate: str) -> frozenset[PII]:
    if type(candidate) is not str or not candidate or len(candidate) > 256:
        raise StreamError()
    if any(c not in CANDIDATE_ALPHABET for c in candidate):
        raise StreamError()
    kinds = set()
    if "@" in candidate:
        kinds.add(PII.EMAIL if is_canonical_email(candidate) else PII.EMAIL_LIKE)
    if _PHONE.search(candidate):
        kinds.add(PII.PHONE)
    if _SSN.search(candidate):
        kinds.add(PII.SSN)
    return frozenset(kinds)


class Redactor:
    """Request-local channels. Only real delimiters/validated done classify a tail."""

    def __init__(self, limits: Limits = DEFAULT_LIMITS) -> None:
        self.limits = limits
        self._holds: dict[int, str] = {}
        self._closed: set[int] = set()
        self._pending = ""
        self._pending_bytes = 0
        self._peak_candidate = self._peak_held = 0
        self._peak_pending = self._peak_pending_bytes = 0
        self._busy = self._failed = self.terminal = self.success = False

    @property
    def stats(self) -> RedactionStats:
        return RedactionStats(
            sum(map(len, self._holds.values())),
            len(self._pending),
            self._pending_bytes,
            self._peak_candidate,
            self._peak_held,
            self._peak_pending,
            self._peak_pending_bytes,
            len(self._holds) + len(self._closed),
        )

    def abort(self) -> None:
        self._holds.clear()
        self._closed.clear()
        self._pending = ""
        self._pending_bytes = 0
        self._failed = True
        self.success = False

    def _drain(self, channel: int) -> Iterator[Event]:
        if self._pending:
            text = self._pending
            self._pending = ""
            self._pending_bytes = 0
            yield Event(Kind.DELTA, channel, text)

    def _safe(self, channel: int, text: str) -> Iterator[Event]:
        for char in text:
            if self._failed:
                raise StreamError()
            size = len(char.encode("utf-8"))
            if (
                len(self._pending) >= self.limits.pending_chars
                or self._pending_bytes + size > self.limits.output_bytes
            ):
                raise StreamError(ErrorCode.LIMIT)
            self._pending += char
            self._pending_bytes += size
            self._peak_pending = max(self._peak_pending, len(self._pending))
            self._peak_pending_bytes = max(self._peak_pending_bytes, self._pending_bytes)
            if len(self._pending) >= self.limits.fragment_chars:
                yield from self._drain(channel)

    def _classify(self, channel: int) -> Iterator[Event]:
        candidate = self._holds[channel]
        self._holds[channel] = ""
        if candidate:
            yield from self._safe(
                channel, REPLACEMENT if classify_candidate(candidate) else candidate
            )

    def process(self, event: Event) -> Iterator[Event]:
        if self._failed or self.terminal or self._busy or type(event) is not Event:
            self.abort()
            raise StreamError()
        self._busy = True
        complete = False
        try:
            if event.kind is Kind.ERROR:
                self.abort()
                self.terminal = True
                yield Event(Kind.ERROR, code=ErrorCode.UPSTREAM)
            elif event.kind is Kind.END:
                if self._holds:
                    raise StreamError()
                self.terminal = self.success = True
                yield event
            else:
                channel = event.channel
                if channel in self._closed:
                    raise StreamError()
                if event.kind is Kind.DONE:
                    if channel not in self._holds:
                        raise StreamError()
                    yield from self._classify(channel)
                    yield from self._drain(channel)
                    del self._holds[channel]
                    self._closed.add(channel)
                    yield event
                else:
                    if len(event.text) > self.limits.delta_chars:
                        raise StreamError(ErrorCode.LIMIT)
                    if channel not in self._holds:
                        if len(self._holds) + len(self._closed) >= self.limits.channels:
                            raise StreamError(ErrorCode.LIMIT)
                        self._holds[channel] = ""
                    for char in event.text:
                        if self._failed:
                            raise StreamError()
                        if char in CANDIDATE_ALPHABET:
                            if len(self._holds[channel]) >= self.limits.candidate_chars:
                                raise StreamError(ErrorCode.LIMIT)
                            self._holds[channel] += char
                            self._peak_candidate = max(
                                self._peak_candidate, len(self._holds[channel])
                            )
                            self._peak_held = max(
                                self._peak_held, sum(map(len, self._holds.values()))
                            )
                        else:
                            yield from self._classify(channel)
                            yield from self._safe(channel, char)
                    yield from self._drain(channel)
            complete = True
        finally:
            self._busy = False
            if not complete:
                self.abort()


class Processor:
    """Pure parser -> profile -> redactor -> encoder. Fully consume/close each call.

    Terminal end/error stops input, including trailing bytes in the current chunk.
    A malformed-input exception drops raw tails; a future transport owns delivering
    a fixed error event. No async lifecycle or network behavior is implemented here.
    """

    def __init__(self, limits: Limits = DEFAULT_LIMITS) -> None:
        self.limits = limits
        self.parser = SSEParser(limits)
        self.redactor = Redactor(limits)
        self.peak_encoded_bytes = 0
        self._busy = self._failed = False

    def abort(self) -> None:
        self.parser.abort()
        self.redactor.abort()
        self._failed = True

    def _events(self, source: Iterator) -> Iterator[bytes]:
        with closing(source):
            for raw in source:
                event = inspect_event(raw, self.limits)
                with closing(self.redactor.process(event)) as sanitized:
                    for output in sanitized:
                        frame = encode_event(output, self.limits)
                        self.peak_encoded_bytes = max(self.peak_encoded_bytes, len(frame))
                        yield frame
                if self.redactor.terminal:
                    return

    def feed(self, chunk: bytes) -> Iterator[bytes]:
        if self._failed or self._busy:
            self.abort()
            raise StreamError()
        if self.redactor.terminal:
            return
        self._busy = True
        complete = False
        try:
            yield from self._events(self.parser.feed(chunk))
            complete = True
        finally:
            self._busy = False
            if not complete:
                self.abort()

    def finish(self) -> Iterator[bytes]:
        if self._failed or self._busy:
            self.abort()
            raise StreamError()
        if self.redactor.terminal:
            return
        self._busy = True
        complete = False
        try:
            yield from self._events(self.parser.finish())
            if not self.redactor.terminal:
                raise StreamError()
            complete = True
        finally:
            self._busy = False
            if not complete:
                self.abort()
