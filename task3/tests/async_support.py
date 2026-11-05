import asyncio
from dataclasses import dataclass, field

import httpx

from task3_streaming.service import StreamService
from task3_streaming.upstream import UpstreamAdapter, UpstreamSettings


class ManualClock:
    def __init__(self):
        self.value = 0.0
        self.pulse = asyncio.Event()

    def now(self):
        return self.value

    async def wait_until(self, deadline):
        while self.value < deadline:
            pulse = self.pulse
            await pulse.wait()

    def advance(self, value):
        assert value >= self.value
        self.value = value
        pulse, self.pulse = self.pulse, asyncio.Event()
        pulse.set()


@dataclass
class Gate:
    data: bytes = b""
    resistant: bool = False
    entered: asyncio.Event = field(default_factory=asyncio.Event)
    release: asyncio.Event = field(default_factory=asyncio.Event)
    cancelled: asyncio.Event = field(default_factory=asyncio.Event)

    async def wait(self):
        self.entered.set()
        while not self.release.is_set():
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.cancelled.set()
                if not self.resistant:
                    raise
        return self.data


class Body(httpx.AsyncByteStream):
    def __init__(self, chunks=(), *, close_gate=None, close_error=False):
        self.chunks = list(chunks)
        self.index = self.reads = self.closes = 0
        self.closed = False
        self.close_gate = close_gate
        self.close_error = close_error

    def __aiter__(self):
        return self

    async def __anext__(self):
        self.reads += 1
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        item = self.chunks[self.index]
        self.index += 1
        if isinstance(item, Gate):
            return await item.wait()
        if isinstance(item, Exception):
            raise item
        return item

    async def aclose(self):
        self.closes += 1
        if self.close_gate:
            await self.close_gate.wait()
        if self.close_error:
            raise RuntimeError("private-close-diagnostic")
        self.closed = True


class Transport(httpx.AsyncBaseTransport):
    def __init__(
        self,
        body=None,
        *,
        factory=None,
        headers=None,
        status=200,
        opening=None,
        close_gate=None,
        error=None,
    ):
        self.body = body or Body()
        self.factory = factory
        self.headers = headers if headers is not None else [("content-type", "text/event-stream")]
        self.status = status
        self.opening = opening
        self.close_gate = close_gate
        self.error = error
        self.requests = []
        self.bodies = []
        self.closes = 0

    async def handle_async_request(self, request):
        self.requests.append(request)
        if self.opening:
            await self.opening.wait()
        if self.error:
            raise self.error
        body = self.factory(request) if self.factory else self.body
        self.bodies.append(body)
        return httpx.Response(
            self.status,
            headers=self.headers,
            stream=body,
            extensions={"reason_phrase": b"private-reason-phrase"},
        )

    async def aclose(self):
        self.closes += 1
        if self.close_gate:
            await self.close_gate.wait()


def make_service(transport, clock=None, token=None):
    adapter = UpstreamAdapter(
        UpstreamSettings("https://synthetic.example.test/stream", token), transport=transport
    )
    return StreamService(adapter, clock=clock)


async def until(predicate):
    for _ in range(300):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("bounded scheduling gate not reached")


async def checked(coro):
    return await asyncio.wait_for(coro, timeout=3)


def exercise(coro):
    asyncio.run(checked(coro))
