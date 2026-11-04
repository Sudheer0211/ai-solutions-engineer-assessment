"""T1-005: subprocess harness; JSON framing here is test-client code only."""

import json
import os
import queue
import subprocess
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODERN_META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "task1-wire-tests", "version": "1.0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


class WireServer:
    def __init__(self, mode="legacy", *, fault=False, console=False, module=None):
        command = [
            sys.executable,
            "-u",
            "-m",
            module or ("tests.fault_server" if fault else "task1"),
        ]
        if console:
            executable = "task1-mcp.exe" if os.name == "nt" else "task1-mcp"
            command = [str(Path(sys.executable).with_name(executable))]
        self.process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        self.mode = mode
        self.lines = []
        self.errors = []
        self.messages = []
        self.pending = queue.Queue()
        self.threads = [
            threading.Thread(target=self._read_stdout, daemon=True),
            threading.Thread(target=self._read_stderr, daemon=True),
        ]
        for thread in self.threads:
            thread.start()

    def _read_stdout(self):
        for line in self.process.stdout:
            self.lines.append(line)
            self.pending.put(line)

    def _read_stderr(self):
        self.errors.extend(self.process.stderr)

    def send_raw(self, line):
        self.process.stdin.write(line)
        self.process.stdin.flush()

    def send(self, message):
        self.send_raw(json.dumps(message, allow_nan=False) + "\n")

    def receive(self, request_id):
        while True:
            try:
                line = self.pending.get(timeout=8)
            except queue.Empty:
                raise AssertionError(
                    f"No response for {request_id!r}; stderr={self.errors!r}"
                ) from None
            assert line.endswith("\n"), line
            message = json.loads(line)
            assert message["jsonrpc"] == "2.0"
            self.messages.append(message)
            if message.get("id") == request_id:
                return message

    def request(self, method, params=None, request_id="request-1"):
        if self.mode == "modern":
            params = {**(params or {}), "_meta": MODERN_META}
        self.send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                **({"params": params} if params is not None else {}),
            }
        )
        return self.receive(request_id)

    def connect(self):
        if self.mode == "modern":
            result = self.request("server/discover", request_id="discover")
            assert "2026-07-28" in result["result"]["supportedVersions"]
        else:
            result = self.request(
                "initialize",
                {
                    "protocolVersion": "2025-11-25",
                    "capabilities": {},
                    "clientInfo": {"name": "task1-wire-tests", "version": "1.0"},
                },
                request_id="initialize",
            )
            assert result["result"]["protocolVersion"] == "2025-11-25"
            self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return self

    def close(self):
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            exit_code = self.process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
            raise AssertionError("Server did not shut down cleanly after stdin EOF") from None
        finally:
            for thread in self.threads:
                thread.join(timeout=2)
            self.process.stdout.close()
            self.process.stderr.close()
        assert exit_code == 0, self.errors
        # Check every captured line, including frames not awaited by receive().
        for line in self.lines:
            assert line.endswith("\n")
            assert json.loads(line)["jsonrpc"] == "2.0"

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()
