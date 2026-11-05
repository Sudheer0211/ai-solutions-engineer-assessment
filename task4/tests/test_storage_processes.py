"""T4-003 S4/S6: actual spawn processes on the same durable SQLite file."""

from uuid import UUID

import pytest
from storage_support import Clock, database, plan

from task4_limiter.storage import SQLiteStore

pytestmark = pytest.mark.task4


def test_barrier_processes_compete_for_final_capacity(state, process_runner):
    store, clock, settings, key = state
    clock.value = 100
    assert store.admit(key, UUID(int=1), plan(24_000, 24_000), reservation_ms=100_000).admitted
    results = process_runner(
        settings.path, settings.identity_secret, key, "admit", range(2, 8), synchronize=True
    )
    assert sum(r[1:] == ("admit", True) for r in results) == 1
    assert sum(r[1:] == ("admit", False) for r in results) == 5
    assert store.usage(key).total_tokens == 50_000
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == 2
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 4
        assert db.execute("SELECT sum(bound_tokens) FROM attempts").fetchone()[0] == 50_000


def test_committed_settlement_and_hold_survive_independent_process_restart(state, process_runner):
    store, _, settings, key = state
    store.close()
    first = process_runner(settings.path, settings.identity_secret, key, "write", [1])
    second = process_runner(settings.path, settings.identity_secret, key, "read", [2])
    assert first == [(1, "write", 1123)] and second == [(2, "read", 1123)]
    with SQLiteStore(settings, clock=Clock(100)) as restarted:
        request = restarted.request(key, UUID(int=1))
        assert request.attempts[0].charged_tokens == 123
        assert request.attempts[1].state == "reserved"


def test_duplicate_request_race_has_one_durable_reservation(state, process_runner):
    store, clock, settings, key = state
    clock.value = 100
    results = process_runner(
        settings.path, settings.identity_secret, key, "duplicate", [2, 3, 4], synchronize=True
    )
    assert sum(r[1:] == ("admit", True) for r in results) == 1
    assert sum(r[1:] == ("error", "duplicate") for r in results) == 2
    assert store.usage(key).total_tokens == 2000
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 2


@pytest.mark.parametrize("mode", ["settle_same", "settle_conflict"])
def test_process_settlement_race_is_idempotent_or_rejects_conflict(state, process_runner, mode):
    store, clock, settings, key = state
    clock.value = 100
    store.admit(key, UUID(int=1), plan(), reservation_ms=100_000)
    store.start_attempt(key, UUID(int=1), 1)
    results = process_runner(
        settings.path, settings.identity_secret, key, mode, [2, 3], synchronize=True
    )
    successes = [r for r in results if r[1] == "settle"]
    assert len(successes) == (2 if mode == "settle_same" else 1)
    if mode == "settle_conflict":
        assert sum(r[1:] == ("error", "conflict") for r in results) == 1
    assert store.usage(key).total_tokens == 1000 + successes[0][2]
    assert store.request(key, UUID(int=1)).attempts[0].charged_tokens == successes[0][2]
