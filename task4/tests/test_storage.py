"""T4-003 S1-S6: actual on-disk SQLite transactions and conservative accounting."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import UUID

import pytest
from storage_support import Clock, database, plan

from task4_limiter import storage
from task4_limiter.models import MAX_INTEGER, AccountingValidationError, BoundsUnavailable
from task4_limiter.storage import SQLiteStore, StorageError, StorageFailure, StorageSettings

pytestmark = pytest.mark.task4
RID = UUID(int=1)


def failure(kind, operation):
    with pytest.raises(StorageError) as caught:
        operation()
    assert caught.value.kind is kind
    assert str(caught.value) == "Storage operation failed"


def paid(store, key, rid, primary, backup):
    assert store.admit(key, rid, plan(primary, backup), reservation_ms=1_000_000).admitted
    store.start_attempt(key, rid, 1)
    store.settle(key, rid, 1, actual_tokens=primary)
    store.start_attempt(key, rid, 2)
    store.settle(key, rid, 2, actual_tokens=backup)


@pytest.mark.parametrize("demand,allowed", [(999, True), (1000, True), (1001, False)])
def test_atomic_49999_50000_50001_boundary(state, demand, allowed):
    store, clock, settings, key = state
    paid(store, key, RID, 24_000, 24_000)
    assert store.admit(key, UUID(int=2), plan(1000, demand), reservation_ms=100).admitted is allowed
    assert store.usage(key).total_tokens == (49_000 + demand if allowed else 48_000)
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == (2 if allowed else 1)
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == (4 if allowed else 2)


@pytest.mark.parametrize(
    "now,expected",
    [
        (59_999, 48_000),
        (60_000, 41_000),
        (60_001, 41_000),
        (70_000, 30_000),
        (90_000, 17_000),
        (119_999, 0),
    ],
)
def test_real_sqlite_weighted_window_and_original_settlement_timestamps(state, now, expected):
    store, clock, _, key = state
    for i, (timestamp, tokens) in enumerate(
        [(0, 7000), (10_000, 11_000), (30_000, 13_000), (59_999, 17_000)], 1
    ):
        clock.value = timestamp
        paid(store, key, UUID(int=i), tokens - 1, 1)
    clock.value = now
    assert store.usage(key).total_tokens == expected
    assert store.request(key, RID).attempts[0].accounting_ms == 0


def test_settlement_releases_only_proven_unused_capacity_and_is_idempotent(state):
    store, clock, _, key = state
    store.admit(key, RID, plan(), reservation_ms=10_000)
    store.start_attempt(key, RID, 1)
    failure(StorageFailure.CONFLICT, lambda: store.release_unused(key, RID, 1))
    clock.value = 500
    store.settle(key, RID, 1, actual_tokens=123)
    store.settle(key, RID, 1, actual_tokens=123)
    assert store.usage(key).total_tokens == 1123
    failure(StorageFailure.CONFLICT, lambda: store.settle(key, RID, 1, actual_tokens=124))
    failure(StorageFailure.CONFLICT, lambda: store.settle(key, RID, 1, actual_tokens=None))
    store.release_unused(key, RID, 2)
    store.release_unused(key, RID, 2)
    assert store.usage(key).total_tokens == 123
    record = store.request(key, RID)
    assert record.phase == "complete" and all(r.accounting_ms == 0 for r in record.attempts)


def test_unknown_usage_is_full_bound_and_backup_is_sequential(state):
    store, _, _, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    failure(StorageFailure.CONFLICT, lambda: store.start_attempt(key, RID, 2))
    failure(StorageFailure.CONFLICT, lambda: store.settle(key, RID, 1, actual_tokens=0))
    store.start_attempt(key, RID, 1)
    failure(StorageFailure.CONFLICT, lambda: store.start_attempt(key, RID, 1))
    failure(StorageFailure.CONFLICT, lambda: store.start_attempt(key, RID, 2))
    store.settle(key, RID, 1, actual_tokens=None)
    store.settle(key, RID, 1, actual_tokens=None)
    store.start_attempt(key, RID, 2)
    store.settle(key, RID, 2, actual_tokens=0)
    assert store.usage(key).total_tokens == 1000
    assert store.request(key, RID).attempts[0].source == "unknown"


def test_released_backup_cannot_be_dispatched_by_stale_primary_owner(state):
    store, _, _, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    store.release_unused(key, RID, 2)
    failure(StorageFailure.CONFLICT, lambda: store.start_attempt(key, RID, 1))
    store.release_unused(key, RID, 1)
    assert store.usage(key).total_tokens == 0


def test_duplicate_ids_are_tenant_scoped_and_not_reusable_after_completion(state):
    store, _, _, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    failure(StorageFailure.DUPLICATE, lambda: store.admit(key, RID, plan(), reservation_ms=1000))
    other = b"different-synthetic-tenant"
    assert store.admit(other, RID, plan(24_000, 24_000), reservation_ms=1000).admitted
    assert store.usage(key).total_tokens == 2000
    assert store.usage(other).total_tokens == 48_000
    failure(StorageFailure.CONFLICT, lambda: store.request(b"unknown", RID))
    store.release_unused(key, RID, 1)
    store.release_unused(key, RID, 2)
    failure(StorageFailure.DUPLICATE, lambda: store.admit(key, RID, plan(), reservation_ms=1000))


def test_holds_survive_window_and_recovery_is_full_bound_once_at_deadline(state):
    store, clock, _, key = state
    store.admit(key, RID, plan(), reservation_ms=100_000)
    store.start_attempt(key, RID, 1)
    clock.value = 60_000
    assert store.usage(key).reserved_tokens == 2000
    clock.value = 100_000
    assert store.recover(key) == 1
    assert store.recover(key) == 0
    record = store.request(key, RID)
    assert record.phase == "abandoned"
    assert all(
        a.state == "recovered" and a.charged_tokens == 1000 and a.accounting_ms == 100_000
        for a in record.attempts
    )
    failure(StorageFailure.CONFLICT, lambda: store.start_attempt(key, RID, 2))
    failure(StorageFailure.CONFLICT, lambda: store.settle(key, RID, 1, actual_tokens=0))
    failure(StorageFailure.CONFLICT, lambda: store.release_unused(key, RID, 2))
    clock.value = 159_999
    assert store.usage(key).total_tokens == 2000
    clock.value = 160_000
    assert store.usage(key).total_tokens == 0


def test_partial_settlement_recovery_does_not_recharge_known_usage(state):
    store, clock, _, key = state
    store.admit(key, RID, plan(), reservation_ms=100_000)
    store.start_attempt(key, RID, 1)
    store.settle(key, RID, 1, actual_tokens=123)
    clock.value = 100_000
    assert store.usage(key).total_tokens == 1000
    record = store.request(key, RID)
    assert record.attempts[0].accounting_ms == 0
    assert record.attempts[1].accounting_ms == 100_000


def test_reopen_keeps_holds_identity_and_clock_and_never_clears_live_owners(state):
    store, clock, settings, key = state
    store.admit(key, RID, plan(), reservation_ms=100_000)
    clock.value = 60_001
    assert store.usage(key).total_tokens == 2000
    with SQLiteStore(settings, clock=Clock(60_001)) as second:
        assert second.usage(key).reserved_tokens == 2000
    store.close()
    with SQLiteStore(settings, clock=Clock(60_001)) as reopened:
        assert reopened.usage(key).reserved_tokens == 2000
        failure(
            StorageFailure.CLOCK_REGRESSION,
            lambda: SQLiteStore(settings, clock=Clock(60_000)).usage(key),
        )
    failure(
        StorageFailure.CONFIGURATION,
        lambda: SQLiteStore(replace(settings, identity_secret=b"x" * 32), clock=clock),
    )
    failure(StorageFailure.UNAVAILABLE, lambda: store.usage(key))


def test_identity_checked_every_transaction_and_unrelated_databases_not_overwritten(state):
    store, _, settings, key = state
    with database(settings.path) as db:
        db.execute("UPDATE store_meta SET identity_verifier=?", (b"x" * 32,))
    failure(StorageFailure.CONFIGURATION, lambda: store.usage(key))
    unrelated = settings.path.with_name("unrelated.sqlite3")
    with database(unrelated) as db:
        db.execute("CREATE TABLE unrelated(data TEXT)")
    failure(
        StorageFailure.CONFIGURATION,
        lambda: SQLiteStore(replace(settings, path=unrelated), clock=Clock()),
    )
    with database(unrelated) as db:
        assert db.execute("SELECT name FROM sqlite_schema WHERE type='table'").fetchall() == [
            ("unrelated",)
        ]


def test_wal_full_busy_policy_indexes_constraints_and_no_plaintext_keys(state):
    store, _, settings, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    db = store._connect()
    try:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert db.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA busy_timeout").fetchone()[0] == 1000
        assert len(db.execute("SELECT name FROM sqlite_schema WHERE type='index'").fetchall()) >= 5
        tenant = db.execute("SELECT tenant FROM requests").fetchone()[0]
        assert len(tenant) == 64 and key.hex() != tenant
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE attempts SET state='settled'")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE attempts SET ordinal=3")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE attempts SET bound_tokens=1.5")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE attempts SET tenant=?", ("0" * 64,))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO attempts SELECT * FROM attempts")
    finally:
        db.close()
    store.close()
    for path in settings.path.parent.glob("usage.sqlite3*"):
        assert key not in path.read_bytes() and settings.identity_secret not in path.read_bytes()


def test_failed_second_insert_rolls_back_request_first_hold_and_watermark(state):
    store, clock, settings, key = state
    with database(settings.path) as db:
        db.execute(
            "CREATE TRIGGER fail_backup BEFORE INSERT ON attempts WHEN NEW.ordinal=2 "
            "BEGIN SELECT RAISE(ABORT,'synthetic-private-diagnostic'); END"
        )
    clock.value = 100
    failure(StorageFailure.UNAVAILABLE, lambda: store.admit(key, RID, plan(), reservation_ms=1000))
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 0
        assert db.execute("SELECT last_ms FROM store_meta").fetchone()[0] == 0
        db.execute("DROP TRIGGER fail_backup")
    assert store.admit(key, RID, plan(), reservation_ms=1000).admitted


def test_denied_commit_cannot_return_success_and_rolls_back(state, monkeypatch):
    store, _, settings, key = state
    original = store._connect

    def connect():
        db = original()
        db.set_authorizer(
            lambda action, arg, *rest: (
                sqlite3.SQLITE_DENY
                if action == sqlite3.SQLITE_TRANSACTION and arg == "COMMIT"
                else sqlite3.SQLITE_OK
            )
        )
        return db

    monkeypatch.setattr(store, "_connect", connect)
    failure(StorageFailure.UNAVAILABLE, lambda: store.admit(key, RID, plan(), reservation_ms=1000))
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM attempts").fetchone()[0] == 0


def test_unavailable_bounds_roll_back_before_any_reservation(state):
    store, _, settings, key = state
    with pytest.raises(BoundsUnavailable):
        store.admit(key, RID, None, reservation_ms=1000)
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0


def test_pure_decision_and_clock_execute_inside_the_writer_transaction(state, monkeypatch):
    store, clock, settings, key = state
    original = storage.assess_admission
    observations = []

    def check_lock():
        with database(settings.path, timeout=0, autocommit=True) as observer:
            with pytest.raises(sqlite3.OperationalError) as caught:
                observer.execute("BEGIN IMMEDIATE")
            assert caught.value.sqlite_errorcode == sqlite3.SQLITE_BUSY
            assert observer.execute("SELECT count(*) FROM requests").fetchone()[0] == 0

    class CheckingClock:
        def now_ms(self):
            check_lock()
            observations.append("clock")
            return 100

    def inspect(*args, **kwargs):
        check_lock()
        observations.append("pure_decision")
        return original(*args, **kwargs)

    store._clock = CheckingClock()
    monkeypatch.setattr(storage, "assess_admission", inspect)
    assert store.admit(key, RID, plan(), reservation_ms=1000).admitted
    assert observations == ["clock", "pure_decision"]
    with database(settings.path) as observer:
        assert observer.execute("SELECT count(*) FROM requests").fetchone()[0] == 1
        assert observer.execute("SELECT count(*) FROM attempts").fetchone()[0] == 2


def test_failed_settlement_preserves_started_hold_and_can_be_retried_idempotently(state):
    store, _, settings, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    store.start_attempt(key, RID, 1)
    with database(settings.path) as db:
        db.execute(
            "CREATE TRIGGER fail_settlement BEFORE UPDATE ON attempts "
            "WHEN NEW.state='settled' BEGIN SELECT RAISE(ABORT,'fixture'); END"
        )
    failure(StorageFailure.UNAVAILABLE, lambda: store.settle(key, RID, 1, actual_tokens=123))
    assert store.usage(key).reserved_tokens == 2000
    assert store.request(key, RID).attempts[0].state == "started"
    with database(settings.path) as db:
        db.execute("DROP TRIGGER fail_settlement")
    store.settle(key, RID, 1, actual_tokens=123)
    store.settle(key, RID, 1, actual_tokens=123)
    assert store.usage(key).total_tokens == 1123


def test_late_known_settlement_keeps_admission_time_after_hold_survives_window(state):
    store, clock, _, key = state
    store.admit(key, RID, plan(), reservation_ms=100_000)
    store.start_attempt(key, RID, 1)
    clock.value = 60_001
    assert store.usage(key).reserved_tokens == 2000
    store.settle(key, RID, 1, actual_tokens=123)
    store.release_unused(key, RID, 2)
    assert store.usage(key).total_tokens == 0
    assert store.request(key, RID).attempts[0].accounting_ms == 0


def test_missing_database_is_not_silently_recreated_by_an_existing_store(state):
    store, _, settings, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    settings.path.rename(settings.path.with_name("retained.sqlite3"))
    failure(StorageFailure.UNAVAILABLE, lambda: store.usage(key))
    assert not settings.path.exists()


def test_busy_timeout_is_controlled_without_sleep_assertions(state):
    store, _, settings, key = state
    with SQLiteStore(replace(settings, busy_timeout_ms=20), clock=Clock()) as impatient:
        with database(settings.path, autocommit=True) as lock:
            lock.execute("BEGIN IMMEDIATE")
            failure(
                StorageFailure.BUSY, lambda: impatient.admit(key, RID, plan(), reservation_ms=1000)
            )
            lock.execute("ROLLBACK")
        assert impatient.admit(key, RID, plan(), reservation_ms=1000).admitted


def test_bound_breach_is_durable_block_not_silent_refund(state):
    store, clock, settings, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    store.start_attempt(key, RID, 1)
    failure(StorageFailure.BOUND_EXCEEDED, lambda: store.settle(key, RID, 1, actual_tokens=1001))
    assert store.request(key, RID).blocked
    assert store.usage(key).total_tokens == 2000
    with SQLiteStore(settings, clock=clock) as restarted:
        failure(
            StorageFailure.BLOCKED,
            lambda: restarted.admit(key, UUID(int=2), plan(), reservation_ms=1000),
        )


def test_threads_share_only_sqlite_atomicity_not_a_python_lock(state):
    store, clock, _, key = state
    store.admit(key, RID, plan(24_000, 24_000), reservation_ms=100_000)
    barrier = Barrier(5, timeout=10)

    def enter(i):
        barrier.wait()
        return store.admit(key, UUID(int=i), plan(), reservation_ms=100_000).admitted

    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(enter, range(2, 7)))
    assert results.count(True) == 1 and results.count(False) == 4
    assert store.usage(key).total_tokens == 50_000


@pytest.mark.parametrize("reservation", [0, -1, True, 1.5, None, MAX_INTEGER])
def test_invalid_deadline_has_no_durable_admission(state, reservation):
    store, clock, settings, key = state
    clock.value = 1
    with pytest.raises(AccountingValidationError):
        store.admit(key, RID, plan(), reservation_ms=reservation)
    with database(settings.path) as db:
        assert db.execute("SELECT count(*) FROM requests").fetchone()[0] == 0


@pytest.mark.parametrize("value", [-1, True, 1.5, "1"])
def test_invalid_settlement_does_not_change_hold(state, value):
    store, _, _, key = state
    store.admit(key, RID, plan(), reservation_ms=1000)
    store.start_attempt(key, RID, 1)
    with pytest.raises(AccountingValidationError):
        store.settle(key, RID, 1, actual_tokens=value)
    assert store.usage(key).reserved_tokens == 2000


@pytest.mark.parametrize("key", [b"", "not-bytes", None])
def test_invalid_identity_or_request_does_not_persist_raw_inputs(state, key):
    store, _, _, _ = state
    failure(StorageFailure.CONFIGURATION, lambda: store.usage(key))
    failure(
        StorageFailure.CONFLICT,
        lambda: store.admit(b"synthetic", "raw-input", plan(), reservation_ms=100),
    )


def test_runtime_and_filesystem_gates_precede_database_creation(tmp_path, monkeypatch):
    settings = StorageSettings(tmp_path / "never-created.sqlite3", b"x" * 32)
    monkeypatch.setattr(storage.sqlite3, "sqlite_version_info", (3, 51, 2))
    failure(StorageFailure.CONFIGURATION, lambda: SQLiteStore(settings, clock=Clock()))
    assert not settings.path.exists()
    monkeypatch.setattr(storage.sqlite3, "sqlite_version_info", (3, 53, 1))

    def reject(path):
        raise StorageError(StorageFailure.CONFIGURATION)

    monkeypatch.setattr(storage, "_require_local_storage", reject)
    failure(StorageFailure.CONFIGURATION, lambda: SQLiteStore(settings, clock=Clock()))
    assert not settings.path.exists()


@pytest.mark.parametrize(
    "changes",
    [
        {"path": Path(":memory:")},
        {"identity_secret": b"short"},
        {"busy_timeout_ms": True},
        {"busy_timeout_ms": 0},
        {"busy_timeout_ms": 10_001},
    ],
)
def test_invalid_settings_are_sanitized(tmp_path, changes):
    failure(
        StorageFailure.CONFIGURATION,
        lambda: StorageSettings(
            **{"path": tmp_path / "a.sqlite3", "identity_secret": b"x" * 32, **changes}
        ),
    )
