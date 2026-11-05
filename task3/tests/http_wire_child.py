"""T3-005 loopback children. Only control receipts/counters reach diagnostics."""

import asyncio
import base64
import ctypes
import json
import os
import re
import socket
import sys
import threading
import time
from collections import Counter

import httpx
import uvicorn

from task3_streaming.app import create_app
from task3_streaming.settings import HTTPSettings
from task3_streaming.upstream import UpstreamSettings


def emit(event, **values):
    print(json.dumps({"event": event, **values}, separators=(",", ":")), flush=True)


def memory():
    if os.name != "nt":
        return {"rss": None, "peak_rss": None}
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
            (name, ctypes.c_size_t)
            for name in (
                "PeakWorkingSetSize",
                "WorkingSetSize",
                "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage",
                "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage",
                "PagefileUsage",
                "PeakPagefileUsage",
            )
        ]

    info = Counters()
    info.cb = ctypes.sizeof(info)
    get_process = ctypes.windll.kernel32.GetCurrentProcess
    get_process.restype = wintypes.HANDLE
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    if not query(get_process(), ctypes.byref(info), info.cb):
        raise RuntimeError("Process memory observation unavailable")
    return {"rss": info.WorkingSetSize, "peak_rss": info.PeakWorkingSetSize}


class Meter:
    def __init__(self):
        self.counts = Counter()
        self.high = Counter()
        self.pending = {}
        self.sequence = 0

    def sample(self, app, include_memory=True):
        rt = getattr(app.state, "runtime", None)
        if rt is not None:
            for owner in rt.owners:
                session = owner.session
                parser, redactor = session.processor.parser.stats, session.processor.redactor.stats
                values = {
                    "line_bytes": parser.peak_line_bytes,
                    "event_bytes": parser.peak_event_bytes,
                    "decoder_bytes": parser.peak_decoder_bytes,
                    "candidate_chars": redactor.peak_candidate_chars,
                    "held_chars": redactor.peak_held_chars,
                    "pending_chars": redactor.peak_pending_chars,
                    "pending_bytes": redactor.peak_pending_bytes,
                    "encoded_bytes": session.processor.peak_encoded_bytes,
                    "raw_block": session.lease.peak_raw_bytes if session.lease else 0,
                }
                for key, value in values.items():
                    self.high[key] = max(self.high[key], value)
        return {
            **dict(self.counts),
            "high": dict(self.high),
            **(memory() if include_memory else {}),
            "active_http": len(rt.owners) if rt else 0,
            "active_upstream": rt.service.active if rt else 0,
            "quarantined": rt.service.adapter.quarantined if rt else False,
            "pending_send": min(self.pending) if self.pending else None,
            "pending_sends": len(self.pending),
        }


class NativeBody(httpx.AsyncByteStream):
    def __init__(self, response, meter):
        self.response, self.meter = response, meter

    async def __aiter__(self):
        iterator = self.response.stream.__aiter__()
        while True:
            self.meter.counts["native_reads"] += 1
            try:
                block = await anext(iterator)
            except StopAsyncIteration:
                return
            self.meter.counts["native_chunks"] += 1
            self.meter.counts["native_bytes"] += len(block)
            yield block  # Original native bytes/partition, no decoding/coalescing.

    async def aclose(self):
        await self.response.aclose()
        self.meter.counts["native_closed"] += 1


class NativeTransport(httpx.AsyncBaseTransport):
    def __init__(self, meter):
        self.meter = meter
        self.transport = httpx.AsyncHTTPTransport(
            retries=0,
            http2=False,
            verify=True,
            trust_env=False,
            limits=httpx.Limits(max_connections=16, max_keepalive_connections=16),
        )

    async def handle_async_request(self, request):
        self.meter.counts["native_requests"] += 1
        response = await self.transport.handle_async_request(request)
        self.meter.counts["native_responses"] += 1
        return httpx.Response(
            response.status_code,
            headers=response.headers.raw,
            stream=NativeBody(response, self.meter),
            extensions=response.extensions,
        )

    async def aclose(self):
        await self.transport.aclose()
        self.meter.counts["pool_closes"] += 1


async def json_reply(send, value, status=200):
    raw = json.dumps(value, separators=(",", ":")).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(raw)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": raw})


def frame(name, value):
    return (
        "event: " + name + "\ndata: " + json.dumps(value, separators=(",", ":")) + "\n\n"
    ).encode()


class Provider:
    def __init__(self):
        self.plans, self.gates = {}, {}
        self.calls = 0
        self.stop = asyncio.Event()

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                event = message["type"] + ".complete"
                await send({"type": event})
                emit(event)
                if message["type"] == "lifespan.shutdown":
                    return
        if scope["path"] == "/health":
            await json_reply(send, {})
            return
        raw = bytearray()
        while True:
            message = await receive()
            if message["type"] != "http.request":
                return
            raw.extend(message.get("body", b""))
            if len(raw) > 65536:
                raise RuntimeError("Invalid synthetic fixture")
            if not message.get("more_body"):
                break
        cid = json.loads(raw)["prompt"]
        if not re.fullmatch(r"c[0-9]{4}", cid) or cid not in self.plans:
            raise RuntimeError("Missing synthetic fixture")
        plan = self.plans.pop(cid)
        self.calls += 1
        headers = dict(scope["headers"])
        private = os.environ["WIRE_CLIENT_TOKEN"].encode()
        emit(
            "called",
            case=cid,
            total=self.calls,
            isolated=(
                headers.get(b"authorization")
                == ("Bearer " + os.environ["WIRE_UPSTREAM_TOKEN"]).encode()
                and all(k not in headers for k in (b"cookie", b"x-role", b"last-event-id"))
                and all(private not in v for v in headers.values())
            ),
        )
        gate = self.gates.setdefault(cid, asyncio.Event())

        async def disconnected():
            while (await receive())["type"] != "http.disconnect":
                pass

        gone = asyncio.create_task(disconnected())
        released, stopping = asyncio.create_task(gate.wait()), asyncio.create_task(self.stop.wait())
        writes = size = 0
        complete = False
        started = time.monotonic()
        try:
            await send(
                {
                    "type": "http.response.start",
                    "status": plan.get("status", 200),
                    "headers": [
                        (b"content-type", plan.get("media", "text/event-stream").encode()),
                        *([(b"content-encoding", b"gzip")] if plan.get("compressed") else []),
                    ],
                }
            )
            if "repeat" in plan:
                repeated = frame("delta", {"channel": 0, "text": "word " * plan.get("width", 205)})
                chunks = (repeated for _ in range(plan["repeat"]))
            else:
                chunks = (base64.b64decode(s) for s in plan.get("chunks", []))
            for block in chunks:
                if plan.get("gate_at") == writes:
                    emit("held", case=cid, writes=writes, bytes=size)
                    await asyncio.wait(
                        {released, gone, stopping}, return_when=asyncio.FIRST_COMPLETED
                    )
                    if gone.done() or stopping.done():
                        return
                if gone.done() or stopping.done():
                    return
                await send({"type": "http.response.body", "body": block, "more_body": True})
                writes += 1
                size += len(block)
                await asyncio.sleep(0)  # Scheduling fairness, not timing synchronization.
            if plan.get("repeat"):
                for block in (frame("done", {"channel": 0}), frame("end", {})):
                    await send({"type": "http.response.body", "body": block, "more_body": True})
                    writes += 1
                    size += len(block)
            if plan.get("abort"):
                raise OSError("Synthetic upstream termination")
            await send({"type": "http.response.body", "body": b""})
            complete = True
        finally:
            observed_disconnect = gone.done() and not gone.cancelled() and gone.exception() is None
            for task in (gone, released, stopping):
                task.cancel()
            await asyncio.gather(gone, released, stopping, return_exceptions=True)
            self.gates.pop(cid, None)
            emit(
                "provider_closed",
                case=cid,
                complete=complete,
                disconnected=observed_disconnect,
                writes=writes,
                bytes=size,
                elapsed=round(time.monotonic() - started, 6),
            )


class Proxy:
    def __init__(self):
        self.meter = Meter()
        settings = HTTPSettings(
            UpstreamSettings(os.environ["WIRE_UPSTREAM_URL"], os.environ["WIRE_UPSTREAM_TOKEN"]),
            os.environ["WIRE_CLIENT_TOKEN"],
        )
        self.app = create_app(settings, upstream_transport=NativeTransport(self.meter))

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":

            async def lifecycle(message):
                emit(message["type"])  # Never forward lifespan traceback/message to diagnostics.
                await send(message)

            await self.app(scope, receive, lifecycle)
            return
        if scope["path"] == "/__wire_stats":
            if (
                dict(scope["headers"]).get(b"x-wire-control")
                != os.environ["WIRE_CONTROL_TOKEN"].encode()
            ):
                await json_reply(send, {}, 403)
            else:
                await json_reply(send, self.meter.sample(self.app))
            return

        async def metered(message):
            self.meter.sample(self.app, False)
            self.meter.sequence += 1
            seq = self.meter.sequence
            self.meter.counts["send_calls"] += 1
            self.meter.counts["send_bytes"] += len(message.get("body", b""))
            self.meter.pending[seq] = self.meter.counts["native_reads"]

            def suspended():
                if seq in self.meter.pending:
                    self.meter.counts["suspended_sends"] += 1

            asyncio.get_running_loop().call_soon(suspended)
            try:
                await send(message)  # Actual Uvicorn send, awaited in the same pull chain.
            finally:
                self.meter.pending.pop(seq, None)
                self.meter.sample(self.app, False)

        trace = dict(scope["headers"]).get(b"x-wire-trace", b"").decode("ascii", errors="ignore")
        try:
            await self.app(scope, receive, metered)
        finally:
            if re.fullmatch(r"c[0-9]{4}", trace):
                emit("http_done", case=trace, **self.meter.sample(self.app))


async def main(role):
    app = Provider() if role == "upstream" else Proxy()
    listener = socket.socket()
    if os.name == "nt":
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 16384)
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    listener.setblocking(False)
    emit(
        "bound",
        port=listener.getsockname()[1],
        pid=os.getpid(),
        listener_send_buffer=listener.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF),
    )
    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host="127.0.0.1",
            port=0,
            loop="asyncio",
            http="h11",
            ws="none",
            lifespan="on",
            access_log=False,
            log_level="critical",
            proxy_headers=False,
            server_header=False,
            timeout_keep_alive=2,
            timeout_graceful_shutdown=2,
        )
    )
    queue = asyncio.Queue(maxsize=64)
    loop = asyncio.get_running_loop()

    def read_commands():
        for line in sys.stdin:
            try:
                command = json.loads(line)
                loop.call_soon_threadsafe(queue.put_nowait, command)
                if command.get("command") == "stop":
                    return
            except (ValueError, RuntimeError):
                return
        loop.call_soon_threadsafe(queue.put_nowait, {"command": "stop"})

    reader = threading.Thread(target=read_commands, daemon=True)
    reader.start()

    async def commands():
        while True:
            command = await queue.get()
            kind = command["command"]
            if kind == "journal" and isinstance(app, Provider):
                cid = command["case"]
                if not re.fullmatch(r"c[0-9]{4}", cid):
                    raise RuntimeError("Invalid control case")
                # Independent provider-side count; never journal prompts or credentials.
                emit("journal_ack", case=cid, calls=app.calls)
            elif kind in {"plan", "release"} and isinstance(app, Provider):
                cid = command["case"]
                if not re.fullmatch(r"c[0-9]{4}", cid):
                    raise RuntimeError("Invalid control case")
                if kind == "plan":
                    if len(app.plans) >= 256:
                        raise RuntimeError("Fixture plan limit")
                    app.plans[cid] = command["plan"]
                else:
                    app.gates.setdefault(cid, asyncio.Event()).set()
                emit(kind + "_ack", case=cid)
            elif kind == "stop":
                if isinstance(app, Proxy):
                    rt = getattr(app.app.state, "runtime", None)
                    clean = rt is None or await rt.aclose()
                    emit("drained", clean=clean, **app.meter.sample(app.app))
                else:
                    app.stop.set()
                server.should_exit = True
                return

    control = asyncio.create_task(commands())
    try:
        await server.serve(sockets=[listener])
    finally:
        control.cancel()
        await asyncio.gather(control, return_exceptions=True)
        listener.close()
    emit("exited", started=server.started)
    return 0 if server.started else 2


if __name__ == "__main__":
    try:
        code = asyncio.run(main(sys.argv[1]))
    except Exception as exc:
        emit("fatal", kind=type(exc).__name__)  # No raw diagnostic or exception context.
        code = 2
    raise SystemExit(code)
