# Persistent task ledger

Last updated: 2026-11-04 (America/Los_Angeles).

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
| TASK-2 | Secure HTTP/JSON-RPC MCP reverse proxy | P0 | IN_PROGRESS | docs/TASK2_REQUIREMENTS.md; task2/CONTRACT.md | T2-003 HTTPX adapter only; FastAPI endpoint deferred to T2-004 |
| T2-001 | Task 2 isolated project and acceptance baseline | P0 | DONE | E008; independently reviewed and accepted, user confirmation 2026-11-04 | Preserve committed baseline e828729b |
| T2-002 | Pure security and strict JSON-RPC guards | P0 | DONE | E009: 186 tests/Ruff pass; Decimal correction independently accepted 2026-11-04 | Preserve accepted behavior; original tests unchanged in T2-003 |
| T2-003 | HTTPX upstream adapter | P0 | DONE | U1-U8/E011; 300 tests/Ruff; independently accepted, user confirmation 2026-11-04 | One milestone commit authorized; no push or T2-004 work |
| T2-004 | FastAPI HTTP endpoint | P0 | NOT_STARTED | Requires separate authorization and HTTP contract | Do not implement in T2-003 |
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

## Task 2 first checkpoint (2026-11-04)

The user supplied Task 2 requirements and authorized T2-001/T2-002 only. Source:
docs/TASK2_REQUIREMENTS.md; implementation choices and criteria T2-C1-T2-C9:
task2/CONTRACT.md. Whole Task 2 remains IN_PROGRESS until later HTTP forwarding,
unfiltered discovery and denied-call wire evidence exist. No Task 1 criteria or
previous evidence have been changed. No commit/push authorized.

### Task 2 checkpoint outcome

- T2-001/T2-002 DONE: T2-C1-T2-C9 verified in E008; 156 passed without
  warnings/skips/xfails; Ruff lint and format pass. Locked isolated setup works.
- TASK-2 remains IN_PROGRESS: no HTTP route or HTTPX forwarding exists; real
  discovery transparency and zero denied downstream HTTP calls remain later work.
- Task 1 source/tests/dependencies/lock and historical evidence preserved;
  TASK-1 stays DONE, Tasks 3/4 NOT_STARTED. No commit/push this session.
- No checkpoint blockers. Next: independent review of task2/CONTRACT.md and
  pure guards before any T2-003 authorization. HTTP mapping/notification policy,
  upstream authentication/headers, limits and failure handling remain deferred.

## Compaction restart handoff (2026-11-04)

- Repository: S:\2026 jobs\Projects\ai-solutions-engineer-assessment; HEAD 6056bc7.
- Task 1 remains DONE: 149 previously verified passing tests (E007); no changes
  to task1/, root tests/, root pyproject.toml or root uv.lock. No tests rerun for
  this handoff. Preserve its implementation and historical evidence.
- T2-001/T2-002 are IMPLEMENTED and unit-verified, not independently approved:
  independent ChatGPT engineering review PENDING. DONE registry statuses refer
  to checkpoint implementation criteria only. TASK-2 remains IN_PROGRESS.
- Prior Task 2 evidence E008: 156 passed in 0.17s; Ruff lint/format passed for
  9 files; isolated locked setup verified. These are prior results, not new runs.
- Approved architecture: independent task2/ project/venv/lock; FastAPI + HTTPX
  for later HTTP proxy work. Current runtime is standard-library settings.py,
  security.py and rpc.py only; no endpoint, HTTP client or forwarding exists.
- Security: authenticate before inspection/authorization; role only from token
  mapping; exact decoded case-sensitive admin_ rule; viewer denial exactly
  -32001 / Unauthorized Tool Call with applicable ID; duplicate keys rejected;
  no ambiguous/uninspected permit; raw body retained without business coercion.
  Batches rejected wholesale. Notifications inspected/authorized then rejected
  without a permit or ordinary JSON-RPC reply. Tokens have no production defaults
  and are redacted from representations/errors. No discovery filtering is planned.
- Pending review/contract decisions: notification HTTP reporting, authentication
  challenge/body/status mappings, proxy path, upstream credentials and header/body
  consistency, limits/timeouts, upstream failure mapping and response relay.
  See task2/CONTRACT.md and ADR-008/009; passing guards is not HTTP wire evidence.
- Next checkpoint is T2-003 HTTP/upstream-adapter integration, only AFTER
  independent review and explicit user authorization. Do not begin it on resume.
- Git working state: unstaged AGENTS.md and docs/{TASK_LEDGER,DECISIONS,BUILD_LOG,
  TEST_EVIDENCE}.md; untracked docs/TASK2_REQUIREMENTS.md and 14 files under task2/
  (project/lock/contract/README, source and tests). Nothing staged. Local task2
  environment/caches are ignored. Preserve all uncommitted work; no commit/push.
- Tasks 3/4 remain NOT_STARTED and unauthorized. No implementation blocker for
  the completed checkpoint; independent review is the next required gate.

## T2-002 independent-review correction (2026-11-04)

- Initial status: IN_PROGRESS. Review reproduction confirmed on Python 3.12.16:
  syntactically valid JSON with an unrepresentable exponent escapes as
  decimal.InvalidOperation. Prior E008 results remain historical.
- Acceptance: contain decimal parsing exceptions; reject unrepresentable numeric
  values as -32700 / Parse error with null ID; preserve representable opaque
  values/raw bytes, strict IDs, decoded-name checks and duplicate-key detection.
  Add extreme-exponent regressions and run all Task 2 tests and both Ruff checks.
- Scope: T2-002 fix only; Task 1 unchanged; no HTTP/forwarding, commit or push.
  Next: implement and verify the correction, then stop for independent re-verification.

- Outcome: correction implemented; E009 records 186 passed in 0.15s and both
  Ruff checks passing (9 files formatted). T2-002 DONE for implementation only;
  independent re-verification PENDING. ADR-010/CONTRACT clarify parser-range
  rejection. No HTTP work or Task 1 modifications. Next: review this fix; T2-003
  still requires completed review and explicit authorization.

## Independent acceptance and foundation commit (2026-11-04)

- The user confirms independent engineering approval of T2-001/T2-002, including
  the Decimal correction. Both are DONE and independently ACCEPTED. This resolves
  the review/re-verification gates in the historical entries above.
- Latest executed evidence remains E009: 186 passed in 0.15s, Ruff lint and format
  checks passing. No tests rerun for this documentation/staging/commit checkpoint.
- User authorizes one descriptive foundation commit containing only task2/ files,
  its requirement snapshot and relevant governance records. Exclude environments,
  caches, credentials and temporary review artifacts. No push is authorized.
- TASK-1 remains DONE with 149 historical passes; preserve its implementation,
  tests, dependencies and lockfile. Whole TASK-2 remains IN_PROGRESS.
- T2-003 is NOT_STARTED/pending: review approval is complete, but HTTP contract
  decisions and explicit implementation authorization remain outstanding.

## T2-003 adapter acceptance (2026-11-04)

User authorizes only an asynchronous HTTPX adapter, preserving baseline e828729b.
No FastAPI endpoint, SSE, OAuth, Tasks 3/4, Task 1 changes, commit or push.

- [x] U1: Minimal typed upstream.py API; pooled AsyncClient; explicit finite timeouts.
- [x] U2: Fixed validated destination and separately configured upstream credentials;
  no client URL/header/cookie/authentication pass-through, redirects or retries.
- [x] U3: Only guard-issued authorization permits reach transport; forged/uninspected/
  denied requests cannot be sent. Existing guard semantics remain passing.
- [x] U4: Original request bytes preserved, including IDs, arguments and extensions.
- [x] U5: Valid correlated JSON-RPC results/errors preserved byte-for-byte, with no
  discovery filtering; explicit response ID/envelope and safe-header policy.
- [x] U6: Documented connection/timeout/redirect/malformed/ID-mismatch failure handling;
  bounded response resources, cancellation/close behavior and no sensitive diagnostics.
- [x] U7: MockTransport integration verifies credential isolation, errors, redirects,
  cancellation and concurrent request/response isolation; no real-server claim.
- [x] U8: Full Task 2 tests and Ruff pass; exact evidence/docs and recovery state updated.

Outcome: T2-003 DONE for implementation, independent engineering review PENDING.
E011: 300 passed in 0.55s, Ruff lint passes and 11 files already formatted;
locked offline setup/dependency checks pass. Prior 186 cases and Task 1 unchanged.
ADRs 011/012 and task2/CONTRACT.md record API, limits, failure/header policies and
process-local proof-bound permits. No endpoint or full MCP HTTP completion claim.

Recovery: HEAD e828729b unchanged; index empty; 11 intended tracked modifications
and two new files (upstream.py/test_upstream.py). Task 1's 149-pass evidence is
historical and was not rerun. No commit/push. No T2-003 implementation blocker;
remaining gates are independent review, real upstream validation and T2-004's
separately authorized HTTP contract/endpoint work. Stop for review.

## T2-003 independent acceptance and Git checkpoint (2026-11-04)

- The user confirms independent engineering approval of the HTTPX adapter. T2-003
  is DONE and independently ACCEPTED; this resolves the historical review gate
  above. ADR-011/012 and the contract retain their documented limits.
- One descriptive T2-003 commit is authorized. Include only approved adapter code,
  tests, Task 2 dependency/lock updates and relevant governance documentation.
  No push, T2-004 implementation or Tasks 3/4 work is authorized.
- E011 remains the latest execution evidence: 300 passed in 0.55s, Ruff lint and
  format pass. No tests rerun for this Git checkpoint; no unexpected code changes.
- Preserve Task 1 and the accepted e828729b foundation. No changes to Task 1,
  original Task 2 tests, rpc.py or settings.py. The approved security.py permit
  issuance addition is part of T2-003, with existing guard behavior preserved.
- Initial tree: 11 modified tracked files, new upstream.py/test_upstream.py,
  untracked task2_t2003_review.zip; index empty; main ahead 1/behind 0 relative to
  the existing origin/main ref. Exclude the archive locally; preserve all artifacts.
- Next: inspect/stage the exact 13-file allowlist, commit and verify status. Then
  stop; TASK-2 remains IN_PROGRESS and T2-004 remains NOT_STARTED/unapproved.
