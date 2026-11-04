# Repository engineering instructions

## Start and end of every session

Read this file and `docs/TASK_LEDGER.md` before development. Inspect Git status,
preserve unrelated changes, and identify the active task's acceptance criteria.
Record its status before implementation. Before ending, update the ledger and
leave an actionable next step, known blockers, and a recoverable working tree.
Report completed task IDs, actual test commands/results, changed files,
architecture decisions, blockers, and the next implementation step.

## Scope and source of truth

`docs/TASK1_REQUIREMENTS.txt` preserves the supplied Task 1 assessment brief.
The user's project governance instructions and this ledger supplement it.
Implement Task 1 only. Do not implement, redefine, or modify Tasks 2–4.
Their requirements have not been supplied. Do not infer them from exclusions.
Use stable IDs: GOV-001, T1-001 through T1-006, TASK-1, TASK-2, TASK-3, TASK-4.
Use those IDs in implementation/test documentation and milestone entries.

## Engineering standards

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
- Keep changes scoped; preserve Git history as the code audit trail. Do not
  duplicate line-level diffs in Markdown. Do not rewrite existing history.

## Required verification

- Use pytest (and pytest-asyncio where useful) for schema/business unit tests,
  SDK integration tests, and actual subprocess STDIO wire tests.
- Cover strict types, missing/extra fields, boundaries, customer lookup, refund
  mutation, insufficient balance and no mutation on failed operations.
- Verify lifecycle, exactly two tools, generated schemas, calls, protocol error
  categories/IDs, business `isError`, stdout purity, stderr diagnostics, shutdown.
- Verify modern and legacy lifecycle connectivity if supported by the SDK.
- Run Ruff. Record the exact command, runtime/version context, exit status,
  actual result counts, failures/skips, and affected task IDs.
- Never invent test results. Inspection, environment probes, diagnostics and
  manual checks must be labeled distinctly from passing automated tests.
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
- Update ledger/build log after each meaningful milestone; record decisions
  when made, including requirement conflicts or compatibility limitations.
- Mark a task DONE only after all its mandatory criteria have evidence.
  Use NOT_STARTED, IN_PROGRESS, BLOCKED, DONE. A blocker records evidence and
  the recommended resolution; a diagnostic pass is not compliance evidence.
- Dates use the user's America/Los_Angeles context; this session is 2026-11-02.
- Never record API keys, bearer tokens, credentials, secrets or sensitive
  customer data in documentation, fixtures, logs or committed artifacts.
