# Task 4: token accounting, SQLite storage and injectable LLM routing

**T4-004 is independently ACCEPTED**, confirmed by the user 2026-11-04.
E024: **324 passed in 7.24s**, zero failures/skips/warnings/xfails;
Ruff lint and format pass (15 files), native Python 3.12.16/SQLite 3.53.1.
No real model/tokenizer or HTTP endpoint is supplied. No vendor credentials needed
for tests. TASK-4 remains IN_PROGRESS; one approved T4-004 milestone commit only,
no T4-005 implementation or push. E025 records reported review: 324 tests passed
in an isolated Linux copy with review-only platform/SQLite changes, additional
category/total-bound checks and approximately 3.020 s real-monotonic fallback with
one backup/conservative accounting. No review changes are shipped or native Linux
support/real-provider guarantee claimed; E024 native Windows evidence is authoritative.

T4-001/T4-002/T4-003 are independently accepted. Storage baseline: ebc226a.
E022 native Windows/SQLite 3.53.1 evidence remains authoritative; E023's Linux
shim review does not add native Linux support. All accepted code/tests/pins and
Tasks 1/2 are unchanged. Historical checkpoint limits below are superseded only
by the expressly authorized T4-004 section at the end.

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

## T4-004 provider/service API (independently accepted)

`providers.Provider` is an injectable trusted adapter. Its pure `prepare(text)`
returns a request-scoped `PreparedAttempt` with model-specific `bounds`,
`async execute()` and `async aclose()`. It MUST reliably count every token category
and enforce the matching output cap, with no hidden retry or redirect. The service
checks typed/model/counter metadata; those checks do not prove real tokenizer
correctness. No vendor contract/tokenizer is invented, and no caller-supplied
bounds are accepted. Unavailable reliable bounds must fail before admission/send.
Test doubles implement a synthetic counting/cap contract only.

Create `LLMService(store, primary, backup, RoutingPolicy(backup_timeout_ms,
reservation_ms), clock=optional_monotonic_clock)` using an initialized supported
SQLiteStore and trusted adapters. There are deliberately no backup/overall budget
defaults: supply positive integer budgets, reservation_ms greater than
3000 + 500 + backup_timeout_ms + 500, plus sufficient DB/scheduling margin.
The 2000/10000 values in tests are fixtures, not deployment requirements.

`await service.generate(validated_key_bytes, text, request_id=optional_internal_UUID)`
returns controlled ServiceOutcome(code/message/text/used_backup/request_id).
The key is shape-checked and used only by storage, never passed to model adapters.
Actual key authentication/provisioning and HTTP schemas remain deferred. Success
text is preserved; errors never copy raw provider/SQL diagnostics.

- Atomic combined admission precedes any send; local quota denial has zero provider
  calls. Durable single-start guards and tenant separation remain in
  accepted storage; provider input is the prompt alone, not a tenant credential.
- Primary deadline is monotonic 3000 ms. At/after the deadline, content loses; late
  reliable usage can still settle. Primary 429 or that deadline triggers exactly
  one backup only after confirmed local termination AND resource close. Early
  adapter timeouts are terminal failures, not evidence of the 3000 ms threshold.
- One shared 500 ms cleanup grace covers termination and close; timeout's ceiling
  remains original deadline+500 even after delayed observation. No confirmed cleanup
  means unavailable/no backup, retained holds and quarantined service dispatch.
- Backup has the explicit finite deadline; failure/timeout has no third attempt.
  Known in-bound usage settles at admission time; unknown usage charges full bound.
  Unsent backup is released only after confirmed cleanup. Bound breaches fail closed.
- All DB calls and pure preparation are offloaded through one bounded lane. DB
  transactions do not enclose provider I/O. SQLite remains the atomic quota arbiter
  across independent service instances and processes.
- Cancelling generate signals an owned workflow and raises CancelledError to the
  caller; it does not cancel a DB thread or assert rollback. The workflow discovers
  actual completion, cleans/accounts and prevents new fallback. Ambiguous storage
  failures preserve durable holds for accepted deadline recovery, with no replay.
- Stop submissions, then `await service.aclose()` BEFORE closing store/event loop.
  It drains owners/DB work and bounds its remaining cleanup wait. False signals
  unconfirmed/failed cleanup; retain ownership and do not claim graceful shutdown.
  An arbitrary uncooperative adapter/blocked OS thread cannot be forcibly killed
  by asyncio. Local cancellation cannot guarantee remote execution/billing stopped.

New tests use real local SQLite plus controlled clocks/events/fake providers,
including 2999/3000/3001 primary and cleanup boundaries, late observation, failure,
cancellation during DB work, duplicate starts, independent concurrent service
owners and tenant isolation. Complete suite includes the unchanged storage process
fixtures (15 normal children/zero forced cleanup). No network/provider socket,
actual model-token bound, HTTP or final fault-injection audit is claimed. Supported
storage remains Windows fixed local drive/SQLite >=3.51.3, actual 3.53.1.
See requirements T4-004 contract, accepted ADR-019 and E024/E025. Preserve approved
implementation; no test rerun or T4-005. The approximately 3.020 s independent
probe is reported evidence, not a latency SLA or new local execution. Stop after
the one authorized milestone commit; no push.
