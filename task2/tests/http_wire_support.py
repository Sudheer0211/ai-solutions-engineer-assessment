"""T2-005: bounded subprocess/TCP support with no persisted credentials or journal."""

import base64
import http.client
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from pathlib import Path

SERVER = Path(__file__).with_name("http_wire_server.py")


class Child:
    created = []

    def __init__(self, mode, environment):
        self.mode = mode
        self.events = []
        self.errors = deque(maxlen=50)
        self.condition = threading.Condition()
        self.forced = False
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(SERVER), mode],
            cwd=SERVER.parent.parent,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        self.readers = [
            threading.Thread(target=self._read, args=(self.process.stdout, True), daemon=True),
            threading.Thread(target=self._read, args=(self.process.stderr, False), daemon=True),
        ]
        for reader in self.readers:
            reader.start()
        self.port = None
        self.created.append(self)

    def _read(self, stream, stdout):
        for line in stream:
            with self.condition:
                if stdout:
                    try:
                        self.events.append(json.loads(line))
                    except ValueError:
                        self.errors.append("Non-event child output")
                else:
                    self.errors.append(line)
                self.condition.notify_all()

    def event(self, name, *, trace=None, timeout=10):
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                for event in self.events:
                    if event["event"] == name and (trace is None or event.get("trace") == trace):
                        return event
                if self.process.poll() is not None:
                    raise RuntimeError("Wire child exited before expected event")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Wire child event deadline")
                self.condition.wait(min(remaining, 0.05))

    def stop(self):
        if self.process.poll() is None:
            try:
                self.process.stdin.write("stop\n")
                self.process.stdin.flush()
                self.process.wait(timeout=6)
            except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                self.forced = True
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=2)
        self.process.stdin.close()
        for reader in self.readers:
            reader.join(timeout=1)
        self.process.stdout.close()
        self.process.stderr.close()


class WireHarness:
    def __init__(self, *, refused=False, invalid_config=False, read_timeout=0.5):
        self._admin = secrets.token_urlsafe(32)
        self._viewer = secrets.token_urlsafe(32)
        self._upstream_token = secrets.token_urlsafe(32)
        self._control_token = secrets.token_urlsafe(32)
        self.children = []
        self.refused = refused
        self.invalid_config = invalid_config
        self.read_timeout = read_timeout
        self.reservation = None
        self._sequence = 0
        self._lock = threading.Lock()

    def __enter__(self):
        try:
            self.start()
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *exc):
        self.close()

    def child(self, mode, values):
        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "PATHEXT"}
        }
        environment.update(PYTHONUTF8="1", **values)
        child = Child(mode, environment)
        self.children.append(child)
        child.port = child.event("bound")["port"]
        return child

    def start(self):
        self.peer = self.child(
            "upstream",
            {
                "WIRE_UPSTREAM_TOKEN": self._upstream_token,
                "WIRE_CONTROL_TOKEN": self._control_token,
                "WIRE_FORBIDDEN_TOKENS": json.dumps([self._admin, self._viewer]),
            },
        )
        self.ready(self.peer, "/health", 200)
        port = self.peer.port
        if self.refused:
            self.reservation = socket.socket()
            self.reservation.bind(("127.0.0.1", 0))
            port = self.reservation.getsockname()[1]  # Bound, deliberately not listening.
        self.proxy = self.child(
            "proxy",
            {
                "TASK2_ROLE_TOKENS": "{}"
                if self.invalid_config
                else json.dumps(
                    {
                        "admin": [self._admin],
                        "viewer": [self._viewer],
                    }
                ),
                "TASK2_UPSTREAM_URL": f"http://127.0.0.1:{port}/rpc",
                "TASK2_UPSTREAM_BEARER_TOKEN": self._upstream_token,
                "WIRE_READ_TIMEOUT": str(self.read_timeout),
            },
        )
        self.proxy.event("lifespan.startup.complete")
        self.ready(self.proxy, "/mcp", 405)

    def ready(self, child, path, expected):
        deadline = time.monotonic() + 10
        pause = threading.Event()
        while time.monotonic() < deadline:
            if child.process.poll() is not None:
                raise RuntimeError("Wire child startup failed")
            try:
                connection = http.client.HTTPConnection("127.0.0.1", child.port, timeout=0.25)
                try:
                    connection.request("GET", path)
                    response = connection.getresponse()
                    response.read()
                    if response.status == expected:
                        return
                finally:
                    connection.close()
            except (OSError, http.client.HTTPException):
                pass
            pause.wait(0.02)  # Bounded readiness polling, never a timing assertion.
        raise TimeoutError("Wire HTTP readiness deadline")

    def control(self, path="journal", **options):
        connection = http.client.HTTPConnection("127.0.0.1", self.peer.port, timeout=6)
        try:
            connection.request(
                "POST",
                "/control/" + path,
                body=json.dumps(options).encode(),
                headers={"X-Wire-Control": self._control_token, "Connection": "close"},
            )
            response = connection.getresponse()
            body = response.read()
            assert response.status == 200
            return json.loads(body)
        finally:
            connection.close()

    def reset(self):
        self.control("reset")

    def auth(self, role="viewer"):
        return "Bearer " + (self._admin if role == "admin" else self._viewer)

    def trace(self):
        with self._lock:
            self._sequence += 1
            return str(self._sequence)

    def request(
        self,
        body=b"",
        *,
        role="viewer",
        auth_headers=None,
        extra_headers=(),
        media="application/json",
        method="POST",
        chunked=False,
        path="/mcp",
    ):
        trace = self.trace()
        fields = [("X-Wire-Trace", trace), *extra_headers]
        if media is not None:
            fields.append(("Content-Type", media))
        if auth_headers is None:
            fields.append(("Authorization", self.auth(role)))
        else:
            fields.extend(("Authorization", value) for value in auth_headers)
        fields.append(
            ("Transfer-Encoding", "chunked") if chunked else ("Content-Length", str(len(body)))
        )
        connection = http.client.HTTPConnection(
            "127.0.0.1", self.proxy.port, timeout=max(5, self.read_timeout + 2)
        )
        try:
            connection.putrequest(method, path, skip_accept_encoding=True)
            for name, value in fields:
                connection.putheader(name, value)
            connection.endheaders()
            if chunked:
                for chunk in (body[:7], body[7:]):
                    if chunk:
                        connection.send(f"{len(chunk):X}\r\n".encode() + chunk + b"\r\n")
                connection.send(b"0\r\n\r\n")
            elif body:
                connection.send(body)
            response = connection.getresponse()
            data = response.read()
            result = (response.status, {k.lower(): v for k, v in response.getheaders()}, data)
        finally:
            connection.close()
        self.proxy.event("http_done", trace=trace, timeout=5)
        return result

    def journal(self, *, count=0, complete=True):
        return self.control(count=count, complete=complete)

    @staticmethod
    def raw(entry, key="body"):
        return base64.b64decode(entry[key])

    def close(self):
        for child in reversed(self.children):
            child.stop()
        if self.reservation is not None:
            self.reservation.close()
        captured = "\n".join(
            "".join(child.errors) + json.dumps(child.events) for child in self.children
        )
        if any(
            value in captured
            for value in [self._admin, self._viewer, self._upstream_token, self._control_token]
        ):
            raise AssertionError("Wire child emitted secret material")
