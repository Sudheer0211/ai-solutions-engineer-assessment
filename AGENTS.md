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
Use those IDs in implementation/test documentation and milestone entries.

Keep changes scoped; preserve Git history as the code audit trail. Do not
duplicate line-level diffs in Markdown. Do not rewrite existing history.

## Task 2 checkpoint restart gate

Read `docs/TASK2_REQUIREMENTS.md`, `task2/CONTRACT.md`, ADR-008 through ADR-014,
and E008/E009/E011/E012/E013/E014/E015/E016.
T2-001/T2-002, including the Decimal correction, were independently reviewed and
accepted as confirmed by the user on 2026-11-04. Task 2 remains IN_PROGRESS.
Foundation baseline: e828729b; accepted T2-003 adapter baseline: 0b2e0b7.
T2-004 FastAPI/ASGI integration is independently ACCEPTED, confirmed by the user
on 2026-11-04 (400 tests and additional zero-upstream rejection probes). E013
contains local execution evidence; E014 records reported review and Git inspection.
Accepted T2-004 baseline: be9ddd8. T2-005 is independently ACCEPTED, confirmed by
the user on 2026-11-04: 400 prior/52 wire passes, 33 zero-forwarding cases and
12 reaped children without forced cleanup. E015 is local evidence; E016 records
reported independent acceptance and Git inspection. One T2-005 commit authorized;
no push or T2-006 work.
Preserve the accepted guard behavior and Task 1 implementation/tests/root pins.
T2-003 is verified in E011 (300 Task 2 passes and Ruff); E012 records acceptance
and commit inspection. Preserve all accepted implementation/components/tests.
Future production corrections require authorization and a documented reproduction.
Do not start T2-006 or Tasks 3/4, or push without authorization.

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
