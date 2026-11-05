"""T2-005 child processes: independent fixture peer and observed real Uvicorn app."""

import base64
import json
import os
import socket
import sys
import threading
from dataclasses import replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_OUTPUT = threading.Lock()


def emit(event, **fields):
    with _OUTPUT:
        print(json.dumps({"event": event, **fields}), flush=True)


class Journal:
    def __init__(self):
        self.condition = threading.Condition()
        self.entries = []
        self.gates = {}

    def add(self, body, headers):
        expected = os.environ["WIRE_UPSTREAM_TOKEN"]
        forbidden = json.loads(os.environ["WIRE_FORBIDDEN_TOKENS"])
        values = list(headers.values())
        entry = {
            "body": base64.b64encode(body).decode(),
            "auth_ok": headers.get_all("Authorization") == [f"Bearer {expected}"],
            "client_token_seen": any(token in value for token in forbidden for value in values),
            "cookie_seen": "cookie" in headers,
            "spoof_seen": any(
                name in headers
                for name in ["role", "x-role", "x-user-role", "x-api-key", "proxy-authorization"]
            ),
            "header_names": sorted(name.lower() for name in headers.keys()),
            "done": False,
        }
        with self.condition:
            self.entries.append(entry)
            self.condition.notify_all()
        return entry

    def complete(self, entry):
        with self.condition:
            entry["done"] = True
            self.condition.notify_all()

    def release(self):
        with self.condition:
            for gate in self.gates.values():
                gate.set()

    def snapshot(self, *, count=0, complete=False):
        with self.condition:
            ready = self.condition.wait_for(
                lambda: (
                    len(self.entries) >= count
                    and (not complete or all(entry["done"] for entry in self.entries))
                ),
                timeout=5,
            )
            if not ready:
                raise TimeoutError("Journal synchronization deadline")
            return [dict(entry) for entry in self.entries]


def upstream():
    state = Journal()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def write(self, status, body, headers=None):
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()

        def control(self):
            if self.headers.get("X-Wire-Control") != os.environ["WIRE_CONTROL_TOKEN"]:
                self.write(403, b"{}")
                return
            length = int(self.headers.get("Content-Length", "0"))
            options = json.loads(self.rfile.read(length)) if length else {}
            if self.path == "/control/reset":
                state.release()
                state.snapshot(complete=True)
                with state.condition:
                    state.entries.clear()
                    state.gates.clear()
                result = {}
            elif self.path == "/control/release":
                state.release()
                result = {}
            else:
                result = state.snapshot(
                    count=options.get("count", 0), complete=options.get("complete", False)
                )
            self.write(200, json.dumps(result).encode())

        def do_GET(self):
            if self.path == "/health":
                self.write(200, b"{}")
            else:
                entry = state.add(b"", self.headers)
                self.write(404, b"{}")
                state.complete(entry)

        def do_POST(self):
            if self.path.startswith("/control/"):
                self.control()
                return
            body = self.rfile.read(int(self.headers["Content-Length"]))
            try:
                value = json.loads(body)
            except ValueError:
                value = {}
            mode = value.get("wire_mode", "normal") if isinstance(value, dict) else "normal"
            if mode == "gate":
                with state.condition:
                    gate = state.gates.setdefault("held", threading.Event())
            entry = state.add(body, self.headers)
            try:
                if mode == "gate":
                    if not gate.wait(timeout=10):
                        raise TimeoutError("Fixture gate deadline")
                if mode == "drop":
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    return
                if value["method"] == "tools/list":
                    result = {
                        "tools": [
                            {
                                "name": "admin_reset",
                                "description": "Fixture protected tool",
                                "inputSchema": {"type": "object"},
                            },
                            {"name": "read", "inputSchema": {"type": "object"}},
                        ],
                        "extension": {"unchanged": True},
                    }
                else:
                    params = value.get("params", {})
                    result = {
                        "owner": params.get("arguments", {}).get("owner"),
                        "tool": params.get("name"),
                    }
                response = {
                    "jsonrpc": "2.0",
                    "id": value["id"],
                    "result": result,
                    "extension": {"precise": "opaque"},
                }
                status = 200
                if mode == "error":
                    response.pop("result")
                    response["error"] = {
                        "code": -32602,
                        "message": "Fixture error",
                        "data": {"unchanged": [1, True]},
                    }
                    status = 400
                raw = json.dumps(response, indent=1, ensure_ascii=True).encode()
                if mode == "malformed":
                    raw = b"{"
                if mode == "redirect":
                    status = 307
                with state.condition:
                    entry["response"] = base64.b64encode(raw).decode()
                    entry["status"] = status
                self.write(
                    status,
                    raw,
                    {
                        "Set-Cookie": "fixture=opaque; Path=/",
                        "X-Upstream-Only": "discard",
                        **(
                            {"Location": f"http://127.0.0.1:{self.server.server_port}/unexpected"}
                            if mode == "redirect"
                            else {}
                        ),
                    },
                )
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass
            finally:
                state.complete(entry)

    class PeerServer(ThreadingHTTPServer):
        request_queue_size = 128
        daemon_threads = True

    server = PeerServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02})
    thread.start()
    emit("bound", port=server.server_port, pid=os.getpid())
    try:
        for line in sys.stdin:
            if line.strip() == "stop":
                break
    finally:
        state.release()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        emit("stopped")


def proxy():
    import uvicorn

    from task2_proxy.app import create_app
    from task2_proxy.upstream import load_upstream_settings

    read_timeout = float(os.environ["WIRE_READ_TIMEOUT"])
    settings = replace(
        load_upstream_settings(),
        max_request_bytes=4096,
        read_timeout=read_timeout,
        connect_timeout=3,
        write_timeout=1,
        pool_timeout=1,
        total_timeout=max(4, read_timeout + 1),
    )
    app = create_app(upstream_settings=settings, body_timeout=0.5)

    async def observed(scope, receive, send):
        trace = dict(scope.get("headers", [])).get(b"x-wire-trace", b"").decode("ascii")
        status = None

        async def relay(message):
            nonlocal status
            if scope["type"] == "lifespan" and message["type"].endswith(("complete", "failed")):
                emit(message["type"])
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await app(scope, receive, relay)
        finally:
            if trace:
                emit("http_done", trace=trace, status=status)

    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(128)
    config = uvicorn.Config(
        observed,
        host="127.0.0.1",
        port=0,
        workers=1,
        loop="asyncio",
        http="h11",
        lifespan="on",
        log_config=None,
        log_level="critical",
        access_log=False,
        proxy_headers=False,
        timeout_graceful_shutdown=2,
        timeout_keep_alive=1,
    )
    server = uvicorn.Server(config)

    def commands():
        for line in sys.stdin:
            if line.strip() == "stop":
                break
        server.should_exit = True

    threading.Thread(target=commands, daemon=True).start()
    emit("bound", port=listener.getsockname()[1], pid=os.getpid())
    try:
        server.run(sockets=[listener])
    finally:
        listener.close()
        emit("stopped")


if __name__ == "__main__":
    {"proxy": proxy, "upstream": upstream}[sys.argv[1]]()
