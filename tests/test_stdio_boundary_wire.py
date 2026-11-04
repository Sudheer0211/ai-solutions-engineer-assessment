"""T1-008: real-process recovery, cancellation, backpressure and output isolation."""

import json
import queue
import re
import subprocess
import sys
import threading
from contextlib import contextmanager

import pytest

from tests.wire_support import MODERN_META, ROOT, WireServer

pytestmark = [pytest.mark.task1, pytest.mark.wire]
TEST_SERVER = "tests.boundary_server"


@contextmanager
def unopened(mode="legacy", *, module=None):
    server = WireServer(mode, module=module)
    try:
        yield server
    finally:
        server.close()


def send_request(server, method, request_id, params=None):
    params = params or {}
    if server.mode == "modern":
        params = {**params, "_meta": MODERN_META}
    server.send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_parse_error_before_and_after_opening_without_choosing_era(mode):
    with unopened(mode) as server:
        # Exceeds the driver's eight-item pre-opening replay limit. The
        # boundary must answer each error before a valid opener is sent.
        server.send_raw('{"jsonrpc":\n' * 12)
        for _ in range(12):
            reply = server.receive(None)
            assert reply == {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
        server.connect()
        server.send_raw('{"id":"do-not-recover",\n')
        assert server.receive(None)["error"]["code"] == -32700
        assert len(server.request("tools/list", request_id="sentinel")["result"]["tools"]) == 2
    assert len([m for m in server.messages if "error" in m]) == 13
    assert "do-not-recover" not in "".join(server.errors)


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_invalid_envelopes_preserve_only_reliable_top_level_ids(mode):
    with WireServer(mode) as server:
        for request_id in (0, 42, "", "original-A", "original-B", "référence"):
            server.send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": 7,
                    "params": [],
                    "result": [],
                    "error": [],
                }
            )
            response = server.receive(request_id)
            assert response["error"]["code"] == -32600
            assert response["id"] == request_id
            assert type(response["id"]) is type(request_id)
        for request_id in (True, False, 1.5, [], {}, None):
            server.send({"jsonrpc": "2.0", "id": request_id, "method": "tools/list"})
            assert server.receive(None)["error"]["code"] == -32600
        for value in ([], 42, "request", None):
            server.send_raw(json.dumps(value) + "\n")
            assert server.receive(None)["error"]["code"] == -32600
        server.send({"jsonrpc": "1.0", "id": "wrong-version", "method": "tools/list"})
        assert server.receive("wrong-version")["error"]["code"] == -32600
        result = server.request(
            "tools/call",
            {
                "name": "trigger_refund",
                "arguments": {
                    "customer_id": "CUST-00001",
                    "amount": 10,
                    "reason": "Synthetic request",
                },
            },
            "first-refund",
        )["result"]["structuredContent"]
        assert result["refund_id"] == "REF-000001"
        assert result["refundable_balance"] == "90.00"


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_valid_notifications_and_responses_do_not_create_error_reply_loops(mode):
    with WireServer(mode) as server:
        before = len(server.messages)
        for message in (
            {"jsonrpc": "2.0", "method": "unknown/notification"},
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": "absent"},
            },
            {"jsonrpc": "2.0", "id": "unsolicited", "result": {}},
            {"jsonrpc": "2.0", "id": "malformed-response", "result": []},
            {"jsonrpc": "2.0", "id": "malformed-error", "error": []},
        ):
            server.send(message)
        server.request("tools/list", request_id="sentinel")
        assert [m["id"] for m in server.messages[before:]] == ["sentinel"]


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_cancellation_survives_malformed_input(mode):
    with WireServer(mode, module=TEST_SERVER) as server:
        send_request(server, "test/slow", "slow-1")
        assert server.request("test/started", request_id="started")["result"]["started"] is True
        server.send_raw('{"jsonrpc":\n')
        assert server.receive(None)["error"]["code"] == -32700
        server.send(
            {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {"requestId": "slow-1"},
            }
        )
        assert (
            server.request("test/cancelled", request_id="cancelled")["result"]["cancelled"] is True
        )
        server.request("tools/list", request_id="after-cancel")
    assert all(json.loads(line).get("id") != "slow-1" for line in server.lines)
    assert "Slow handler stopped" in "".join(server.errors)


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_stdout_isolation_covers_print_fd_and_child_output(mode):
    with WireServer(mode, module=TEST_SERVER) as server:
        assert server.request("test/noise", request_id="noise")["result"]["ok"] is True
        server.send_raw('{"jsonrpc":\n')
        assert server.receive(None)["error"]["code"] == -32700
    stderr = "".join(server.errors)
    for expected in ("BOUNDARY_PRINT_NOISE", "BOUNDARY_FD_NOISE", "BOUNDARY_CHILD_NOISE"):
        assert expected in stderr
        assert expected not in "".join(server.lines)


@pytest.mark.parametrize("state", ["no-opener", "bad-frame", "pending-work"])
def test_eof_closes_with_no_opener_bad_input_or_pending_work(state):
    with unopened(module=TEST_SERVER) as server:
        if state == "bad-frame":
            server.send_raw("{\n")
            assert server.receive(None)["error"]["code"] == -32700
        elif state == "pending-work":
            server.connect()
            send_request(server, "test/slow", "pending-at-eof")
            server.request("test/started", request_id="started")
    assert server.process.returncode == 0
    if state == "pending-work":
        assert "Slow handler stopped" in "".join(server.errors)


def test_broken_stdout_exits_without_hanging():
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", "task1"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        process.stdout.close()
        process.stdout = None  # communicate must not start a reader on our closed pipe.
        _, stderr = process.communicate(b'{"jsonrpc":\n', timeout=8)
        assert process.returncode is not None
        assert b"Rejected STDIO envelope" in stderr
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def test_actual_pipe_backpressure_retains_order_and_bounded_capture():
    # Do not use WireServer's eager stdout drainer for this test: make the
    # real output pipe stall on large error frames while stdin is pipelined.
    process = subprocess.Popen(
        [sys.executable, "-u", "-m", TEST_SERVER],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ids = [f"{index}:" + "x" * 16384 for index in range(24)]
    payload = b"".join(
        (json.dumps({"jsonrpc": "2.0", "id": rid, "method": 7}) + "\n").encode() for rid in ids
    )
    stderr_parts, writer_errors = [], []
    prefix_queue, output_queue = queue.Queue(), queue.Queue()

    def feed():
        try:
            process.stdin.write(payload)
            process.stdin.close()
        except Exception as error:
            writer_errors.append(error)

    feeder = threading.Thread(target=feed, daemon=True)
    err_reader = threading.Thread(
        target=lambda: stderr_parts.append(process.stderr.read()), daemon=True
    )
    prefix_reader = threading.Thread(
        target=lambda: prefix_queue.put(process.stdout.read(64)), daemon=True
    )
    tail_reader = None
    try:
        feeder.start()
        err_reader.start()
        prefix_reader.start()
        prefix = prefix_queue.get(timeout=8)  # Proof that output has begun, not a timed sleep.
        assert len(prefix) == 64
        # Each frame exceeds pipe capacity. Resume draining only after observing
        # this partial frame; the SDK writer has faced actual pipe backpressure.
        tail_reader = threading.Thread(
            target=lambda: output_queue.put(process.stdout.read()), daemon=True
        )
        tail_reader.start()
        tail = output_queue.get(timeout=12)
        process.wait(timeout=5)
        feeder.join(timeout=3)
        err_reader.join(timeout=3)
        assert not feeder.is_alive()
        assert not writer_errors
        assert process.returncode == 0
        replies = [json.loads(line) for line in (prefix + tail).splitlines()]
        assert [reply["id"] for reply in replies] == ids
        assert all(reply["error"]["code"] == -32600 for reply in replies)
        stderr = b"".join(stderr_parts).decode()
        assert re.search(r"Capture high_watermark=[12]\b", stderr)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        for thread in (feeder, err_reader, prefix_reader, tail_reader):
            if thread is not None and thread.ident is not None:
                thread.join(timeout=2)
        for pipe in (process.stdin, process.stdout, process.stderr):
            pipe.close()


@pytest.mark.parametrize("mode", ["legacy", "modern"])
def test_fragmented_utf8_and_escaped_newlines(mode):
    with WireServer(mode) as server:
        params = {
            "name": "trigger_refund",
            "arguments": {
                "customer_id": "CUST-00001",
                "amount": 0.001,
                "reason": "Synthetic café\nrefund request",
            },
        }
        if mode == "modern":
            params["_meta"] = MODERN_META
        raw = (
            json.dumps(
                {"jsonrpc": "2.0", "id": "café", "method": "tools/call", "params": params},
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        split = raw.index("é".encode()) + 1
        server.process.stdin.buffer.write(raw[:split])
        server.process.stdin.buffer.flush()
        server.process.stdin.buffer.write(raw[split:])
        server.process.stdin.buffer.flush()
        result = server.receive("café")["result"]["structuredContent"]
        assert result["refundable_balance"] == "99.999"
    assert "café" not in "".join(server.errors)
