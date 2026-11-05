"""T2-005/W1-W8: independent processes and loopback TCP, never mock transports."""

import gzip
import http.client
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from http_wire_support import Child, WireHarness

pytestmark = [pytest.mark.task2, pytest.mark.http_wire]


def body(*, name="read", request_id=1, method="tools/call", owner=None, mode="normal"):
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "wire_mode": mode,
            "params": {"name": name, "arguments": {"owner": owner}},
        },
        indent=1,
    ).encode()


@pytest.fixture(scope="module")
def pair():
    with WireHarness() as harness:
        yield harness
    assert all(child.process.returncode == 0 and not child.forced for child in harness.children)
    assert any(event["event"] == "lifespan.shutdown.complete" for event in harness.proxy.events)
    summary = {
        "children": len(Child.created),
        "alive": sum(child.process.poll() is None for child in Child.created),
        "forced_cleanup": sum(child.forced for child in Child.created),
        "reader_threads_alive": sum(
            reader.is_alive() for child in Child.created for reader in child.readers
        ),
        "exit_codes": [
            {"mode": child.mode, "code": child.process.returncode} for child in Child.created
        ],
    }
    assert summary["alive"] == summary["forced_cleanup"] == summary["reader_threads_alive"] == 0
    target = Path(__file__).parents[1] / ".cache" / "http_wire_summary.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def wire(pair):
    pair.reset()
    yield pair


@pytest.mark.parametrize(
    "kind", ["missing", "invalid", "scheme", "bare", "spaces", "duplicate", "same"]
)
def test_wire_authentication_rejections_have_zero_upstream_calls(wire, kind):
    values = {
        "missing": [],
        "invalid": ["Bearer invalid"],
        "scheme": ["Basic opaque"],
        "bare": ["Bearer"],
        "spaces": ["Bearer x y"],
        "duplicate": [wire.auth("admin"), wire.auth()],
        "same": [wire.auth(), wire.auth()],
    }[kind]
    status, headers, raw = wire.request(b"{", auth_headers=values)
    assert status == 401
    assert headers["www-authenticate"] == 'Bearer realm="mcp"'
    assert json.loads(raw) == {"detail": "Invalid Bearer credentials"}
    assert wire.journal() == []


@pytest.mark.parametrize("request_id", [0, "", None, 2**100, "wire-id"])
def test_wire_viewer_denial_preserves_id_and_zero_journal(wire, request_id):
    status, _, raw = wire.request(body(name="admin_reset", request_id=request_id))
    assert status == 403
    assert json.loads(raw) == {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32001, "message": "Unauthorized Tool Call"},
    }
    assert wire.journal() == []


@pytest.mark.parametrize(
    "role,name", [("admin", "admin_reset"), ("admin", "read"), ("viewer", "read")]
)
def test_wire_authorized_calls_preserve_request_and_response_bytes(wire, role, name):
    original = body(name=name, request_id="\\u0061", owner=17)
    status, headers, raw = wire.request(original, role=role)
    journal = wire.journal(count=1)
    assert len(journal) == 1
    assert wire.raw(journal[0]) == original
    assert status == journal[0]["status"] == 200
    assert raw == wire.raw(journal[0], "response")
    assert json.loads(raw)["id"] == "\\u0061"
    assert headers["content-length"] == str(len(raw))
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert "set-cookie" not in headers
    assert "x-upstream-only" not in headers


@pytest.mark.parametrize("role", ["admin", "viewer"])
def test_wire_discovery_is_transparent_including_admin_tools(wire, role):
    status, _, raw = wire.request(body(method="tools/list"), role=role)
    journal = wire.journal(count=1)
    assert len(journal) == 1
    assert status == 200
    assert raw == wire.raw(journal[0], "response")
    assert [tool["name"] for tool in json.loads(raw)["result"]["tools"]] == ["admin_reset", "read"]


def test_wire_upstream_jsonrpc_errors_keep_bytes_and_status(wire):
    status, _, raw = wire.request(body(mode="error", request_id="error-id"))
    journal = wire.journal(count=1)
    assert len(journal) == 1
    assert status == 400
    assert raw == wire.raw(journal[0], "response")
    assert json.loads(raw)["error"]["data"] == {"unchanged": [1, True]}


def test_wire_client_credentials_cookies_and_role_claims_do_not_reach_upstream(wire):
    status, _, _ = wire.request(
        body(),
        extra_headers=[
            ("Cookie", "session=synthetic"),
            ("X-Role", "admin"),
            ("Role", "admin"),
            ("X-API-Key", "unapproved"),
        ],
    )
    journal = wire.journal(count=1)
    assert status == 200 and len(journal) == 1
    assert journal[0]["auth_ok"]
    assert not journal[0]["client_token_seen"]
    assert not journal[0]["cookie_seen"]
    assert not journal[0]["spoof_seen"]
    assert "x-wire-trace" not in journal[0]["header_names"]


@pytest.mark.parametrize(
    "raw,code,request_id",
    [
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"\\u0061dmin_reset"}}',
            -32001,
            7,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"admin\\u005freset"}}',
            -32001,
            7,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"read","name":"admin_reset"}}',
            -32600,
            7,
        ),
        (
            b'{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"read","na\\u006de":"admin_reset"}}',
            -32600,
            7,
        ),
        (b"{", -32700, None),
        (b'{"jsonrpc":"2.0","id":true,"method":"tools/list"}', -32600, None),
        (b'{"jsonrpc":"2.0","id":1.0,"method":"tools/list"}', -32600, None),
        (b'{"jsonrpc":"2.0","id":1,"method":7}', -32600, 1),
        (b'[{"jsonrpc":"2.0","id":1,"method":"tools/list"}]', -32600, None),
        (b'{"jsonrpc":"2.0","id":7,"method":"tools/call"}', -32602, 7),
    ],
)
def test_wire_bypasses_malformed_rpc_and_batches_fail_closed(wire, raw, code, request_id):
    status, _, response = wire.request(raw)
    assert status == (403 if code == -32001 else 400)
    assert json.loads(response)["error"]["code"] == code
    assert json.loads(response)["id"] == request_id
    assert wire.journal() == []


@pytest.mark.parametrize(
    "role,name,status",
    [("viewer", "admin_reset", 403), ("viewer", "read", 400), ("admin", "admin_reset", 400)],
)
def test_wire_notifications_have_empty_reply_and_no_delivery(wire, role, name, status):
    raw = json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": name}}).encode()
    code, _, response = wire.request(raw, role=role)
    assert code == status and response == b""
    assert wire.journal() == []


@pytest.mark.parametrize("chunked", [False, True])
def test_wire_content_length_and_chunked_preserve_bytes(wire, chunked):
    original = b'{ "jsonrpc":"2.0", "id":"a", "method":"tools/list", "extra":1e9999 }'
    status, _, _ = wire.request(original, chunked=chunked)
    journal = wire.journal(count=1)
    assert status == 200 and len(journal) == 1
    assert wire.raw(journal[0]) == original


@pytest.mark.parametrize("chunked", [False, True])
def test_wire_oversized_bodies_have_zero_upstream_calls(wire, chunked):
    status, _, raw = wire.request(body() + b" " * 4096, chunked=chunked)
    assert status == 413
    assert json.loads(raw) == {"detail": "Request body too large"}
    assert wire.journal() == []


@pytest.mark.parametrize(
    "media,encoding", [(None, None), ("text/plain", None), ("application/json", "gzip")]
)
def test_wire_unsupported_media_and_encoding_have_zero_upstream_calls(wire, media, encoding):
    status, _, _ = wire.request(
        gzip.compress(body()) if encoding else body(),
        media=media,
        extra_headers=[("Content-Encoding", encoding)] if encoding else [],
    )
    assert status == 415
    assert wire.journal() == []


def test_wire_concurrent_roles_repeated_ids_and_separate_connections():
    def call(number):
        role = "admin" if number % 2 else "viewer"
        name = "admin_reset" if number % 3 == 0 else "read"
        result = wire.request(body(name=name, request_id=1, owner=number, mode="gate"), role=role)
        denied = role == "viewer" and name == "admin_reset"
        assert result[0] == (403 if denied else 200)
        if not denied:
            assert json.loads(result[2])["result"]["owner"] == number
        assert json.loads(result[2])["id"] == 1

    with WireHarness(read_timeout=5) as wire, ThreadPoolExecutor(max_workers=12) as executor:
        pending = [executor.submit(call, number) for number in range(12)]
        try:
            active = wire.journal(count=10, complete=False)
            assert len(active) == 10 and all(not entry["done"] for entry in active)
        finally:
            wire.control("release")
        for request in pending:
            request.result(timeout=6)
        journal = wire.journal(count=10)
        assert len(journal) == 10
        assert {
            json.loads(wire.raw(entry))["params"]["arguments"]["owner"] for entry in journal
        } == set(range(12)) - {0, 6}
        assert all(entry["auth_ok"] and not entry["client_token_seen"] for entry in journal)


def test_wire_slow_upstream_timeout_is_synchronized_and_not_retried(wire):
    with ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(wire.request, body(mode="gate", request_id="slow"))
        try:
            assert len(wire.journal(count=1, complete=False)) == 1
            status, _, raw = pending.result(timeout=4)
            assert status == 504
            assert json.loads(raw) == {
                "jsonrpc": "2.0",
                "id": "slow",
                "error": {"code": -32603, "message": "Upstream timeout"},
            }
        finally:
            wire.control("release")
    assert len(wire.journal(count=1)) == 1


@pytest.mark.parametrize("mode", ["drop", "malformed", "redirect"])
def test_wire_upstream_protocol_failures_are_controlled(wire, mode):
    status, _, raw = wire.request(body(mode=mode))
    assert status == 502
    assert json.loads(raw)["error"] == {"code": -32603, "message": "Upstream request failed"}
    assert len(wire.journal(count=1)) == 1


def test_wire_client_disconnect_mid_body_is_not_forwarded_and_proxy_recovers(wire):
    trace = wire.trace()
    connection = socket.create_connection(("127.0.0.1", wire.proxy.port), timeout=2)
    request = (
        f"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1\r\nX-Wire-Trace: {trace}\r\n"
        f"Authorization: {wire.auth()}\r\nContent-Type: application/json\r\n"
        "Content-Length: 1000\r\n\r\n{"
    ).encode()
    connection.sendall(request)
    connection.shutdown(socket.SHUT_WR)
    connection.close()
    assert wire.proxy.event("http_done", trace=trace, timeout=3)["status"] == 400
    assert wire.journal() == []
    assert wire.request(body())[0] == 200
    assert len(wire.journal(count=1)) == 1


def test_wire_upstream_connection_refusal_is_controlled():
    with WireHarness(refused=True) as wire:
        status, _, raw = wire.request(body(request_id="refused"))
        assert status == 502
        assert json.loads(raw)["id"] == "refused"
        assert wire.journal() == []
    assert all(not child.forced for child in wire.children)


def test_wire_unexpected_upstream_process_termination_is_controlled():
    with WireHarness() as wire, ThreadPoolExecutor(max_workers=1) as executor:
        pending = executor.submit(wire.request, body(mode="gate", request_id="killed"))
        assert len(wire.journal(count=1, complete=False)) == 1
        wire.peer.process.kill()
        wire.peer.process.wait(timeout=3)
        status, _, raw = pending.result(timeout=4)
        assert status == 502
        assert json.loads(raw)["id"] == "killed"
    assert all(child.process.poll() is not None for child in wire.children)
    assert not any(child.forced for child in wire.children)


def test_wire_cleanup_runs_after_a_failed_test_body():
    wire = WireHarness()
    with pytest.raises(AssertionError, match="simulated assertion"):
        with wire:
            raise AssertionError("simulated assertion")
    assert all(child.process.returncode == 0 and not child.forced for child in wire.children)
    assert any(event["event"] == "lifespan.shutdown.complete" for event in wire.proxy.events)


def test_wire_startup_failure_cleans_up_both_processes():
    wire = WireHarness(invalid_config=True)
    with pytest.raises(RuntimeError):
        with wire:
            pytest.fail("Invalid configuration started a server")
    assert len(wire.children) == 2
    assert all(child.process.poll() is not None and not child.forced for child in wire.children)


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_wire_method_rejections_have_zero_upstream_calls(wire, method):
    status, headers, _ = wire.request(method=method)
    assert status == 405 and headers["allow"] == "POST"
    assert wire.journal() == []


def test_wire_incomplete_body_deadline_has_zero_upstream_calls(wire):
    trace = wire.trace()
    connection = http.client.HTTPConnection("127.0.0.1", wire.proxy.port, timeout=3)
    try:
        connection.putrequest("POST", "/mcp")
        for name, value in [
            ("Authorization", wire.auth()),
            ("X-Wire-Trace", trace),
            ("Content-Type", "application/json"),
            ("Content-Length", "1000"),
        ]:
            connection.putheader(name, value)
        connection.endheaders()
        connection.send(b"{")
        response = connection.getresponse()
        assert response.status == 408
        assert json.loads(response.read()) == {"detail": "Request body timeout"}
    finally:
        connection.close()
    wire.proxy.event("http_done", trace=trace, timeout=3)
    assert wire.journal() == []
