"""T4-003 deterministic clocks and real spawned-process workers (no provider I/O)."""

import json
import multiprocessing
import secrets
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import pytest

from task4_limiter.models import ModelTokenBounds, ReservationPlan
from task4_limiter.storage import SQLiteStore, StorageError, StorageSettings


@contextmanager
def database(path, **kwargs):
    with closing(sqlite3.connect(path, **kwargs)) as db, db:
        yield db


@dataclass
class Clock:
    value: int = 0

    def now_ms(self) -> int:
        return self.value


def plan(primary=1000, backup=1000):
    return ReservationPlan(
        ModelTokenBounds("primary", primary, 0, "fixture-v1"),
        ModelTokenBounds("backup", backup, 0, "fixture-v2"),
    )


def worker(path, secret, key, mode, index, barrier, output):
    try:
        with SQLiteStore(StorageSettings(Path(path), secret, 3000), clock=Clock(100)) as store:
            if barrier is not None:
                barrier.wait(timeout=20)
            if mode == "admit":
                result = store.admit(key, UUID(int=index), plan(), reservation_ms=100_000)
                output.put((index, "admit", result.admitted))
            elif mode == "duplicate":
                result = store.admit(key, UUID(int=1), plan(), reservation_ms=100_000)
                output.put((index, "admit", result.admitted))
            elif mode in ("settle_same", "settle_conflict"):
                actual = 123 if mode == "settle_same" else 100 + index
                store.settle(key, UUID(int=1), 1, actual_tokens=actual)
                output.put((index, "settle", actual))
            elif mode == "write":
                store.admit(key, UUID(int=index), plan(), reservation_ms=100_000)
                store.start_attempt(key, UUID(int=index), 1)
                store.settle(key, UUID(int=index), 1, actual_tokens=123)
                output.put((index, "write", store.usage(key).total_tokens))
            else:
                output.put((index, "read", store.usage(key).total_tokens))
    except StorageError as exc:
        output.put((index, "error", exc.kind.value))


@pytest.fixture(scope="session")
def process_runner():
    outcomes = []

    def run(path, secret, key, mode, indexes, *, synchronize=False):
        context = multiprocessing.get_context("spawn")
        barrier = context.Barrier(len(indexes) + 1) if synchronize else None
        output = context.Queue()
        children = []
        try:
            for index in indexes:
                child = context.Process(
                    target=worker, args=(str(path), secret, key, mode, index, barrier, output)
                )
                child.start()
                children.append(child)
            if barrier is not None:
                barrier.wait(timeout=25)
            results = [output.get(timeout=25) for _ in children]
            for child in children:
                child.join(timeout=10)
                assert child.exitcode == 0
            return results
        finally:
            for child in children:
                forced = child.is_alive()
                if forced:
                    child.terminate()
                child.join(timeout=5)
                if child.is_alive():
                    child.kill()
                    child.join(timeout=5)
                outcomes.append(
                    {"alive": child.is_alive(), "forced": forced, "exitcode": child.exitcode}
                )
                child.close()
            output.close()
            output.join_thread()

    yield run
    report = {
        "children": len(outcomes),
        "alive": sum(p["alive"] for p in outcomes),
        "forced": sum(p["forced"] for p in outcomes),
        "outcomes": outcomes,
    }
    directory = Path(__file__).parents[1] / ".cache"
    directory.mkdir(exist_ok=True)
    (directory / "sqlite_process_summary.json").write_text(json.dumps(report, indent=2))


@pytest.fixture
def state(tmp_path):
    secret, key = secrets.token_bytes(32), secrets.token_bytes(32)
    settings = StorageSettings(tmp_path / "usage.sqlite3", secret)
    clock = Clock()
    with SQLiteStore(settings, clock=clock) as store:
        yield store, clock, settings, key
