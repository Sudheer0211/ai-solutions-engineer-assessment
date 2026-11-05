"""T4-005 child entrypoints. TEST ONLY synthetic protocol, not an LLM integration."""

import asyncio
import json
import os
import socket
import sqlite3
import sys
import threading
from contextlib import asynccontextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

import httpx
import uvicorn

from task4_limiter.app import create_app
from task4_limiter.models import ModelTokenBounds
from task4_limiter.providers import ProviderResult, ProviderStatus, TokenUsage


def write_json(path, value):
    Path(path).write_text(json.dumps(value), encoding="utf-8")


def upstream():
    journal = os.environ["WIRE_JOURNAL"]
    mode = os.environ["WIRE_MODE"]
    gate = threading.Event()
    with sqlite3.connect(journal) as db:
        db.execute("CREATE TABLE events (id TEXT, ordinal INTEGER, phase TEXT, auth INTEGER)")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log headers, paths, requests or response payloads.

        def do_GET(self):
            if self.path == "/release":
                gate.set()
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["content-length"])))
            ordinal, attempt_id = data["ordinal"], data["id"]

            def record(phase):
                with sqlite3.connect(journal, timeout=5) as db:
                    db.execute(
                        "INSERT INTO events VALUES (?,?,?,?)",
                        (
                            attempt_id,
                            ordinal,
                            phase,
                            int(
                                bool(
                                    self.headers.get("authorization") or self.headers.get("cookie")
                                )
                            ),
                        ),
                    )

            record("start")
            if ordinal == 1 and mode in ("timeout", "concurrency", "disconnect"):
                gate.wait(15)  # Release endpoint/shutdown normally ends this bounded fixture wait.
            record("finish")
            if mode == "transport":
                self.close_connection = True
                return
            status = 200
            if ordinal == 1 and mode in ("429", "backup_failure", "backup_429"):
                status = 429
            if ordinal == 2 and mode == "backup_failure":
                status = 503
            if ordinal == 2 and mode == "backup_429":
                status = 429
            payload = {"text": "Synthetic completion", "input_tokens": 3, "output_tokens": 2}
            if mode in ("unknown", "quota", "overquota", "concurrency"):
                payload["input_tokens"] = payload["output_tokens"] = None
            body = json.dumps(payload).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # A timed-out/disconnected peer is an explicit fixture scenario.

    class Server(ThreadingHTTPServer):
        daemon_threads = False
        block_on_close = True

    server = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    thread.start()
    write_json(os.environ["WIRE_READY"], {"port": server.server_port})
    try:
        sys.stdin.buffer.readline()
    finally:
        gate.set()
        server.shutdown()
        server.server_close()
        thread.join(5)
        assert not thread.is_alive()


class Attempt:
    def __init__(self, provider):
        self.provider = provider
        mode = os.environ["WIRE_MODE"]
        total = (
            (25000 if provider.ordinal == 1 else 25001)
            if mode == "overquota"
            else (25000 if mode == "quota" else 5000 if mode == "concurrency" else 20)
        )
        self.bounds = ModelTokenBounds(provider.model_id, total - 10, 10, provider.counter_id)
        self.id = str(uuid4())

    async def execute(self):
        try:
            async with self.provider.client.stream(
                "POST",
                os.environ["WIRE_UPSTREAM"],
                json={"id": self.id, "ordinal": self.provider.ordinal},
            ) as response:
                await response.aread()
                if response.status_code == 429:
                    return ProviderResult(ProviderStatus.RATE_LIMITED)
                if response.status_code != 200:
                    return ProviderResult(ProviderStatus.TRANSPORT_FAILURE)
                data = response.json()
                usage = (
                    None
                    if data["input_tokens"] is None
                    else TokenUsage(data["input_tokens"], data["output_tokens"])
                )
                return ProviderResult(ProviderStatus.SUCCESS, usage, data["text"])
        except httpx.HTTPError:
            return ProviderResult(ProviderStatus.TRANSPORT_FAILURE)

    async def aclose(self):
        # execute's async context closes the individual exchange, including on cancel.
        pass


class Provider:
    def __init__(self, ordinal, client):
        self.ordinal, self.client = ordinal, client
        self.model_id = f"synthetic-{ordinal}"
        self.counter_id = "synthetic-wire-v1"

    def prepare(self, text):
        # Fixture configuration only; request text/estimates never select accounting.
        return Attempt(self)


async def proxy():
    @asynccontextmanager
    async def resources():
        async with httpx.AsyncClient(
            timeout=None,
            trust_env=False,
            follow_redirects=False,
            transport=httpx.AsyncHTTPTransport(retries=0),
        ) as client:
            try:
                yield Provider(1, client), Provider(2, client)
            finally:
                write_json(os.environ["WIRE_LIFECYCLE"], {"provider_context_closed": True})

    app = create_app(provider_resources=resources)
    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=0,
        access_log=False,
        proxy_headers=False,
        log_level="warning",
        timeout_graceful_shutdown=8,
    )
    server = uvicorn.Server(config)

    async def stop():
        while not Path(os.environ["WIRE_STOP"]).exists():
            await asyncio.sleep(0.02)
        server.should_exit = True

    watcher = asyncio.create_task(stop())
    try:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            write_json(os.environ["WIRE_READY"], {"port": listener.getsockname()[1]})
            await server.serve(sockets=[listener])
    finally:
        watcher.cancel()
        await asyncio.gather(watcher, return_exceptions=True)
    if not server.started:
        raise SystemExit(3)  # Expected only in the invalid-startup fixture.


if __name__ == "__main__":
    if sys.argv[1] == "upstream":
        upstream()
    else:
        asyncio.run(proxy())
