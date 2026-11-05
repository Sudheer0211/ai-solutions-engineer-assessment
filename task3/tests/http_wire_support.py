"""T3-005 native processes/TCP. No persisted credentials or raw body journals."""

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

CHILD = Path(__file__).with_name("http_wire_child.py")


def wait_until(predicate, timeout=6):
    deadline = time.monotonic() + timeout
    pause = threading.Event()
    while time.monotonic() < deadline:
        result = predicate()
        if result:
            return result
        pause.wait(0.01)  # State/readiness polling, never a fixed timing assertion.
    raise AssertionError("Bounded wire state deadline")


class Child:
    created = []

    def __init__(self, role, values, expected=0):
        self.role, self.expected = role, expected
        self.events, self.errors = deque(maxlen=1024), deque(maxlen=40)
        self.condition = threading.Condition()
        self.forced = self.killed = False
        self.privacy_violations = 0
        self._private = [v for k, v in values.items() if "TOKEN" in k] + [
            "private@example.test",
            "000-12-3456",
            "+12025550123",
        ]
        environment = {
            k: v
            for k, v in os.environ.items()
            if k.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "COMSPEC", "PATHEXT"}
        }
        environment.update(values, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        self.process = subprocess.Popen(
            [sys.executable, "-B", str(CHILD), role],
            cwd=CHILD.parent.parent,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        Child.created.append(self)
        self.readers = [
            threading.Thread(target=self._read, args=(stream, output), daemon=True)
            for stream, output in ((self.process.stdout, True), (self.process.stderr, False))
        ]
        for thread in self.readers:
            thread.start()
        self.port = None

    def _read(self, stream, output):
        for line in stream:
            with self.condition:
                if any(value in line for value in self._private):
                    self.privacy_violations += 1
                    self.errors.append("Private material in child diagnostics")
                elif output:
                    try:
                        self.events.append(json.loads(line))
                    except ValueError:
                        self.errors.append("Invalid child event")
                else:
                    self.errors.append(line[:2000])
                self.condition.notify_all()

    def event(self, name, case=None, timeout=10):
        deadline = time.monotonic() + timeout
        with self.condition:
            while True:
                for item in self.events:
                    if item["event"] == name and (case is None or item.get("case") == case):
                        return item
                if self.process.poll() is not None:
                    raise AssertionError("Wire child exited before expected receipt")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AssertionError("Wire child receipt deadline: " + name)
                self.condition.wait(min(remaining, 0.05))

    def command(self, command, **values):
        self.process.stdin.write(json.dumps({"command": command, **values}) + "\n")
        self.process.stdin.flush()

    def stop(self):
        if self.process.poll() is None:
            try:
                self.command("stop")
                self.process.wait(timeout=7)
            except (OSError, subprocess.TimeoutExpired):
                self.forced = True
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.killed = True
                    self.process.kill()
                    self.process.wait(timeout=2)
        if not self.process.stdin.closed:
            self.process.stdin.close()
        for thread in self.readers:
            thread.join(timeout=1)
        self.process.stdout.close()
        self.process.stderr.close()


class Stream:
    def __init__(self, connection, response):
        self.connection, self.response = connection, response
        self.pending = bytearray()
        self.frames = deque()
        self.ended = False
        self.http_complete = True

    @property
    def status(self):
        return self.response.status

    @property
    def headers(self):
        return {k.lower(): v for k, v in self.response.getheaders()}

    def frame(self):
        while not self.frames and not self.ended:
            try:
                data = self.response.read1(8192)
            except http.client.IncompleteRead as exc:
                data = exc.partial
                self.http_complete = False
                self.ended = True
            if not data:
                self.ended = True
                break
            self.pending.extend(data)
            while b"\n\n" in self.pending:
                frame, _, rest = self.pending.partition(b"\n\n")
                self.pending = bytearray(rest)
                lines = frame.decode("utf-8", errors="strict").splitlines()
                assert len(lines) == 2 and lines[0].startswith("event: ")
                assert lines[1].startswith("data: ")
                self.frames.append((lines[0][7:], json.loads(lines[1][6:])))
            assert len(self.pending) <= 8192
        return self.frames.popleft() if self.frames else None

    def all(self):
        values = []
        while (value := self.frame()) is not None:
            values.append(value)
        return values

    def close(self):
        if self.connection.sock is not None:
            try:
                self.connection.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
        self.response.close()
        self.connection.close()


class Lab:
    observations = {}

    def __init__(self, refused=False, invalid=False):
        self.children, self.streams, self.connections = [], [], []
        self.refused, self.invalid = refused, invalid
        self.reservation = None
        self._sequence = 0
        self._client = secrets.token_urlsafe(32)
        self._upstream = secrets.token_urlsafe(32)
        self._control = secrets.token_urlsafe(32)

    def __enter__(self):
        try:
            self.start()
            return self
        except BaseException:
            self.close()
            raise

    def __exit__(self, *exc):
        self.close()

    def spawn(self, role, values, expected=0):
        child = Child(
            role,
            {
                "WIRE_CLIENT_TOKEN": self._client,
                "WIRE_UPSTREAM_TOKEN": self._upstream,
                "WIRE_CONTROL_TOKEN": self._control,
                **values,
            },
            expected,
        )
        self.children.append(child)
        return child

    def start(self):
        if not self.refused and not self.invalid:
            self.peer = self.spawn("upstream", {})
            self.peer.port = self.peer.event("bound")["port"]
            self.ready(self.peer, "/health", 200)
            port = self.peer.port
        else:
            self.reservation = socket.socket()
            self.reservation.bind(("127.0.0.1", 0))
            port = self.reservation.getsockname()[1]
        self.proxy = self.spawn(
            "proxy",
            {
                "WIRE_UPSTREAM_URL": "file:///invalid"
                if self.invalid
                else f"http://127.0.0.1:{port}/stream"
            },
            expected=2 if self.invalid else 0,
        )
        if self.invalid:
            self.proxy.event("fatal")
            self.proxy.process.wait(timeout=5)
            return
        self.proxy.port = self.proxy.event("bound")["port"]
        self.proxy.event("lifespan.startup.complete")
        self.ready(self.proxy, "/stream", 405)

    def ready(self, child, path, expected):
        def check():
            if child.process.poll() is not None:
                raise AssertionError("Wire readiness child exit")
            connection = http.client.HTTPConnection("127.0.0.1", child.port, timeout=0.3)
            try:
                connection.request("GET", path)
                response = connection.getresponse()
                response.read()
                return response.status == expected
            except (OSError, http.client.HTTPException):
                return False
            finally:
                connection.close()

        wait_until(check, 10)

    def case(self):
        self._sequence += 1
        return f"c{self._sequence:04d}"

    def plan(self, chunks=(), **options):
        cid = self.case()
        plan = {"chunks": [base64.b64encode(chunk).decode() for chunk in chunks], **options}
        self.peer.command("plan", case=cid, plan=plan)
        self.peer.event("plan_ack", cid)
        return cid

    def release(self, cid):
        self.peer.command("release", case=cid)
        self.peer.event("release_ack", cid)

    def stats(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.proxy.port, timeout=3)
        try:
            connection.request("GET", "/__wire_stats", headers={"X-Wire-Control": self._control})
            response = connection.getresponse()
            assert response.status == 200
            return json.loads(response.read())
        finally:
            connection.close()

    def open(
        self,
        cid=None,
        *,
        raw=None,
        auth=None,
        media="application/json",
        extra=(),
        chunked=False,
        path="/stream",
        receive_buffer=None,
        timeout=22,
    ):
        cid = cid or self.case()
        raw = json.dumps({"prompt": cid}).encode() if raw is None else raw
        connection = http.client.HTTPConnection("127.0.0.1", self.proxy.port, timeout=timeout)
        self.connections.append(
            connection
        )  # Retain even a failed handshake/send for final cleanup.
        connection.connect()
        if receive_buffer is not None:
            connection.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, receive_buffer)
        connection.putrequest("POST", path, skip_accept_encoding=True)
        for value in ["Bearer " + self._client] if auth is None else auth:
            connection.putheader("Authorization", value)
        if media is not None:
            connection.putheader("Content-Type", media)
        connection.putheader("X-Wire-Trace", cid)
        connection.putheader("Connection", "close")
        for key, value in extra:
            connection.putheader(key, value)
        connection.putheader("Transfer-Encoding", "chunked") if chunked else connection.putheader(
            "Content-Length", str(len(raw))
        )
        connection.endheaders()
        if chunked:
            for block in (raw[:7], raw[7:]):
                if block:
                    connection.send(f"{len(block):x}\r\n".encode() + block + b"\r\n")
            connection.send(b"0\r\n\r\n")
        else:
            connection.send(raw)
        try:
            response = connection.getresponse()
        except BaseException:
            connection.close()
            raise
        stream = Stream(connection, response)
        self.streams.append(stream)
        return stream, cid

    def settled(self, cid):
        self.proxy.event("http_done", cid, timeout=6)
        return wait_until(
            lambda: s if (s := self.stats())["active_http"] == s["active_upstream"] == 0 else None
        )

    def calls(self):
        attempts = self.stats().get("native_requests", 0)
        if hasattr(self, "peer"):
            cid = self.case()
            self.peer.command("journal", case=cid)
            journal = self.peer.event("journal_ack", cid)
            assert journal["calls"] == attempts
        return attempts

    def close(self):
        for stream in self.streams:
            stream.close()
        for connection in self.connections:
            connection.close()
        for child in reversed(self.children):
            child.stop()
        if self.reservation is not None:
            self.reservation.close()
        assert all(
            not child.forced
            and not child.killed
            and child.process.returncode == child.expected
            and child.privacy_violations == 0
            for child in self.children
        )
        assert not any(t.is_alive() for c in self.children for t in c.readers)


def summary():
    children = [
        {
            "role": c.role,
            "pid": c.process.pid,
            "exit": c.process.returncode,
            "expected": c.expected,
            "forced": c.forced,
            "killed": c.killed,
            "privacy_violations": c.privacy_violations,
            "reader_threads_alive": sum(t.is_alive() for t in c.readers),
        }
        for c in Child.created
    ]
    return {"children": children, "observations": Lab.observations}
