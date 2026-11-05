"""T4-005 real loopback TCP against independent proxy and synthetic upstream."""

import concurrent.futures
import json
import socket

import httpx
import pytest
from http_support import auth
from http_wire_support import StartupFailure, WireLab, wait_until

pytestmark = pytest.mark.http_wire


@pytest.fixture(scope="module")
def lab(tmp_path_factory):
    value = WireLab(tmp_path_factory.mktemp("http-wire"))
    try:
        yield value
    finally:
        value.close()


def post(server, key, **kwargs):
    with httpx.Client(trust_env=False, timeout=8) as client:
        return client.post(server.url + "/generate", headers=auth(key), **kwargs)


@pytest.mark.parametrize("case", ["missing", "invalid", "malformed", "duplicate", "cookie_only"])
def test_wire_authentication_rejection_zero_calls_and_rows(lab, case):
    server = lab.get()
    key = server.key()
    before = len(server.calls())
    before_rows = server.request_count()
    headers = []
    if case == "invalid":
        headers = [("authorization", "Bearer " + "x" * 43)]
    if case == "malformed":
        headers = [("authorization", "Basic invalid")]
    if case == "duplicate":
        headers = list(auth(key).items()) * 2
    if case == "cookie_only":
        headers = [("cookie", "tenant=" + key.decode()), ("x-tenant-id", key.decode())]
    with httpx.Client(trust_env=False, timeout=5) as client:
        response = client.post(server.url + "/generate", headers=headers, json={"prompt": "safe"})
    assert response.status_code == 401 and response.json()["error"]["code"] == "invalid_credentials"
    assert len(server.calls()) == before and server.rows(key) == []
    server.rejected(before, before_rows, "authentication")


@pytest.mark.parametrize(
    "body,headers,status",
    [
        (b"{", {"content-type": "application/json"}, 400),
        (b'{"prompt":"x","prompt":"y"}', {"content-type": "application/json"}, 400),
        (b'{"prompt":"x","tenant_id":"spoof"}', {"content-type": "application/json"}, 400),
        (b'{"prompt":"x","tokens":1}', {"content-type": "application/json"}, 400),
        (b'{"prompt":1}', {"content-type": "application/json"}, 400),
        (b'{"prompt":"x"}', {"content-type": "text/plain"}, 415),
        (b'{"prompt":"x"}', {"content-type": "application/json", "content-encoding": "gzip"}, 415),
        (b"x" * 1025, {"content-type": "application/json"}, 413),
    ],
)
def test_wire_entity_rejection_zero_calls_and_rows(lab, body, headers, status):
    server = lab.get()
    key = server.key()
    before = len(server.calls())
    before_rows = server.request_count()
    with httpx.Client(trust_env=False, timeout=5) as client:
        response = client.post(
            server.url + "/generate", headers={**auth(key), **headers}, content=body
        )
    assert (
        response.status_code == status and len(server.calls()) == before and server.rows(key) == []
    )
    server.rejected(before, before_rows, "body_or_schema")


def test_wire_content_length_chunked_and_success_privacy(lab):
    server = lab.get()
    key = server.key()
    body = json.dumps({"prompt": "wire-private-prompt"}).encode()
    with httpx.Client(trust_env=False, timeout=5) as client:
        for content in (body, iter([body[:10], body[10:]])):
            response = client.post(
                server.url + "/generate",
                headers={
                    **auth(key),
                    "content-type": "application/json",
                    "cookie": "unapproved",
                    "x-tenant-id": "spoof",
                    "x-role": "admin",
                },
                content=content,
            )
            assert response.status_code == 200
            assert response.json()["result"] == {
                "text": "Synthetic completion",
                "used_backup": False,
            }
            assert "wire-private-prompt" not in response.text and key.decode() not in response.text
            assert response.headers["cache-control"] == "no-store"
            assert response.headers["content-type"] == "application/json"
            assert response.headers["x-content-type-options"] == "nosniff"
            assert response.headers["x-request-id"] == response.json()["request_id"]
    assert all(auth_seen == 0 for _, auth_seen in server.calls())


def test_wire_chunked_oversize_and_incomplete_body_deadline(lab):
    server = lab.get()
    key = server.key()
    before = len(server.calls())
    before_rows = server.request_count()
    with httpx.Client(trust_env=False, timeout=5) as client:
        response = client.post(
            server.url + "/generate",
            headers={**auth(key), "content-type": "application/json"},
            content=iter([b"x" * 512] * 3),
        )
    assert response.status_code == 413
    server.rejected(before, before_rows, "chunked_size")
    with socket.create_connection(("127.0.0.1", server.proxy["port"]), timeout=5) as peer:
        peer.sendall(
            b"POST /generate HTTP/1.1\r\nHost: test\r\nAuthorization: Bearer "
            + key
            + b"\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n"
        )
        data = peer.recv(4096)
        assert data.startswith(b"HTTP/1.1 408")
    assert len(server.calls()) == before and server.rows(key) == []
    server.rejected(before, before_rows, "body_deadline")


@pytest.mark.parametrize(
    "mode,status,backup,charge,code",
    [
        ("429", 200, True, 25, None),
        ("timeout", 200, True, 25, None),
        ("backup_failure", 502, True, 40, "model_unavailable"),
        ("backup_429", 429, True, 40, "provider_rate_limited"),
        ("transport", 502, False, 20, "model_unavailable"),
        ("unknown", 200, False, 20, None),
    ],
)
def test_wire_routing_and_conservative_accounting(lab, mode, status, backup, charge, code):
    server = lab.get(mode)
    key = server.key()
    before = len(server.calls())
    response = post(server, key, json={"prompt": "wire-private-prompt"})
    assert response.status_code == status
    calls = server.calls()[before:]
    assert [ordinal for ordinal, _ in calls] == ([1, 2] if backup else [1])
    assert sum(row[3] for row in server.rows(key)) == charge
    assert all(row[0] == "complete" for row in server.rows(key))
    if code:
        assert response.json()["error"]["code"] == code
    else:
        assert response.json()["result"]["used_backup"] == backup
    if mode == "timeout":
        server.release()  # Remote work is uncertain, not proven stopped locally.


@pytest.mark.parametrize("mode,status,total", [("quota", 200, 50000), ("overquota", 429, 50001)])
def test_wire_exact_quota_and_denial_never_dispatches(lab, mode, status, total):
    server = lab.get(mode)
    key = server.key()
    before = len(server.calls())
    before_rows = server.request_count()
    response = post(server, key, json={"prompt": "safe"})
    assert response.status_code == status
    if status == 200:
        assert sum(row[4] for row in server.rows(key)) == total
        before = len(server.calls())
        before_rows = server.request_count()
        assert post(server, key, json={"prompt": "safe"}).status_code == 429
    assert len(server.calls()) == before and (status == 200 or server.rows(key) == [])
    server.rejected(before, before_rows, "tenant_quota")


def test_wire_concurrent_tenants_atomic_quota_and_persistence_across_process_restart(lab):
    server = lab.get("concurrency")
    key, other = server.key(), server.key()
    before = len(server.calls())
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        pending = [executor.submit(post, server, key, json={"prompt": "safe"}) for _ in range(5)]
        wait_until(lambda: len(server.calls()) == before + 5)
        before_rows = server.request_count()
        denied = post(server, key, json={"prompt": "safe"})
        assert denied.status_code == 429 and len(server.calls()) == before + 5
        server.rejected(before + 5, before_rows, "concurrent_quota")
        separate = executor.submit(post, server, other, json={"prompt": "safe"})
        wait_until(lambda: len(server.calls()) == before + 6)
        server.release()
        assert all(future.result(timeout=8).status_code == 200 for future in pending + [separate])
    assert sum(row[3] for row in server.rows(key)) == 25000
    assert sum(row[3] for row in server.rows(other)) == 5000
    previous = server.rows(key)
    server.restart()
    assert server.rows(key) == previous
    assert post(server, key, json={"prompt": "safe"}).status_code == 200


def test_wire_disconnect_accounts_primary_and_does_not_launch_backup(lab):
    server = lab.get("disconnect")
    key = server.key()
    before = len(server.calls())
    body = b'{"prompt":"safe"}'
    with socket.create_connection(("127.0.0.1", server.proxy["port"]), timeout=5) as peer:
        peer.sendall(
            b"POST /generate HTTP/1.1\r\nHost: test\r\nAuthorization: Bearer "
            + key
            + b"\r\nContent-Type: application/json\r\nContent-Length: "
            + str(len(body)).encode()
            + b"\r\n\r\n"
            + body
        )
        wait_until(lambda: len(server.calls()) == before + 1)
        peer.shutdown(socket.SHUT_RDWR)
    wait_until(lambda: bool(server.rows(key)) and all(r[0] == "complete" for r in server.rows(key)))
    assert len(server.calls()) == before + 1
    assert sum(row[3] for row in server.rows(key)) == 20
    server.release()


def test_wire_database_unavailability_fails_safely(lab):
    server = lab.get("db_failure")
    key = server.key()
    before = len(server.calls())
    from pathlib import Path

    path = Path(server.env["TASK4_DATABASE_PATH"])
    path.replace(path.with_suffix(".offline"))  # Dedicated fixture directory, no open connections.
    response = post(server, key, json={"prompt": "safe"})
    assert response.status_code == 503 and len(server.calls()) == before
    assert str(path) not in response.text
    assert not path.exists()  # Existing-store mode never recreates a missing database.
    lab.rejections.append(
        {"category": "database_unavailable", "provider_delta": 0, "reservation_delta": 0}
    )


def test_wire_bad_startup_reaps_process_without_forced_cleanup(lab):
    server = lab.get("startup_fixture")
    env = {**server.env, "TASK4_TENANT_KEYS_JSON": "[]"}
    with pytest.raises(StartupFailure):
        lab.spawn("proxy", env, server.directory, expected=3)
    lab.stop(lab.children[-1])


@pytest.mark.parametrize(
    "framing", [b"Content-Length: 1\r\nContent-Length: 2\r\n", b"Content-Length: invalid\r\n"]
)
def test_wire_invalid_framing_rejected_before_application(lab, framing):
    server = lab.get()
    before, before_rows = len(server.calls()), server.request_count()
    with socket.create_connection(("127.0.0.1", server.proxy["port"]), timeout=5) as peer:
        peer.sendall(b"POST /generate HTTP/1.1\r\nHost: test\r\n" + framing + b"\r\nx")
        assert peer.recv(4096).startswith(b"HTTP/1.1 400")
    server.rejected(before, before_rows, "protocol_framing")
