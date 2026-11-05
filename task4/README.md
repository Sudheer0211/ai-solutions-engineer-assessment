# Task 4: pure sliding-window accounting (T4-002)

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
One T4-001/T4-002 foundation commit is authorized. Preserve accepted logic; no test
reruns, T4-003 implementation or push during this Git checkpoint.
