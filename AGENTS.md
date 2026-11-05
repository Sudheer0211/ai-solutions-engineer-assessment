# Repository engineering instructions

## Start and end of every session

Read this file and `docs/TASK_LEDGER.md` before development. Inspect Git status,
preserve unrelated changes, and identify the active task's acceptance criteria.
Record its status before implementation. Before ending, update the ledger and
leave an actionable next step, known blockers, and a recoverable working tree.
Report completed task IDs, actual test commands/results, changed files,
architecture decisions, blockers, and the next implementation step.

## Scope and source of truth

Implement only the currently authorized assessment task.
Preserve completed tasks and their passing tests.
Tasks 1–4 are independent assessment components.
Use each task's supplied requirements as its source of truth.
`docs/TASK1_REQUIREMENTS.txt` preserves the supplied Task 1 assessment brief.
The user's project governance instructions and the ledger supplement each task's
supplied requirements.
Do not modify another task without explicit authorization.
Use stable IDs: GOV-001, T1-001 through T1-006, TASK-1, TASK-2, TASK-3, TASK-4.
Task 4 checkpoints use T4-001 through T4-006; contract/assumption/test IDs are
defined in `docs/TASK4_REQUIREMENTS.md`.
Use those IDs in implementation/test documentation and milestone entries.

Keep changes scoped; preserve Git history as the code audit trail. Do not
duplicate line-level diffs in Markdown. Do not rewrite existing history.

## Task 2 checkpoint restart gate

Read `docs/TASK2_REQUIREMENTS.md`, `task2/CONTRACT.md`, ADR-008 through ADR-015,
E008/E009/E011/E012/E013/E014/E015/E016/E017/E018 and `docs/TASK2_FINAL_AUDIT.md`.
T2-001/T2-002, including the Decimal correction, were independently reviewed and
accepted as confirmed by the user on 2026-11-04. Task 2 is DONE.
Foundation baseline: e828729b; accepted T2-003 adapter baseline: 0b2e0b7.
T2-004 FastAPI/ASGI integration is independently ACCEPTED, confirmed by the user
on 2026-11-04 (400 tests and additional zero-upstream rejection probes). E013
contains local execution evidence; E014 records reported review and Git inspection.
Accepted T2-004 baseline: be9ddd8. T2-005 is independently ACCEPTED, confirmed by
the user on 2026-11-04: 400 prior/52 wire passes, 33 zero-forwarding cases and
12 reaped children without forced cleanup. E015 is local evidence; E016 records
reported independent acceptance and Git inspection. Accepted T2-005 baseline:
aa343b3. T2-006 and TASK-2 are DONE following independent ChatGPT engineering
approval, confirmed by the user on 2026-11-04: assessment-ready within documented
requirements. All eight traceability rows, test references and final evidence/docs
were reviewed. E017 preserves actual audit executions (452 Task 2/149 Task 1
passes and both Ruff checks per task, locked setup/CLI/security inspection).
E018 records reported independent acceptance and documentation/Git inspection,
not new tests. One final documentation-only acceptance commit is authorized.
Preserve all implementation/tests/configuration/dependencies/lockfiles; no test
rerun unless unexpected code/config changes appear. No push or Tasks 3/4.
After the Git checkpoint, stop; future implementation/publication needs separate
authorization. Retain documented limitations and explicit staging precautions.
Preserve the accepted guard behavior and Task 1 implementation/tests/root pins.
T2-003 is verified in E011 (300 Task 2 passes and Ruff); E012 records acceptance
and commit inspection. Preserve all accepted implementation/components/tests.
Future production corrections require authorization and a documented reproduction.
Do not start Tasks 3/4 or publish without authorization.

## Task 4 current checkpoint

The user authorizes T4-001 documentation/design only (2026-11-04), superseding
the historical Task 2 no-Task-4 gate for this scope. Read
`docs/TASK4_REQUIREMENTS.md`, ADR-016/017, E019/E020/E021, task4/README.md and the ledger.
Confirmed: 50,000 tokens/sliding 60s per tenant API key, persistent SQLite,
concurrency, automatic backup on primary HTTP 429 or 3,000 ms primary timeout,
sanitized errors. Local quota 429 never triggers fallback. Distinguish confirmed
requirements from proposed accounting/reservation/provider/HTTP choices.
T4-001 is independently APPROVED WITH CONDITIONS; finalized engineering policies
P1-P4 in the requirements record satisfy the requested design conditions.
T4-002 is independently ACCEPTED, confirmed by the user on 2026-11-04: 169
existing tests, 12,000 randomized differential checks and six targeted invariants
passed independently; no blocking defect. Ruff evidence remains the actual E020
local execution record, not a newly supplied independent command.
One descriptive T4-001/T4-002 foundation commit is authorized, containing only
approved project/source/tests/configuration/lock/requirements and governance docs.
Do not change accepted logic or rerun tests. Exclude environments/caches/egg-info/
credentials/review ZIPs. No SQLite/provider/HTTP/recovery work, T4-003, Task 3 or push.
Pure arithmetic is not an atomic admission permit or tokenizer provenance proof.
Preserve completed Task 1/2 implementation/tests/config/dependencies/locks.
T4-002 is implemented and unit-verified (E020): 169 passes, Ruff lint/format pass,
isolated Python 3.12.16 environment/eight-package lock. E021 records reported
independent acceptance and Git inspection without new tests. TASK-4 IN_PROGRESS;
no T4-003 implementation authorized. SQLite 3.53.1 is metadata-only in root and
Task 4 interpreters; no WAL/database/concurrency verification or provider integration.
After the authorized commit, verify SHA/clean status/ahead-behind and stop. Preserve
the accepted pure API; future implementation/publication needs separate authorization.

T4-003 is now expressly authorized: SQLite on-disk atomic admission, persistent
identity/clock metadata, storage-only attempt transitions/settlement/release and
finite-deadline conservative recovery, plus real multiprocess tests. Read the
current requirements/ledger, ADR-018 and E022/E023. Preserve models.py/accounting.py and all
accepted tests/configuration/locks. T4-003 is independently ACCEPTED, confirmed by
user on 2026-11-04, within Windows fixed-local-drive/supported SQLite scope.
E022 native Windows/SQLite 3.53.1 verification remains authoritative. E023 records
reported review: isolated Linux copy with TEST-ONLY platform/runtime compatibility
shim, 221 passes/15 normal children/three additional scenarios; no source defect.
The shim run does not establish native Linux or Windows gate verification. Do not
ship/remove gates or modify accepted implementation/tests. One descriptive T4-003
commit is authorized for approved source/test/support/requirements/governance only.
Exclude environments/DBs/WAL/caches/credentials/review archives. No tests/Ruff rerun,
provider/fallback/HTTP execution, T4-004, Task 3 or push. Verify commit/status and stop.

## Task 1 engineering standards

The following standards apply only to Task 1. Other tasks follow their supplied
requirements; Task 1's STDIO-only and no-HTTP restrictions do not constrain them.

- Target Python 3.12, official `mcp` SDK and Pydantic v2; pin verified versions.
- Verify installed versions and documented public SDK APIs before selecting them.
- Keep a small `task1/` package separating schemas, repository, service, server,
  and entry point. Prefer readable typed functions and explicit error boundaries.
- Use strict reusable Pydantic models with forbidden extra fields. Derive
  advertised schemas from those models. Validate before changing mock state.
- Customer IDs use exactly five ASCII digits. Accept finite positive JSON
  numbers without coercing strings/bools or adding a two-decimal restriction.
- Use Decimal arithmetic for balances. State is synthetic and process-local.
- Use official STDIO/protocol machinery and public SDK APIs. No monkeypatches,
  custom JSON-RPC framing/lifecycle, HTTP servers, or out-of-scope infrastructure.
- Reserve stdout for JSON-RPC; logging goes exclusively to stderr. Never expose
  internal exception details to clients or log raw customer records unnecessarily.

## Task 1 required verification

The following verification requirements apply only to Task 1. Verify each other
task against its own supplied acceptance criteria while preserving completed
tasks and their regression coverage.

- Use pytest (and pytest-asyncio where useful) for schema/business unit tests,
  SDK integration tests, and actual subprocess STDIO wire tests.
- Cover strict types, missing/extra fields, boundaries, customer lookup, refund
  mutation, insufficient balance and no mutation on failed operations.
- Verify lifecycle, exactly two tools, generated schemas, calls, protocol error
  categories/IDs, business `isError`, stdout purity, stderr diagnostics, shutdown.
- Verify modern and legacy lifecycle connectivity if supported by the SDK.
- Run Ruff. Record the exact command, runtime/version context, exit status,
  actual result counts, failures/skips, and affected task IDs.
- If SDK limitations prevent required wire errors, retain a failing/diagnostic
  test and document the limitation; do not claim compliance or mark TASK-1 DONE.

## Durable record rules

- `docs/TASK_LEDGER.md`: priorities, statuses, mandatory acceptance criteria,
  verification references, specific blockers, and next actions.
- `docs/DECISIONS.md`: dated architecture decision records with alternatives,
  rationale, tradeoffs, consequences, and affected task/file references.
- `docs/BUILD_LOG.md`: append chronological dated milestones/investigations with
  task IDs, affected files, findings, unresolved problems, and actionable steps.
- `docs/TEST_EVIDENCE.md`: commands actually executed, outcomes and evidence.
- Never invent test results. Inspection, environment probes, diagnostics and
  manual checks must be labeled distinctly from passing automated tests.
- Update ledger/build log after each meaningful milestone; record decisions
  when made, including requirement conflicts or compatibility limitations.
- Mark a task DONE only after all its mandatory criteria have evidence.
  Use NOT_STARTED, IN_PROGRESS, BLOCKED, DONE. A blocker records evidence and
  the recommended resolution; a diagnostic pass is not compliance evidence.
- Date records using America/Los_Angeles and the actual date of the recorded
  activity; do not reuse a fixed session date.
- Never record API keys, bearer tokens, credentials, secrets or sensitive
  customer data in documentation, fixtures, logs or committed artifacts.

T4-003 outcome: DONE and independently ACCEPTED with the environment qualification
above. E022 actual local 221-pass/Ruff evidence is unchanged; no new local tests.
TASK-4 remains IN_PROGRESS; T4-004 NOT_STARTED and not authorized. Preserve Tasks
1/2 and the accounting/storage baseline. After the one Git checkpoint, stop; future
implementation/publication requires separate authorization.

## T4-004 active authorization (2026-11-04)

The latest user instruction supersedes historical no-T4-004 gates for injectable
providers.py/service.py and new tests only. Preserve ebc226a accounting/storage,
accepted tests/pins and Tasks 1/2. Required primary monotonic 3000 ms/shared cleanup
500 ms; uncertain cleanup prevents backup; no retries/hedging. Offload whole DB
operations and discover completion after caller cancellation. No vendor contract or
untrusted token estimates. Run full Task 4 suite and both Ruff checks, record actual
results and stop for independent review. No HTTP/T4-005, commit or push.

T4-004 outcome: DONE and independently ACCEPTED, user confirmation 2026-11-04.
Read E024/E025 and ADR-019. E024 native Windows/Python 3.12.16/SQLite 3.53.1
verification (324 passes/Ruff) remains authoritative. E025 records reported Linux
review-copy passes with review-only platform/SQLite compatibility changes, plus
adversarial category/total-bound probes and approximately 3.020 s real-monotonic
fallback with one backup/conservative usage. No blocking source defect; no new
native Linux support, real-vendor guarantee or shipped compatibility change.

The latest user instruction authorizes ONE descriptive T4-004 Git checkpoint,
superseding historical no-commit/no-T4-004 gates for this scope only. Preserve
providers.py/service.py, all accepted code/tests/pins and Tasks 1/2 unchanged.
Record acceptance in docs, inspect/stage only approved T4-004 files, exclude
DB/WAL/environments/cache/credentials/review archives, run staged whitespace check,
commit once and verify SHA/clean tree/ahead-behind. No tests/Ruff rerun unless an
unexpected implementation change appears. TASK-4 IN_PROGRESS; T4-005 NOT_STARTED
and not authorized. No push/HTTP/vendor changes/Task 3. Stop after Git checkpoint.

## T4-005 active authorization (2026-11-04 America/Los_Angeles)

Latest user attachment authorizes authenticated FastAPI integration and independent
loopback wire verification over c889236/324 tests. Preserve all accepted components
unless an integration defect is reproduced/documented first; preserve Tasks 1/2.
Document HTTP/auth/config choices, bounded strict input, stable HMAC identity,
trusted adapter bounds, lifecycle and cancellation; no caller token estimates.
Run full native Windows Task 4 suite and Ruff, update evidence and stop for review.
Task 4 dependency/lock additions are isolated. No real vendor/tokenizer claim,
OAuth/distributed infrastructure/Task 3/T4-006, commit or push.

T4-005 outcome: DONE and independently ACCEPTED, user confirmation 2026-11-04.
Read E026/E027 and accepted ADR-020. Reported review: all 427 cases passed across
separate runs, including 29 wire cases in split groups; authentication/quota/
fallback/concurrency/persistence/sanitization reviewed, no blocking source defect.
Linux used review-only compatibility substitutions. One COMBINED Linux wire run
STALLED in fixture teardown, not a completed all-at-once pass. Do not infer native
Linux support or ship review substitutions. E026 native Windows/Python 3.12.16/
SQLite 3.53.1 full 427-pass result remains authoritative; no new test execution.

Latest authorization permits ONE descriptive T4-005 Git checkpoint, superseding
historical no-commit gates for this scope only. Preserve all approved production
code/tests/configuration/lock and Tasks 1/2. Stage only approved HTTP source/tests/
support/config/lock/README/governance; exclude envs/DB/WAL/caches/credentials/review
archives. Inspect full diff/index, run git diff --cached --check, commit once,
verify SHA/clean tree/ahead-behind and stop. No test/Ruff rerun absent unexpected
implementation changes; no T4-006, Task 3, feature work or push. TASK-4 IN_PROGRESS.
