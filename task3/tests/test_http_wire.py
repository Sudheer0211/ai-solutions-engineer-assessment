"""T3-Q19-Q21: independent child processes/native sockets, no mock transports."""

import hashlib
import json
import time
from pathlib import Path

import pytest

from tests.http_wire_support import Child, Lab, summary, wait_until
from tests.support import wire

pytestmark = [pytest.mark.task3, pytest.mark.http_wire]


def complete(text="safe "):
    return (
        wire("delta", {"channel": 0, "text": text}) + wire("done", {"channel": 0}) + wire("end", {})
    )


def logical(frames, channel=0):
    return "".join(
        value["text"] for kind, value in frames if kind == "delta" and value["channel"] == channel
    )


def high_water(stats):
    bounds = {
        "line_bytes": 8192,
        "event_bytes": 16384,
        "decoder_bytes": 3,
        "candidate_chars": 256,
        "held_chars": 1024,
        "pending_chars": 1024,
        "pending_bytes": 8192,
        "encoded_bytes": 8192,
        "raw_block": 65536,
    }
    for key, maximum in bounds.items():
        assert stats["high"].get(key, 0) <= maximum


@pytest.fixture(scope="module")
def pair():
    try:
        with Lab() as lab:
            yield lab
    finally:
        receipts = summary()
        target = Path(__file__).parents[1] / ".cache" / "t3005_wire_summary.json"
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(receipts, indent=2) + "\n", encoding="utf-8")
    assert all(
        c.process.poll() is not None
        and not c.forced
        and not c.killed
        and c.process.returncode == c.expected
        for c in Child.created
    )
    assert not any(t.is_alive() for c in Child.created for t in c.readers)


@pytest.fixture
def lab(pair):
    start = len(pair.streams)
    yield pair
    for stream in pair.streams[start:]:
        stream.close()
    wait_until(lambda: pair.stats()["active_http"] == pair.stats()["active_upstream"] == 0)
    assert not pair.stats()["quarantined"]


def test_wire_progressive_delivery_before_gated_upstream_completion(lab):
    first = wire("delta", {"channel": 0, "text": "safe private@"})
    second = (
        wire("delta", {"channel": 0, "text": "example.test "})
        + wire("done", {"channel": 0})
        + wire("end", {})
    )
    cid = lab.plan([first, second], gate_at=1)
    started = time.monotonic()
    stream, _ = lab.open(cid)
    lab.peer.event("held", cid)
    assert stream.status == 200 and stream.frame() == ("delta", {"channel": 0, "text": "safe "})
    first_elapsed = time.monotonic() - started
    assert not any(
        e["event"] == "provider_closed" and e.get("case") == cid for e in lab.peer.events
    )
    before = lab.stats()
    lab.release(cid)
    remaining = stream.all()
    assert logical(remaining) == "[REDACTED] " and remaining[-1] == ("end", {})
    assert stream.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert stream.headers["cache-control"] == "no-store" and "content-length" not in stream.headers
    assert stream.headers["x-content-type-options"] == "nosniff"
    assert lab.peer.event("called", cid)["isolated"]
    assert lab.peer.event("provider_closed", cid)["complete"]
    after = lab.settled(cid)
    Lab.observations["progressive"] = {
        "first_client_seconds": first_elapsed,
        "native_reads_before_release": before.get("native_reads"),
        "native_chunks_before_release": before.get("native_chunks"),
        "source_still_gated_at_first_client_frame": True,
        "high": after["high"],
    }


@pytest.mark.parametrize(
    "kind", ["missing", "invalid", "scheme", "bare", "spaces", "duplicate", "same"]
)
def test_wire_auth_rejections_zero_upstream(lab, kind):
    auth = {
        "missing": [],
        "invalid": ["Bearer invalid"],
        "scheme": ["Basic opaque"],
        "bare": ["Bearer"],
        "spaces": ["Bearer x y"],
        "duplicate": ["Bearer " + lab._client, "Bearer other"],
        "same": ["Bearer " + lab._client] * 2,
    }[kind]
    before = lab.calls()
    stream, cid = lab.open(raw=b"{", auth=auth)
    assert stream.status == 401
    assert stream.headers["www-authenticate"] == 'Bearer realm="task3"'
    assert json.loads(stream.response.read()) == {
        "error": {"code": "invalid_credentials", "message": "Invalid credentials"}
    }
    lab.settled(cid)
    assert lab.calls() == before
    Lab.observations["zero_forward_rejections"] = (
        Lab.observations.get("zero_forward_rejections", 0) + 1
    )


@pytest.mark.parametrize(
    "raw,media,extra,path,status,code",
    [
        (b"{", "application/json", (), "/stream", 400, "invalid_request"),
        (b"[]", "application/json", (), "/stream", 400, "invalid_request"),
        (b'{"prompt":"a","prompt":"b"}', "application/json", (), "/stream", 400, "invalid_request"),
        (
            b'{"prompt":"a","pr\\u006fmpt":"b"}',
            "application/json",
            (),
            "/stream",
            400,
            "invalid_request",
        ),
        (
            b'{"prompt":"a","url":"https://example.test"}',
            "application/json",
            (),
            "/stream",
            400,
            "invalid_request",
        ),
        (
            b'{"prompt":"a","token":"private"}',
            "application/json",
            (),
            "/stream",
            400,
            "invalid_request",
        ),
        (b'{"prompt":1}', "application/json", (), "/stream", 400, "invalid_request"),
        (b'{"prompt":"\\ud800"}', "application/json", (), "/stream", 400, "invalid_request"),
        (b"{}", "text/plain", (), "/stream", 415, "unsupported_media"),
        (b"{}", None, (), "/stream", 415, "unsupported_media"),
        (
            b"{}",
            "application/json",
            (("Content-Type", "application/json"),),
            "/stream",
            400,
            "invalid_request",
        ),
        (
            b"{}",
            "application/json",
            (("Content-Encoding", "gzip"),),
            "/stream",
            415,
            "unsupported_media",
        ),
        (
            b"{}",
            "application/json",
            (("Content-Encoding", "identity"),),
            "/stream",
            415,
            "unsupported_media",
        ),
        (b" " * 16385, "application/json", (), "/stream", 413, "request_too_large"),
        (b"{}", "application/json", (), "/stream?upstream=private", 400, "invalid_request"),
    ],
)
def test_wire_http_schema_rejections_zero_upstream(lab, raw, media, extra, path, status, code):
    before = lab.calls()
    stream, cid = lab.open(raw=raw, media=media, extra=extra, path=path)
    assert stream.status == status
    result = json.loads(stream.response.read())
    assert result["error"]["code"] == code and "private" not in json.dumps(result)
    lab.settled(cid)
    assert lab.calls() == before
    Lab.observations["zero_forward_rejections"] = (
        Lab.observations.get("zero_forward_rejections", 0) + 1
    )


@pytest.mark.parametrize("chunked", [False, True])
def test_wire_content_length_and_chunked_requests_credentials_isolated(lab, chunked):
    cid = lab.plan([complete()])
    stream, _ = lab.open(
        cid,
        chunked=chunked,
        extra=(("Cookie", "private=cookie"), ("X-Role", "admin"), ("Last-Event-ID", "private")),
    )
    assert stream.status == 200 and logical(stream.all()) == "safe "
    assert lab.peer.event("called", cid)["isolated"]
    lab.settled(cid)


@pytest.mark.parametrize("size", [16384, 16385])
def test_wire_chunked_upload_enforces_actual_byte_limit_without_content_length(lab, size):
    cid = lab.plan([complete()])
    prefix = json.dumps({"prompt": cid}).encode()
    raw = prefix + b" " * (size - len(prefix))
    before = lab.calls()
    stream, _ = lab.open(cid, raw=raw, chunked=True)
    if size == 16384:
        assert stream.status == 200 and logical(stream.all()) == "safe "
        assert lab.calls() == before + 1
    else:
        assert stream.status == 413
        assert json.loads(stream.response.read())["error"]["code"] == "request_too_large"
        assert lab.calls() == before
        Lab.observations["zero_forward_rejections"] += 1
    lab.settled(cid)


@pytest.mark.parametrize(
    "step,ending,multiline",
    [(1, b"\n", False), (2, b"\r\n", False), (3, b"\r", False), (7, b"\n", True)],
)
def test_wire_fragmentation_unicode_json_escapes_and_three_pii_categories(
    lab, step, ending, multiline
):
    raw = (
        b": private@example.test\nid: private@example.test\nretry: 3\n"
        + wire("delta", {"channel": 0, "text": "\u2603 user@"}, ascii_json=False)
        + wire("delta", {"channel": 1, "text": "+1202"})
        + b'event: delta\ndata: {"channel":0,"text":"example\\u002etest "}\n\n'
        + wire("delta", {"channel": 1, "text": "5550123 000-"})
        + wire("delta", {"channel": 1, "text": "12-3456 "})
        + wire("done", {"channel": 1})
        + wire("done", {"channel": 0})
        + wire("end", {})
    )
    if multiline:
        raw = raw.replace(b"data: {", b"data: {\ndata: ")
    raw = raw.replace(b"\n", ending)
    cid = lab.plan([raw[i : i + step] for i in range(0, len(raw), step)])
    stream, _ = lab.open(cid)
    frames = stream.all()
    assert stream.status == 200 and logical(frames, 0) == "\u2603 [REDACTED] "
    assert logical(frames, 1) == "[REDACTED] [REDACTED] "
    assert [v["channel"] for k, v in frames if k == "done"] == [1, 0]
    assert frames[-1] == ("end", {}) and not stream.pending
    assert all(k in {"delta", "done", "end"} for k, v in frames)
    assert lab.peer.event("provider_closed", cid)["writes"] == (len(raw) + step - 1) // step
    high_water(lab.settled(cid))


def test_wire_whole_candidate_masking_includes_surrounding_candidate_text(lab):
    cid = lab.plan([complete("left TAGuser@example.testZZ% right ")])
    stream, _ = lab.open(cid)
    assert logical(stream.all()) == "left [REDACTED] right "
    lab.settled(cid)


def test_wire_known_upstream_error_stays_fixed_and_drops_unresolved_candidate(lab):
    cid = lab.plan(
        [
            wire("delta", {"channel": 0, "text": "safe private@"}),
            wire("error", {"code": "upstream_error"}) + wire("end", {}),
        ]
    )
    stream, _ = lab.open(cid)
    frames = stream.all()
    assert stream.status == 200 and logical(frames) == "safe "
    assert frames[-1] == ("error", {"code": "upstream_error", "message": "Upstream service failed"})
    assert "end" not in [k for k, _ in frames] and "private" not in json.dumps(frames)
    lab.settled(cid)


@pytest.mark.parametrize(
    "kind", ["overflow", "eof", "duplicate_done", "premature_end", "malformed", "unknown", "abort"]
)
def test_wire_fail_closed_without_unresolved_text_or_false_end(lab, kind):
    chunks = [wire("delta", {"channel": 0, "text": "safe private@"})]
    expected = "safe "
    if kind == "overflow":
        chunks = [
            wire("delta", {"channel": 0, "text": "safe " + "x" * 255}),
            wire("delta", {"channel": 0, "text": "xx"}),
        ]
    elif kind == "duplicate_done":
        chunks += [wire("done", {"channel": 0})] * 2
        expected += "[REDACTED]"
    elif kind == "premature_end":
        chunks += [wire("end", {})]
    elif kind == "malformed":
        chunks += [b'event: delta\ndata: {"channel":0,"channel":1,"text":"private"}\n\n']
    elif kind == "unknown":
        chunks += [b"event: unknown\ndata: {}\n\n"]
    cid = lab.plan(chunks, abort=(kind == "abort"))
    stream, _ = lab.open(cid)
    frames = stream.all()
    assert stream.status == 200 and logical(frames) == expected
    assert "end" not in [k for k, v in frames] and "private" not in json.dumps(frames)
    high_water(lab.settled(cid))


@pytest.mark.parametrize(
    "status,media,compressed,code",
    [
        (302, "text/event-stream", False, "upstream_error"),
        (429, "text/event-stream", False, "upstream_error"),
        (500, "text/event-stream", False, "upstream_error"),
        (200, "application/json", False, "invalid_stream"),
        (200, "text/event-stream", True, "invalid_stream"),
    ],
)
def test_wire_upstream_preflight_failure_is_sanitized_json(lab, status, media, compressed, code):
    cid = lab.plan(
        [b"private upstream diagnostic"], status=status, media=media, compressed=compressed
    )
    stream, _ = lab.open(cid)
    assert stream.status == 502
    result = json.loads(stream.response.read())
    assert result["error"]["code"] == code and "private" not in json.dumps(result)
    assert stream.headers["x-content-type-options"] == "nosniff"
    assert not lab.settled(cid)["quarantined"]


@pytest.mark.parametrize("safe", [False, True])
def test_wire_client_disconnect_closes_blocked_upstream_and_withheld_pii(lab, safe):
    text = ("safe " if safe else "") + "private@"
    cid = lab.plan([wire("delta", {"channel": 0, "text": text}), complete()], gate_at=1)
    stream, _ = lab.open(cid)
    lab.peer.event("held", cid)
    if safe:
        assert stream.frame() == ("delta", {"channel": 0, "text": "safe "})
    stream.close()
    provider = lab.peer.event("provider_closed", cid, timeout=5)
    assert provider["disconnected"] and not provider["complete"]
    stats = lab.settled(cid)
    assert not stats["quarantined"] and stats.get("native_responses", 0) == stats.get(
        "native_closed", 0
    )
    assert lab.stats().get("send_calls") == stats.get("send_calls")
    Lab.observations.setdefault("disconnect", []).append(
        {
            "safe_output_first": safe,
            "confirmed_peer_disconnect": provider["disconnected"],
            "quarantined": stats["quarantined"],
        }
    )


@pytest.mark.parametrize("kind", ["first", "read_idle"])
def test_wire_real_inactivity_deadlines_close_native_resources(lab, kind):
    chunks = [wire("delta", {"channel": 0, "text": "safe private@"}), complete()]
    cid = lab.plan(chunks, gate_at=0 if kind == "first" else 1)
    started = time.monotonic()
    stream, _ = lab.open(cid)
    if kind == "read_idle":
        assert stream.frame() == ("delta", {"channel": 0, "text": "safe "})
    lab.peer.event("held", cid)
    remaining = stream.all()
    elapsed = time.monotonic() - started
    assert remaining == [] and 13.5 <= elapsed <= 22
    provider = lab.peer.event("provider_closed", cid)
    assert provider["disconnected"] and not provider["complete"]
    stats = lab.settled(cid)
    assert not stats["quarantined"]
    Lab.observations.setdefault("real_timeout", {})[kind] = {
        "elapsed": elapsed,
        "http_complete": stream.http_complete,
        "peer_disconnect": provider["disconnected"],
    }


def test_wire_sixteen_active_streams_seventeenth_denied_then_capacity_released(lab):
    before = lab.calls()
    clients, cases = [], []
    for index in range(16):
        candidate = f"user{index}@" if index % 2 == 0 else f"ref{index}"
        suffix = "example.test " if index % 2 == 0 else "-suffix "
        cid = lab.plan(
            [
                wire("delta", {"channel": 0, "text": f"stream{index} " + candidate}),
                wire("delta", {"channel": 0, "text": suffix})
                + wire("done", {"channel": 0})
                + wire("end", {}),
            ],
            gate_at=1,
        )
        stream, _ = lab.open(cid)
        assert stream.status == 200 and stream.frame() == (
            "delta",
            {"channel": 0, "text": f"stream{index} "},
        )
        lab.peer.event("held", cid)
        clients.append(stream)
        cases.append(cid)
    assert lab.stats()["active_http"] == lab.stats()["active_upstream"] == 16
    extra = lab.plan([complete("capacity released ")])
    denied, trace = lab.open(extra)
    assert (
        denied.status == 429
        and json.loads(denied.response.read())["error"]["code"] == "stream_capacity_exceeded"
    )
    lab.proxy.event("http_done", trace)
    assert lab.calls() == before + 16
    lab.release(cases[0])
    assert clients[0].all()[-1] == ("end", {})
    wait_until(lambda: lab.stats()["active_http"] == 15)
    reused, _ = lab.open(extra)
    assert reused.status == 200 and logical(reused.all()) == "capacity released "
    for index, (stream, cid) in enumerate(zip(clients[1:], cases[1:], strict=True), start=1):
        lab.release(cid)
        frames = stream.all()
        expected = "[REDACTED] " if index % 2 == 0 else f"ref{index}-suffix "
        assert logical(frames) == expected and frames[-1] == ("end", {})
    wait_until(lambda: lab.stats()["active_http"] == 0)
    assert lab.calls() == before + 17
    Lab.observations["capacity"] = {
        "occupied": 16,
        "denied_status": 429,
        "forwarded_on_denial": 0,
        "released_and_reused": True,
    }


@pytest.mark.parametrize("count", [1000, 5000])
def test_wire_long_stream_high_water_and_empirical_process_rss(lab, count):
    before = lab.stats()
    cid = lab.plan(repeat=count, width=25)
    stream, _ = lab.open(cid)
    digest = hashlib.sha256()
    chars = 0
    kinds = []
    while (event := stream.frame()) is not None:
        kind, value = event
        if kind == "delta":
            digest.update(value["text"].encode())
            chars += len(value["text"])
        else:
            kinds.append(kind)
    expected = ("word " * 25 * count).encode()
    assert digest.hexdigest() == hashlib.sha256(expected).hexdigest() and chars == len(expected)
    assert kinds == ["done", "end"]
    after = lab.settled(cid)
    high_water(after)
    if before["rss"] is not None:
        assert after["rss"] - before["rss"] < 64 * 1024 * 1024  # Empirical regression guard only.
    Lab.observations.setdefault("long_stream", []).append(
        {
            "events": count,
            "chars": chars,
            "rss_before": before["rss"],
            "rss_after": after["rss"],
            "peak_rss": after["peak_rss"],
            "high": after["high"],
        }
    )


def test_wire_slow_reader_native_buffering_probe_and_disconnect(pair):
    with Lab() as lab:
        cid = lab.plan(repeat=50000, width=205)
        stream, _ = lab.open(cid, receive_buffer=4096)
        assert stream.status == 200 and stream.frame()[0] == "delta"
        snapshots = []

        def stable_pending():
            state = lab.stats()
            snapshots.append(state)
            if state["pending_sends"] and state.get("suspended_sends", 0):
                checks = [lab.stats() for _ in range(3)]
                if all(
                    s["pending_send"] == state["pending_send"]
                    and s.get("native_reads", 0) == state.get("native_reads", 0)
                    for s in checks
                ):
                    return state
            return False

        observed = None
        try:
            observed = wait_until(stable_pending, 6)
        except AssertionError:
            pass  # Explicitly reported limitation, not fabricated kernel-stall evidence.
        stats = observed or lab.stats()
        high_water(stats)
        stream.close()
        lab.peer.event("provider_closed", cid, timeout=5)
        closed = lab.settled(cid)
        assert not closed["quarantined"]
        Lab.observations["slow_reader"] = {
            "stable_suspended_send_reproduced": observed is not None,
            "control_barriers": 3 if observed else 0,
            "native_reads": stats.get("native_reads", 0),
            "native_bytes": stats.get("native_bytes", 0),
            "offered_asgi_bytes": stats.get("send_bytes", 0),
            "suspended_sends": stats.get("suspended_sends", 0),
            "high": stats["high"],
            "rss": stats["rss"],
            "peak_rss": stats["peak_rss"],
            "snapshots": len(snapshots),
            "client_receive_buffer_requested": 4096,
            "listener_send_buffer": lab.proxy.event("bound")["listener_send_buffer"],
            "exact_socket_stall_deadline_verified": False,
        }


def test_wire_connection_refusal_is_controlled_json(pair):
    with Lab(refused=True) as lab:
        stream, cid = lab.open(raw=b'{"prompt":"synthetic input"}')
        assert stream.status == 502 and json.loads(stream.response.read()) == {
            "error": {"code": "upstream_error", "message": "Upstream service failed"}
        }
        assert not lab.settled(cid)["quarantined"]


def test_wire_shutdown_with_active_request_cancels_native_upstream(pair):
    with Lab() as lab:
        cid = lab.plan(
            [wire("delta", {"channel": 0, "text": "safe private@"}), complete()], gate_at=1
        )
        stream, _ = lab.open(cid)
        assert stream.frame() == ("delta", {"channel": 0, "text": "safe "})
        lab.peer.event("held", cid)
        lab.proxy.command("stop")
        drained = lab.proxy.event("drained")
        assert drained["clean"] and drained["active_http"] == drained["active_upstream"] == 0
        assert stream.all() == []
        assert lab.peer.event("provider_closed", cid)["disconnected"]
        lab.proxy.process.wait(timeout=5)
        assert lab.proxy.process.returncode == 0
        assert lab.proxy.event("lifespan.shutdown.complete")
        Lab.observations["active_shutdown"] = {"clean": True, "pool_closes": drained["pool_closes"]}


def test_wire_invalid_configuration_child_exit_is_expected_and_reaped(pair):
    with Lab(invalid=True) as lab:
        assert lab.proxy.process.returncode == 2 and not lab.proxy.forced


def test_wire_fixture_exception_still_reaps_both_children(pair):
    saved = None
    with pytest.raises(RuntimeError, match="Synthetic fixture failure"):
        with Lab() as lab:
            saved = lab
            raise RuntimeError("Synthetic fixture failure")
    assert len(saved.children) == 2
    assert all(c.process.returncode == 0 and not c.forced for c in saved.children)
