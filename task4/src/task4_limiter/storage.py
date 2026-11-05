"""T4-003: synchronous, short SQLite transactions; no network/provider execution."""

import ctypes
import hmac
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from uuid import UUID

from task4_limiter.accounting import AccountingClock, assess_admission, calculate_usage
from task4_limiter.models import (
    QUOTA_TOKENS,
    WINDOW_MS,
    AdmissionDecision,
    OutstandingReservation,
    ReservationPlan,
    SettledUsage,
    UsageSnapshot,
    _integer,
)

_APPLICATION_ID = 0x54340003
_SCHEMA_VERSION = 1
_SCHEMA = (
    """CREATE TABLE store_meta (
        id INTEGER PRIMARY KEY CHECK(id=1),
        schema_version INTEGER NOT NULL CHECK(schema_version=1),
        identity_verifier BLOB NOT NULL CHECK(length(identity_verifier)=32),
        last_ms INTEGER NOT NULL CHECK(last_ms>=0),
        quota INTEGER NOT NULL CHECK(quota=50000),
        window_ms INTEGER NOT NULL CHECK(window_ms=60000)
    ) STRICT""",
    """CREATE TABLE requests (
        tenant TEXT NOT NULL CHECK(length(tenant)=64 AND tenant NOT GLOB '*[^0-9a-f]*'),
        request_id TEXT NOT NULL CHECK(length(request_id)=32),
        admission_ms INTEGER NOT NULL CHECK(admission_ms>=0),
        deadline_ms INTEGER NOT NULL CHECK(deadline_ms>admission_ms),
        phase TEXT NOT NULL CHECK(phase IN ('open','complete','abandoned')),
        blocked INTEGER NOT NULL DEFAULT 0 CHECK(blocked IN (0,1)),
        PRIMARY KEY(tenant,request_id)
    ) STRICT""",
    """CREATE TABLE attempts (
        tenant TEXT NOT NULL, request_id TEXT NOT NULL,
        ordinal INTEGER NOT NULL CHECK(ordinal IN (1,2)),
        bound_tokens INTEGER NOT NULL CHECK(bound_tokens>0),
        state TEXT NOT NULL CHECK(state IN ('reserved','started','settled','released','recovered')),
        charged_tokens INTEGER, accounting_ms INTEGER NOT NULL CHECK(accounting_ms>=0),
        source TEXT CHECK(source IN ('known','unknown','unused','deadline')),
        PRIMARY KEY(tenant,request_id,ordinal),
        FOREIGN KEY(tenant,request_id) REFERENCES requests(tenant,request_id),
        CHECK((state IN ('reserved','started') AND charged_tokens IS NULL AND source IS NULL)
           OR (state='settled' AND charged_tokens IS NOT NULL AND source IS NOT NULL
               AND charged_tokens BETWEEN 0 AND bound_tokens AND source IN ('known','unknown')
               AND (source='known' OR charged_tokens=bound_tokens))
           OR (state='released' AND charged_tokens IS NOT NULL AND source IS NOT NULL
               AND charged_tokens=0 AND source='unused')
           OR (state='recovered' AND charged_tokens IS NOT NULL AND source IS NOT NULL
               AND charged_tokens=bound_tokens AND source='deadline'))
    ) STRICT""",
    "CREATE INDEX usage_by_tenant_time ON attempts(tenant,state,accounting_ms)",
    "CREATE INDEX recovery_by_tenant_deadline ON requests(tenant,phase,deadline_ms)",
    "CREATE INDEX blocked_by_tenant ON requests(tenant,blocked)",
)


class StorageFailure(StrEnum):
    CONFIGURATION = "configuration"
    BUSY = "busy"
    UNAVAILABLE = "unavailable"
    DUPLICATE = "duplicate"
    CONFLICT = "conflict"
    CLOCK_REGRESSION = "clock_regression"
    BOUND_EXCEEDED = "bound_exceeded"
    BLOCKED = "blocked"


class StorageError(RuntimeError):
    def __init__(self, kind: StorageFailure) -> None:
        super().__init__("Storage operation failed")
        self.kind = kind


@dataclass(frozen=True, slots=True)
class StorageSettings:
    path: Path = field(repr=False)
    identity_secret: bytes = field(repr=False)
    busy_timeout_ms: int = 1000

    def __post_init__(self) -> None:
        try:
            if (
                not isinstance(self.path, Path)
                or not self.path.is_absolute()
                or type(self.identity_secret) is not bytes
                or not 32 <= len(self.identity_secret) <= 1024
                or type(self.busy_timeout_ms) is not int
                or not 1 <= self.busy_timeout_ms <= 10_000
            ):
                raise ValueError
            path = self.path.resolve()
            if not path.parent.is_dir() or path.is_dir():
                raise ValueError
            object.__setattr__(self, "path", path)
        except (OSError, ValueError):
            raise StorageError(StorageFailure.CONFIGURATION) from None


def _require_local_storage(path: Path) -> None:
    # Fail closed on platforms lacking a verified filesystem detector in this milestone.
    if os.name != "nt":
        raise StorageError(StorageFailure.CONFIGURATION)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetVolumePathNameW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint]
    kernel.GetVolumePathNameW.restype = ctypes.c_int
    kernel.GetDriveTypeW.argtypes = [ctypes.c_wchar_p]
    kernel.GetDriveTypeW.restype = ctypes.c_uint
    volume = ctypes.create_unicode_buffer(1024)
    if not kernel.GetVolumePathNameW(str(path.parent), volume, len(volume)):
        raise StorageError(StorageFailure.CONFIGURATION)
    if kernel.GetDriveTypeW(volume.value) != 3:  # DRIVE_FIXED; rejects UNC/mapped network drives.
        raise StorageError(StorageFailure.CONFIGURATION)


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    request_id: UUID
    decision: AdmissionDecision

    @property
    def admitted(self) -> bool:
        return self.decision.allowed


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    ordinal: int
    bound_tokens: int
    state: str
    charged_tokens: int | None
    accounting_ms: int
    source: str | None


@dataclass(frozen=True, slots=True)
class RequestRecord:
    request_id: UUID
    admission_ms: int
    deadline_ms: int
    phase: str
    blocked: bool
    attempts: tuple[AttemptRecord, ...]


@dataclass(frozen=True, slots=True)
class _Sample:
    value: int

    def now_ms(self) -> int:
        return self.value


class SQLiteStore:
    """One connection per operation/calling thread; offload whole calls in async code.

    close() prevents new operations; the owner must drain in-flight operations.
    No client authentication or provider-token-bound certification is performed.
    """

    def __init__(self, settings: StorageSettings, *, clock: AccountingClock) -> None:
        if type(settings) is not StorageSettings:
            raise StorageError(StorageFailure.CONFIGURATION)
        self._settings = settings
        self._clock = clock
        self._closed = False
        self._verifier = hmac.digest(settings.identity_secret, b"task4-store-identity-v1", "sha256")
        self._initialize()

    def __enter__(self) -> "SQLiteStore":
        if self._closed:
            raise StorageError(StorageFailure.UNAVAILABLE)
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._closed = True

    def _connect(self, *, create: bool = False) -> sqlite3.Connection:
        if self._closed:
            raise StorageError(StorageFailure.UNAVAILABLE)
        if sqlite3.sqlite_version_info < (3, 51, 3):
            raise StorageError(StorageFailure.CONFIGURATION)
        _require_local_storage(self._settings.path)
        db = None
        try:
            db = sqlite3.connect(
                self._settings.path.as_uri() + ("?mode=rwc" if create else "?mode=rw"),
                uri=True,
                autocommit=True,
                timeout=self._settings.busy_timeout_ms / 1000,
            )
            db.row_factory = sqlite3.Row
            db.execute(f"PRAGMA busy_timeout={self._settings.busy_timeout_ms}")
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("PRAGMA synchronous=EXTRA" if create else "PRAGMA synchronous=FULL")
            if db.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise StorageError(StorageFailure.CONFIGURATION)
            if not create and (
                db.execute("PRAGMA journal_mode").fetchone()[0] != "wal"
                or db.execute("PRAGMA synchronous").fetchone()[0] != 2
            ):
                raise StorageError(StorageFailure.CONFIGURATION)
            return db
        except (sqlite3.Error, OSError) as exc:
            if db is not None:
                db.close()
            raise self._database_error(exc) from None
        except BaseException:
            if db is not None:
                db.close()
            raise

    @staticmethod
    def _database_error(exc: Exception) -> StorageError:
        code = getattr(exc, "sqlite_errorcode", 0) & 0xFF
        return StorageError(
            StorageFailure.BUSY
            if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED)
            else StorageFailure.UNAVAILABLE
        )

    @staticmethod
    def _rollback(db: sqlite3.Connection) -> None:
        try:
            if db.in_transaction:
                db.execute("ROLLBACK")
        except sqlite3.Error:
            pass  # Closing the private connection is the final rollback boundary.

    def _verify(self, db: sqlite3.Connection) -> sqlite3.Row:
        if (
            db.execute("PRAGMA application_id").fetchone()[0] != _APPLICATION_ID
            or db.execute("PRAGMA user_version").fetchone()[0] != _SCHEMA_VERSION
        ):
            raise StorageError(StorageFailure.CONFIGURATION)
        row = db.execute("SELECT * FROM store_meta WHERE id=1").fetchone()
        if (
            row is None
            or row["schema_version"] != _SCHEMA_VERSION
            or row["quota"] != QUOTA_TOKENS
            or row["window_ms"] != WINDOW_MS
            or not hmac.compare_digest(row["identity_verifier"], self._verifier)
        ):
            raise StorageError(StorageFailure.CONFIGURATION)
        return row

    def _initialize(self) -> None:
        db = self._connect(create=True)
        try:
            db.execute("BEGIN IMMEDIATE")
            tables = {
                r[0]
                for r in db.execute(
                    "SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            if (
                not tables
                and db.execute("PRAGMA application_id").fetchone()[0] == 0
                and db.execute("PRAGMA user_version").fetchone()[0] == 0
            ):
                for statement in _SCHEMA:
                    db.execute(statement)
                db.execute(
                    "INSERT INTO store_meta VALUES (1,1,?,0,?,?)",
                    (self._verifier, QUOTA_TOKENS, WINDOW_MS),
                )
                db.execute(f"PRAGMA application_id={_APPLICATION_ID}")
                db.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
            elif tables != {"store_meta", "requests", "attempts"}:
                raise StorageError(StorageFailure.CONFIGURATION)
            self._verify(db)
            db.execute("COMMIT")
            if db.execute("PRAGMA journal_mode=WAL").fetchone()[0] != "wal":
                raise StorageError(StorageFailure.CONFIGURATION)
            db.execute("PRAGMA synchronous=FULL")
            if db.execute("PRAGMA synchronous").fetchone()[0] != 2:
                raise StorageError(StorageFailure.CONFIGURATION)
        except (sqlite3.Error, OSError) as exc:
            self._rollback(db)
            raise self._database_error(exc) from None
        except BaseException:
            self._rollback(db)
            raise
        finally:
            db.close()

    @contextmanager
    def _transaction(self) -> Iterator[tuple[sqlite3.Connection, int]]:
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            metadata = self._verify(db)
            now = self._clock.now_ms()  # Sample only after acquiring the writer transaction.
            _integer(now)
            if now < metadata["last_ms"]:
                raise StorageError(StorageFailure.CLOCK_REGRESSION)
            db.execute("UPDATE store_meta SET last_ms=? WHERE id=1", (now,))
            yield db, now
            db.execute("COMMIT")  # autocommit=True requires explicit SQL, not db.commit().
        except (sqlite3.Error, OSError) as exc:
            self._rollback(db)
            raise self._database_error(exc) from None
        except BaseException:
            self._rollback(db)
            raise
        finally:
            db.close()

    def _tenant(self, api_key: bytes) -> str:
        if type(api_key) is not bytes or not 1 <= len(api_key) <= 4096:
            raise StorageError(StorageFailure.CONFIGURATION)
        return hmac.digest(
            self._settings.identity_secret, b"task4-tenant-v1\0" + api_key, "sha256"
        ).hex()

    @staticmethod
    def _request_id(request_id: UUID) -> str:
        if type(request_id) is not UUID:
            raise StorageError(StorageFailure.CONFLICT)
        return request_id.hex

    @staticmethod
    def _recover(db: sqlite3.Connection, tenant: str, now: int) -> int:
        due = db.execute(
            "SELECT request_id,deadline_ms FROM requests "
            "WHERE tenant=? AND phase='open' AND deadline_ms<=?",
            (tenant, now),
        ).fetchall()
        for row in due:
            db.execute(
                "UPDATE attempts SET state='recovered',charged_tokens=bound_tokens,"
                "accounting_ms=?,source='deadline' WHERE tenant=? AND request_id=? "
                "AND state IN ('reserved','started')",
                (row["deadline_ms"], tenant, row["request_id"]),
            )
            db.execute(
                "UPDATE requests SET phase='abandoned' WHERE tenant=? AND request_id=?",
                (tenant, row["request_id"]),
            )
        return len(due)

    @staticmethod
    def _entries(
        db: sqlite3.Connection, tenant: str, now: int
    ) -> tuple[list[SettledUsage], list[OutstandingReservation]]:
        settled, holds = [], []
        rows = db.execute(
            "SELECT * FROM attempts WHERE tenant=? AND "
            "(state IN ('reserved','started') OR accounting_ms>?)",
            (tenant, now - WINDOW_MS),
        )
        for row in rows:
            entry_id = f"{row['request_id']}:{row['ordinal']}"
            if row["state"] in ("reserved", "started"):
                holds.append(
                    OutstandingReservation(
                        tenant, entry_id, row["accounting_ms"], row["bound_tokens"]
                    )
                )
            else:
                settled.append(
                    SettledUsage(tenant, entry_id, row["accounting_ms"], row["charged_tokens"])
                )
        return settled, holds

    def admit(
        self, api_key: bytes, request_id: UUID, plan: ReservationPlan, *, reservation_ms: int
    ) -> AdmissionResult:
        tenant, rid = self._tenant(api_key), self._request_id(request_id)
        _integer(reservation_ms, minimum=1)
        with self._transaction() as (db, now):
            _integer(now + reservation_ms)
            self._recover(db, tenant, now)
            if db.execute(
                "SELECT 1 FROM requests WHERE tenant=? AND blocked=1", (tenant,)
            ).fetchone():
                raise StorageError(StorageFailure.BLOCKED)
            if db.execute(
                "SELECT 1 FROM requests WHERE tenant=? AND request_id=?", (tenant, rid)
            ).fetchone():
                raise StorageError(StorageFailure.DUPLICATE)
            settled, holds = self._entries(db, tenant, now)
            decision = assess_admission(tenant, plan, settled, holds, clock=_Sample(now))
            if decision.allowed:
                db.execute(
                    "INSERT INTO requests VALUES (?,?,?,?, 'open',0)",
                    (tenant, rid, now, now + reservation_ms),
                )
                for ordinal, bound in enumerate((plan.primary, plan.backup), 1):
                    db.execute(
                        "INSERT INTO attempts VALUES (?,?,?,?, 'reserved',NULL,?,NULL)",
                        (tenant, rid, ordinal, bound.total_tokens, now),
                    )
            result = AdmissionResult(request_id, decision)
        return result  # Never exposes success before the transaction's COMMIT succeeds.

    def usage(self, api_key: bytes) -> UsageSnapshot:
        tenant = self._tenant(api_key)
        with self._transaction() as (db, now):
            self._recover(db, tenant, now)
            settled, holds = self._entries(db, tenant, now)
            result = calculate_usage(tenant, now, settled, holds)
        return result

    def recover(self, api_key: bytes) -> int:
        tenant = self._tenant(api_key)
        with self._transaction() as (db, now):
            result = self._recover(db, tenant, now)
        return result

    @staticmethod
    def _row(db: sqlite3.Connection, tenant: str, rid: str) -> sqlite3.Row:
        row = db.execute(
            "SELECT * FROM requests WHERE tenant=? AND request_id=?", (tenant, rid)
        ).fetchone()
        if row is None:
            raise StorageError(StorageFailure.CONFLICT)
        return row

    def request(self, api_key: bytes, request_id: UUID) -> RequestRecord:
        tenant, rid = self._tenant(api_key), self._request_id(request_id)
        with self._transaction() as (db, now):
            self._recover(db, tenant, now)
            row = self._row(db, tenant, rid)
            attempts = tuple(
                AttemptRecord(
                    r["ordinal"],
                    r["bound_tokens"],
                    r["state"],
                    r["charged_tokens"],
                    r["accounting_ms"],
                    r["source"],
                )
                for r in db.execute(
                    "SELECT * FROM attempts WHERE tenant=? AND request_id=? ORDER BY ordinal",
                    (tenant, rid),
                )
            )
            result = RequestRecord(
                request_id,
                row["admission_ms"],
                row["deadline_ms"],
                row["phase"],
                bool(row["blocked"]),
                attempts,
            )
        return result

    def _attempt(
        self, db: sqlite3.Connection, tenant: str, rid: str, ordinal: int, now: int
    ) -> tuple[sqlite3.Row, sqlite3.Row]:
        if type(ordinal) is not int or ordinal not in (1, 2):
            raise StorageError(StorageFailure.CONFLICT)
        self._recover(db, tenant, now)
        request = self._row(db, tenant, rid)
        row = db.execute(
            "SELECT * FROM attempts WHERE tenant=? AND request_id=? AND ordinal=?",
            (tenant, rid, ordinal),
        ).fetchone()
        if request["phase"] == "abandoned" or row is None:
            raise StorageError(StorageFailure.CONFLICT)
        return request, row

    def start_attempt(self, api_key: bytes, request_id: UUID, ordinal: int) -> None:
        """Commit a single dispatch intent; does not select or call a provider."""
        tenant, rid = self._tenant(api_key), self._request_id(request_id)
        with self._transaction() as (db, now):
            request, row = self._attempt(db, tenant, rid, ordinal, now)
            other = db.execute(
                "SELECT state FROM attempts WHERE tenant=? AND request_id=? AND ordinal=?",
                (tenant, rid, 3 - ordinal),
            ).fetchone()
            if (
                request["phase"] != "open"
                or request["blocked"]
                or row["state"] != "reserved"
                or other is None
                or other[0] != ("reserved" if ordinal == 1 else "settled")
            ):
                raise StorageError(StorageFailure.CONFLICT)
            db.execute(
                "UPDATE attempts SET state='started' WHERE tenant=? AND request_id=? AND ordinal=?",
                (tenant, rid, ordinal),
            )

    @staticmethod
    def _finish(db: sqlite3.Connection, tenant: str, rid: str) -> None:
        if not db.execute(
            "SELECT 1 FROM attempts WHERE tenant=? AND request_id=? "
            "AND state IN ('reserved','started')",
            (tenant, rid),
        ).fetchone():
            db.execute(
                "UPDATE requests SET phase='complete' WHERE tenant=? AND request_id=?",
                (tenant, rid),
            )

    def settle(
        self, api_key: bytes, request_id: UUID, ordinal: int, *, actual_tokens: int | None
    ) -> None:
        """None means unknown dispatched usage: charge its full bound, never zero."""
        tenant, rid = self._tenant(api_key), self._request_id(request_id)
        if actual_tokens is not None:
            _integer(actual_tokens)
        breach = False
        with self._transaction() as (db, now):
            _, row = self._attempt(db, tenant, rid, ordinal, now)
            charged = row["bound_tokens"] if actual_tokens is None else actual_tokens
            source = "unknown" if actual_tokens is None else "known"
            if row["state"] == "settled" and (row["charged_tokens"], row["source"]) == (
                charged,
                source,
            ):
                pass
            elif row["state"] != "started":
                raise StorageError(StorageFailure.CONFLICT)
            elif charged > row["bound_tokens"]:
                db.execute(
                    "UPDATE requests SET blocked=1 WHERE tenant=? AND request_id=?", (tenant, rid)
                )
                breach = True  # Commit the durable block before reporting the invariant breach.
            else:
                db.execute(
                    "UPDATE attempts SET state='settled',charged_tokens=?,source=? "
                    "WHERE tenant=? AND request_id=? AND ordinal=?",
                    (charged, source, tenant, rid, ordinal),
                )
                self._finish(db, tenant, rid)
        if breach:
            raise StorageError(StorageFailure.BOUND_EXCEEDED)

    def release_unused(self, api_key: bytes, request_id: UUID, ordinal: int) -> None:
        """Only never-started capacity is releasable; repeated release is a no-op."""
        tenant, rid = self._tenant(api_key), self._request_id(request_id)
        with self._transaction() as (db, now):
            _, row = self._attempt(db, tenant, rid, ordinal, now)
            if row["state"] == "released":
                pass
            elif row["state"] != "reserved":
                raise StorageError(StorageFailure.CONFLICT)
            else:
                db.execute(
                    "UPDATE attempts SET state='released',charged_tokens=0,source='unused' "
                    "WHERE tenant=? AND request_id=? AND ordinal=?",
                    (tenant, rid, ordinal),
                )
                self._finish(db, tenant, rid)
