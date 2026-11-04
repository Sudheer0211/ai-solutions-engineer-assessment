# Build log

Entries use America/Los_Angeles dates and stable task IDs. Record milestones,
investigations and material changes; Git remains the line-level code history.

## 2026-11-02 — M001: Scope and environment inspection (GOV-001, T1-001)

- Read the supplied assessment brief and governance request before implementation.
- Confirmed workspace root is not a Git repository. User selected the new
  `Projects/ai-solutions-engineer-assessment` directory.
- Initial runtime: Python 3.11.1; launcher also lists Anaconda 3.9; no 3.12.
  Pydantic 2.12.5 and pytest 8.4.2 exist globally; MCP/Ruff absent.
- Initial registry probe could not find `mcp`; cause not yet established.
- Changes/affected files: AGENTS.md; docs/TASK_LEDGER.md, DECISIONS.md,
  BUILD_LOG.md, TEST_EVIDENCE.md. Source snapshot to be copied next.
- Decisions: ADR-001 and ADR-002. No application code implemented yet.
- Unresolved: Python 3.12/SDK availability; no executable compliance tests run.
- Next: Verify governance files/source snapshot, initialize isolated Git repo,
  then investigate T1-001. Preserve Tasks 2–4 unchanged.

## 2026-11-02 — M002: Governance established before implementation (GOV-001)

- Verified all five requested documents are present and nonempty; copied the
  assessment brief byte-for-byte to docs/TASK1_REQUIREMENTS.txt (E002).
- Initialized a new local Git repository; no commits or remote configured.
- Affected files: governance records, source snapshot, .gitignore (local runtime,
  dependency environments, caches and secrets excluded).
- GOV-001 is DONE; TASK-1/T1-001 now IN_PROGRESS, before application code.
- Investigation: PIP_NO_INDEX is set in the inherited environment, explaining
  why passing an index URL alone did not enable package discovery.
- Unresolved: Python 3.12/SDK setup; no application tests have run.
- Next: Use process-local registry settings and a repository-local runtime.

## 2026-11-02 — M003: Runtime and initial implementation (T1-001–T1-004)

- Installed uv 0.13.7 under .tools; Python 3.12.16 under .runtime; MCP 2.3.0,
  Pydantic 2.12.5 and test/lint tools in .venv. See E003.
- Inspected versioned official docs, public signatures and installed SDK source.
- Implemented model-derived schemas, mock domain, Decimal updates, explicit
  protocol/business boundaries and SDK-only STDIO entry point.
- Affected files: .python-version, pyproject.toml, task1/*.py, governance records.
- Decisions: ADR-003 and ADR-004; GOV-001 already complete before source creation.
- Unresolved: No implementation tests yet; malformed-frame behavior must be
  demonstrated. Task 1 criteria remain unchecked until actual verification.
- Next: Add unit, SDK integration and subprocess wire tests and run them.

## 2026-11-02 — M004: Verification and compatibility investigation (T1-002–006)

- First unit/integration run: 78 passed, 1 failed. A real schema parity test
  found the union-level gt constraint was not emitted as exclusiveMinimum.
  Moved the bound to each numeric branch; schema and runtime now agree.
- Added true subprocess tests alongside in-process SDK integration. Initial
  full run: 88 passed, 2 failed, 4 xfailed. Both failures were sandbox-denied
  Windows named pipes in the official async STDIO client; rerun outside the
  sandbox: 90 passed, 4 xfailed. No application workaround or SDK patch added.
- Ruff initially found one long line and six files needing formatting; formatter
  applied and lint then passed. Full transitive uv.lock generated and sync verified.
- Affected files: task1/schemas.py, task1/repository.py (format), tests/*.py,
  pyproject.toml, uv.lock, governance records.
- Confirmed B3: SDK 2.3.0 silently drops malformed JSON/envelopes in both eras.
  Four strict xfail diagnostics retain the unmet -32700/-32600 requirements;
  successful subsequent tools/list proves the connection remains usable.
- Unresolved: B3 prevents TASK-1 completion; --runxfail proof and final README
  remain. Added nonfinite wire cases for a final targeted boundary verification.
- Next: Execute strict diagnostics and final checks, document matrix/setup,
  update all statuses without treating expected failures as compliance.

## 2026-11-02 — M005: Recoverable session handoff (GOV-001, TASK-1, T1-001–006)

- Final regression suite: 94 passed, 4 xfailed, no skips. Strict diagnostics:
  4 failed, 94 deselected, all caused by missing SDK error responses (E005).
- Lint and formatting pass. Locked environment sync and dependency compatibility
  pass. Setup commands/module and console entry points verified on Windows.
- Added README with exact versions, setup/startup/test commands, samples, final
  tree, error matrix, lifecycle/dispatch, STDIO isolation and state explanation.
- Affected files: all new project files listed in README's project tree;
  ignored local environments/caches excluded. No existing source history was
  overwritten; Git initialized locally, with no commits or remote yet.
- Decisions: ADR-005 preserves SDK limitation as explicit strict diagnostics;
  ADR-001–004 remain accepted. No changes to Tasks 2–4 requirements.
- Completed IDs: GOV-001, T1-001, T1-002, T1-004, T1-006.
- Remaining: TASK-1, T1-003 and T1-005 BLOCKED by B3; A7/A12/A13 not complete.
- Recovery: read AGENTS.md and ledger; inspect Git status; use README's local
  locked setup; run strict probes before changing any status.
- Next recommended implementation step: identify and verify an official SDK
  public transport fix/release for -32700/-32600 with request-ID handling, then
  rerun the four --runxfail probes and full suite. Keep task requirements intact.

## 2026-11-03 — M006: Read-only blocker research (T1-007, TASK-1)

- User requested research/source inspection and a recommendation before any
  implementation. Read AGENTS.md/ledger and inspected Git status first. Existing
  manual_refund_lab.py/manual_validation_lab.py are user files and were preserved.
- Captured SHA256 baselines for 18 application/test/config/requirements/manual-lab
  files; final recomputation matched all 18. No code, test or dependency changes.
- Inspected installed STDIO reader, runner, dispatcher, public signatures and
  AnyIO file wrappers; researched official release listings, main source,
  API/migration docs, JSON-RPC errors and modern STDIO cancellation.
- Findings: latest checked release remains 2.3.0; observer exists but Server.run
  cannot accept it; server middleware is downstream of wire decoding. Two valid
  IDs yielded identical error details, proving exception-only recovery is lossy.
  Also observed invalid boolean ID accepted as a notification by the SDK adapter.
- Existing full suite rerun: 94 passed, 4 xfailed in 20.40s. Original strict
  diagnostic rerun: 4 failed, 94 deselected in 4.38s. See E006; B3 remains OPEN.
- Compared A/B/C; proposed raw-input observation/error composition through public
  interfaces, retaining the SDK's default stdout writer and dual-era runner.
  ADR-006 is PROPOSED; no implementation decision has been executed.
- Affected files: docs/STDIO_BLOCKER_INVESTIGATION.md (new), TASK_LEDGER.md,
  DECISIONS.md, BUILD_LOG.md, TEST_EVIDENCE.md. No Tasks 2-4 changes.
- Unresolved: no verified transport remedy; lifecycle-independent raw correlation,
  cancellation/backpressure/shutdown and assessment interpretation need verification.
- Final checks: five changed documentation files are valid nonempty UTF-8, have
  no trailing whitespace, and preserve TASK-1 BLOCKED and Tasks 2-4 registry rows.
  Exact runtime reconfirmed: Python 3.12.16 / MCP 2.3.0 / Pydantic 2.12.5.
- T1-007 DONE for research acceptance R1-R5 only. TASK-1/T1-003/T1-005 remain
  BLOCKED; no architecture change adopted. Other completed IDs are historical.
- Next: review ADR-006 and the report's candidate. Implementation proceeds after
  a subsequent request authorizes code changes; retain the four XFAIL cases and
  use --runxfail for successful remediation acceptance. Keep TASK-1 BLOCKED until
  all mandatory criteria have actual passing evidence.

## 2026-11-03 — M007: Controlled implementation baseline (T1-008)

- Read all five requested governance/investigation/evidence files and inspected
  the current untracked repository. User explicitly authorized Approach C.
- Before editing, staged the existing project and user manual labs and created
  root baseline commit dfb329b9e91620b3075710bb2466c11ba8703936. Git status clean.
  No discarded changes; ignored runtimes/caches not committed.
- Recorded C1-C7 before implementation. TASK-1 remains BLOCKED pending evidence.
- Next: implement a bounded input observer and receive filter around official
  stdio_server(stdin=...) and unchanged Server.run; retain all original tests.

## 2026-11-03 — M008: Prototype and first verification (T1-008)

- Added task1/stdio_boundary.py: public AsyncFile input observation, fail-closed
  two-line capture, receive decoration and SDK error emission. __main__.py still
  calls Server.run; stdio_server retains its default stdout writer/descriptor claim.
- Original four diagnostic cases: 4 passed under --runxfail in 6.12s. Original
  ordinary suite: 94 passed, 4 deselected in 18.81s. Original test bodies unchanged.
- Added 49 boundary/unit/wire tests and test-only public method fixtures. First
  new-test run: 45 passed, 4 failed, 1 warning in 35.57s. Failures involved modern
  SDK result metadata in fixture assertions, child-output fixture stalls, and an
  unsupported no-response assumption for pending-work EOF. Broken-pipe test also
  started a Python communicate reader on an already closed stdout.
- Correcting new fixtures to respect SDK-owned modern metadata and EOF behavior;
  child gets DEVNULL stdin and a timeout; closed-output test avoids a second reader.
  Explicit notification-cancellation still requires no response for the cancelled ID.
- Affected files: boundary module, entry point, new tests/fixture, optional module
  selection in tests/wire_support.py, documentation. Tools/schemas/dependencies intact.
- No original-suite regression observed; rollback condition has not occurred.
- Next: rerun new tests, investigate any remaining failures, then run full
  --runxfail before the separately authorized obsolete-decorator cleanup.

## 2026-11-03 — M009: All assertions pass; separate decorator cleanup (T1-008)

- New tests passed 49/49 after fixture fixes. Added two further malformed-method
  union-fallback cases; all original and new assertions then passed together:
  149 passed in 37.19s under --runxfail, with original test_wire.py byte-identical.
- SDK source integrity: all 124 installed MCP 2.3.0 Python files match wheel RECORD.
- Checkpointed implementation/new tests in 7b0c79fdda6949e9a18a8919910ae58e9d04360f.
- In a separate cleanup step, removed only the obsolete parametrized XFAIL
  decorator. Byte comparison proves all four original test bodies/assertions intact.
- Ruff lint/format passed, 17 files formatted. Normal final suite is running;
  no claim of final completion until its result and documentation checks are recorded.
- Next: record normal-suite outcome, adopt ADR-006 if verified, update README,
  investigation report and all acceptance criteria. Rollback not triggered: no
  original ordinary-test regression occurred.

## 2026-11-03 — M010: Verified adoption and final handoff (TASK-1, T1-008)

- Normal suite after separate obsolete-decorator cleanup: 149 passed in 39.94s,
  no failures/skips/XFAIL/XPASS. Earlier full --runxfail: 149 passed in 37.19s.
- Cleanup committed independently as 93a861f7bfd6f49bf40a882753aa376ac4662d0f,
  exactly one decorator-line deletion. Original four bodies/assertions intact.
- ADR-006 adopted; ADR-007 records user-authorized cleanup and supersedes the
  old retained-XFAIL policy for the now-fixed cases. SDK/tool/schema/pin/manual-lab
  changes remain excluded. No existing-suite regression; no rollback needed.
- Updated README, ledger, decisions, evidence and preserved investigation report
  with actual counts, error matrix, acceptance mapping, adoption and limitations.
- All mandatory A1-A15 and controlled criteria C1-C7 verified in E007.
  Completed this implementation: TASK-1, T1-003, T1-005, T1-008.
- Remaining blockers: none for Task 1. Limits: Windows verified; pin/retest SDK
  input correlation on upgrades; explicit stdin skips fd0 diversion while keeping
  stdout protection; frame count is not byte-size limiting; SDK UTF-8/nonfinite
  behavior preserved; broken pipes may exit nonzero within the tested bound.
- Recovery: baseline dfb329b; implementation 7b0c79f; cleanup 93a861f. Read
  AGENTS.md and ledger, inspect Git status, and run the documented normal suite.
- Next recommended step: adopt/review this assessed implementation. Before an
  SDK upgrade rerun all boundary tests. Tasks 2-4 await independent requirements.

## 2026-11-04 — M011: Task 2 first checkpoint baseline (T2-001, T2-002)

- Read repository instructions/ledger, current dependency configuration and
  prior evidence. Git clean at 6056bc7; no commit or push authorized.
- Captured hashes of 31 tracked files and exact historical governance prefixes
  before changes. Task 1 source/tests/root dependencies/lockfile are protected.
- Recorded supplied Task 2 requirements in docs/TASK2_REQUIREMENTS.md and exact
  checkpoint criteria/implementation choices in task2/CONTRACT.md before code.
- Created isolated task2 project configuration and standard-library pure modules
  for explicit token loading, Bearer authentication, strict RPC inspection and
  ordered authorization permits. No endpoint or network client implemented.
- Choices: exact denial message/code; reject batches wholly; inspect/authorize
  notifications then reject without RPC reply/permit; retain immutable raw body;
  no default credentials; independent environment; FastAPI/HTTPX deferred until used.
- Affected files: task2 project; new requirement snapshot; ledger; appended records.
- Unresolved: tests/environment/lint not yet executed; full HTTP Task 2 remains
  incomplete. Next: focused boundary/bypass tests, isolated install, actual checks.

## 2026-11-04 — M012: Task 2 guard checkpoint verification (T2-001, T2-002)

- Implemented isolated settings.py/security.py/rpc.py and 156 focused unit cases.
  Exact authorization denial is -32001 / Unauthorized Tool Call with applicable ID.
  No role is sourced from request content; duplicate/escaped key/name cases fail
  safely. Batches and notifications cannot become permits under this checkpoint.
- Initial suite: 156 passed with one sandbox pytest-cache warning. Precreated
  ignored cache directories; final suite: 156 passed in 0.17s with no warnings,
  skips, xfails or failures. Ruff lint/format pass (9 files). Evidence: E008.
- Created task2/.venv and independent lock; Python 3.12.16, pytest 9.2.0,
  Ruff 0.17.3. Locked offline sync and dependency consistency checks pass.
- Affected files: task2 project/source/tests/contract/README; supplied requirement
  snapshot; Task 2 ledger rows; append-only decisions/build/test evidence records.
- Architecture: ADR-008 isolation and ADR-009 strict transport-neutral guard policy.
  Approved FastAPI/HTTPX architecture deferred until used by the HTTP checkpoint.
- Unresolved for later review: HTTP path/status/challenge/notification reporting,
  upstream credentials/headers, limits, failure mapping and transparent forwarding.
  These are not implemented and do not block the authorized pure-guard checkpoint.
- Next: finish preservation/status checks, then stop for independent review.
  Whole TASK-2 remains IN_PROGRESS; no HTTP/wire completion claim or commit/push.

## 2026-11-04 — M013: Checkpoint handoff (T2-001, T2-002)

- Preservation checks passed: 27 non-governance tracked files byte-identical;
  all historical Task 1 decisions/build/test evidence prefixes and acceptance
  criteria unchanged; TASK-1/3/4 rows and Git HEAD unchanged. No commit/push.
- T2-001/T2-002 DONE with T2-C1-T2-C9 verified in E008. TASK-2 remains IN_PROGRESS;
  the authorized checkpoint has no unresolved implementation blocker.
- Created: task2 isolated config/lock/contract/README, four runtime package files
  and five focused test/fixture files; docs/TASK2_REQUIREMENTS.md. Modified only
  four existing governance files for Task 2 status and appended evidence/decisions.
- Decisions ADR-008/009; no HTTP endpoint, HTTPX client or forwarding module.
- Next recommended step: independent review of contract choices and guard API,
  particularly notification reporting/ID policy, before authorizing T2-003.
  Stop here; HTTP integration and Tasks 3/4 are not part of this checkpoint.

## 2026-11-04 — M014: Compaction context handoff (T2-001, T2-002)

- Verified AGENTS, ledger, decisions, build log and test evidence against the
  current checkpoint. E008 already contains the actual 156-pass/Ruff results;
  E007 preserves Task 1's prior 149-pass verification. No additional tests run.
- Essential documentation correction: distinguish implemented/unit-verified
  T2-001/T2-002 from still-PENDING independent ChatGPT engineering review.
  Added restart gate/source pointers to AGENTS and a self-contained ledger
  handoff; clarified ADR-009 review status. Test evidence left unchanged.
- Recorded architecture, security invariants, deferred contract decisions and
  T2-003 as a future checkpoint requiring review and new user authorization.
- Git: HEAD 6056bc7; five unstaged governance documents, untracked Task 2
  requirement snapshot and 14 task2 project files; nothing staged. No commit/push.
- Affected during this handoff: AGENTS.md, TASK_LEDGER.md, DECISIONS.md and
  BUILD_LOG.md only. No source/tests/dependencies/config changes; Task 1 preserved.
- Next: independent ChatGPT review of task2/CONTRACT.md and guard implementation.
  Stop; do not execute tests or begin HTTP forwarding/T2-003 during handoff.

## 2026-11-04 — M015: Independent-review numeric parser correction (T2-002)

- Reproduced review input on pinned Python 3.12.16: inspect_request leaked
  decimal.InvalidOperation for an enormous exponent in an opaque extension.
  Positive/negative exponents and zero coefficients exceeded Decimal's range.
- Applied targeted Decimal conversion helper: reject nonfinite fallback values;
  contain the DecimalException family alongside existing parse failures. Policy:
  -32700 / Parse error, null ID, no partial envelope recovery or forwarding permit.
- Added 30 regressions: unrepresentable values in arguments/extensions/IDs,
  enabled/disabled InvalidOperation traps, and representable raw-byte preservation.
- Actual checks: 186 passed in 0.15s; Ruff lint passes; format check reports
  9 files already formatted. No failing tests/checks in this correction run.
- Affected: task2/src/task2_proxy/rpc.py, task2/tests/test_rpc.py; parser policy in
  task2/CONTRACT.md; ledger, ADR-010, build log and test evidence E009.
- Task 1 remains untouched. No endpoint/forwarding, dependency changes, commit
  or push. Independent re-verification remains pending; next: review this fix,
  then obtain explicit authorization before any T2-003 work.

## 2026-11-04 — M016: Independent acceptance and commit preparation (T2-001/T2-002)

- User confirms independent engineering acceptance of both foundation tasks,
  including the Decimal correction. Recorded acceptance in the ledger, current
  restart gate, ADR-009/010, contract and Task 2 README. T2-003 remains NOT_STARTED.
- User authorizes one foundation commit; no push or HTTP implementation.
  Existing E009 evidence remains 186 passes and both Ruff checks passing;
  no tests rerun during this documentation/staging/commit checkpoint.
- Initial Git inventory: five modified governance files, fifteen untracked
  Task 2 foundation/requirement files and task2_review.zip; index empty.
- Commit scope: Task 2 config/lock/source/tests/docs and relevant governance.
  Exclude local environments/caches/credentials/review ZIP; preserve Task 1.
- Next: inspect the exact staged allowlist/diff, create the authorized foundation
  commit, verify its contents/status, then stop pending T2-003 authorization.
- Staging inspection complete (E010): 20 authorized files only; no unexpected
  paths, whitespace errors or targeted credential-pattern matches. Reviewed code,
  tests and lockfile remain byte-identical; Task 1 preserved. Local-only Git
  exclusions keep review exports and credential reports out of staging, alongside
  existing environment/cache exclusions. Proceed with the one authorized commit.
