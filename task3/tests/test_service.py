import asyncio

import httpx
import pytest

from task3_streaming.models import ErrorCode, StreamError
from task3_streaming.service import CapacityExceeded, StreamService
from task3_streaming.upstream import UpstreamAdapter, UpstreamRequest, UpstreamSettings
from tests.async_support import (
    Body,
    Gate,
    ManualClock,
    Transport,
    checked,
    exercise,
    make_service,
    until,
)
from tests.support import output, stream, text_output, wire

pytestmark = pytest.mark.task3
REQUEST = UpstreamRequest(b'{"synthetic_input":"not-a-vendor-schema"}')


def test_progressive_delivery_and_exact_read_counts_under_blocked_demand():
    async def scenario():
        gate = Gate(
            data=wire("delta", {"channel": 0, "text": "example.test "})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
        body = Body([wire("delta", {"channel": 0, "text": "safe prefix private@"}), gate])
        service = make_service(Transport(body))
        async with service.stream(REQUEST) as session:
            first = await checked(anext(session))
            assert text_output([first]) == "safe prefix "
            assert not session.completed and not gate.entered.is_set()
            assert body.reads == session.lease.raw_reads == session.lease.processing_chunks == 1
            for _ in range(20):
                await asyncio.sleep(0)
            assert body.reads == 1  # No demand, no background reader.
            pending = asyncio.create_task(anext(session))
            await checked(gate.entered.wait())
            assert body.reads == 2 and not pending.done()
            gate.release.set()
            rest = [await checked(pending)] + [frame async for frame in session]
            assert text_output([first] + rest) == "safe prefix [REDACTED] "
            assert body.reads == 2 and session.completed and session.cleaned
        assert body.closed and body.closes == 1 and service.capacity.active == 0
        assert await service.aclose()

    exercise(scenario())


def test_pending_sanitized_frames_do_not_read_next_network_chunk():
    async def scenario():
        # Many tiny safe delimiters create multiple bounded frames in one input.
        body = Body(
            [
                wire("delta", {"channel": 0, "text": " " * 600}),
                wire("done", {"channel": 0}) + wire("end", {}),
            ]
        )
        service = make_service(Transport(body))
        async with service.stream(REQUEST) as session:
            frames = [await anext(session), await anext(session), await anext(session)]
            assert [len(output([f])[0][1]["text"]) for f in frames] == [256, 256, 88]
            assert body.reads == 1
            frames += [frame async for frame in session]
            assert body.reads == 2 and text_output(frames) == " " * 600
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize("step", [1, 2, 3, 7, 4096])
def test_cross_network_chunks_unicode_channels_and_order(step):
    async def scenario():
        raw = (
            wire("delta", {"channel": 0, "text": "\u2603 a@"}, ascii_json=False)
            + wire("delta", {"channel": 1, "text": "000-"})
            + wire("delta", {"channel": 0, "text": "b.test"})
            + wire("delta", {"channel": 1, "text": "12-3456"})
            + wire("done", {"channel": 1})
            + wire("done", {"channel": 0})
            + wire("end", {})
        )
        body = Body([raw[i : i + step] for i in range(0, len(raw), step)])
        service = make_service(Transport(body))
        async with service.stream(REQUEST) as session:
            frames = [frame async for frame in session]
            assert text_output(frames, 0) == "\u2603 [REDACTED]"
            assert text_output(frames, 1) == "[REDACTED]"
            assert session.completed and session.lease.peak_raw_bytes <= step
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        wire("delta", {"channel": 0, "text": "private@"}),
        b'event: delta\ndata: {"channel":0,"channel":1,"text":"private"}\n\n',
        wire("delta", {"channel": 0, "text": "x" * 257}),
        wire("done", {"channel": 0}),
    ],
)
def test_truncation_invalid_envelopes_and_overflow_drop_raw_candidates(raw):
    async def scenario():
        body = Body([raw])
        service = make_service(Transport(body))
        with pytest.raises(StreamError) as caught:
            async with service.stream(REQUEST) as session:
                frames = [frame async for frame in session]
                assert not frames
        assert "private" not in str(caught.value) + repr(caught.value)
        assert session.processor.redactor.stats.held_chars == 0 and body.closed
        assert not session.completed and await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize(
    "error,code",
    [
        (httpx.ReadTimeout("private timeout"), ErrorCode.TIMEOUT),
        (httpx.ReadError("private read error"), ErrorCode.UPSTREAM),
        (RuntimeError("private failure"), ErrorCode.UPSTREAM),
    ],
)
@pytest.mark.parametrize("after_output", [False, True])
def test_upstream_failure_before_and_after_safe_output(error, code, after_output):
    async def scenario():
        prefix = wire("delta", {"channel": 0, "text": "safe private@"})
        body = Body(([prefix] if after_output else []) + [error])
        transport = Transport(body)
        service = make_service(transport)
        frames = []
        with pytest.raises(StreamError) as caught:
            async with service.stream(REQUEST) as session:
                async for frame in session:
                    frames.append(frame)
        assert text_output(frames) == ("safe " if after_output else "")
        assert caught.value.code is code and caught.value.__context__ is None
        assert "private" not in str(caught.value) and body.closed
        assert not session.completed and len(transport.requests) == 1
        assert await service.aclose()

    exercise(scenario())


def test_known_upstream_error_is_sanitized_terminal_without_success():
    async def scenario():
        body = Body(
            [
                wire("delta", {"channel": 0, "text": "private@"})
                + wire("error", {"code": "upstream_error"})
                + wire("end", {})
            ]
        )
        service = make_service(Transport(body))
        async with service.stream(REQUEST) as session:
            frames = [frame async for frame in session]
            assert output(frames) == [
                ("error", {"code": "upstream_error", "message": "Upstream service failed"})
            ]
            assert not session.completed and session.cleaned
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize("kind", ["connect", "read", "pending_output", "redaction_checkpoint"])
def test_client_cancellation_all_processing_phases(kind):
    async def scenario():
        gate = Gate()
        body = Body([gate] if kind == "read" else [stream(" " * 600)])
        transport = Transport(body, opening=gate if kind == "connect" else None)
        service = make_service(transport)
        session = service.stream(REQUEST)
        if kind == "connect":
            task = asyncio.create_task(session.__aenter__())
            await checked(gate.entered.wait())
        else:
            await session.__aenter__()
            if kind == "pending_output":
                await anext(session)
                task = asyncio.create_task(session.aclose())
                # Explicit close drops already generated but unconsumed safe frames.
                assert await checked(task)
                assert body.reads == 1 and session.processor.redactor.stats.pending_chars == 0
                assert await service.aclose()
                return
            task = asyncio.create_task(anext(session))
            if kind == "read":
                await checked(gate.entered.wait())
            else:
                await until(lambda: body.reads == 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await checked(task)
        assert session.cleaned and not session.completed and service.capacity.active == 0
        if kind != "connect":
            assert body.closed
        assert len(transport.requests) == 1 and await service.aclose()

    exercise(scenario())


def test_cancellation_while_cleanup_retains_shielded_owner():
    async def scenario():
        gate = Gate()
        body = Body([wire("delta", {"channel": 0, "text": "private@"})], close_gate=gate)
        service = make_service(Transport(body))
        session = await service.stream(REQUEST).__aenter__()
        closing = asyncio.create_task(session.aclose())
        await checked(gate.entered.wait())
        closing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await closing
        assert service.active == 1 and not body.closed
        gate.release.set()
        await until(lambda: session.cleaned)
        assert service.active == 0 and await session.aclose()
        assert await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize("stage", ["connect", "read", "response_close"])
def test_uncertain_cleanup_one_grace_retained_quarantine_and_late_release(stage):
    async def scenario():
        clock = ManualClock()
        gate = Gate(resistant=True)
        body = Body(
            [gate] if stage == "read" else [],
            close_gate=gate if stage == "response_close" else None,
        )
        transport = Transport(body, opening=gate if stage == "connect" else None)
        service = make_service(transport, clock)
        session = service.stream(REQUEST)
        if stage == "connect":
            task = asyncio.create_task(session.__aenter__())
            await checked(gate.entered.wait())
        else:
            await session.__aenter__()
            task = (
                asyncio.create_task(anext(session))
                if stage == "read"
                else asyncio.create_task(session.aclose())
            )
            if stage == "read":
                await checked(gate.entered.wait())
        if stage != "response_close":
            task.cancel()
            await checked(gate.cancelled.wait())
        else:
            await checked(gate.entered.wait())
        await until(lambda: session._cleanup_work is not None)
        clock.advance(1.001)
        if stage == "response_close":
            assert await checked(task) is False
        else:
            with pytest.raises(asyncio.CancelledError):
                await checked(task)
        assert service.adapter.quarantined and service.active == service.capacity.active == 1
        assert session._cleanup_work is not None and not session._cleanup_work.done()
        with pytest.raises(StreamError) as caught:
            async with service.stream(REQUEST):
                pass
        assert caught.value.code is ErrorCode.UNAVAILABLE and len(transport.requests) == 1
        assert not await service.aclose()  # No new grace and no pool close under live resource.
        assert transport.closes == 0
        gate.release.set()
        await until(lambda: session.cleaned)
        assert body.closed and service.capacity.active == 0
        assert await service.aclose() and transport.closes == 1

    exercise(scenario())


@pytest.mark.parametrize("time", [14.999, 15.0, 15.001])
def test_first_valid_event_monotonic_boundary_and_no_partial_flush(time):
    async def scenario():
        clock = ManualClock()
        gate = Gate(data=stream("a@b.test "))
        body = Body([gate])
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        task = asyncio.create_task(anext(session))
        await checked(gate.entered.wait())
        clock.advance(time)
        gate.release.set()
        if time < 15:
            assert text_output([await checked(task)]) == "[REDACTED] "
        else:
            with pytest.raises(StreamError) as caught:
                await checked(task)
            assert caught.value.code is ErrorCode.TIMEOUT
        assert await session.aclose() and body.closed and await service.aclose()

    exercise(scenario())


@pytest.mark.parametrize("chunk", [b":comment\n\n", b"event: delta\ndata: {", b"x"])
def test_frequent_chunks_cannot_renew_first_valid_event_deadline(chunk):
    async def scenario():
        clock = ManualClock()
        gate = Gate(data=chunk)
        body = Body([chunk, gate])
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        task = asyncio.create_task(anext(session))
        await checked(gate.entered.wait())
        clock.advance(14)
        gate.release.set()
        # Next read is held, so the final one-second budget cannot renew to 15.
        next_gate = Gate()
        body.chunks.append(next_gate)
        await checked(next_gate.entered.wait())
        clock.advance(15)
        with pytest.raises(StreamError) as caught:
            await checked(task)
        assert caught.value.code is ErrorCode.TIMEOUT and body.closed
        assert await service.aclose()

    exercise(scenario())


def test_valid_empty_delta_counts_as_first_event_then_read_idle_applies():
    async def scenario():
        clock = ManualClock()
        gate = Gate(data=wire("delta", {"channel": 0, "text": ""}))
        second = Gate()
        body = Body([gate, second])
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        task = asyncio.create_task(anext(session))
        await checked(gate.entered.wait())
        clock.advance(14)
        gate.release.set()
        await checked(second.entered.wait())
        clock.advance(15)
        for _ in range(10):
            await asyncio.sleep(0)
        assert not task.done()  # Valid event was received, no first-output requirement.
        clock.advance(29)
        with pytest.raises(StreamError) as caught:
            await checked(task)
        assert caught.value.code is ErrorCode.TIMEOUT and body.closed
        assert await service.aclose()

    exercise(scenario())


def test_overall_deadline_closes_while_consumer_is_paused():
    async def scenario():
        clock = ManualClock()
        body = Body([wire("delta", {"channel": 0, "text": "safe private@"}), stream("unused")])
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        assert text_output([await anext(session)]) == "safe "
        clock.advance(119.999)
        for _ in range(10):
            await asyncio.sleep(0)
        assert not body.closed and body.reads == 1
        clock.advance(120)
        await until(lambda: session.cleaned)
        assert body.closed and body.reads == 1 and session.processor.redactor.stats.held_chars == 0
        with pytest.raises(StreamError) as caught:
            await anext(session)
        assert caught.value.code is ErrorCode.TIMEOUT and not session.completed
        assert await service.aclose()

    exercise(scenario())


def test_first_event_deadline_closes_even_if_consumer_never_pulls():
    async def scenario():
        clock = ManualClock()
        body = Body([stream("unused")])
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        clock.advance(15)
        await until(lambda: session.cleaned)
        assert body.reads == 0 and body.closed and session.failure is ErrorCode.TIMEOUT
        assert await service.aclose()

    exercise(scenario())


def test_process_global_16_stream_cap_across_services_zero_requests_for_excess():
    async def scenario():
        transports = [Transport(factory=lambda r: Body([stream("safe ")])) for _ in range(2)]
        services = [
            StreamService(UpstreamAdapter(UpstreamSettings("https://example.test"), transport=t))
            for t in transports
        ]
        sessions = []
        try:
            for i in range(16):
                sessions.append(await services[i % 2].stream(REQUEST).__aenter__())
            assert sum(len(t.requests) for t in transports) == 16
            with pytest.raises(CapacityExceeded):
                await services[0].stream(REQUEST).__aenter__()
            assert sum(len(t.requests) for t in transports) == 16
            assert services[0].capacity.active == 16
        finally:
            assert all(await asyncio.gather(*(s.aclose() for s in sessions)))
            assert all(await asyncio.gather(*(s.aclose() for s in services)))
        assert services[0].capacity.active == 0

    exercise(scenario())


def test_concurrent_streams_isolate_raw_candidates_and_credentials():
    async def scenario():
        def factory(request):
            number = int(request.content)
            return Body(
                [
                    wire("delta", {"channel": 0, "text": f"user{number}@"}),
                    wire("delta", {"channel": 0, "text": "example.test "})
                    + wire("done", {"channel": 0})
                    + wire("end", {}),
                ]
            )

        transport = Transport(factory=factory)
        service = make_service(transport)

        async def consume(number):
            async with service.stream(UpstreamRequest(str(number).encode())) as session:
                return [frame async for frame in session]

        results = await asyncio.gather(*(consume(i) for i in range(16)))
        assert all(text_output(frames) == "[REDACTED] " for frames in results)
        assert len(transport.requests) == 16 and service.capacity.active == 0
        assert all(body.closed and body.closes == 1 for body in transport.bodies)
        assert await service.aclose()

    exercise(scenario())


def test_pool_close_grace_and_shutdown_cancellation_are_owned():
    async def scenario():
        clock = ManualClock()
        gate = Gate()
        transport = Transport(close_gate=gate)
        service = make_service(transport, clock)
        closing = asyncio.create_task(service.aclose())
        await checked(gate.entered.wait())
        closing.cancel()
        with pytest.raises(asyncio.CancelledError):
            await closing
        clock.advance(1.001)
        await until(lambda: service._shutdown.done())
        assert service._shutdown.result() is False and service.adapter.quarantined
        assert not service.adapter.closed and transport.closes == 1
        gate.release.set()
        await until(lambda: service.adapter.closed)
        assert await service.aclose() and transport.closes == 1

    exercise(scenario())


def test_long_stream_has_no_producer_queue_or_accumulated_pure_buffers():
    async def scenario():
        body = Body(
            [wire("delta", {"channel": 0, "text": "word "})] * 2000
            + [wire("done", {"channel": 0}) + wire("end", {})]
        )
        service = make_service(Transport(body))
        count = 0
        async with service.stream(REQUEST) as session:
            async for frame in session:
                if output([frame])[0][0] == "delta":
                    count += 1
                    assert body.reads == count
                    assert session.processor.redactor.stats.held_chars == 0
                    assert session.processor.redactor.stats.pending_chars == 0
            assert count == 2000 and session.completed
            assert session.lease.raw_reads == 2001
            assert session.lease.peak_raw_bytes < 4096
        assert await service.aclose()

    exercise(scenario())


def test_cancelling_consumer_paused_with_pending_safe_output_closes_owner():
    async def scenario():
        paused = asyncio.Event()
        hold = asyncio.Event()
        body = Body([wire("delta", {"channel": 0, "text": " " * 600}), stream("unused")])
        service = make_service(Transport(body))
        session = service.stream(REQUEST)

        async def consume():
            async with session:
                await anext(session)
                paused.set()
                await hold.wait()  # Model a blocked downstream transport, no next demand.

        task = asyncio.create_task(consume())
        await checked(paused.wait())
        assert body.reads == 1
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await checked(task)
        assert session.cleaned and not session.completed and body.closed
        assert session.processor.redactor.stats.pending_chars == 0
        assert service.capacity.active == 0 and await service.aclose()

    exercise(scenario())


def test_cancel_and_response_close_share_original_cleanup_deadline():
    async def scenario():
        clock = ManualClock()
        opening = Gate(resistant=True)
        closing = Gate()
        body = Body([], close_gate=closing)
        transport = Transport(body, opening=opening)
        service = make_service(transport, clock)
        session = service.stream(REQUEST)
        task = asyncio.create_task(session.__aenter__())
        await checked(opening.entered.wait())
        task.cancel()
        await checked(opening.cancelled.wait())
        clock.advance(0.75)
        opening.release.set()
        await checked(closing.entered.wait())
        clock.advance(1.001)  # Not 1.75: opening cancellation consumed 750 ms.
        with pytest.raises(asyncio.CancelledError):
            await checked(task)
        assert service.adapter.quarantined and service.active == 1
        closing.release.set()
        await until(lambda: session.cleaned)
        assert await service.aclose()

    exercise(scenario())


def test_cleanup_confirmed_before_grace_is_not_quarantined():
    async def scenario():
        clock = ManualClock()
        gate = Gate()
        body = Body([], close_gate=gate)
        service = make_service(Transport(body), clock)
        session = await service.stream(REQUEST).__aenter__()
        task = asyncio.create_task(session.aclose())
        await checked(gate.entered.wait())
        clock.advance(0.999)
        gate.release.set()
        assert await checked(task) and body.closed and not service.adapter.quarantined
        assert service.capacity.active == 0 and await service.aclose()

    exercise(scenario())


def test_headers_do_not_renew_first_valid_event_budget():
    async def scenario():
        clock = ManualClock()
        opening = Gate()
        reading = Gate(data=stream("safe "))
        body = Body([reading])
        service = make_service(Transport(body, opening=opening), clock)
        task = asyncio.create_task(service.stream(REQUEST).__aenter__())
        await checked(opening.entered.wait())
        clock.advance(10)
        opening.release.set()
        session = await checked(task)
        pulling = asyncio.create_task(anext(session))
        await checked(reading.entered.wait())
        clock.advance(15)
        with pytest.raises(StreamError) as caught:
            await checked(pulling)
        assert caught.value.code is ErrorCode.TIMEOUT and body.closed
        assert await service.aclose()

    exercise(scenario())


def test_shutdown_aborts_paused_stream_without_further_reads():
    async def scenario():
        body = Body([wire("delta", {"channel": 0, "text": "safe private@"}), stream("unused")])
        service = make_service(Transport(body))
        session = await service.stream(REQUEST).__aenter__()
        assert text_output([await anext(session)]) == "safe "
        assert await service.aclose()
        assert body.reads == 1 and session.cleaned and not session.completed
        assert session.processor.redactor.stats.held_chars == 0
        with pytest.raises(StopAsyncIteration):
            await anext(session)
        with pytest.raises(StreamError):
            await service.stream(REQUEST).__aenter__()

    exercise(scenario())


def test_close_exception_is_owned_quarantined_and_no_success_end_is_sent():
    async def scenario():
        body = Body([stream("private@example.test ")], close_error=True)
        service = make_service(Transport(body))
        frames = []
        with pytest.raises(StreamError) as caught:
            async with service.stream(REQUEST) as session:
                async for frame in session:
                    frames.append(frame)
        assert caught.value.code is ErrorCode.UNAVAILABLE
        assert "end" not in [kind for kind, _ in output(frames)]
        assert not session.completed and service.active == 1 and service.adapter.quarantined
        assert not await service.aclose()
        assert session._cleanup_work.done() and not session.cleaned
        # Test-only disposal of failed fake resource; no production recovery/retry API.
        body.close_error = False
        await body.aclose()
        await service.adapter.aclose()

    exercise(scenario())


def test_capacity_rejection_parallel_open_has_no_waiting_queue():
    async def scenario():
        gate = Gate()
        transport = Transport(opening=gate, factory=lambda r: Body([stream("safe ")]))
        service = make_service(transport)
        sessions = [service.stream(REQUEST) for _ in range(17)]
        tasks = [asyncio.create_task(session.__aenter__()) for session in sessions]
        await until(lambda: len(transport.requests) == 16)
        assert tasks[-1].done()
        with pytest.raises(CapacityExceeded):
            await tasks[-1]
        assert service.capacity.active == 16
        gate.release.set()
        await asyncio.gather(*tasks[:-1])
        assert all(await asyncio.gather(*(session.aclose() for session in sessions[:-1])))
        assert await service.aclose() and len(transport.requests) == 16

    exercise(scenario())


def test_repeated_cancel_cannot_discard_request_cleanup_worker():
    async def scenario():
        gate = Gate()
        body = Body([gate])
        service = make_service(Transport(body))
        session = await service.stream(REQUEST).__aenter__()
        pulling = asyncio.create_task(anext(session))
        await checked(gate.entered.wait())
        pulling.cancel()
        pulling.cancel()
        with pytest.raises(asyncio.CancelledError):
            await checked(pulling)
        assert session.cleaned and body.closed and service.active == 0
        assert await service.aclose()

    exercise(scenario())
