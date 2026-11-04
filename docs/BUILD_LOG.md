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
