import asyncio
import json
import logging

import httpx
import pytest

from task3_streaming import app as module
from task3_streaming.app import create_app
from task3_streaming.service import Capacity
from tests.async_support import Body, Gate, ManualClock, Transport, checked, exercise, until
from tests.http_support import HTTP, SETTINGS, TOKEN, UPSTREAM, Lifespan, running
from tests.support import output, stream, text_output, wire

pytestmark = pytest.mark.task3


@pytest.fixture(autouse=True)
def isolate_http_capacity(monkeypatch):
    # Only new HTTP tests isolate their own process counter; production has no override.
    monkeypatch.setattr(module, "_HTTP_CAPACITY", Capacity())


@pytest.mark.parametrize(
    "values",
    [
        [],
        [b"Basic private"],
        [b"Bearer private"],
        [("Bearer " + TOKEN).encode()] * 2,
        [("Bearer  " + TOKEN).encode()],
        [("Bearer\t" + TOKEN).encode()],
        [("Bearer " + TOKEN + ",x").encode()],
        [("Bearer " + TOKEN + " ").encode()],
        [b"Bearer \xff"],
    ],
)
def test_http_authentication_rejects_before_body_or_upstream(values):
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(raw=b"private malformed", headers=[(b"authorization", v) for v in values])
            await http(app)
            assert http.status == 401 and http.receives == 0
            assert http.json == {
                "error": {"code": "invalid_credentials", "message": "Invalid credentials"}
            }
            assert not transport.requests
            assert dict(http.messages[0]["headers"])[b"www-authenticate"] == b'Bearer realm="task3"'

    exercise(scenario())


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not-json private",
        b"[]",
        b"null",
        b"{}",
        b'{"prompt":true}',
        b'{"prompt":1}',
        b'{"prompt":1e9999999999999999999}',
        b'{"prompt":""}',
        b'{"prompt":"a","prompt":"private"}',
        b'{"prompt":"a","pr\\u006fmpt":"private"}',
        b'{"prompt":"\\ud800"}',
        b'{"prompt":"\xff"}',
        b'{"prompt":"a","url":"https://private.test"}',
        b'{"prompt":"a","authorization":"private"}',
        b'{"prompt":"a","model":"private"}',
        b'{"prompt":NaN}',
        b'{"prompt":[[]]}',
        b'\xef\xbb\xbf{"prompt":"a"}',
        json.dumps({"prompt": "x" * 4097}).encode(),
        b'{"prompt":' + b"[" * 1100 + b"]" * 1100 + b"}",
    ],
)
def test_strict_prompt_validation_zero_upstream(raw):
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(raw=raw)
            await http(app)
            assert http.status == 400 and http.json["error"]["code"] == "invalid_request"
            assert not transport.requests and b"private" not in http.body

    exercise(scenario())


@pytest.mark.parametrize(
    "extra,status",
    [
        ([(b"content-type", b"text/plain")], 415),
        ([], 415),
        ([(b"content-type", b"application/json")] * 2, 400),
        ([(b"content-type", b"application/json; charset=latin1")], 415),
        ([(b"content-type", b"application/json"), (b"content-encoding", b"gzip")], 415),
        ([(b"content-type", b"application/json"), (b"content-encoding", b"identity")], 415),
        (
            [
                (b"content-type", b"application/json"),
                (b"content-length", b"1"),
                (b"content-length", b"1"),
            ],
            400,
        ),
        ([(b"content-type", b"application/json"), (b"content-length", b"-1")], 400),
        ([(b"content-type", b"application/json"), (b"content-length", b"16385")], 413),
        ([(b"content-type", b"application/json"), (b"content-length", b"1,2")], 400),
        ([(b"content-type", b"application/json"), (b"transfer-encoding", b"gzip")], 400),
        (
            [
                (b"content-type", b"application/json"),
                (b"transfer-encoding", b"chunked"),
                (b"content-length", b"1"),
            ],
            400,
        ),
    ],
)
def test_metadata_failures_do_not_read_body_or_contact_upstream(extra, status):
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(headers=[(b"Authorization", ("Bearer " + TOKEN).encode()), *extra])
            await http(app)
            assert http.status == status and http.receives == 0 and not transport.requests

    exercise(scenario())


@pytest.mark.parametrize("raw,status", [(b" " * 16384, 200), (b" " * 16385, 413)])
def test_body_limit_enforced_across_chunked_receive_messages(raw, status):
    async def scenario():
        prefix = b'{"prompt":"safe"}'
        body = prefix + raw[len(prefix) :]
        transport = Transport(Body([stream("safe ")]))
        async with running(transport) as app:
            http = HTTP(
                chunks=[body[:8000], body[8000:]],
                headers=[
                    (b"authorization", ("Bearer " + TOKEN).encode()),
                    (b"content-type", b"application/json"),
                    (b"transfer-encoding", b"chunked"),
                ],
            )
            await http(app)
            assert http.status == status and len(transport.requests) == (status == 200)

    exercise(scenario())


@pytest.mark.parametrize("length", [0, 1, 99])
def test_declared_length_mismatch_rejects_without_upstream(length):
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(
                headers=[
                    (b"authorization", ("Bearer " + TOKEN).encode()),
                    (b"content-type", b"application/json"),
                    (b"content-length", str(length).encode()),
                ]
            )
            await http(app)
            assert http.status == 400 and not transport.requests

    exercise(scenario())


@pytest.mark.parametrize(
    "method,path,status",
    [
        ("GET", "/stream", 405),
        ("HEAD", "/stream", 405),
        ("OPTIONS", "/stream", 405),
        ("POST", "/stream/", 404),
        ("POST", "/docs", 404),
    ],
)
def test_routes_methods_no_redirect_or_upstream(method, path, status):
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(method=method, path=path)
            await http(app)
            assert http.status == status and not transport.requests

    exercise(scenario())


def test_query_credentials_rejected_without_upstream():
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP(query=b"token=private")
            await http(app)
            assert http.status == 400 and not transport.requests

    exercise(scenario())


@pytest.mark.parametrize("step", [1, 2, 7, 4096])
def test_sanitized_success_unicode_multiple_channels_and_separate_credentials(step, caplog):
    caplog.set_level(logging.DEBUG)

    async def scenario():
        raw = (
            wire("delta", {"channel": 0, "text": "\u2603 user@"}, ascii_json=False)
            + wire("delta", {"channel": 1, "text": "000-"})
            + wire("delta", {"channel": 0, "text": "example.test "})
            + wire("delta", {"channel": 1, "text": "12-3456"})
            + wire("done", {"channel": 1})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
        body = Body([raw[i : i + step] for i in range(0, len(raw), step)])
        transport = Transport(body)
        async with running(transport) as app:
            http = HTTP(
                raw=b' {"prompt":"synthetic input"} ',
                headers=[
                    (b"authorization", ("Bearer " + TOKEN).encode()),
                    (b"content-type", b"application/json"),
                    (b"cookie", b"private=cookie"),
                    (b"x-role", b"admin"),
                    (b"last-event-id", b"private"),
                ],
            )
            await http(app)
            assert http.status == 200 and text_output(http.frames, 0) == "\u2603 [REDACTED] "
            assert text_output(http.frames, 1) == "[REDACTED]" and output(http.frames)[-1] == (
                "end",
                {},
            )
            assert len([m for m in http.messages if m["type"] == "http.response.start"]) == 1
            headers = dict(http.messages[0]["headers"])
            assert headers == {
                b"content-type": b"text/event-stream; charset=utf-8",
                b"cache-control": b"no-store",
                b"x-content-type-options": b"nosniff",
            }
            sent = transport.requests[0]
            assert sent.content == b'{"prompt":"synthetic input"}'
            assert sent.headers["authorization"] == "Bearer " + UPSTREAM
            assert all(h not in sent.headers for h in ("cookie", "x-role", "last-event-id"))
            assert app.state.runtime.service.active == 0 and not app.state.runtime.owners
            assert body.closed and len(transport.requests) == 1
        assert transport.closes == 1

    exercise(scenario())
    assert (
        TOKEN not in caplog.text
        and UPSTREAM not in caplog.text
        and "user@example.test" not in caplog.text
    )


def test_asgi_send_backpressure_counts_and_progressive_safe_delivery():
    async def scenario():
        sending, reading = (
            Gate(),
            Gate(
                data=wire("delta", {"channel": 0, "text": "example.test "})
                + wire("done", {"channel": 0})
                + wire("end", {})
            ),
        )
        body = Body([wire("delta", {"channel": 0, "text": "safe private@"}), reading])

        async def block(message):
            if message.get("body") and not sending.entered.is_set():
                await sending.wait()

        transport = Transport(body)
        async with running(transport) as app:
            http = HTTP(block=block)
            task = asyncio.create_task(http(app))
            await checked(sending.entered.wait())
            assert http.status == 200 and body.reads == 1 and not reading.entered.is_set()
            for _ in range(20):
                await asyncio.sleep(0)
            assert body.reads == 1 and not http.frames
            sending.release.set()
            await checked(reading.entered.wait())
            assert text_output(http.frames) == "safe " and body.reads == 2 and not task.done()
            reading.release.set()
            await checked(task)
            assert text_output(http.frames) == "safe [REDACTED] " and body.reads == 2
            assert body.closed and not app.state.runtime.owners

    exercise(scenario())


@pytest.mark.parametrize("time", [9.999, 10.0, 10.001])
def test_exact_send_deadline_no_raw_tail_or_error_write_after_stall(time):
    async def scenario():
        clock, gate = ManualClock(), Gate()
        body = Body([wire("delta", {"channel": 0, "text": "safe private@"}), stream("unused")])

        async def block(message):
            if message.get("body") and not gate.entered.is_set():
                await gate.wait()

        async with running(Transport(body), clock) as app:
            http = HTTP(block=block)
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            clock.advance(time)
            if time >= 10:
                # Observe deadline cancellation before releasing the server send.
                # Bytes already offered to ASGI cannot be retracted by a timer.
                await checked(gate.cancelled.wait())
            gate.release.set()
            await checked(task)
            if time < 10:
                assert output(http.frames)[-1] == ("end", {})
            else:
                assert not http.frames and len(http.attempts) == 2
            assert body.closed and not app.state.runtime.owners
            assert b"private" not in http.body

    exercise(scenario())


@pytest.mark.parametrize("point", ["before_headers", "during_send", "unresolved", "request_body"])
def test_disconnect_never_writes_error_or_flushes_pending_pii(point):
    async def scenario():
        gate = Gate()
        body = Body([gate] if point == "unresolved" else [stream("safe ")])
        if point == "unresolved":
            body.chunks.insert(0, wire("delta", {"channel": 0, "text": "private@"}))
        transport = Transport(body, opening=gate if point == "before_headers" else None)

        async def block(message):
            if point == "during_send" and message.get("body"):
                await gate.wait()

        async with running(transport) as app:
            http = HTTP(block=block, chunks=[] if point == "request_body" else None)
            task = asyncio.create_task(http(app))
            if point == "request_body":
                await until(lambda: http.receives == 1)
            else:
                await checked(gate.entered.wait())
            attempts = len(http.attempts)
            http.disconnect()
            await checked(task)
            assert len(http.attempts) == attempts and b"private" not in http.body
            assert not app.state.runtime.owners and app.state.runtime.service.active == 0
            assert len(transport.requests) == (point != "request_body")

    exercise(scenario())


def test_cancellation_while_upstream_blocked_propagates_and_closes():
    async def scenario():
        gate = Gate()
        body = Body([gate])
        async with running(Transport(body)) as app:
            http = HTTP()
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await checked(task)
            assert body.closed and not app.state.runtime.owners

    exercise(scenario())


@pytest.mark.parametrize(
    "status,headers,error,expected,code",
    [
        (302, [("content-type", "text/event-stream")], None, 502, "upstream_error"),
        (429, [("content-type", "text/event-stream")], None, 502, "upstream_error"),
        (200, [("content-type", "application/json")], None, 502, "invalid_stream"),
        (
            200,
            [("content-type", "text/event-stream")],
            httpx.ConnectTimeout("private"),
            504,
            "stream_timeout",
        ),
        (
            200,
            [("content-type", "text/event-stream")],
            httpx.ConnectError("private"),
            502,
            "upstream_error",
        ),
    ],
)
def test_upstream_preflight_error_is_one_json_response_no_body_read(
    status, headers, error, expected, code
):
    async def scenario():
        body = Body([b"private@upstream"])
        transport = Transport(body, status=status, headers=headers, error=error)
        async with running(transport) as app:
            http = HTTP()
            await http(app)
            assert http.status == expected and http.json["error"]["code"] == code
            assert len(http.messages) == 2 and body.reads == 0 and len(transport.requests) == 1
            assert b"private" not in http.body

    exercise(scenario())


@pytest.mark.parametrize(
    "raw",
    [wire("delta", {"channel": 0, "text": "safe private@"}), b"event: invalid\ndata: private\n\n"],
)
def test_postheader_failure_closes_without_end_or_new_status(raw):
    async def scenario():
        body = Body([raw, httpx.ReadError("private provider diagnostic")])
        async with running(Transport(body)) as app:
            http = HTTP()
            await http(app)
            assert http.status == 200
            assert all(kind not in {"end", "error"} for kind, _ in output(http.frames))
            assert http.messages[-1] == {"type": "http.response.body", "body": b""}
            assert len([m for m in http.messages if m["type"] == "http.response.start"]) == 1
            assert b"private" not in http.body and body.closed

    exercise(scenario())


def test_known_upstream_error_remains_processor_owned_fixed_frame():
    async def scenario():
        body = Body(
            [
                wire("delta", {"channel": 0, "text": "private@"})
                + wire("error", {"code": "upstream_error"})
            ]
        )
        async with running(Transport(body)) as app:
            http = HTTP()
            await http(app)
            assert output(http.frames) == [
                ("error", {"code": "upstream_error", "message": "Upstream service failed"})
            ]
            assert body.closed

    exercise(scenario())


@pytest.mark.parametrize("stage", ["start", "body"])
def test_send_failure_no_second_status_or_error_send(stage):
    async def scenario():
        def fail(message):
            if (message["type"] == "http.response.start") == (stage == "start"):
                raise OSError("private disconnected")

        body = Body([stream("private@example.test ")])
        async with running(Transport(body)) as app:
            http = HTTP(fail=fail)
            await http(app)
            assert len(http.attempts) == (1 if stage == "start" else 2)
            assert body.closed and not app.state.runtime.owners

    exercise(scenario())


def test_body_timeout_and_lifespan_without_startup():
    async def scenario():
        transport, clock = Transport(), ManualClock()
        app = create_app(SETTINGS, upstream_transport=transport, clock=clock)
        http = HTTP()
        await http(app)
        assert http.status == 503 and not transport.requests
        async with app.router.lifespan_context(app):
            http = HTTP(chunks=[])
            task = asyncio.create_task(http(app))
            await until(lambda: http.receives == 1)
            clock.advance(10)
            await checked(task)
            assert http.status == 408 and not transport.requests

    exercise(scenario())


def test_http_cap_includes_blocked_terminal_sends_after_upstream_releases():
    async def scenario():
        gate = Gate()
        transport = Transport(factory=lambda r: Body([wire("end", {})]))

        async def block(message):
            if message.get("body"):
                await gate.wait()

        async with running(transport) as app:
            clients = [HTTP(block=block) for _ in range(16)]
            tasks = [asyncio.create_task(c(app)) for c in clients]
            await until(
                lambda: (
                    len(app.state.runtime.owners) == 16
                    and all(len(c.attempts) == 2 for c in clients)
                )
            )
            assert app.state.runtime.service.active == 0
            excess = HTTP()
            await excess(app)
            assert excess.status == 429 and len(transport.requests) == 16
            gate.release.set()
            await checked(asyncio.gather(*tasks))
            assert not app.state.runtime.owners and module._HTTP_CAPACITY.active == 0

    exercise(scenario())


def test_concurrent_clients_isolate_prompts_channels_and_responses():
    async def scenario():
        transport = Transport(
            factory=lambda r: Body([stream(json.loads(r.content)["prompt"] + " ")])
        )
        async with running(transport) as app:
            clients = [HTTP(raw=json.dumps({"prompt": f"client{i}"}).encode()) for i in range(16)]
            await checked(asyncio.gather(*(c(app) for c in clients)))
            assert [text_output(c.frames) for c in clients] == [f"client{i} " for i in range(16)]
            assert len(transport.requests) == 16 and all(b.closed for b in transport.bodies)

    exercise(scenario())


def test_real_asgi_lifespan_startup_shutdown_messages_and_shared_close_once():
    async def scenario():
        transport = Transport(
            Body([wire("delta", {"channel": 0, "text": "safe private@"}), Gate()])
        )
        app = create_app(SETTINGS, upstream_transport=transport)
        life = Lifespan(app)
        assert (await life.start())["type"] == "lifespan.startup.complete"
        client = HTTP()
        task = asyncio.create_task(client(app))
        await checked(transport.body.chunks[1].entered.wait())
        runtime = app.state.runtime
        assert all(await asyncio.gather(runtime.aclose(), runtime.aclose()))
        await checked(task)
        assert transport.closes == 1 and transport.body.closed
        rejected = HTTP()
        await rejected(app)
        assert rejected.status == 503 and len(transport.requests) == 1
        assert (await life.close())["type"] == "lifespan.shutdown.complete"
        await checked(life.task)
        assert transport.closes == 1 and not app.state.unclean_shutdown

    exercise(scenario())


def test_startup_configuration_failure_is_sanitized_and_opens_no_transport(monkeypatch):
    async def scenario():
        monkeypatch.delenv("T3_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("T3_UPSTREAM_URL", raising=False)
        transport = Transport()
        life = Lifespan(create_app(upstream_transport=transport))
        failure = await life.start()
        assert failure["type"] == "lifespan.startup.failed"
        with pytest.raises(ValueError, match="Invalid HTTP configuration"):
            await life.task
        assert not transport.requests and transport.closes == 0

    exercise(scenario())


def test_uncertain_send_cleanup_retains_owner_quarantine_and_late_confirmed_release():
    async def scenario():
        clock, gate = ManualClock(), Gate(resistant=True)
        transport = Transport(Body([stream("safe ")]))

        async def block(message):
            if message.get("body") and not gate.entered.is_set():
                await gate.wait()

        app = create_app(SETTINGS, upstream_transport=transport, clock=clock)
        life = Lifespan(app)
        await life.start()
        http = HTTP(block=block)
        task = asyncio.create_task(http(app))
        await checked(gate.entered.wait())
        clock.advance(10)
        await checked(gate.cancelled.wait())
        runtime = app.state.runtime
        owner = next(iter(runtime.owners))
        clock.advance(11.001)
        await checked(task)
        assert runtime.owners and runtime.service.adapter.quarantined and not owner.work.done()
        rejected = HTTP()
        await rejected(app)
        assert rejected.status == 503 and len(transport.requests) == 1
        assert not await runtime.aclose() and transport.closes == 0
        gate.release.set()
        await until(lambda: not runtime.owners)
        assert await runtime.aclose() and transport.closes == 1
        assert (await life.close())["type"] == "lifespan.shutdown.complete"
        await life.task
        assert "end" not in [kind for kind, _ in output(http.frames)]

    exercise(scenario())


def test_queued_disconnect_is_seen_before_admission_or_headers():
    async def scenario():
        transport = Transport()
        async with running(transport) as app:
            http = HTTP()
            http.disconnect()
            await http(app)
            assert not http.messages and not transport.requests and not app.state.runtime.owners

    exercise(scenario())


def test_pending_sanitized_frames_await_individual_asgi_sends_without_more_reads():
    async def scenario():
        gates = [Gate(), Gate(), Gate()]
        count = 0

        async def block(message):
            nonlocal count
            if message.get("body") and count < 3:
                gate = gates[count]
                count += 1
                await gate.wait()

        body = Body(
            [
                wire("delta", {"channel": 0, "text": " " * 600}),
                wire("done", {"channel": 0}) + wire("end", {}),
            ]
        )
        async with running(Transport(body)) as app:
            http = HTTP(block=block)
            task = asyncio.create_task(http(app))
            for i, gate in enumerate(gates):
                await checked(gate.entered.wait())
                assert body.reads == 1 and len(http.frames) == i
                gate.release.set()
            await checked(task)
            assert [len(v["text"]) for kind, v in output(http.frames) if kind == "delta"] == [
                256,
                256,
                88,
            ]
            assert body.reads == 2 and body.closed

    exercise(scenario())


@pytest.mark.parametrize("before", [119.999, 120.0, 120.001])
def test_send_uses_remaining_overall_budget_instead_of_another_ten_seconds(before):
    async def scenario():
        clock, gate = ManualClock(), Gate()

        class ScheduledBody(Body):
            async def __anext__(self):
                if self.index < 14:
                    clock.advance(self.index * 9)
                return await super().__anext__()

        body = ScheduledBody(
            [wire("delta", {"channel": 0, "text": "safe "})] * 14
            + [wire("done", {"channel": 0}) + wire("end", {})]
        )
        count = 0

        async def block(message):
            nonlocal count
            if message.get("body"):
                count += 1
                if count == 14:
                    await gate.wait()

        async with running(Transport(body), clock) as app:
            http = HTTP(block=block)
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            assert clock.now() == 117 and body.reads == 14
            clock.advance(before)
            if before < 120:
                for _ in range(20):
                    await asyncio.sleep(0)
                assert not task.done() and not body.closed
                gate.release.set()
            else:
                await checked(gate.cancelled.wait())
            await checked(task)
            assert body.closed
            assert ("end" in [kind for kind, _ in output(http.frames)]) == (before < 120)
            assert not app.state.runtime.owners

    exercise(scenario())


def test_postheader_failure_cannot_renew_an_expired_send_budget_for_error_or_close():
    async def scenario():
        clock, gate = ManualClock(), Gate()
        body = Body([wire("delta", {"channel": 0, "text": "safe private@"}), gate])
        async with running(Transport(body), clock) as app:
            http = HTTP()
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            assert len(http.attempts) == 2
            clock.advance(11)
            gate.release.set()  # Empty chunk then EOF -> invalid stream.
            await checked(task)
            assert len(http.attempts) == 2 and text_output(http.frames) == "safe "
            assert body.closed

    exercise(scenario())


def test_send_cancellation_and_response_close_share_one_cleanup_grace():
    async def scenario():
        clock = ManualClock()
        sending, closing = Gate(resistant=True), Gate()
        body = Body([stream("safe ")], close_gate=closing)

        async def block(message):
            if message.get("body") and not sending.entered.is_set():
                await sending.wait()

        app = create_app(SETTINGS, upstream_transport=Transport(body), clock=clock)
        life = Lifespan(app)
        await life.start()
        http = HTTP(block=block)
        request = asyncio.create_task(http(app))
        await checked(sending.entered.wait())
        clock.advance(10)
        await checked(sending.cancelled.wait())
        await checked(closing.entered.wait())
        owner = next(iter(app.state.runtime.owners))
        assert owner.cleanup_deadline == 11
        clock.advance(10.75)
        sending.release.set()
        clock.advance(11.001)
        await checked(request)
        assert owner in app.state.runtime.owners and not owner.session.cleaned
        assert app.state.runtime.service.adapter.quarantined
        closing.release.set()
        await until(lambda: owner.session.cleaned)
        # Read public confirmation state; never retry close/replay or renew its grace.
        assert await app.state.runtime.aclose()
        assert not app.state.runtime.owners
        assert (await life.close())["type"] == "lifespan.shutdown.complete"
        await life.task

    exercise(scenario())


def test_unclean_lifespan_retains_resource_owner_and_reports_fixed_shutdown_failure():
    async def scenario():
        clock, gate = ManualClock(), Gate(resistant=True)
        body = Body([wire("delta", {"channel": 0, "text": "private@"}), gate])
        transport = Transport(body)
        app = create_app(SETTINGS, upstream_transport=transport, clock=clock)
        life = Lifespan(app)
        await life.start()
        http = HTTP()
        request = asyncio.create_task(http(app))
        await checked(gate.entered.wait())
        closing = asyncio.create_task(life.close())
        await checked(gate.cancelled.wait())
        clock.advance(1.001)
        failure = await checked(closing)
        assert failure["type"] == "lifespan.shutdown.failed"
        with pytest.raises(RuntimeError, match="Unclean streaming shutdown"):
            await life.task
        await checked(request)
        assert app.state.unclean_shutdown and app.state.runtime.owners
        assert transport.closes == 0 and not body.closed and b"private" not in http.body
        gate.release.set()
        owner = next(iter(app.state.runtime.owners))
        await until(lambda: owner.session.cleaned)
        assert await app.state.runtime.aclose() and transport.closes == 1

    exercise(scenario())


def test_repeated_request_cancellation_cannot_discard_owned_send_cleanup():
    async def scenario():
        gate = Gate(resistant=True)

        async def block(message):
            if message.get("body") and not gate.entered.is_set():
                await gate.wait()

        transport = Transport(Body([stream("safe ")]))
        async with running(transport) as app:
            http = HTTP(block=block)
            request = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            request.cancel()
            await checked(gate.cancelled.wait())
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
            assert app.state.runtime.owners
            gate.release.set()
            await until(lambda: not app.state.runtime.owners)
            assert module._HTTP_CAPACITY.active == 0

    exercise(scenario())


def test_cancelled_lifespan_waiter_retains_and_finishes_shared_pool_close():
    async def scenario():
        gate = Gate()
        transport = Transport(close_gate=gate)
        app = create_app(SETTINGS, upstream_transport=transport)
        life = Lifespan(app)
        await life.start()
        await life.input.put({"type": "lifespan.shutdown"})
        await checked(gate.entered.wait())
        life.task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await life.task
        assert app.state.unclean_shutdown
        assert app.state.runtime.stopped.is_set() and transport.closes == 1
        gate.release.set()
        await until(lambda: app.state.runtime.service.adapter.closed)
        assert await app.state.runtime.aclose() and transport.closes == 1

    exercise(scenario())


@pytest.mark.parametrize("text", ["x" * 4096, "\u2603" * 4096])
def test_prompt_character_boundary_and_utf8_request_are_preserved(text):
    async def scenario():
        transport = Transport(Body([wire("end", {})]))
        async with running(transport) as app:
            raw = json.dumps({"prompt": text}, ensure_ascii=False).encode()
            http = HTTP(
                raw=raw,
                headers=[
                    (b"authorization", ("Bearer " + TOKEN).encode()),
                    (b"content-type", b'application/json; charset="UTF-8"'),
                    (b"content-length", str(len(raw)).encode()),
                ],
            )
            await http(app)
            assert http.status == 200 and json.loads(transport.requests[0].content) == {
                "prompt": text
            }

    exercise(scenario())


def test_httpx_asgi_client_success_is_not_claimed_as_socket_backpressure():
    async def scenario():
        body = Body([stream("private@example.test ")])
        async with running(Transport(body)) as app:
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://synthetic.local"
            ) as client:
                response = await client.post(
                    "/stream",
                    json={"prompt": "synthetic input"},
                    headers={"authorization": "Bearer " + TOKEN},
                )
            assert response.status_code == 200
            # ASGITransport coalesces frames; parse its completed body explicitly.
            frames = [part + b"\n\n" for part in response.content.split(b"\n\n") if part]
            assert text_output(frames) == "[REDACTED] "
            assert body.closed

    exercise(scenario())


@pytest.mark.parametrize("condition", ["timeout", "disconnect"])
def test_blocked_response_start_does_not_pull_upstream_body(condition):
    async def scenario():
        clock, gate = ManualClock(), Gate()
        body = Body([stream("private@example.test ")])

        async def block(message):
            if message["type"] == "http.response.start":
                await gate.wait()

        async with running(Transport(body), clock) as app:
            http = HTTP(block=block)
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            assert body.reads == 0 and not http.messages
            if condition == "timeout":
                clock.advance(10)
            else:
                http.disconnect()
            await checked(task)
            assert body.closed and len(http.attempts) == 1 and not http.messages
            assert not app.state.runtime.owners

    exercise(scenario())


def test_http_capacity_is_process_global_across_application_instances():
    async def scenario():
        gate = Gate()

        async def block(message):
            if message.get("body"):
                await gate.wait()

        transports = [Transport(factory=lambda r: Body([wire("end", {})])) for _ in range(2)]
        async with running(transports[0]) as first, running(transports[1]) as second:
            apps = [first, second]
            clients = [HTTP(block=block) for _ in range(16)]
            tasks = [asyncio.create_task(c(apps[i % 2])) for i, c in enumerate(clients)]
            await until(lambda: all(len(c.attempts) == 2 for c in clients))
            excess = HTTP()
            await excess(second)
            assert excess.status == 429 and sum(len(t.requests) for t in transports) == 16
            gate.release.set()
            await checked(asyncio.gather(*tasks))
            assert module._HTTP_CAPACITY.active == 0

    exercise(scenario())


@pytest.mark.parametrize("separator", ["", " ", "-"])
def test_pan_asgi_gated_cross_delta_backpressure_and_safe_output(separator):
    async def scenario():
        value = separator.join(["4111"] + ["1111"] * 3)
        gate = Gate(
            wire("delta", {"channel": 0, "text": value[5:]})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
        body = Body([wire("delta", {"channel": 0, "text": "safe " + value[:5]}), gate])
        async with running(Transport(body)) as app:
            http = HTTP()
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            assert http.status == 200 and text_output(http.frames) == "safe "
            gate.release.set()
            await checked(task)
            assert text_output(http.frames) == "safe [REDACTED]"
            assert output(http.frames)[-1] == ("end", {})
            assert body.closed and body.closes == 1

    exercise(scenario())


def test_pan_asgi_concurrent_channel_context_and_disconnect_withheld_numbers():
    async def scenario():
        def make_body(request):
            return Body(
                [
                    wire("delta", {"channel": 0, "text": "4111 1111 "}),
                    wire("delta", {"channel": 0, "text": "1111 1111"})
                    + wire("done", {"channel": 0})
                    + wire("end", {}),
                ]
            )

        transport = Transport(factory=make_body)
        async with running(transport) as app:
            clients = [HTTP() for _ in range(8)]
            await checked(asyncio.gather(*(client(app) for client in clients)))
            assert all(text_output(client.frames) == "[REDACTED]" for client in clients)
            assert all(body.closed for body in transport.bodies)
        gate = Gate()
        body = Body([wire("delta", {"channel": 0, "text": "4111 1111 "}), gate])
        async with running(Transport(body)) as app:
            http = HTTP()
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            http.disconnect()
            await checked(task)
            assert http.frames == [] and body.closed

    exercise(scenario())


@pytest.mark.parametrize("cause", ["cancel", "idle_timeout"])
def test_pan_asgi_cancellation_and_timeout_discard_numeric_bridge(cause):
    async def scenario():
        clock, gate = ManualClock(), Gate()
        body = Body([wire("delta", {"channel": 0, "text": "4111 1111 "}), gate])
        async with running(Transport(body), clock=clock) as app:
            http = HTTP()
            task = asyncio.create_task(http(app))
            await checked(gate.entered.wait())
            if cause == "cancel":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await checked(task)
            else:
                clock.advance(15)
                await checked(task)
            assert http.frames == [] and body.closed

    exercise(scenario())
