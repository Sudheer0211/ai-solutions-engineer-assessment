# Task 4: token accounting and SQLite storage

T4-003 local verification: **221 passed in 3.37s**, no failures/skips/warnings/xfails;
Ruff lint/format pass (10 files). **T4-003 is independently ACCEPTED** within
Windows fixed-local-drive/supported SQLite scope, confirmed by the user 2026-11-04.
E022 native Windows/SQLite 3.53.1 results remain authoritative. E023 records reported
Linux review-copy passes with test-only platform/runtime gate shims (221 tests,
15 normal child exits and three additional scenarios). That review does not add
native Linux support or native Windows gate evidence; no shim/gate change ships.
One T4-003 milestone commit authorized; no new tests, T4-004, provider/HTTP or push.

## Accepted T4-001/T4-002 foundation

Isolated Python 3.12 project with standard-library-only runtime. Task 1/2 source,
tests, environments and dependency configurations are separate and unchanged.
Source contract: [TASK4_REQUIREMENTS.md](../docs/TASK4_REQUIREMENTS.md), finalized
engineering policies P1-P4; ADR-016. T4-001 architecture is independently approved
with conditions now finalized. **T4-002 is independently ACCEPTED**, confirmed by
the user on 2026-11-04: 169 existing tests, 12,000 randomized differential checks
and six targeted invariants passed; no blocking defect. These are reported review
results, not new local executions. E020 retains actual local pytest/Ruff evidence;
E021 records acceptance/Git inspection. Whole TASK-4 remains IN_PROGRESS.

From task4/, with uv installed:

```powershell
uv sync --locked --extra dev --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Local verification E020 (2026-11-04 America/Los_Angeles): **169 passed in 0.12s**,
zero failures/skips/warnings/xfails, both Ruff checks pass (5 Python files).
Initial sandbox execution passed 169 with one cache-permission warning; the same
command outside the sandbox resolved it. No tests/markers/warning filters changed.
Runtime Python 3.12.16, pytest 9.2.0, Ruff 0.17.3; setuptools 82.0.1 isolated build.
The lock selects eight installed packages including this editable project.

## Interface and trust boundary

- models.ModelTokenBounds: model alias, input/output bounds and counting-policy
  identifier. Requires exact nonnegative integers, positive total and signed-64-bit
  range. These are TRUSTED INTERNAL ADAPTER OUTPUTS, not client estimates. A name
  or successful construction cannot prove a tokenizer/output-cap guarantee.
- models.ReservationPlan: both typed model bounds required; total is the combined
  primary+backup reservation, checked for overflow. No missing-backup shortcut.
- models.SettledUsage / OutstandingReservation: immutable tenant-scoped entry ID,
  admission timestamp and token amount. Holds must be positive; settled zero is valid.
- accounting.calculate_usage(tenant_id, now_ms, settled, outstanding,
  last_observed_ms=None): sum settled entries in (now-60,000,now] plus ALL target-
  tenant holds, even old holds. Future entries, regressed watermark, wrong record
  types or duplicate identities (including both states) fail closed.
- accounting.assess_admission(..., clock=..., last_observed_ms=None): sample injected
  AccountingClock.now_ms once and return immutable AdmissionDecision. Allowed iff
  settled + outstanding + both new model bounds <= 50,000. Existing overage denies.
  Denied decisions leave reported remaining capacity unchanged, never negative.

Opaque tenant IDs are compared exactly, without normalization/case-folding. Raw
API-key authentication/HMAC identity resolution is not implemented in this checkpoint.
Future trusted adapters must establish model-specific token bounds/output enforcement
or reject before dispatch. No actual provider/tokenizer is selected or certified.

Each entry represents one attempt's accounting identity; future storage projects
its attempt rows into these records once. Settlement replaces an outstanding entry
at its original admission timestamp; it must not supply that ID in both collections.
T4-002 receives snapshots; it does not perform settlement, refunds or recovery.

## Important limits

Pure decisions do not reserve tokens or mutate a store. Repeating an allowed
calculation can return allowed again: atomic concurrent admission belongs to
T4-003's SQLite transaction. Do not use these results as authorization permits.
Unresolved holds never expire in pure calculations; future recovery must supply
an explicit valid replacement rather than expecting automatic quota release.

No SQLite database/transactions, provider clients, timeout/fallback execution, HTTP
endpoints, crash-recovery infrastructure or Task 3 is implemented. P3's monotonic
3,000 ms primary/500 ms cleanup policy is documented only. Persistence, concurrency,
real token provenance, provider behavior and full Task 4 compliance remain unverified.
The accepted foundation is committed as 3d8d3e5 and unchanged. Historical pure-only
limits above describe T4-002; T4-003 adds storage below, with its own review gate.

## T4-003 storage API

`storage.SQLiteStore(StorageSettings(absolute_path, external_identity_secret),
clock=injected_UTC_clock)` bootstraps/validates a local SQLite store. The parent
directory must exist. Only Windows fixed local volumes are currently verified;
network volumes and other platforms fail closed. Runtime minimum SQLite 3.51.3;
this environment verifies 3.53.1. No database file or secret ships in the repository.

| Operation | Guarantee |
| --- | --- |
| admit(key_bytes, UUID, plan, reservation_ms=...) | Atomic read/pure decision/two reservations; return only after COMMIT |
| start_attempt(key_bytes, UUID, ordinal) | One durable dispatch intent; does not execute/select a provider |
| settle(..., actual_tokens=int or None) | Known charge or full unknown bound; same admission time; identical repeat no-op |
| release_unused(...) | Only never-started reservation; idempotent zero charge |
| usage(key_bytes) / request(key_bytes, UUID) | Tenant-scoped immutable accounting/state; persistent clock and lazy recovery |
| recover(key_bytes) | Convert due unresolved holds to full deadline charges once; no provider replay |

API keys are transient opaque bytes HMACed under the external 32-1024-byte identity
secret; only full digests/verifier/internal UUIDs/numeric states are persisted.
Actual key authentication/provisioning remains a future boundary. Raw prompts,
completions, model/counter strings and provider credentials are not stored. Reopening
with incompatible identity/configuration fails. Do not rotate the secret/delete the
DB to recover availability; use separately reviewed migration/restore procedures.

SQLite uses STRICT schema/PK/FK/check constraints, WAL/FULL, explicit 1,000 ms busy
policy (configurable 1-10,000), and short BEGIN IMMEDIATE transactions. Connections
are private to each synchronous operation/calling thread. Async callers must offload
whole calls and drain before close. No provider/network I/O belongs inside a store
operation. Existing-file calls use mode=rw; missing stores are not recreated silently.

All unresolved holds count beyond their original 60s window. At the explicitly
supplied finite reservation deadline, lazy recovery changes remaining holds to full
charges anchored at that deadline and marks the request abandoned. Those charges
expire exactly 60s later; settled earlier attempts keep original timestamps.
Duplicate IDs, stale/invalid transitions and clock regression fail; failed
transactions retain original state. Over-bound actual usage durably blocks further
tenant admission. Generic StorageError exposes only an internal failure kind, not
SQLite diagnostics/paths/credentials. No automatic retry, pruning or unblock API.

Six barrier-synchronized processes competed for the final 2,000 tokens: one winner,
five denials, durable total 50,000. Duplicate-ID and identical/conflicting settlement
races and two independent writer/reader processes pass. Full run reaped 15 children,
all exit 0, no live/forced cleanup. Sanitized `.cache/sqlite_process_summary.json`
contains only cleanup outcomes; databases and artifacts under .cache are ignored.

This is storage-level durability/concurrency, not provider fallback/timeout, HTTP,
remote billing recovery, cross-platform filesystem or power-loss/hardware audit.
No Task 1/2 rerun was needed: no shared code/env changed. See
[T4-003 contract](../docs/TASK4_REQUIREMENTS.md), ADR-018 and E022 for exact schema,
transaction/error/recovery policy, actual commands, initial lint correction and risks.
T4-003 is accepted with the qualification above; preserve implementation and stop
after the authorized milestone commit. No T4-004 implementation or push authorized.
