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

## T4-006 current audit authorization (2026-11-04 America/Los_Angeles)

Latest user authorizes final verification/documentation only over 6eaccaf. Fresh
complete Task 1/2/4 pytest and Ruff in separate environments, clean Task 4 locked
installation, traceability, recovery/routing/HTTP/source/history security audit.
Preserve accepted production code/tests/config/locks. Documentation corrections
allowed; reproduce/document any blocking implementation defect and stop. No Task 3,
feature work, commit/push, or T4-006/TASK-4 DONE before independent approval.

T4-006 local outcome: audit complete, READY within documented scope, independent
approval PENDING. Read TASK4_FINAL_AUDIT.md, ADR-021 and E028. Fresh native suites
149/452/427 pass; six Ruff checks pass, new locked Task 4 install and deterministic
primary/fallback fixtures plus stock CLI 503 verified. No accepted code/test/config/
lock changes; Task 1/2 DONE preserved. Crash/power/disk/remote billing and real
vendor/tokenizer/deployment limitations explicit. T4-006/TASK-4 IN_PROGRESS; next
is independent review, no feature work/stage/commit/push or automatic DONE claim.

## T4-006 final acceptance / Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user confirms independent ChatGPT engineering APPROVAL: Task 4 is
assessment-ready within documented requirements, supported Windows/SQLite and
trusted-adapter policies. TASK-4/T4-006 DONE; all seven traceability rows, named
test references, E028 results, docs, limitations and submission findings reviewed
and consistent. Read final audit, E029 and ADR-021 acceptance provenance. Preserve
E028 actual 2026-11-04 executions and all historical review/environment qualifications;
no new test result or native Linux/real-provider/deployment guarantee is inferred.

Supersedes historical pending/no-commit gates only for ONE final docs-only commit:
AGENTS.md, root/Task 4 README, TASK4_FINAL_AUDIT.md, TASK4_REQUIREMENTS.md, ledger,
build log, decisions and test evidence. Preserve all source/tests/configuration/
dependencies/locks and Tasks 1/2. Inspect complete diff/new audit/exact staged
inventory, exclude envs/caches/DB/WAL/SHM/credentials/generated artifacts/review ZIPs,
run git diff --cached --check, commit once and verify SHA/manifest/clean tree/
ahead-behind. No tests/Ruff/install unless unexpected code/config changes found.
No Task 3, push or further implementation; stop after reporting Git checkpoint.

## T3-001 current design authorization (2026-11-05 America/Los_Angeles)

Latest user authorizes documentation/design only for Task 3, superseding historical
no-Task-3 gates ONLY for this scope. Tasks 1/2/4 remain DONE; preserve their code,
tests/dependencies/configuration/locks and acceptance/environment evidence.
Architecture is independently APPROVED CONDITIONALLY: isolated FastAPI/HTTPX,
explicit SSE parser, per-channel incremental redactor, bounded memory, pull-driven
backpressure and owned cancellation. Exact contract is NOT approved yet.

Read docs/TASK3_REQUIREMENTS.md, ADR-022, E030 and ledger. Original Task 3 brief
unavailable after repeat bounded search; only high-level user requirements T3-R1-R8
are available. T3-P1-P8/T3-L/T3-Q are PROVISIONAL proposals, including narrow ASCII
email/phone/SSN rules, conservative whole-candidate masking, synthetic JSON-over-SSE
profile, dropped metadata, limits and strict errors. Do not present them as original
assessment wording or universal PII protection. Independent approval required.

T3-001/TASK-3 IN_PROGRESS; T3-002 through T3-006 NOT_STARTED. Do not create source,
task3 project/env/lock, install dependencies, run implementation tests, commit/push
or begin T3-002. Allowed files this checkpoint: requirements and relevant AGENTS/
ledger/decisions/build/evidence documentation only. Stop after contract presentation
for independent approval; later source work needs explicit implementation authority.

## T3-002 active authorization (2026-11-05 America/Los_Angeles)

Latest user independently APPROVES T3-001 for the documented synthetic profile and
authorizes isolated T3-002 models/SSE/payload/redaction pure code, tests, pins/env/lock.
Read approved TASK3_REQUIREMENTS and ADR-022/023. Preserve candidate alphabet,
256-char withholding/overflow rule, four channels, valid-done finalization, strict
termination/duplicate keys and separate byte/scalar/encoded limits. Never claim
universal PII or vendor interoperability; original vendor brief remains unavailable.
Run complete new Task 3 pytest and both Ruff checks, record actual results and stop
for independent review. Preserve Tasks 1/2/4. No HTTPX/network/upstream/service,
FastAPI endpoints/wire/final-audit/T3-003, commit or push. This authorization
supersedes historical no-source/no-install gates only for this checkpoint.

T3-002 local outcome: implemented/verified, independent review PENDING. E031 native
362 passes/zero failures/skips/warnings/xfails and both Ruff checks (11 files);
Python 3.12.16, isolated eight-package lock, stdlib-only runtime. Preserve new
verified code/tests and completed Task 1/2/4 baseline. T3-001 DONE/accepted;
T3-002/TASK-3 IN_PROGRESS, T3-003 NOT_STARTED. Read task3/README.md and ADR-023.
Pure counters/iterators are not actual async transport/backpressure/RSS evidence.
Original vendor brief still unavailable. Stop for review; no commit/push/network.

## T3-002 independent acceptance / Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user APPROVES T3-002; DONE/independently accepted. Read E032 and ADR-023
provenance: reported 362 passes plus 1200 randomized interleaved streams, 2961
channel-reference comparisons, 256 prefix/257-overflow probes, 376 truncated-wire
cuts, 24000-event retained state and compilation; no blocking production defect.
Review Linux/Python 3.13.5/pytest 9.0.2 had one configuration warning; warning
details not provided. Native Windows/Python 3.12.16 E031 tests/Ruff authoritative;
do not widen Python pins or claim new runtime/vendor/universal PII support.

One descriptive T3-001/T3-002 accepted foundation commit authorized, superseding
historical no-commit gates only for this checkpoint. Preserve all 11 approved
Python files, pins/config/lock and Tasks 1/2/4. Update acceptance docs, inspect full
diff/new files/index, stage exact approved Task 3 foundation and related governance
only, exclude env/cache/pycache/egg-info/temp/credentials/review ZIP. Run staged
whitespace check, commit once, verify SHA/inventory/clean tree/ahead-behind and stop.
No tests/Ruff/install rerun unless unexpected implementation changes are found.
TASK-3 IN_PROGRESS; T3-003 NOT_STARTED/not authorized. No push or further code.

## T3-003 active authorization (2026-11-05 America/Los_Angeles)

Latest attachment authorizes upstream.py/service.py and necessary typed interfaces/
tests/isolated HTTPX pins/lock only. Integrate accepted Processor over 0a75587;
preserve all 11 accepted Python files/362 tests and completed Tasks 1/2/4. Any
pure correction requires a concrete reproduced/documented integration defect first.
Owned pooled HTTPX, trusted destination/credentials, no retry/redirect/decompression,
4 KiB processing, pull-driven reads, 5 s pool/connect/write, 15 s first-valid/read
idle, 120 s monotonic overall, one 1 s cleanup grace, immediate 16/process cap.
Retain/quarantine uncertain cleanup. Run complete Task 3 suite and both Ruff checks,
document actual progressive/read-count/cancel/deadline evidence and stop for review.
No FastAPI/public HTTP/T3-004, wire harness/T3-005, final audit/T3-006, vendor APIs,
persist/resume, commit or push. Actual downstream-send 10 s enforcement is deferred
to T3-004; an async generator is not proof of socket-send completion.

T3-003 local outcome: implemented/verified, independent acceptance PENDING. E033
native 457 passes (362 unchanged pure +95 async), no failures/skips/warnings/xfails;
Ruff lint/format pass (17 files), HTTPX 0.28.1/httpcore 1.0.9, 15-package lock.
ADR-024 documents direct public raw-stream ownership, 64 KiB transport/4 KiB slices,
first-valid/overall watchdogs and fixed quarantine policy. Preserve all tested code
and T3-002 baseline. No actual socket send/wire/RSS/vendor certification. T3-003 /
TASK-3 IN_PROGRESS; next independent review, not T3-004 or commit/push.

## T3-003 independent acceptance / Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user independently APPROVES T3-003; DONE. Read E034 and ADR-024 acceptance
provenance: reported 457 suite passes, 240 additional randomized HTTPX fragmentation
cases, resistant-cancellation ownership/quarantine/confirmed release, concurrent
shutdown blocking admission/one shared close, 11 pure files byte-identical and
compilation pass; no blocking defect. Linux/Python 3.13.5 review recorded one
nonfatal pytest configuration warning, details not supplied. Native Windows/
Python 3.12.16 E033 and Ruff authoritative; no real socket/ASGI claims or pin changes.

One descriptive T3-003 acceptance commit authorized, superseding historical
no-commit/pending gates only for this checkpoint. Preserve all 17 verified Python
files, approved dependencies/lock and Tasks 1/2/4. Record review, inspect full diff/
new files/index, stage exact approved source/tests/dependency/lock/README/governance,
exclude env/cache/pycache/egg-info/credentials/review archives (retain locally),
run git diff --cached --check, commit once, verify SHA/inventory/clean tree/branch
counts and stop. No test/Ruff rerun absent unexpected functional change. TASK-3
IN_PROGRESS; T3-004 NOT_STARTED/not authorized. No push or further implementation.

## T3-004 active authorization (2026-11-05 America/Los_Angeles)

Latest supplied attachment authorizes app.py/narrow HTTP settings and deterministic
ASGI integration tests over e4bd001/457 accepted tests. Preserve pure/upstream/service
source and accepted tests unless an integration defect is reproduced/documented.
Strict bounded synthetic POST /stream, separate operator Bearer, FastAPI lifespan,
preflight before headers, pull-driven actual ASGI sends under min(10s, remaining
120s overall), one additional 1s cleanup, disconnect monitoring AFTER body read,
immediate process cap16 including blocked HTTP sends, retained/quarantined uncertain
ownership. Run native full Task 3 pytest/Ruff; record actual results and stop for
independent review. No real wire/T3-005, final audit, vendor/deployment/resume,
Tasks 1/2/4 changes, commit or push. Supersedes historical no-T3-004 gates only.

T3-004 local outcome: verified/independent review PENDING. E035 final native
Windows/Python 3.12.16: 580 passed (457 unchanged +123 new), zero failures/skips/
warnings/xfails, Ruff lint/format pass (22 Python files). Read T3-H1-H9, ADR-025 and
task3/README.md. New app/settings/direct ASGI tests only; isolated FastAPI/optional
Uvicorn additions/25-package lock. Original 17 Python files and Tasks 1/2/4 unchanged.
POST /stream strict prompt/operator Bearer, preflight before 200, bounded ASGI sends,
separate process-global HTTP cap16, retained/quarantined uncertain cleanup. No real
socket/send-ack/RSS/vendor certification. No tests after final source verification
unless new changes/concerns; docs-only handoff. T3-004/TASK-3 IN_PROGRESS; next is
independent review, not T3-005 or staging/commit/push.

## T3-004 independent acceptance / Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user independently APPROVES T3-004; DONE. Read E036/ADR-025 acceptance
provenance: reported580 suite passes,180 randomized interleaved two-channel ASGI
scenarios/4613 upstream reads, five fail-closed scenarios, all17 prior Python files
unchanged, no blocking source defect. Linux/Python3.13.5 review recorded one
nonfatal pytest configuration warning, details not supplied; native Windows/
Python3.12.16 E035 tests/Ruff authoritative. Real sockets/RSS remain unverified,
original brief unavailable; no pin widening/vendor/universal privacy claim.

One descriptive T3-004 acceptance commit authorized, superseding historical
pending/no-commit gates only for this checkpoint. Preserve all22 verified Python
files, approved config/dependencies/lock and Tasks1/2/4. Record review in docs,
inspect full diff/new files/index, stage exact approved source/tests/config/lock/
READMEs/governance only, retain/exclude env/cache/pycache/egg-info/credentials/
databases/review ZIPs. Run git diff --cached --check, commit once, verify full SHA/
manifest/clean tree/recorded-origin counts and stop. No tests/Ruff/install rerun
absent unexpected functional change. TASK-3 IN_PROGRESS; T3-005 NOT_STARTED/not
authorized. No push or further implementation.

## T3-005 active authorization (2026-11-05 America/Los_Angeles)

Latest attachment authorizes independent-process loopback HTTP wire harness/tests
only over ecbd61c/580 accepted tests. Read Q19-Q21/T3-H/ADR-022/024/025; preserve
all accepted production/tests/dependencies and Tasks1/2/4. Record/reproduce any
wire-level defect before a narrow correction. Real provider/proxy processes with
dynamic child-bound ports, explicit gates/readiness, bounded deadlines/cleanup,
sanitized metrics/journals and tracked child exit receipts. Native full Task3
pytest and both Ruff checks; report measured progression/read/send/RSS separately
from formal bounds/kernel guarantees. Keep exact10/120 boundaries in accepted
deterministic tests; no repeated long boundary waits. No vendor/deployment/resume/
T3-006, commit/push or independent-acceptance claim. Stop for review.

T3-005 local outcome: native E037: 637 passes (580 unchanged +57 new wire), zero
failures/skips/warnings/xfails; Ruff lint/format25 pass. Read ADR-026/T3-W1-W8 and
Task3 README. Final-run10 children reaped:9 normal0/1 expected startup2, zero forced/
killed/live reader threads. Three runs total30 children/27 normal/3 expected2.
Actual loopback progression/flow-control counter freeze/native15s timeouts and
Windows working-set observations recorded, NOT exact10s socket-stall/120s real-time
or formal RSS/deployment/vendor guarantees. Accepted22 Python files/580 tests,
source/dependencies/lock and Tasks1/2/4 unchanged; only pytest marker config added.
T3-005/TASK-3 IN_PROGRESS, independent review PENDING. No further test repetitions
absent new changes/concerns; finish docs/integrity handoff, no T3-006/commit/push.

## T3-005 independent acceptance / Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user APPROVES T3-005; DONE, no blocking implementation defect or correction.
Read E038/ADR-026 provenance: reported580 existing passes, all57 wire cases passing
assertions across split executions,40 extra real-socket fragmentation passes,22
prior Python files unchanged; behavior/cleanup reviewed. Linux/Python3.13.5 import-
path change ONLY in extracted review harness. Combined wire run stalled after50
completed cases;19-case split printed passing summary but command did not return
promptly. NEVER label it clean combined637 Linux verification. Native E037 Windows/
Python3.12.16 full637/exit0/Ruff authoritative. Kernel10s expiry/TLS/formal RSS/
real-provider limitations retained, original brief unavailable.

One descriptive T3-005 acceptance commit authorized, superseding historical
pending/no-commit gates for exact approved wire tests/pytest marker/READMEs/
governance only. Preserve all25 verified Python files, dependencies/lock and
Tasks1/2/4; no shipped Linux import shim. Exclude/retain locally env/cache/egg-info/
credentials/review ZIPs/generated receipts, inspect full diff/index, run staged
whitespace check, commit once, verify full SHA/manifest/clean tree/recorded-origin
counts and stop. No tests/Ruff/compile/install rerun absent unexpected functional
change. TASK-3 IN_PROGRESS, T3-006 NOT_STARTED/not authorized; no push or audit.

## T3-006 active audit authorization (2026-11-05 America/Los_Angeles)

Latest user attachment authorizes verification/documentation only over 6b76878.
Read approved Task3 contract/ADRs/evidence and all relevant source/tests. Fresh native
Task1/2/4/3 complete pytest and Ruff in separate environments, clean locked Task3
install and assessor synthetic demo, requirements matrix, privacy/lifecycle/security/
history/whole-repo audit. Preserve all accepted source/tests/dependencies/config/
locks; docs-only corrections allowed. Reproduce/document any blocking defect and
STOP, no feature fix. Original brief unavailable; never infer vendor/universal PII
compliance or clean combined Linux637 run. Retain E038 split-run/import-path/stall
qualifications and kernel10s/TLS/formal RSS/provider limits. No commit/push or
T3-006/TASK-3 DONE until independent acceptance. Stop after report/review handoff.

T3-006 local outcome: READY within approved synthetic/Windows scope, independent
acceptance PENDING; T3-006/TASK-3 IN_PROGRESS. Read docs/TASK3_FINAL_AUDIT.md,
E039 and ADR-027. Fresh native suites149/452/427/637 (1665), all8 Ruff checks0,
zero failures/skips/warnings/xfails; clean locked25-package Task3 install and two
real-TCP synthetic demos passed. Current/reachable-history contextual scan found
no actual disclosure; portable ignore/kernel/RSS/vendor limits retained. All
accepted source/tests/config/dependencies/locks and Tasks1/2/4 preserved. Historical
test evidence/qualified Linux review unchanged. Documentation-only corrections
include stale root Task3 status and a self-contained assessor recipe. Do not rerun
tests absent new functional concerns, stage, commit, push or markDONE; next is
independent final engineering review. No new implementation authorized.


## T3-006 independent acceptance / final Git checkpoint (2026-11-05 America/Los_Angeles)

Latest user independently APPROVES final Task3 audit: T3-006/TASK-3 DONE within
accepted synthetic SSE/PII contract; all four assessment tasks DONE in documented
scopes. Read E040/ADR-027 acceptance provenance and final audit. Reported review:
eight requirements/21 criteria/73 named tests against prior source archive,
symbols/links/demo syntax and E039 consistency; no blocking discrepancy. Review
did not rerun native Windows tests, directly audit unpublished local history or
validate unavailable vendor requirements. E039 native1665/eight Ruff unchanged.
Preserve all production/RSS/TLS/socket/PII/environment qualifications and history.

Supersedes prior pending/no-commit gates only for ONE descriptive final nine-file
documentation acceptance commit. Preserve all accepted source/tests/config/pins/
locks and Tasks1/2/4; do not rerun tests absent unexpected functional change.
Inspect entire diff, explicitly stage AGENTS/root&Task3 READMEs/requirements/
ledger/decisions/build/evidence/new TASK3_FINAL_AUDIT.md; exclude/retain local ZIPs,
cache/env/diagnostics/temporary scripts/DB/WAL/SHM/credentials/generated artifacts.
Run git diff --cached --check, commit once, verify full SHA/inventory/clean status/
recorded-origin counts, then STOP. No push, new feature or future work authorized.


## T3-007 evaluator correction authorization - 2026-11-06 America/Los_Angeles

Latest user authorizes targeted PAN remediation plus Task4 read-only evaluator
audit/docs and fresh native four-task regression/Ruff. Supersedes prior no-source-
change/stop gates for this checkpoint only. Read supplied ignored gap audit at
.cache/evaluator_gap_audit_tasks_3_4.md, requirements/ADR-028 and remediation report.
Recovered high-level categories email/SSN/card; full vendor rubric still unavailable.
No new vendor assumptions. Keep original approvals/evidence; correction IN_PROGRESS /
PENDING INDEPENDENT ACCEPTANCE, not DONE. Preserve Tasks1/2 and ALL Task4 source/
tests/config/dependencies/lock. Task4 README/governance corrections only.

Task3 patch only redaction.py with numeric bridge/PII.PAN; tests/oracle extended.
No generic whitespace alphabet, parser/HTTPX/service/app/harness rewrite or new
runtime dependency. New exact PAN grammar/boundaries/294-per-channel auxiliary
budget are explicit pending-review policies, not recovered evaluator wording.
E041 actual733/427/149/452 (1761) passes/eight Ruff0, new96 PAN cases, focused100
and Task4 existing-fixture demo9 pass. No source changes after final verification.
Keep gap input/receipts/temp scripts/cache/DB/archive ignored. No staging/commit/
push, independent acceptance claim or further feature work. Stop for review.


## T3-007 independent acceptance / Git checkpoint - 2026-11-06 America/Los_Angeles

Latest user APPROVES T3-007 within documented13-19-digit synthetic PAN grammar;
DONE. Read E042/ADR-028 acceptance and remediation report. Reported review659
non-wire/17 PAN wire with review-only Linux subprocess import-path adjustment,
1200 random streams/8812 deltas and withholding/overflow/four-channel probes pass;
no blocking defect. E041 native1761/eight Ruff NOT independently rerun in full.
No shipped review shim or widened vendor/universal PII/RSS/TLS/socket claims.
294/channel/1176 total auxiliary policy and scoped boundaries preserved. Task4
real-provider interoperability stays NOT VERIFIED/rubric-dependent; no new adapter.

Supersedes previous no-commit/pending gates only for ONE descriptive T3-007
acceptance commit. Freeze accepted PAN source/tests/deps/config/lock, Tasks1/2 and
Task4 non-doc files. No tests/install/features. Inspect entire diff, stage only19
approved remediation source/test/doc paths, retain/exclude review ZIP/input MD/
.cache scripts/receipts/env/DB/credentials/generated artifacts, run staged whitespace
check, commit once, verify fullSHA/manifest/clean tree/recorded-origin counts, STOP.
No push or further work authorized. Preserve historical approvals/evidence/limits.
