# Persistent task ledger

Last updated: 2026-11-03 (America/Los_Angeles).

## Task registry

| ID | Description | Priority | Status | Acceptance / evidence | Blocker / next action |
| --- | --- | --- | --- | --- | --- |
| GOV-001 | Establish persistent engineering governance before implementation | P0 | DONE | G1-G5 verified in E002 | Maintain records at every milestone |
| TASK-1 | Strict MCP server assessment | P0 | DONE | A1-A15 verified; E007; 149 normal passes | Adopted Approach C; retain pinned boundary regression tests |
| T1-001 | Confirm runtime, SDK/public APIs, dependency versions | P0 | DONE | Python 3.12.16/MCP 2.3.0/Pydantic 2.12.5; E003/E004; uv.lock | Maintain verified pins |
| T1-002 | Strict schemas and mock refund domain | P0 | DONE | Strict schemas, parity and exact mock state verified; E004 | No open domain defect |
| T1-003 | MCP tool dispatch and protocol errors | P0 | DONE | All error codes/IDs and business separation verified; E007 | B3 resolved by SDK-preserving boundary adapter |
| T1-004 | STDIO entry point and diagnostics | P0 | DONE | Module/console startup, wire purity, stderr, EOF shutdown verified; E004 | Retain subprocess regression tests |
| T1-005 | Unit, SDK integration and subprocess wire verification | P0 | DONE | 149 passed under --runxfail and normal execution; E007 | Original diagnostic bodies retained as passing regression tests |
| T1-006 | Reproducibility, lint, README and final evidence | P1 | DONE | Setup/lock and README verified; final lint/format/evidence E007 | Maintain evidence on future changes |
| T1-007 | Read-only STDIO blocker remediation investigation | P0 | DONE | R1-R5 verified; investigation report; E006 | Proposed candidate implemented and verified under T1-008 |
| T1-008 | Controlled Approach C implementation and adoption | P0 | DONE | C1-C7 verified; E007; ADR-006/007 | Adopt; rerun boundary contract tests before any SDK upgrade |
| TASK-2 | Reserved; requirements not supplied | Unspecified | NOT_STARTED | Not defined; do not infer or modify | Await separately supplied requirements and authorization |
| TASK-3 | Reserved; requirements not supplied | Unspecified | NOT_STARTED | Not defined; do not infer or modify | Await separately supplied requirements and authorization |
| TASK-4 | Reserved; requirements not supplied | Unspecified | NOT_STARTED | Not defined; do not infer or modify | Await separately supplied requirements and authorization |

## GOV-001 mandatory acceptance criteria

- [x] G1: Repository-root AGENTS.md includes coding, testing, session and update rules.
- [x] G2: All four requested docs exist with useful initial records and consistent IDs.
- [x] G3: Task 1 criteria and Tasks 2–4 scope protection are recorded before implementation.
- [x] G4: Actual inspection/verification outcomes are recorded without invented tests.
- [x] G5: Source brief preserved; repository location and recovery/next steps documented.

## TASK-1 mandatory acceptance criteria

All mandatory criteria are verified. Final evidence: E007 in TEST_EVIDENCE.md,
supplementing E003-E005 environment/domain evidence. All 149 assertions pass
normally after controlled removal of only the obsolete XFAIL decorator.

- [x] A1: Server starts successfully with Python 3.12.
- [x] A2: Official MCP SDK and Pydantic v2 used with tested version pins/public APIs.
- [x] A3: Exactly `get_customer_record` and `trigger_refund` discoverable.
- [x] A4: Both tools succeed with valid inputs and advertise model-derived schemas.
- [x] A5: Strict Pydantic validation, ASCII ID format, finite positive numbers,
  reason minimum length/nonblank, missing/null/extra/type rejection verified.
- [x] A6: Invalid tool arguments and unknown tool names yield JSON-RPC -32602.
- [x] A7: Parse -32700, request -32600, method -32601, internal -32603 and
  applicable request IDs verified; business failures use `isError=true`.
- [x] A8: At least three synthetic records, deterministic refund IDs, Decimal
  balances and process-local transaction state verified.
- [x] A9: Validation/business failures never mutate balances or transactions.
- [x] A10: stdout contains only valid newline-delimited MCP JSON-RPC messages.
- [x] A11: stderr receives startup/shutdown, execution and failure diagnostics.
- [x] A12: Actual subprocess STDIO/lifecycle/isolation/termination tests pass;
  supported modern and legacy lifecycle behavior is verified.
- [x] A13: Required unit and SDK integration suite passes; all errors/IDs covered.
- [x] A14: Ruff passes; installation/startup commands work from documented cwd.
- [x] A15: README covers setup, examples, limitations and state lifecycle;
  final report includes tree, versions, matrix, results and exclusions.

## Current blockers and recovery

- No open TASK-1 blockers. B1/B2 resolved by the local pinned environment;
  B3 resolved by the verified Approach C boundary (E007).
- Final normal suite: 149 passed, no skips/xfails. Before decorator cleanup,
  all 149 assertions passed under --runxfail; the original four bodies and
  assertions remain byte-identical. SDK source integrity verified (124 files).
- Baseline dfb329b9e91620b3075710bb2466c11ba8703936 preserves user work.
  Implementation checkpoint 7b0c79fdda6949e9a18a8919910ae58e9d04360f;
  separate decorator cleanup 93a861f7bfd6f49bf40a882753aa376ac4662d0f.
- Adoption: ADR-006 accepted; ADR-007 records the user-authorized cleanup.
  See STDIO_BLOCKER_INVESTIGATION.md for preserved research and current adoption.
- Maintenance: keep MCP 2.3.0 pinned until all correlation/cancellation/STDIO
  tests pass on an upgrade. Two-frame bound is not a byte-size limit. Explicit
  stdin owns a duplicate handle and preserves default SDK stdout protection.
  Only Windows was verified; existing UTF-8 replacement/nonfinite token handling
  remains unchanged. Broken-output termination can be nonzero.
- Resume by reading AGENTS.md and this ledger and inspecting Git status.
  Next recommended action: adopt/review the implementation; retain this suite
  before any future SDK upgrade. Tasks 2-4 await separate requirements.

## T1-007 investigation acceptance criteria

- [x] R1: Inspect installed source/public APIs and current official release/source evidence.
- [x] R2: Compare A/B/C for error codes/IDs, both eras, cancellation, shutdown,
  stdout isolation, maintenance and assessment risks.
- [x] R3: Record a recommended candidate, affected files, limitations and exact future validation commands.
- [x] R4: Verify implementation/tests/dependency pins/source requirements/manual labs unchanged by hashes.
- [x] R5: Record actual baseline/strict diagnostic results and keep TASK-1 BLOCKED.

These are historical research-session criteria (E006). The subsequent user request
approved implementation and conditional decorator cleanup, verified in E007.

## T1-008 controlled remediation criteria (2026-11-03)

The user now authorizes Approach C implementation and conditional removal of
only obsolete XFAIL decorators after all assertions pass under --runxfail.
This supersedes the previous research-only session restriction above.

- [x] C1: Recoverable Git baseline created without discarding existing files.
  Baseline: dfb329b9e91620b3075710bb2466c11ba8703936, including manual labs.
- [x] C2: Official SDK 2.3.0 parser/runner/writer/stdout protection retained;
  single-reader observation with bounded exact input/item correlation.
- [x] C3: Correct -32700/null and -32600/reliable top-level ID in both lifecycle modes.
- [x] C4: Original 94 ordinary tests pass; four original diagnostic bodies and
  assertions byte-identical and passing under --runxfail before marker cleanup.
- [x] C5: New correlation/backpressure/ordering/cancellation/EOF/isolation tests pass.
- [x] C6: Ruff passes; only obsolete XFAIL decorators removed in separate cleanup;
  normal suite rerun passing. Tools/schemas/dependencies/Tasks 2-4 unchanged.
- [x] C7: Actual evidence, adoption decision and handoff updated; TASK-1 DONE only
  after A1-A15 verified. Roll back a prototype that regresses existing behavior.

## T1-007 investigation acceptance criteria

- [x] R1: Inspect installed source/public APIs and current official release/source evidence.
- [x] R2: Compare A/B/C for error codes/IDs, both eras, cancellation, shutdown,
  stdout isolation, maintenance and assessment risks.
- [x] R3: Record a recommended candidate, affected files, limitations and exact future validation commands.
- [x] R4: Verify implementation/tests/dependency pins/source requirements/manual labs unchanged by hashes.
- [x] R5: Record actual baseline/strict diagnostic results and keep TASK-1 BLOCKED.

This research task does not implement a remedy, complete A7/A12/A13, or change
any Tasks 2-4 requirement. The four existing strict XFAIL cases must remain intact.
