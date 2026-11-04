"""T1-008: observe SDK input; recover malformed frames via its protocol writer.

The pinned SDK emits one decoded item per readline, with a rendezvous channel.
One consumed item plus one reader lookahead bounds raw capture to two lines.
No framing, dispatcher, descriptor-isolation or lifecycle code is copied here.
"""

import json
import logging
import os
import sys
from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TextIO

import anyio
from anyio.abc import ObjectReceiveStream, ObjectSendStream
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
from mcp.types import (
    INVALID_REQUEST,
    PARSE_ERROR,
    ErrorData,
    JSONRPCError,
    JSONRPCRequest,
)
from pydantic import ValidationError

logger = logging.getLogger(__name__)


class ObservedInput(anyio.AsyncFile[str]):
    """Public AsyncFile interface with a fail-closed, bounded correlation FIFO."""

    CAPACITY = 2

    def __init__(self, file: TextIO) -> None:
        super().__init__(file)
        self.frames: deque[str] = deque()
        self.high_watermark = 0

    async def readline(self) -> str:
        line = await super().readline()
        if line:
            if len(self.frames) >= self.CAPACITY:
                raise RuntimeError("SDK STDIO input lookahead contract exceeded")
            self.frames.append(line)
            self.high_watermark = max(self.high_watermark, len(self.frames))
        return line

    def take_frame(self) -> str:
        if not self.frames:
            raise RuntimeError("SDK STDIO input correlation unavailable")
        return self.frames.popleft()

    async def aclose(self) -> None:
        try:
            await super().aclose()
        finally:
            self.frames.clear()


def protocol_error(code: int, request_id: str | int | None) -> JSONRPCError:
    return JSONRPCError(
        jsonrpc="2.0",
        id=request_id,
        error=ErrorData(
            code=code, message="Parse error" if code == PARSE_ERROR else "Invalid Request"
        ),
    )


def classify_frame(raw: str, item: SessionMessage | ValidationError) -> JSONRPCError | None:
    """Classify the rejected envelope, never the method's arguments or business data.

    Accepted requests remain SDK-owned. Notification/response union fallback
    needs the original top-level id: an invalid id must not become a notification.
    Malformed response-shaped frames are not answered (avoid error-reply loops).
    """
    if isinstance(item, SessionMessage) and isinstance(item.message, JSONRPCRequest):
        return None
    if isinstance(item, ValidationError) and any(
        error["type"] == "json_invalid" for error in item.errors(include_input=False)
    ):
        return protocol_error(PARSE_ERROR, None)
    try:
        envelope = json.loads(raw)
    except (ValueError, RecursionError):
        # The SDK already parsed this input. A secondary decoder resource limit
        # cannot establish an ID; do not invent one or reject accepted messages.
        return protocol_error(INVALID_REQUEST, None) if isinstance(item, ValidationError) else None
    if isinstance(envelope, dict):
        if "method" not in envelope and ("result" in envelope or "error" in envelope):
            return None
        if (
            "id" not in envelope
            and envelope.get("jsonrpc") == "2.0"
            and isinstance(envelope.get("method"), str)
        ):
            return None  # Notifications, including invalid params, have no reply.
        request_id = envelope.get("id")
        if type(request_id) not in (str, int):
            request_id = None
    else:
        request_id = None
    return protocol_error(INVALID_REQUEST, request_id)


class BoundaryReceiveStream(ObjectReceiveStream[SessionMessage | Exception]):
    """Read-only stream decoration before the SDK's opening-request selection."""

    def __init__(
        self,
        read: ObjectReceiveStream[SessionMessage | Exception],
        write: ObjectSendStream[SessionMessage],
        observed: ObservedInput,
    ) -> None:
        self.read = read
        self.write = write
        self.observed = observed

    @property
    def last_context(self):
        return getattr(self.read, "last_context", None)

    async def receive(self) -> SessionMessage | Exception:
        while True:
            item = await self.read.receive()
            raw = self.observed.take_frame()
            if isinstance(item, Exception) and not isinstance(item, ValidationError):
                raise item  # I/O/internal failures are not malformed client JSON.
            error = classify_frame(raw, item)
            del raw  # Retain no raw customer inputs while blocked on output.
            if error is not None:
                del item  # ValidationError can also retain the original input.
                logger.warning("Rejected STDIO envelope code=%s", error.error.code)
                await self.write.send(SessionMessage(error))
            elif isinstance(item, SessionMessage):
                return item
            else:
                del item

    async def aclose(self) -> None:
        await self.read.aclose()


@asynccontextmanager
async def validated_stdio() -> AsyncIterator[
    tuple[BoundaryReceiveStream, ObjectSendStream[SessionMessage]]
]:
    # Own only a duplicate of input; supplying stdin skips the SDK's fd0 claim.
    # stdout is deliberately omitted: the SDK keeps its private writer and fd1
    # diversion to stderr. Its parser and serializer still handle every frame.
    source = os.fdopen(os.dup(sys.stdin.fileno()), "r", encoding="utf-8", errors="replace")
    async with ObservedInput(source) as observed:
        async with stdio_server(stdin=observed) as (read, write):
            yield BoundaryReceiveStream(read, write, observed), write
