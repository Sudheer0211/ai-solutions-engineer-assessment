"""T4-004 / Q6-Q10: real SQLite + controlled async adapters, no external I/O."""

import asyncio
import gc
import threading
import weakref
from uuid import UUID, uuid4

import pytest
from orchestration_support import FakeProvider, ManualClock, until
from storage_support import plan

from task4_limiter.models import BoundsUnavailable
from task4_limiter.providers import ProviderStatus, TokenUsage
from task4_limiter.service import LLMService, LoopClock, RoutingPolicy
from task4_limiter.storage import StorageError, StorageFailure


def service(store, clock=None, primary=None, backup=None, policy=None):
    primary = primary or FakeProvider()
    backup = backup or FakeProvider("backup", journal=primary.journal)
    result = LLMService(
        store, primary, backup, policy or RoutingPolicy(2000, 10_000), clock=clock or ManualClock()
    )
    return result, primary, backup


def test_primary_success_releases_backup_and_preserves_admission(state):
    store, wall, _, key = state
    wall.value = 123

    async def scenario():
        svc, primary, backup = service(store)
        rid = uuid4()
        out = await svc.generate(key, "hello", request_id=rid)
        assert out.request_id == rid and out.text == "hello" and out.code is None
        assert out.message is None and not out.used_backup
        row = store.request(key, rid)
        assert row.phase == "complete"
        assert [(a.state, a.charged_tokens, a.accounting_ms) for a in row.attempts] == [
            ("settled", 5, 123),
            ("released", 0, 123),
        ]
        assert primary.calls == ["hello"] and backup.calls == []
        assert store.usage(key).total_tokens == 5
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("usage,charge", [(None, 20), (TokenUsage(0, 0), 0), (TokenUsage(4, 3), 7)])
def test_primary_429_exactly_one_backup_after_cleanup(state, usage, charge):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(status=ProviderStatus.RATE_LIMITED, usage=usage)
        svc, primary, backup = service(store, primary=primary)
        rid = uuid4()
        out = await svc.generate(key, "fallback", request_id=rid)
        assert out.code is None and out.used_backup
        assert primary.calls == backup.calls == ["fallback"]
        assert primary.journal == [
            ("primary", "start", "fallback"),
            ("primary", "finish", "fallback"),
            ("primary", "close", "fallback"),
            ("backup", "start", "fallback"),
            ("backup", "finish", "fallback"),
            ("backup", "close", "fallback"),
        ]
        row = store.request(key, rid)
        assert [a.charged_tokens for a in row.attempts] == [charge, 5]
        assert row.phase == "complete" and await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("at,falls_back", [(2999, False), (3000, True), (3001, True)])
def test_primary_monotonic_timeout_boundaries(state, at, falls_back):
    store, _, _, key = state

    async def scenario():
        clock = ManualClock()
        primary = FakeProvider()
        primary.gate = asyncio.Event()
        svc, _, backup = service(store, clock, primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "boundary", request_id=rid))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        clock.advance(at)
        primary.gate.set()
        out = await task
        assert out.code is None and out.used_backup == falls_back
        assert len(backup.calls) == int(falls_back)
        row = store.request(key, rid)
        # At/after deadline content loses, but the completed fake's usage is reliable.
        assert row.attempts[0].charged_tokens == 5
        assert row.attempts[0].source == "known"
        assert primary.prepared[0].closed.is_set()
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("offset,confirmed", [(499, True), (500, False), (501, False)])
def test_cleanup_shared_grace_and_no_concurrent_backup(state, offset, confirmed):
    store, _, _, key = state

    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate, primary.finish = asyncio.Event(), asyncio.Event()
        primary.resistant = True
        svc, _, backup = service(store, clock, primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "slow", request_id=rid))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        clock.advance(3000)
        await primary.prepared[0].cancelled.wait()
        await clock.waiting(3500)
        assert backup.calls == []
        clock.advance(3000 + offset)
        if confirmed:
            primary.finish.set()
        out = await task
        assert len(backup.calls) == int(confirmed)
        if confirmed:
            assert out.code is None and out.used_backup
        else:
            assert out.code == "service_unavailable"
            row = store.request(key, rid)
            assert [a.state for a in row.attempts] == ["started", "reserved"]
            assert store.usage(key).reserved_tokens == 40
            assert svc.pending_cleanup == 1
            assert (await svc.generate(key, "quarantined")).code == "service_unavailable"
            primary.finish.set()
            await until(lambda: svc.pending_cleanup == 0)
        assert await svc.aclose()

    asyncio.run(scenario())


def test_429_resource_close_also_has_one_bounded_grace(state):
    store, _, _, key = state

    async def scenario():
        clock, primary = ManualClock(), FakeProvider(status=ProviderStatus.RATE_LIMITED)
        primary.close_gate = asyncio.Event()
        svc, _, backup = service(store, clock, primary)
        task = asyncio.create_task(svc.generate(key, "close"))
        await until(lambda: bool(primary.calls))
        await clock.waiting(500)
        clock.advance(500)
        assert (await task).code == "service_unavailable" and not backup.calls
        primary.close_gate.set()
        await until(lambda: svc.pending_cleanup == 0)
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "error", [RuntimeError("private diagnostic"), TimeoutError("private timeout")]
)
def test_primary_exceptions_do_not_trigger_fallback_or_leak(state, error, caplog):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider()
        primary.error = error
        svc, _, backup = service(store, primary=primary)
        rid = uuid4()
        out = await svc.generate(key, "failure", request_id=rid)
        assert out.code == "model_unavailable" and out.message == "Model unavailable"
        assert "private" not in repr(out) + caplog.text and not backup.calls
        assert store.usage(key).total_tokens == 20
        assert store.request(key, rid).phase == "complete"
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "status,code",
    [
        (ProviderStatus.RATE_LIMITED, "provider_rate_limited"),
        (ProviderStatus.TRANSPORT_FAILURE, "model_unavailable"),
        (ProviderStatus.TIMEOUT, "model_timeout"),
    ],
)
def test_backup_failure_is_terminal_no_third_attempt(state, status, code):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(status=ProviderStatus.RATE_LIMITED, usage=None)
        backup = FakeProvider("backup", status=status, usage=None)
        svc, _, _ = service(store, primary=primary, backup=backup)
        out = await svc.generate(key, "backup failure")
        assert out.code == code and out.used_backup
        assert primary.calls == backup.calls == ["backup failure"]
        assert store.usage(key).total_tokens == 40
        assert await svc.aclose()

    asyncio.run(scenario())


def test_backup_real_deadline_no_third_attempt(state):
    store, _, _, key = state

    async def scenario():
        clock = ManualClock()
        primary = FakeProvider(status=ProviderStatus.RATE_LIMITED, usage=None)
        backup = FakeProvider("backup")
        backup.gate = asyncio.Event()
        svc, _, _ = service(store, clock, primary, backup)
        task = asyncio.create_task(svc.generate(key, "backup timeout"))
        await until(lambda: bool(backup.calls))
        await clock.waiting(2000)
        clock.advance(2000)
        out = await task
        assert out.code == "model_timeout" and out.used_backup
        assert backup.prepared[0].cancelled.is_set() and backup.prepared[0].closed.is_set()
        assert primary.calls == backup.calls == ["backup timeout"]
        assert store.usage(key).total_tokens == 40
        assert await svc.aclose()

    asyncio.run(scenario())


def test_local_quota_denial_zero_provider_calls(state):
    store, _, _, key = state
    store.admit(key, uuid4(), plan(25_000, 25_000), reservation_ms=100_000)

    async def scenario():
        svc, primary, backup = service(store)
        out = await svc.generate(key, "no quota")
        assert out.code == "tenant_quota_exceeded" and not primary.calls and not backup.calls
        assert store.usage(key).total_tokens == 50_000
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("which", ["missing", "wrong_model", "wrong_counter", "backup_missing"])
def test_unreliable_bounds_fail_before_reservation_or_dispatch(state, which):
    store, _, _, key = state

    async def scenario():
        svc, primary, backup = service(store)
        if which == "missing":
            primary.prepare_error = BoundsUnavailable()
        elif which == "backup_missing":
            backup.prepare_error = BoundsUnavailable()
        else:
            setattr(primary, which, True)
        out = await svc.generate(key, "bounds")
        assert out.code == "service_unavailable" and not primary.calls and not backup.calls
        assert store.usage(key).total_tokens == 0
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("usage", [TokenUsage(21, 0), TokenUsage(0, 11)])
def test_adapter_bound_breach_fails_closed(state, usage):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(usage=usage)
        svc, _, backup = service(store, primary=primary)
        rid = uuid4()
        out = await svc.generate(key, "breach", request_id=rid)
        assert out.code == "service_unavailable" and not backup.calls
        row = store.request(key, rid)
        if usage.total_tokens > 20:
            assert row.blocked and row.attempts[0].state == "started"
            with pytest.raises(StorageError) as error:
                store.admit(key, uuid4(), plan(1, 1), reservation_ms=1000)
            assert error.value.kind == StorageFailure.BLOCKED
        else:
            assert row.attempts[0].charged_tokens == 20
            assert row.attempts[0].source == "unknown"
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("kind", ["cancel", "close_failure", "invalid_result", "early_timeout"])
def test_nonfallback_primary_failures(state, kind):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider()
        if kind == "cancel":
            primary.error = asyncio.CancelledError()
        elif kind == "close_failure":
            primary.close_error = True
        elif kind == "invalid_result":
            primary.raw_result = {"private": "unsafe provider body"}
        else:
            primary.status = ProviderStatus.TIMEOUT
        svc, _, backup = service(store, primary=primary)
        out = await svc.generate(key, "bad")
        assert out.code in ("model_unavailable", "service_unavailable", "model_timeout")
        assert not backup.calls and out.text is None
        assert (await svc.aclose()) == (kind != "close_failure")

    asyncio.run(scenario())


def test_concurrent_admission_shared_budget_and_tenant_isolation(state):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(input_bound=2500, output_cap=2500)
        primary.gate = asyncio.Event()
        backup = FakeProvider("backup", input_bound=2500, output_cap=2500)
        svc, _, _ = service(store, primary=primary, backup=backup)
        tasks = [asyncio.create_task(svc.generate(key, f"same-{n}")) for n in range(6)]
        await until(lambda: len(primary.calls) == 5 and any(t.done() for t in tasks))
        assert store.usage(key).total_tokens == 50_000
        other = asyncio.create_task(svc.generate(b"separate-fixture-tenant", "other"))
        await until(lambda: "other" in primary.calls)
        assert store.usage(b"separate-fixture-tenant").total_tokens == 10_000
        primary.gate.set()
        results = await asyncio.gather(*tasks, other)
        assert sum(r.code == "tenant_quota_exceeded" for r in results) == 1
        assert sum(r.code is None for r in results) == 6
        assert store.usage(key).total_tokens == 25
        assert store.usage(b"separate-fixture-tenant").total_tokens == 5
        assert not backup.calls and await svc.aclose()

    asyncio.run(scenario())


def test_duplicate_request_has_one_dispatch_and_one_settlement(state):
    store, _, _, key = state

    async def scenario():
        svc, primary, backup = service(store)
        rid = uuid4()
        results = await asyncio.gather(
            *(svc.generate(key, "duplicate", request_id=rid) for _ in range(4))
        )
        assert sum(r.code is None for r in results) == 1
        assert primary.calls == ["duplicate"] and not backup.calls
        assert store.usage(key).total_tokens == 5
        # Identical storage settlement remains idempotent, no service replay.
        store.settle(key, rid, 1, actual_tokens=5)
        assert (await svc.generate(key, "again", request_id=rid)).code == "service_unavailable"
        assert store.usage(key).total_tokens == 5 and len(primary.calls) == 1
        assert await svc.aclose()

    asyncio.run(scenario())


def test_client_cancellation_cleans_and_never_falls_back(state):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider()
        primary.gate = asyncio.Event()
        svc, _, backup = service(store, primary=primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "cancel", request_id=rid))
        await until(lambda: bool(primary.calls))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await svc.drain()
        assert primary.prepared[0].closed.is_set() and not backup.calls
        assert store.request(key, rid).phase == "complete"
        assert store.usage(key).total_tokens == 20
        assert await svc.aclose()

    asyncio.run(scenario())


class StoreProbe:
    def __init__(self, store, method, ordinal=None, *, after=False):
        self.store, self.method, self.ordinal, self.after = store, method, ordinal, after
        self.calls = []
        self.entered = self.release = None
        self.loop = None

    def __getattr__(self, name):
        target = getattr(self.store, name)

        def invoke(*args, **kwargs):
            self.calls.append((name, threading.get_ident()))
            selected = name == self.method and (self.ordinal is None or args[2] == self.ordinal)
            if selected and self.after:
                result = target(*args, **kwargs)
            if selected and self.entered is not None:
                self.loop.call_soon_threadsafe(self.entered.set)
                assert self.release.wait(10), "test worker synchronization failed"
                if not self.after:
                    result = target(*args, **kwargs)
                return result
            if selected:
                raise StorageError(StorageFailure.UNAVAILABLE)
            return target(*args, **kwargs)

        return invoke


@pytest.mark.parametrize(
    "method,ordinal,after",
    [
        ("admit", None, False),
        ("admit", None, True),
        ("start_attempt", 1, False),
        ("start_attempt", 1, True),
        ("settle", 1, False),
        ("settle", 1, True),
        ("release_unused", 2, False),
        ("start_attempt", 2, False),
        ("start_attempt", 2, True),
        ("settle", 2, False),
    ],
)
def test_storage_failure_no_unauthorized_send_or_replay(state, method, ordinal, after):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(
            status=ProviderStatus.RATE_LIMITED
            if ordinal == 2 and method != "release_unused"
            else ProviderStatus.SUCCESS
        )
        probe = StoreProbe(store, method, ordinal, after=after)
        svc, _, backup = service(probe, primary=primary)
        out = await svc.generate(key, "storage failure")
        assert out.code == "service_unavailable"
        if method in ("admit", "start_attempt"):
            assert len(primary.calls) == int(ordinal == 2)
            assert not backup.calls
        assert all(thread != threading.get_ident() for _, thread in probe.calls)
        assert sum(name == method for name, _ in probe.calls) <= (2 if method == "settle" else 2)
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "method,ordinal,after",
    [
        ("admit", None, False),
        ("admit", None, True),
        ("start_attempt", 1, False),
        ("start_attempt", 1, True),
        ("settle", 1, False),
        ("settle", 1, True),
        ("start_attempt", 2, False),
        ("start_attempt", 2, True),
    ],
)
def test_cancelled_db_worker_completion_discovered(state, method, ordinal, after):
    store, _, _, key = state

    async def scenario():
        probe = StoreProbe(store, method, ordinal, after=after)
        probe.entered, probe.release = asyncio.Event(), threading.Event()
        probe.loop = asyncio.get_running_loop()
        primary = FakeProvider(
            status=ProviderStatus.RATE_LIMITED if ordinal == 2 else ProviderStatus.SUCCESS
        )
        svc, _, backup = service(probe, primary=primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "db cancel", request_id=rid))
        await probe.entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert not backup.calls
        probe.release.set()
        await svc.drain()
        assert not backup.calls
        row = store.request(key, rid)
        assert row.phase == "complete"
        if method in ("admit", "start_attempt"):
            assert len(primary.calls) == int(ordinal == 2)
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "key,text,rid,code",
    [
        (None, "x", None, "invalid_credentials"),
        (b"", "x", None, "invalid_credentials"),
        (b"x", "", None, "invalid_request"),
        (b"x", 123, None, "invalid_request"),
        (b"x", "x", "caller-id", "invalid_request"),
    ],
)
def test_input_validation_no_provider_calls(state, key, text, rid, code):
    async def scenario():
        svc, primary, backup = service(state[0])
        out = await svc.generate(key, text, request_id=rid)
        assert out.code == code and isinstance(out.request_id, UUID)
        assert not primary.prepared and not backup.prepared
        assert await svc.aclose()

    asyncio.run(scenario())


def test_real_loop_clock_and_shutdown(state):
    async def scenario():
        clock = LoopClock()
        now = clock.now_ms()
        await clock.wait_until(now)
        assert clock.now_ms() >= now
        svc, primary, _ = service(state[0], clock)
        assert (await svc.generate(state[3], "loop")).code is None
        assert await svc.aclose()
        assert (await svc.generate(state[3], "closed")).code == "service_unavailable"
        assert primary.calls == ["loop"]

    asyncio.run(scenario())


def test_timeout_unknown_usage_is_full_primary_charge(state):
    store, wall, _, key = state
    wall.value = 50

    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate = asyncio.Event()
        svc, _, backup = service(store, clock, primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "unknown", request_id=rid))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        # UTC does not drive the provider timeout.
        wall.value = 51
        clock.advance(2999)
        assert not task.done() and not backup.calls
        clock.advance(3000)
        out = await task
        assert out.code is None and out.used_backup
        row = store.request(key, rid)
        assert [(a.charged_tokens, a.source, a.accounting_ms) for a in row.attempts] == [
            (20, "unknown", 50),
            (5, "known", 50),
        ]
        assert primary.prepared[0].cancelled.is_set()
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("close_at,success", [(3499, True), (3500, False)])
def test_cancellation_and_close_share_one_grace_budget(state, close_at, success):
    store, _, _, key = state

    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate, primary.finish, primary.close_gate = (
            asyncio.Event(),
            asyncio.Event(),
            asyncio.Event(),
        )
        primary.resistant = True
        svc, _, backup = service(store, clock, primary)
        task = asyncio.create_task(svc.generate(key, "shared grace"))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        clock.advance(3000)
        await primary.prepared[0].cancelled.wait()
        await clock.waiting(3500)
        clock.advance(3400)
        primary.finish.set()
        await primary.prepared[0].finished.wait()
        clock.advance(close_at)
        primary.close_gate.set()
        out = await task
        assert (out.code is None) == success
        assert len(backup.calls) == int(success)
        await until(lambda: svc.pending_cleanup == 0)
        assert await svc.aclose()

    asyncio.run(scenario())


def test_shutdown_reports_unconfirmed_cleanup_without_unbounded_wait(state):
    store, _, _, key = state

    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate, primary.finish = asyncio.Event(), asyncio.Event()
        primary.resistant = True
        svc, _, backup = service(store, clock, primary)
        task = asyncio.create_task(svc.generate(key, "shutdown"))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        clock.advance(3000)
        await clock.waiting(3500)
        clock.advance(3500)
        assert (await task).code == "service_unavailable"
        closing = asyncio.create_task(svc.aclose())
        await clock.waiting(4000)
        clock.advance(4000)
        assert not await closing and not backup.calls
        primary.finish.set()
        await until(lambda: svc.pending_cleanup == 0)
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("ordinal", [1, 2])
def test_durable_intent_visible_before_execution_and_no_transaction_held(state, ordinal):
    store, _, _, key = state

    async def scenario():
        rid = uuid4()

        class InspectProvider(FakeProvider):
            def prepare(self, text):
                attempt = super().prepare(text)
                original = attempt.execute

                async def execute():
                    # A separate connection acquires BEGIN IMMEDIATE via request():
                    # both durable visibility and absence of a held writer are checked.
                    row = await asyncio.to_thread(store.request, key, rid)
                    assert row.attempts[ordinal - 1].state == "started"
                    if ordinal == 2:
                        assert row.attempts[0].state == "settled"
                    return await original()

                attempt.execute = execute
                return attempt

        primary = (
            InspectProvider() if ordinal == 1 else FakeProvider(status=ProviderStatus.RATE_LIMITED)
        )
        backup = InspectProvider("backup") if ordinal == 2 else FakeProvider("backup")
        svc, _, _ = service(store, primary=primary, backup=backup)
        out = await svc.generate(key, "intent", request_id=rid)
        assert out.code is None and out.used_backup == (ordinal == 2)
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "method,ordinal", [("admit", None), ("start_attempt", 1), ("start_attempt", 2)]
)
def test_db_delay_exhausts_overall_send_budget_without_dispatch(state, method, ordinal):
    store, _, _, key = state

    async def scenario():
        clock = ManualClock()
        probe = StoreProbe(store, method, ordinal, after=True)
        probe.entered, probe.release = asyncio.Event(), threading.Event()
        probe.loop = asyncio.get_running_loop()
        primary = FakeProvider(
            status=ProviderStatus.RATE_LIMITED if ordinal == 2 else ProviderStatus.SUCCESS
        )
        svc, _, backup = service(probe, clock, primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "slow db", request_id=rid))
        await probe.entered.wait()
        clock.advance(8000)
        probe.release.set()
        out = await task
        assert out.code == "service_unavailable"
        assert len(primary.calls) == int(ordinal == 2) and not backup.calls
        assert store.request(key, rid).phase == "complete"
        assert await svc.aclose()

    asyncio.run(scenario())


def test_expired_sqlite_reservation_prevents_dispatch_and_keeps_deadline_charges(state):
    store, wall, _, key = state

    async def scenario():
        probe = StoreProbe(store, "admit", after=True)
        probe.entered, probe.release = asyncio.Event(), threading.Event()
        probe.loop = asyncio.get_running_loop()
        svc, primary, backup = service(probe)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "expired", request_id=rid))
        await probe.entered.wait()
        wall.value = 10_000
        probe.release.set()
        out = await task
        assert out.code == "service_unavailable" and not primary.calls and not backup.calls
        row = store.request(key, rid)
        assert row.phase == "abandoned"
        assert [(a.charged_tokens, a.accounting_ms) for a in row.attempts] == [
            (20, 10_000),
            (20, 10_000),
        ]
        assert await svc.aclose()

    asyncio.run(scenario())


def test_repeated_uuid_across_tenants_does_not_mix_results_or_usage(state):
    store, _, _, _ = state

    async def scenario():
        primary = FakeProvider(status=ProviderStatus.RATE_LIMITED, usage=None)
        svc, _, backup = service(store, primary=primary)
        rid = uuid4()
        keys = [f"fixture-tenant-{n}".encode() for n in range(8)]
        results = await asyncio.gather(
            *(svc.generate(key, f"content-{n}", request_id=rid) for n, key in enumerate(keys))
        )
        assert [r.text for r in results] == [f"content-{n}" for n in range(8)]
        assert all(r.request_id == rid and r.used_backup for r in results)
        assert len(primary.calls) == len(backup.calls) == 8
        assert all(store.usage(key).total_tokens == 25 for key in keys)
        assert await svc.aclose()

    asyncio.run(scenario())


def test_client_cancel_during_resistant_primary_retains_holds_and_starts_no_backup(state):
    store, _, _, key = state

    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate, primary.finish = asyncio.Event(), asyncio.Event()
        primary.resistant = True
        svc, _, backup = service(store, clock, primary)
        rid = uuid4()
        task = asyncio.create_task(svc.generate(key, "client gone", request_id=rid))
        await until(lambda: bool(primary.calls))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await primary.prepared[0].cancelled.wait()
        await clock.waiting(500)
        clock.advance(500)
        await svc.drain()
        assert not backup.calls
        assert store.usage(key).reserved_tokens == 40
        primary.finish.set()
        await until(lambda: svc.pending_cleanup == 0)
        assert store.request(key, rid).attempts[0].state == "started"
        assert await svc.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize("finish_at,backup_runs", [(3499, True), (3500, False)])
def test_late_timeout_observation_does_not_renew_cleanup_budget(state, finish_at, backup_runs):
    async def scenario():
        clock, primary = ManualClock(), FakeProvider()
        primary.gate, primary.finish = asyncio.Event(), asyncio.Event()
        primary.resistant = True
        svc, _, backup = service(state[0], clock, primary)
        task = asyncio.create_task(svc.generate(state[3], "late timeout observation"))
        await until(lambda: bool(primary.calls))
        await clock.waiting(3000)
        clock.advance(3400)
        await primary.prepared[0].cancelled.wait()
        await clock.waiting(3500)  # Not a new 3900 ms grace deadline.
        clock.advance(finish_at)
        primary.finish.set()
        out = await task
        assert (out.code is None) == backup_runs
        assert len(backup.calls) == int(backup_runs)
        await until(lambda: svc.pending_cleanup == 0)
        assert await svc.aclose()

    asyncio.run(scenario())


def test_client_cancel_backup_has_no_third_attempt_and_unknown_backup_charge(state):
    store, _, _, key = state

    async def scenario():
        primary = FakeProvider(status=ProviderStatus.RATE_LIMITED, usage=None)
        backup = FakeProvider("backup")
        backup.gate = asyncio.Event()
        svc, _, _ = service(store, primary=primary, backup=backup)
        task = asyncio.create_task(svc.generate(key, "cancel backup"))
        await until(lambda: bool(backup.calls))
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        await svc.drain()
        assert primary.calls == backup.calls == ["cancel backup"]
        assert backup.prepared[0].closed.is_set()
        assert store.usage(key).total_tokens == 40
        assert await svc.aclose()

    asyncio.run(scenario())


def test_independent_service_owners_share_sqlite_quota_without_shared_python_lock(state):
    store, _, _, key = state

    async def scenario():
        primaries = [FakeProvider(input_bound=7500, output_cap=7500) for _ in range(2)]
        for primary in primaries:
            primary.gate = asyncio.Event()
        services = [
            service(
                store,
                primary=primary,
                backup=FakeProvider("backup", input_bound=7500, output_cap=7500),
            )[0]
            for primary in primaries
        ]
        tasks = [
            asyncio.create_task(svc.generate(key, f"owner-{n}")) for n, svc in enumerate(services)
        ]
        await until(
            lambda: any(t.done() for t in tasks) and sum(len(p.calls) for p in primaries) == 1
        )
        assert store.usage(key).total_tokens == 30_000
        for primary in primaries:
            primary.gate.set()
        outcomes = await asyncio.gather(*tasks)
        assert sorted(out.code or "success" for out in outcomes) == [
            "success",
            "tenant_quota_exceeded",
        ]
        assert store.usage(key).total_tokens == 5
        assert all(await asyncio.gather(*(svc.aclose() for svc in services)))

    asyncio.run(scenario())


def test_preparation_cancellation_does_not_admit_or_dispatch(state):
    store, _, _, key = state

    async def scenario():
        entered, release = asyncio.Event(), threading.Event()
        loop = asyncio.get_running_loop()

        class BlockingCounter(FakeProvider):
            def prepare(self, text):
                loop.call_soon_threadsafe(entered.set)
                assert release.wait(10)
                return super().prepare(text)

        svc, primary, backup = service(store, primary=BlockingCounter())
        task = asyncio.create_task(svc.generate(key, "prepare cancelled"))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        release.set()
        await svc.drain()
        assert not primary.calls and not backup.calls
        assert store.usage(key).total_tokens == 0 and await svc.aclose()

    asyncio.run(scenario())


def test_failed_close_retains_resource_handle_and_reports_unclean_shutdown(state):
    async def scenario():
        class NonRetainingAdapter(FakeProvider):
            def prepare(self, text):
                attempt = super().prepare(text)
                self.reference = weakref.ref(attempt)
                self.prepared.clear()
                return attempt

        primary = NonRetainingAdapter()
        primary.close_error = True
        svc, _, backup = service(state[0], primary=primary)
        out = await svc.generate(state[3], "failed resource close")
        assert out.code == "service_unavailable" and not backup.calls
        await svc.drain()
        gc.collect()
        assert primary.reference() is not None
        assert not await svc.aclose()
        assert not await svc.aclose()
        assert state[0].usage(state[3]).reserved_tokens == 40

    asyncio.run(scenario())
