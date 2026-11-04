# Persistent task ledger

Last updated: 2026-11-03 (America/Los_Angeles).

## Task registry

| ID | Description | Priority | Status | Acceptance / evidence | Blocker / next action |
| --- | --- | --- | --- | --- | --- |
| GOV-001 | Establish persistent engineering governance before implementation | P0 | DONE | G1-G5 verified in E002 | Maintain records at every milestone |
| TASK-1 | Strict MCP server assessment | P0 | BLOCKED | A1-A15 below; E005 | B3: SDK omits required malformed-frame errors |
| T1-001 | Confirm runtime, SDK/public APIs, dependency versions | P0 | DONE | Python 3.12.16/MCP 2.3.0/Pydantic 2.12.5; E003/E004; uv.lock | Maintain verified pins |
| T1-002 | Strict schemas and mock refund domain | P0 | DONE | Strict schemas, parity and exact mock state verified; E004 | No open domain defect |
| T1-003 | MCP tool dispatch and protocol errors | P0 | BLOCKED | Dispatch/validation/business/internal errors verified; E005 | B3: -32700/-32600 missing at SDK transport boundary |
| T1-004 | STDIO entry point and diagnostics | P0 | DONE | Module/console startup, wire purity, stderr, EOF shutdown verified; E004 | Retain subprocess regression tests |
| T1-005 | Unit, SDK integration and subprocess wire verification | P0 | BLOCKED | 94 passed, 4 xfailed; 4 strict failures; E005 | B3: retain strict diagnostics; verify upstream remedy |
| T1-006 | Reproducibility, lint, README and final evidence | P1 | DONE | Setup/install/lock/lint/format, README and final report verified; E004/E005 | Maintain evidence; TASK-1 remains BLOCKED |
| T1-007 | Read-only STDIO blocker remediation investigation | P0 | DONE | R1-R5 verified; investigation report; E006 | Research complete; ADR-006 proposed; TASK-1 remains BLOCKED |
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

Unchecked means not verified or unmet. Final evidence: E005 in TEST_EVIDENCE.md.
A7 is unmet at the SDK boundary; A12/A13 remain incomplete because the mandatory
malformed-frame subprocess checks fail. Expected failures never count as passes.

- [x] A1: Server starts successfully with Python 3.12.
- [x] A2: Official MCP SDK and Pydantic v2 used with tested version pins/public APIs.
- [x] A3: Exactly `get_customer_record` and `trigger_refund` discoverable.
- [x] A4: Both tools succeed with valid inputs and advertise model-derived schemas.
- [x] A5: Strict Pydantic validation, ASCII ID format, finite positive numbers,
  reason minimum length/nonblank, missing/null/extra/type rejection verified.
- [x] A6: Invalid tool arguments and unknown tool names yield JSON-RPC -32602.
- [ ] A7: Parse -32700, request -32600, method -32601, internal -32603 and
  applicable request IDs verified; business failures use `isError=true`.
- [x] A8: At least three synthetic records, deterministic refund IDs, Decimal
  balances and process-local transaction state verified.
- [x] A9: Validation/business failures never mutate balances or transactions.
- [x] A10: stdout contains only valid newline-delimited MCP JSON-RPC messages.
- [x] A11: stderr receives startup/shutdown, execution and failure diagnostics.
- [ ] A12: Actual subprocess STDIO/lifecycle/isolation/termination tests pass;
  supported modern and legacy lifecycle behavior is verified.
- [ ] A13: Required unit and SDK integration suite passes; all errors/IDs covered.
- [x] A14: Ruff passes; installation/startup commands work from documented cwd.
- [x] A15: README covers setup, examples, limitations and state lifecycle;
  final report includes tree, versions, matrix, results and exclusions.

## Current blockers and recovery

- B1/B2 RESOLVED: project-local Python 3.12.16 and official dependencies are
  installed; uv.lock preserves tested dependency selection. E003/E004.
- B3 OPEN (TASK-1, T1-003, T1-005): MCP 2.3.0 STDIO drops parse/envelope
  validation exceptions without -32700/-32600 responses. Four wire diagnostics
  xfail in both lifecycle eras. A7 is not met; applicable malformed-envelope
  request ID cannot be returned when no response exists. E005; --runxfail yields 4 failed, 94 deselected.
- Reconfirmed on 2026-11-03: E006 gives 94 passed/4 xfailed; strict diagnostics
  give 4 failed/94 deselected. No implementation files or four XFAIL cases changed.
- Investigation: [T1-007 report](STDIO_BLOCKER_INVESTIGATION.md) evaluates A/B/C.
  Checked release listings still show 2.3.0; Server.run has no observer injection;
  Pydantic error details cannot reliably recover IDs. A minimal raw-input
  observation adapter using public STDIO parameters is the proposed local fallback.
- Recommended resolution: prefer a verified official transport fix; otherwise
  review/implement the proposed minimal boundary composition in a separately
  authorized implementation session. Keep SDK runner/writer and XFAIL tests;
  verify the exact report test plan with --runxfail. ADR-006 is PROPOSED,
  not adopted or verified. Do not change mandatory acceptance criteria.
- Sandbox Windows named-pipe denial was environmental; approved unsandboxed
  rerun passed both official SDK subprocess client tests. Not an open defect.
- Resume by reading AGENTS.md and this ledger and inspecting Git status.
  Next: use the investigation report and ADR-006 for the remediation decision.
  The current user request permits documentation/research only, not code changes.

## T1-007 investigation acceptance criteria

- [x] R1: Inspect installed source/public APIs and current official release/source evidence.
- [x] R2: Compare A/B/C for error codes/IDs, both eras, cancellation, shutdown,
  stdout isolation, maintenance and assessment risks.
- [x] R3: Record a recommended candidate, affected files, limitations and exact future validation commands.
- [x] R4: Verify implementation/tests/dependency pins/source requirements/manual labs unchanged by hashes.
- [x] R5: Record actual baseline/strict diagnostic results and keep TASK-1 BLOCKED.

This research task does not implement a remedy, complete A7/A12/A13, or change
any Tasks 2-4 requirement. The four existing strict XFAIL cases must remain intact.
