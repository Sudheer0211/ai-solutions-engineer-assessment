"""T3-004 direct ASGI gates; no sockets or claims about server/OS buffering."""

import asyncio
import json
from contextlib import asynccontextmanager

from task3_streaming.app import create_app
from task3_streaming.settings import HTTPSettings
from task3_streaming.upstream import UpstreamSettings
from tests.async_support import checked

TOKEN = "synthetic-assessment-access-credential"
UPSTREAM = "synthetic-separate-upstream-credential"
SETTINGS = HTTPSettings(UpstreamSettings("https://synthetic.example.test/stream", UPSTREAM), TOKEN)


class HTTP:
    def __init__(
        self,
        *,
        raw=b'{"prompt":"synthetic input"}',
        headers=None,
        method="POST",
        path="/stream",
        query=b"",
        chunks=None,
        block=None,
        fail=None,
    ):
        self.scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.4"},
            "http_version": "1.1",
            "method": method,
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query,
            "root_path": "",
            "server": ("127.0.0.1", 8000),
            "client": ("127.0.0.1", 9000),
            "headers": headers
            if headers is not None
            else [
                (b"authorization", ("Bearer " + TOKEN).encode()),
                (b"content-type", b"application/json"),
            ],
        }
        self.inbox = asyncio.Queue()
        chunks = [raw] if chunks is None else chunks
        for i, chunk in enumerate(chunks):
            self.inbox.put_nowait(
                {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
            )
        self.messages = []
        self.attempts = []
        self.receives = 0
        self.block, self.fail = block, fail
        self.started = asyncio.Event()

    async def receive(self):
        self.receives += 1
        return await self.inbox.get()

    async def send(self, message):
        self.attempts.append(message)
        if self.fail:
            self.fail(message)
        if self.block:
            await self.block(message)
        self.messages.append(message)
        if message["type"] == "http.response.start":
            self.started.set()

    async def __call__(self, app):
        await app(self.scope, self.receive, self.send)

    def disconnect(self):
        self.inbox.put_nowait({"type": "http.disconnect"})

    @property
    def status(self):
        return next(
            (m["status"] for m in self.messages if m["type"] == "http.response.start"), None
        )

    @property
    def body(self):
        return b"".join(m.get("body", b"") for m in self.messages)

    @property
    def frames(self):
        return [m["body"] for m in self.messages if m.get("body") and m.get("more_body")]

    @property
    def json(self):
        return json.loads(self.body)


@asynccontextmanager
async def running(transport, clock=None, settings=SETTINGS):
    app = create_app(settings, upstream_transport=transport, clock=clock)
    async with app.router.lifespan_context(app):
        yield app


class Lifespan:
    """Actual ASGI lifespan messages, including cancelled or failed shutdown."""

    def __init__(self, app):
        self.app = app
        self.input, self.output = asyncio.Queue(), asyncio.Queue()
        self.task = None

    async def start(self):
        self.task = asyncio.create_task(
            self.app(
                {"type": "lifespan", "asgi": {"version": "3.0"}}, self.input.get, self.output.put
            )
        )
        await self.input.put({"type": "lifespan.startup"})
        return await checked(self.output.get())

    async def close(self):
        await self.input.put({"type": "lifespan.shutdown"})
        return await checked(self.output.get())
