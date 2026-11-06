# Persistent task ledger

Last updated: 2026-11-06 (America/Los_Angeles).

## Task registry

Current corrective checkpoint: T3-007 DONE / independently APPROVED within the
documented13-19-digit synthetic PAN grammar, confirmed2026-11-06/E042. Historical
approvals preserved. E041 native1761/eight Ruff NOT independently rerun in full;
E042 distinguishes reported659 non-wire/17 PAN wire/randomized review from local
Git inspection. One descriptive acceptance commit authorized; no push/features.
Task4 non-documentation remains frozen; real-provider integration NOT VERIFIED.

Historical T3-006 outcome: independently APPROVED within the accepted synthetic
SSE/PII contract; T3-006/TASK-3 DONE, user confirmation 2026-11-05/E040. All four
assessment tasks are DONE within their documented scopes. E039 actual native
verification is unchanged; no tests rerun for that acceptance. Its documentation
commit is complete; current T3-007 authority is acceptance documentation/Git only, no push.

| ID | Description | Priority | Status | Acceptance / evidence | Blocker / next action |
| --- | --- | --- | --- | --- | --- |
| GOV-001 | Establish persistent engineering governance before implementation | P0 | DONE | G1-G5 verified in E002 | Maintain records at every milestone |
| TASK-1 | Strict MCP server assessment | P0 | DONE | A1-A15/E007; fresh 149 passes/Ruff E028 | Approach C preserved; no implementation/test/dependency changes |
| T1-001 | Confirm runtime, SDK/public APIs, dependency versions | P0 | DONE | Python 3.12.16/MCP 2.3.0/Pydantic 2.12.5; E003/E004; uv.lock | Maintain verified pins |
| T1-002 | Strict schemas and mock refund domain | P0 | DONE | Strict schemas, parity and exact mock state verified; E004 | No open domain defect |
| T1-003 | MCP tool dispatch and protocol errors | P0 | DONE | All error codes/IDs and business separation verified; E007 | B3 resolved by SDK-preserving boundary adapter |
| T1-004 | STDIO entry point and diagnostics | P0 | DONE | Module/console startup, wire purity, stderr, EOF shutdown verified; E004 | Retain subprocess regression tests |
| T1-005 | Unit, SDK integration and subprocess wire verification | P0 | DONE | 149 passed under --runxfail and normal execution; E007 | Original diagnostic bodies retained as passing regression tests |
| T1-006 | Reproducibility, lint, README and final evidence | P1 | DONE | Setup/lock and README verified; final lint/format/evidence E007 | Maintain evidence on future changes |
| T1-007 | Read-only STDIO blocker remediation investigation | P0 | DONE | R1-R5 verified; investigation report; E006 | Proposed candidate implemented and verified under T1-008 |
| T1-008 | Controlled Approach C implementation and adoption | P0 | DONE | C1-C7 verified; E007; ADR-006/007 | Adopt; rerun boundary contract tests before any SDK upgrade |
| TASK-2 | Secure HTTP/JSON-RPC MCP reverse proxy | P0 | DONE | T2-001 through T2-006 independently accepted; fresh 452 passes/Ruff E028 | Accepted implementation/config/tests preserved; no push |
| T2-001 | Task 2 isolated project and acceptance baseline | P0 | DONE | E008; independently reviewed and accepted, user confirmation 2026-11-04 | Preserve committed baseline e828729b |
| T2-002 | Pure security and strict JSON-RPC guards | P0 | DONE | E009: 186 tests/Ruff pass; Decimal correction independently accepted 2026-11-04 | Preserve accepted behavior; original tests unchanged in T2-003 |
| T2-003 | HTTPX upstream adapter | P0 | DONE | U1-U8/E011; 300 tests/Ruff; independently accepted, user confirmation 2026-11-04 | Preserve committed baseline 0b2e0b7 |
| T2-004 | FastAPI HTTP endpoint | P0 | DONE | H1-H8/E013; independently accepted; be9ddd8 | Preserve approved implementation and existing 400 tests |
| T2-005 | Real HTTP wire verification | P0 | DONE | W1-W8/E015; independently accepted; aa343b3 | Preserve accepted wire tests/production baseline |
| T2-006 | Final Task 2 assessment audit | P0 | DONE | F1-F7/E017; independently APPROVED, user confirmation 2026-11-04/E018 | Accepted final documentation/Git checkpoint; implementation preserved |
| TASK-3 | Asynchronous SSE streaming proxy with PII redaction | P0 | DONE | T3-001..007 independently accepted; PAN correction APPROVED2026-11-06/E042; actual native733/E041 | Preserve scoped PAN/PII/resource/lifecycle limits; no vendor/universal-PII claim or push |
| T3-001 | Requirements provenance, architecture and exact streaming contract | P0 | DONE | Independently APPROVED 2026-11-05 for documented synthetic profile; ADR-022 | Original vendor brief unavailable; preserve narrow approved scope |
| T3-002 | Isolated project and pure SSE/redaction components | P0 | DONE | Independently APPROVED 2026-11-05; E031 native verification / qualified review E032; ADR-023 | Preserve accepted foundation 0a75587 |
| T3-003 | Async upstream adapter, orchestration and lifecycle | P0 | DONE | Independently APPROVED 2026-11-05; native Q13-Q15/E033, qualified review E034; ADR-024 | Preserve accepted baseline e4bd001 |
| T3-004 | FastAPI streaming HTTP integration | P0 | DONE | Independently APPROVED 2026-11-05; native Q16-Q18/E035, qualified review E036; ADR-025/T3-H policies | Preserve accepted baseline ecbd61c |
| T3-005 | Independent-process real HTTP wire verification | P1 | DONE | Independently APPROVED 2026-11-05; native Q19-Q21/E037, qualified split-review E038; ADR-026 | Preserve accepted wire milestone 6b76878; T3-006 accepted; preserve all wire evidence and limitations, no push |
| T3-006 | Final Task 3 assessment audit | P1 | DONE | Independently APPROVED 2026-11-05/E040; eight requirements/21 criteria/73 test refs/symbols/links/demo syntax reviewed; actual audit E039 | One final documentation-only acceptance commit authorized; no source/config changes or push |
| T3-007 | Post-acceptance PAN compliance correction and Task4 evaluator-readiness audit | P0 | DONE | Independently APPROVED2026-11-06/E042 within documented13-19-digit PAN grammar; actual E041 native1761/eight Ruff unchanged | Preserve accepted PAN/294-char auxiliary policy, all limitations and protected projects; one acceptance commit, no push |
| TASK-4 | Multi-Tenant LLM Rate Limiter | P0 | DONE | T4-001 through T4-006 independently accepted; final APPROVED 2026-11-05/E029; actual audit E028 | Assessment-ready within supported Windows/SQLite/trusted-adapter scope; preserve implementation, no push |
| T4-001 | Recovered contract and revised architecture | P0 | DONE | Independent APPROVED WITH CONDITIONS; P1-P4 finalized; ADR-016 | Preserve approved assumptions; provider/HTTP specifics deferred |
| T4-002 | Isolated project and pure sliding-window accounting | P0 | DONE | Independently ACCEPTED; 169 tests/12,000 differential checks/6 invariants reported; E021 | Preserve accepted foundation 3d8d3e5 |
| T4-003 | SQLite atomic admission, persistence and settlement | P0 | DONE | Independently ACCEPTED within supported Windows/SQLite scope; E022/E023 | Preserve accepted storage baseline ebc226a |
| T4-004 | Primary/backup provider routing | P0 | DONE | Independently ACCEPTED in supported environment; native E024/qualified review E025 | Preserve accepted orchestration baseline c889236 |
| T4-005 | Authenticated HTTP and real-wire verification | P1 | DONE | Independently ACCEPTED; native E026 / qualified split-review E027, H1-H8 | Preserve committed baseline 6eaccaf |
| T4-006 | Final Task 4 assessment audit | P1 | DONE | Independently APPROVED 2026-11-05/E029; seven traceability rows/test references/E028/docs/limitations reviewed | One final documentation-only acceptance commit authorized; no implementation changes or push |

## T3-005 independent acceptance / Git checkpoint - 2026-11-05

America/Los_Angeles. User independently APPROVES T3-005, no blocking implementation
defect or production correction. Reported580 existing passes, all57 wire cases
produced passing assertions across split executions,40 extra randomized real-socket
fragmentation passes,22 prior Python files unchanged; behavior/cleanup reviewed.
Linux/Python3.13.5 used import-path change ONLY in extracted review harness. Combined
Linux wire run stalled after50 completed cases;19-case split printed passing summary
but did not return promptly to enclosing command. NOT a clean combined637 run.
E037 native Windows/Python3.12.16 full637/exit0/Ruff remains authoritative; E038
records reported review and Git inspection only. Preserve kernel10s/TLS/formal RSS/
real-provider limitations. One descriptive acceptance commit authorized for approved
wire tests/marker/READMEs/governance only, retain/exclude ZIP/receipts/caches. No
test rerun absent unexpected functional change. TASK-3 IN_PROGRESS, T3-005 DONE,
T3-006 NOT_STARTED/not authorized. Verify Git checkpoint and stop; no push.

## T3-004 independent acceptance / Git checkpoint - 2026-11-05

America/Los_Angeles. User confirms independent APPROVAL; T3-004 DONE. Reported
580 suite passes, 180 additional randomized interleaved two-channel ASGI scenarios
with 4613 upstream reads, five extra fail-closed scenarios (candidate overflow,
unexpected EOF, duplicate done, premature end, malformed payload), all17 prior
Python files byte-identical and no blocking source defect. E036 records reported
review and Git inspection only; no new tests. Linux/Python3.13.5 review had one
nonfatal pytest configuration warning; E035 native Windows/Python3.12.16 and Ruff
remain authoritative. Real sockets/RSS still unverified, original brief unavailable.
One descriptive acceptance commit authorized for exact approved source/tests/
config/lock/README/governance; preserve all accepted bytes and Tasks1/2/4. After
SHA/manifest/clean-tree/recorded-origin verification stop. TASK-3 IN_PROGRESS;
T3-005 NOT_STARTED/not authorized; no push.

## T3-003 independent acceptance / Git checkpoint - 2026-11-05

America/Los_Angeles. User independently APPROVES T3-003; DONE. E033 preserves
actual native 457-pass/Ruff execution; E034 records reported independent 457 passes,
240 additional fragmentation cases, ownership/quarantine/confirmed release,
concurrent shutdown/one shared close, 11 pure file comparisons and compilation.
Linux/Python 3.13.5 review had one nonfatal pytest configuration warning; native
Windows/Python 3.12.16 and Ruff remain authoritative. No real socket/ASGI claims.
No blocking defect reported, no functional change or new local test execution.
One descriptive acceptance commit authorized for exact approved 15-file inventory;
retain/exclude local review ZIP, preserve source/tests/dependencies and Tasks 1/2/4.
After SHA/inventory/clean-tree/recorded-origin verification, stop. TASK-3 remains
IN_PROGRESS; T3-004 NOT_STARTED, requires separate authorization; no push.

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

## Task 1 closure, maintenance and historical handoff (E007)

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
  before any future SDK upgrade. Task 2 has separate requirements/checkpoints
  below; Tasks 3/4 still await supplied requirements and authorization.

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

## T2-004 acceptance baseline (2026-11-04)

Authorized: FastAPI factory/app.py, POST /mcp, lifespan, HTTP policies and injected
ASGI/HTTPX integration tests only. Preserve 0b2e0b7/e828729b and Task 1. No T2-005,
SSE, OAuth/JWT issuance, Tasks 3/4, commit or push.

- [x] H1: Factory and lifespan initialize/close one existing pooled adapter per app;
  missing/invalid trusted configuration fails startup, with no import-time secrets.
- [x] H2: POST-only /mcp; metadata/framing/media/encoding/size policies before RPC;
  bounded streaming body reads (including chunked), early auth and body timeout.
- [x] H3: Reuse accepted guards and adapter; denied/malformed/unsupported input
  reaches zero upstream requests; no duplicate auth/JSON parsing implementation.
- [x] H4: Admin protected calls, both roles' ordinary calls and transparent discovery;
  request/response bytes and applicable IDs preserved, including error paths.
- [x] H5: Explicit HTTP mappings, fail-closed batches/notifications, generic failures
  and no tokens/internal exception details in service responses/logs.
- [x] H6: ASGI/mock tests for credentials, bypasses, headers, chunk limits, failures,
  zero-upstream rejection, concurrency/context isolation and lifecycle cleanup.
- [x] H7: All original 300 tests and new integration tests pass; both Ruff checks pass.
- [x] H8: Exact evidence, decisions, build/ledger/restart docs and preservation checks;
  stop for independent engineering review, without T2-005 work or commit/push.

Outcome: T2-004 DONE for implementation, independent engineering review PENDING.
E013: 400 passed in 1.88s; zero failures/skips/warnings; Ruff lint and format pass
(13 files). All original 300 tests and accepted settings/security/rpc/upstream
modules are byte-identical; Task 1 implementation/tests/root pins unchanged.
Only Task 2 isolated dependencies added; previously locked versions retained.

HTTP contract: task2/CONTRACT.md; architecture: ADR-013. Rejected local inputs
produce zero upstream calls; the 24-request/two-client test has 4 viewer denials
and exactly 20 correlated upstream calls. No socket/T2-005 completion claim.
Remaining limitations: stateless JSON-only upstream, server-owned wire framing,
TLS/access logs/graceful draining/deployment limits and real interoperability.

Recovery: HEAD 0b2e0b7 unchanged, index empty; 10 intended tracked modifications
and new app.py/test_app.py. No T2-004 implementation blocker. Stop for independent
review; T2-005 and any commit/push require separate authorization. TASK-2 remains
IN_PROGRESS; Task 1 remains DONE with 149 historical passes (not rerun).

## T2-004 independent acceptance and Git checkpoint (2026-11-04)

- User confirms independent engineering approval of T2-004, a reviewed 400-test
  pass and additional probes confirming zero upstream calls for rejected input.
  These additional results are independently reported, not new local executions;
  probe commands/counts were not supplied. T2-004 is DONE and ACCEPTED, resolving
  the historical review gate above. Local execution evidence remains E013.
- Authorized: one descriptive commit of approved app.py/test_app.py, Task 2
  dependency/lock updates and relevant governance documentation. Do not alter
  accepted implementation, push, or start T2-005. No tests rerun for this checkpoint.
- Initial Git state: HEAD 0b2e0b7; index empty; 10 tracked modifications, two new
  app/test files and task2_t2004_review.zip; ahead 2/behind 0 versus local origin/main.
  Exclude environments/caches/egg-info/credentials/review ZIPs, preserving artifacts.
- Task 1 and all accepted Task 2 components/tests remain unchanged. ADR-013 is
  ACCEPTED with its existing HTTP contract/limits; no architecture redesign.
- Next: stage/inspect the exact 12-file allowlist, create the approved commit and
  verify Git status/ahead-behind. Stop; TASK-2 IN_PROGRESS, T2-005 NOT_STARTED.

## T2-005 acceptance baseline (2026-11-04)

User authorizes real loopback TCP verification against independent Uvicorn proxy
and mock upstream processes; preserve be9ddd8 and the existing 400 cases. No
external services/public listeners, full MCP sessions/SSE/OAuth, Tasks 3/4,
T2-006, commit or push. Prefer tests; reproduce/log defects before production edits.

- [x] W1: Reproducible loopback processes, child-owned dynamic ports, explicit
  readiness and bounded startup/cleanup, including startup/test failure paths.
- [x] W2: Real credentials/roles/IDs/decoded-name/duplicate-key security; exactly
  zero journaled upstream calls for each locally rejected request.
- [x] W3: Approved requests, discovery/admin definitions, bytes/IDs/errors/statuses/
  headers preserved; inbound tokens/cookies/spoofed roles never reach upstream.
- [x] W4: Content-Length/chunked bodies, limits, media/encoding, malformed envelopes,
  invalid IDs, batches and notification contract verified on real TCP.
- [x] W5: Concurrent independent clients/roles/repeated IDs with synchronization
  and bounded deadlines; no response/context mixing.
- [x] W6: Slow-peer timeout, refusal, unexpected process termination, disconnects
  and actual lifespan/shutdown/failed-test cleanup verified without timing sleeps.
- [x] W7: Full Task 2 suite and Ruff executed; no Task 1 regressions needed unless
  shared code/environment changes. Capture failures honestly; no invented passes.
- [x] W8: Journal outcomes, process config, limitations, decisions, build/evidence
  and recoverable status recorded; stop for independent review, not acceptance.

Outcome: T2-005 DONE for verification only; independent engineering review PENDING,
not independently accepted. E015: 452 passed in 13.14s, zero failures/skips/warnings;
Ruff lint and format pass (16 files). Original 400 cases/production modules untouched.

33 dedicated local-rejection cases each journal zero upstream calls. Concurrent
12 independent connections/repeated IDs yield 2 viewer denials and exactly 10
simultaneously held approved requests, all correlated correctly. Cleanup summary:
12 child processes, zero alive/forced cleanup/live readers; deliberate kill and
startup failure accounted for. Initial refusal fixture expected 502 with too-short
0.5s connect budget; direct probing justified a 3s fixture budget, with no production
defect/fix. See M024/E015 and ADR-014; Windows loopback fixture limits remain explicit.

Recovery: HEAD be9ddd8 unchanged; index empty; 9 intended tracked modifications
and 3 new test files. No dependency/lock/root config or Task 1 changes. Task 1 stays
DONE with 149 historical passes, not rerun because no shared code/environment changed.
No implementation blocker; stop for independent review. TASK-2 remains IN_PROGRESS;
T2-006 scope and any commit/push require explicit authorization.

## T2-005 independent acceptance and Git checkpoint (2026-11-04)

- User confirms independent engineering approval: 400 existing and 52 real-wire
  tests passed independently; 33 rejection cases enforce zero forwarding; all
  12 children reaped without forced cleanup. Review also confirms production/
  earlier tests match the T2-004 snapshot. These are reported independent results,
  not new local executions; commands/timings were not supplied. Local record: E015.
- T2-005 is DONE and independently ACCEPTED, resolving the historical review gate
  above. No implementation/test change is needed. ADR-014 retains its existing
  design, evidence boundaries and Windows-specific limits.
- Authorize one descriptive commit containing only three approved wire-test files,
  the pytest marker update and relevant engineering documentation. Exclude local
  environments/caches/credentials/review ZIPs, retaining all artifacts. No push or
  T2-006 scope is authorized; Task 1/accepted production implementation unchanged.
- Initial Git state: be9ddd8, empty index, 9 tracked modifications, 3 new test
  files and task2_t2005_review.zip; ahead 3/behind 0 versus local origin/main.
- Next: stage/inspect exact 12-file allowlist, commit, verify clean status/counts
  and stop. TASK-2 remains IN_PROGRESS; no tests rerun for this Git checkpoint.

## T2-006 audit acceptance baseline (2026-11-04)

User authorizes verification/documentation only against clean aa343b3, initially
ahead 4/behind 0 local origin/main. No accepted production/test/config changes,
Tasks 3/4, commit or push. A discovered production defect must be reproduced/logged
and work stopped for independent review; TASK-2 cannot be DONE before audit acceptance.

- [x] F1: Original requirements mapped to functions/tests/actual checkpoint evidence,
  PASS/FAIL/NOT VERIFIED; implementation choices clearly distinguished.
- [x] F2: Execute complete Task 2 and Task 1 suites in separate pinned environments,
  plus both Ruff checks per task; record versions/counts/warnings/exits exactly.
- [x] F3: Verify locked Task 2 installation, installed imports, documented CLI,
  trusted configuration, example calls and actual startup/shutdown.
- [x] F4: Inspect current project files/relevant reachable Git history and ignore
  rules for credentials/generated/sensitive artifacts; classify false positives.
- [x] F5: Verify task independence/Task 1 preservation and accepted authorization/
  response contracts; correct public README/governance documentation if needed.
- [x] F6: Produce durable traceability, regression/security/publication results,
  submission checklist, remaining limitations and READY/CHANGES REQUIRED decision.
- [x] F7: Preserve all accepted code/config/tests; leave recoverable ledger and
  uncommitted documentation-only changes, pending independent final audit review.

Local outcome: READY within supplied scope; F1-F7 verified, independent final audit
review PENDING. T2-006/TASK-2 remain IN_PROGRESS. Fresh E017: Task 2 452 passed in
13.87s, Task 1 149 passed in 38.44s, no failures/skips/warnings/xfails; both Ruff
checks per task pass. Fresh Task 2 install has all 27 locked packages/imports and
no Task 1 distribution; default-settings Uvicorn CLI startup/shutdown and six real
loopback smoke probes pass. All eight original requirement rows PASS; excluded
vendor/full-session/TLS/DNS/load/other-OS behavior is NOT VERIFIED, not implied.

No production defect/implementation blocker found. Local archive exclusions are
not portable; retain explicit staging precautions for later publication. Changed
files are documentation only, no staging/commit/push; HEAD aa343b3, ahead 4/behind 0
local origin/main, not fetched. Task 1 source/tests/root dependencies/manual labs
remain preserved; Tasks 3/4 NOT_STARTED. Next: independent review of final audit,
traceability/checklist and documentation diff; no new implementation authorization.

## T2-006 independent acceptance and final Git checkpoint (2026-11-04)

- User confirms independent ChatGPT engineering verdict APPROVED: Task 2 is
  assessment-ready within documented requirements. All eight traceability rows,
  references to previously reviewed source/tests and final evidence/submission
  docs were reviewed and found consistent. Reported review, not new execution.
- T2-006 and TASK-2 are DONE, resolving the historical review-pending gate above.
  Task 1 remains DONE; Tasks 3/4 remain NOT_STARTED. Existing architecture/security
  contracts and documented operational limitations are unchanged.
- E017 retains actual 452 Task 2/149 Task 1 passes and Ruff evidence; E018 records
  this acceptance/Git checkpoint. No tests/Ruff rerun: no unexpected source/config
  change exists. All accepted implementation/tests/dependencies/lockfiles preserved.
- Initial state: HEAD aa343b3, nine modified tracked docs, one new audit report,
  one untracked review ZIP, empty index; ahead 4/behind 0 local origin/main.
  Review ZIP retained and excluded locally. Stage only the exact ten-document
  allowlist, inspect full staged diff and whitespace, create one descriptive commit.
- No push or new implementation authorized. After the commit, verify clean status
  and branch counts against the existing origin/main ref, report SHA/files and stop.
  Any later publication or Tasks 3/4 work requires separate authorization.

## T4-001 recovered contract and design checkpoint (2026-11-04)

User authorizes documentation/design only, superseding earlier reserved Task 4
status. Confirmed requirements/clarifications: docs/TASK4_REQUIREMENTS.md R1-R7.
Architecture is ADR-016 PROPOSED; accounting assumptions A1-A10 require review.

- [x] D1: Record confirmed 50,000-token/sliding-minute tenant-key quota, on-disk
  SQLite/concurrency, primary-429 and 3,000 ms timeout fallback, sanitized errors;
  distinguish local 429 (zero provider calls) from upstream 429 (automatic backup).
- [x] D2: Inspect actual SQLite runtime before proposing WAL; E019 metadata probe
  gives SQLite 3.53.1/Python 3.12.16. No DB/WAL behavior claim or installed Task 4 env.
- [x] D3: Propose isolated modules, tenant identity, schema/transactions, sliding
  accounting, sequential routing and bounded crash recovery without extra services.
- [x] D4: Identify chosen accounting/reservation/timing/provider/HTTP assumptions,
  conservative admission/unknown-usage tradeoffs and remote cancellation limits.
- [x] D5: Define T4-Q1-Q12 future tests and staged acceptance milestones; preserve
  Tasks 1/2/3, source/tests/dependencies/locks; no installs, implementation or Git writes.
- [x] D6: Independent architecture review APPROVED WITH CONDITIONS; P1-P4 finalized
  under subsequent user authorization. Provider/HTTP details remain deferred.

Outcome: T4-001/TASK-4 IN_PROGRESS; design documented, review PENDING, no T4-002
authorization. No application tests/Ruff executed; only runtime metadata and
documentation/preservation checks. Historical Task 1/2 evidence/status unchanged.
Open inputs: provider/model/tokenizer/usage fields and enforceable output caps;
accept combined reservation/clock/recovery conventions; backup/overall deadlines;
tenant-key provisioning/transport/identity-secret rotation and exact HTTP schemas.
Next: independent design review and resolve these inputs before any implementation.
No commit/push or Task 3 work authorized; leave only this checkpoint's docs diff.

## T4-002 acceptance baseline (2026-11-04)

User reports independent T4-001 architecture APPROVED WITH CONDITIONS. Finalized
P1-P4 in docs/TASK4_REQUIREMENTS.md / ADR-016 complete those design conditions;
T4-001 DONE. Implementation is authorized for pure accounting only.

- [x] K1: Isolated task4 project/environment/lock and installed package; preserve
  root/Task 1/Task 2 source/tests/configuration/dependencies/lockfiles.
- [x] K2: Immutable typed settled/outstanding/bounds/decision records; integer,
  identifier, model and overflow validation; unavailable bounds fail closed.
- [x] K3: Exact 50,000 invariant: window-settled + ALL outstanding + new combined
  primary/backup bounds <= quota; no double counting/duplicate snapshot identities.
- [x] K4: Inject accounting clock, deterministic exact expiry/weighted expiration,
  clock regression/future entry, tenant isolation and conservative hold coverage.
- [x] K5: Primary+backup reservation math and insufficient/invalid bound rejection;
  pure decisions only, no state writes/concurrent-admission claim/provenance shortcut.
- [x] K6: Execute Task 4 pytest and Ruff lint/format; record actual counts/exits,
  environment versions and failures. No invented or reused test results.
- [x] K7: Update governance/status/remaining limitations; no SQLite/provider/HTTP/
  recovery execution, T4-003, Task 3, commit/push; stop for independent review.

### T4-002 checkpoint outcome

T4-001 DONE after reported conditional architecture approval and finalized P1-P4.
T4-002 DONE for implementation/unit verification; independent review PENDING, not
accepted. TASK-4 remains IN_PROGRESS. E020: 169 passed in 0.12s, zero failures/
skips/warnings/xfails; Ruff lint and format pass (5 Python files). Initial sandbox
run also passed 169 but warned about cache permissions; identical outside-sandbox
rerun resolved the warning without test/warning-filter changes. Eight locked
packages installed in task4/.venv and imports/version/pip checks pass.

No concurrent admission, persistence, real token provenance, provider fallback,
HTTP or recovery compliance claim. Pure results do not mutate/reserve capacity.
No source/test/config/dependency/lock changes to accepted Tasks 1/2; no rerun needed
because shared code/environments remain unchanged. No Task 3/T4-003, commit/push.
Next: independent T4-002 review; approve real model/provider/HTTP specifics at their
later checkpoints and authorize T4-003 separately. Resume from AGENTS/contract/E020.

## T4-001/T4-002 independent acceptance and Git checkpoint (2026-11-04)

- User independently APPROVES T4-002: 169 existing tests, 12,000 randomized
  differential checks and six targeted invariants passed; no blocking defect.
  Ruff checks are supported by recorded Codex E020 evidence, not a newly reported
  independent command. E021 distinguishes reported review from local executions.
- T4-002 is DONE and independently ACCEPTED, resolving the historical review gate
  above. T4-001 remains DONE with finalized P1-P4. Whole TASK-4 IN_PROGRESS;
  T4-003 NOT_STARTED and not authorized. Tasks 1/2/3 statuses/implementation preserved.
- Initial Git state: HEAD 6904b1f, empty index, five tracked docs modified, new Task 4
  requirements/nine project files and task4_t4002_review.zip; ahead 0/behind 0 local
  origin/main. Capture existing hashes and retain/exclude the review ZIP locally.
- Authorize one descriptive foundation commit: exactly 15 project/requirements/
  governance files. Preserve accepted code/tests/pyproject/lock bytes; no tests/Ruff
  rerun or dependency installation. Inspect complete diff/index and whitespace;
  exclude environments, caches, bytecode, egg-info, credentials and review artifacts.
- Next: one approved commit, verify SHA/clean tree/ahead-behind against existing
  origin/main and stop. No push, Task 3 work or T4-003 implementation authorized.

## T4-003 acceptance baseline (2026-11-04)

User authorizes storage only against accepted 3d8d3e5/169 tests. Earlier scope
restrictions are historical. Preserve all accepted models/calculations/tests/pins.

- [x] S1: Verified runtime/local disk, strict tenant-scoped schema/indexes/unique
  constraints, persistent identity verifier and clock watermark, WAL/FULL/busy policy.
- [x] S2: BEGIN IMMEDIATE encloses clock/snapshot/pure decision/combined insert;
  return successful admission only after COMMIT; no process-local-lock shortcut.
- [x] S3: Storage-only dispatch intent, known/unknown settlement and unused release;
  strict transitions, idempotence, original timestamps, no double charge.
- [x] S4: Reopen/restart preserves usage/holds/identity; reject mismatched identity,
  clock regression and stale operations. No credentials/prompt/completion persisted.
- [x] S5: Finite-deadline recovery converts unresolved bounds conservatively once,
  never silently frees uncertain execution or replays providers.
- [x] S6: Unit/SQLite and barrier-synchronized real-process tests cover quota/window,
  tenant isolation, duplicate IDs, failed transactions, busy locks and durable results.
- [x] S7: Full Task 4 suite plus Ruff lint/format executed; actual runtime/counts/
  warnings/exits/process cleanup recorded, including failures.
- [x] S8: Update docs/decisions/build/evidence and protected-file checks; no provider,
  timeout/fallback execution, HTTP, final audit, T4-004, Tasks 1/2/3 edits, commit/push.

### T4-003 checkpoint outcome

T4-003 DONE for local implementation/verification, independent acceptance PENDING.
TASK-4 remains IN_PROGRESS. E022: 221 passed in 3.37s, zero failures/skips/warnings/
xfails; Ruff lint/format pass, 10 files. All original 169 tests/source/pins unchanged.
15 child processes reaped normally with zero forced cleanup/live processes; six-way
final-capacity race one winner/five denials/durable 50,000; duplicate-ID and settlement
races plus independent writer/reader restart confirm persistence. No provider replay.

No current test failures/blocker. Limits: Windows-fixed-drive verifier only, SQLite
single writer/synchronous per-operation connections, trusted UTC/local storage/identity
secret, no automatic retention/unblock, no provider-bound provenance or public API
integration. Numeric reservation lifetime is explicit trusted caller configuration;
future routing must enforce send deadline/cleanup. No T4-004, Task 3, commit/push.
Next: independent engineering review of storage APIs/schema/recovery/evidence before
any provider integration. Preserve uncommitted docs/source/test checkpoint.

## T4-003 independent acceptance and Git checkpoint (2026-11-04)

- User APPROVES storage within documented Windows fixed-local-drive/supported
  SQLite environment. E022 native Windows/SQLite 3.53.1 run is authoritative.
  Reported review: isolated Linux copy with test-only compatibility shim for
  unsupported platform/runtime gates, 221 tests passed, 15 children exited normally
  with zero forced cleanup; ten-thread admission, tenant isolation and exact
  deadline-anchored recovery scenarios also passed. No blocking source defect.
- These are reported independent results, not new local executions or evidence of
  native Linux support/Windows filesystem gate validation. E023 records provenance;
  no shim/gate changes included. T4-003 DONE/ACCEPTED; whole TASK-4 IN_PROGRESS.
- Initial HEAD 3d8d3e5, empty index, seven tracked docs modified/five new Python
  source/test files and review ZIP; ahead 1/behind 0 local origin/main. Capture 70
  file hashes; retain/exclude archive locally. No accepted source/test/pin changes.
- Stage exactly 12 approved storage/test/support/requirements/governance files,
  exclude environments/SQLite DBs/WAL/cache/credentials/archives; inspect all content,
  staged inventory and whitespace. One descriptive milestone commit authorized.
- No tests/Ruff rerun, provider/HTTP work, Tasks 1/2/3 changes, T4-004 or push. Verify
  resulting commit/clean tree/branch counts and stop; later work needs authorization.

## T4-004 start - 2026-11-04 (America/Los_Angeles)

User authorizes provider abstraction and async orchestration against ebc226a/221 tests.
Acceptance: trusted bounds/output caps before admission, durable start before each
send, monotonic 3000 ms primary deadline and shared 500 ms cleanup grace, exactly
one backup on primary 429/timeout only, no fallback on quota denial or uncertainty,
known/unknown settlement, cancellation-safe offloaded DB completion, deterministic
concurrency/failure tests and full Task 4 pytest/Ruff evidence. Preserve all accepted
code/tests/pins and Tasks 1/2. No vendor API, HTTP, T4-005, commit or push.

T4-004 milestone M038: prototype plus native focused 85-pass/full 318-pass runs;
final late-observation cleanup tests and final verification pending. All accepted
accounting/storage/tests/pins unchanged. Independent acceptance remains pending.

## T4-004 review handoff - 2026-11-04 (America/Los_Angeles)

Implementation/local mandatory verification complete; independent acceptance PENDING.
E024 final native Python 3.12.16/SQLite 3.53.1: 324 passed in 7.24s (221 unchanged
accepted + 103 new), zero failures/skips/warnings/xfails; Ruff lint and format pass
(15 files). Existing 15 storage child processes all exit 0, no forced/live children.
ADR-019 and requirements' T4-004 section record adapter trust, mandatory explicit
backup/overall budgets, monotonic primary/cleanup tie rules, no early-timeout
fallback, known/unknown settlement, retained ownership after caller cancellation,
and quarantine/unclean-close limitations. Admission/dispatch/settlement are short
offloaded SQLite operations; no production storage/accounting/test/pin edits.

All local acceptance bullets at session start have deterministic test evidence.
No local test blocker; no external provider/tokenizer/cap guarantee or socket/HTTP
verification claimed. Future real adapter and key-provisioning contracts plus
production backup/overall budgets remain unspecified. Next action: independent
review of providers.py/service.py, tests, E024 and ADR-019. Preserve recoverable
uncommitted work; do not mark whole TASK-4 DONE, begin T4-005, commit or push.

## T4-004 independent acceptance and Git checkpoint - 2026-11-04 (America/Los_Angeles)

User APPROVES T4-004; DONE/independently ACCEPTED. TASK-4 remains IN_PROGRESS;
T4-005 is NOT_STARTED and no implementation is authorized. No blocking production
defect identified. Existing architecture and limitations are unchanged.

Reported review: all 324 tests passed in an isolated Linux copy with review-only
platform/SQLite compatibility changes; additional output-category cap and total
reservation-bound adversarial checks passed. A real monotonic-clock probe observed
successful fallback at approximately 3.020 seconds, exactly one backup execution
and conservative usage accounting. These are reported independent results, not new
local executions, native Linux support, real-vendor certification or a timing SLA.
E024 native Windows/Python 3.12.16/SQLite 3.53.1 verification remains authoritative.
No review-only compatibility change is shipped. E025 records provenance.

One descriptive T4-004 commit is authorized for approved providers/service/tests/
support/README/requirements/governance, superseding historical no-commit gates for
this checkpoint only. Preserve all implementation/tests/pins and Tasks 1/2; no
reruns absent unexpected implementation changes. Initial HEAD ebc226a, index empty,
ahead 2/behind 0 recorded origin/main; seven modified docs/five new Python files
and a local review ZIP. Capture hashes, retain/exclude archive, inspect full diff
and exact index inventory, run git diff --cached --check, commit once and verify
SHA/clean status/branch counts. No push, T4-005, Task 3 or new provider/HTTP work.

## T4-005 start - 2026-11-04 (America/Los_Angeles)

Latest attachment authorizes FastAPI factory, external tenant-key authentication,
strict bounded HTTP JSON, reuse of accepted service/storage, resource lifespan and
independent loopback process/socket tests. Acceptance: zero reservations/provider
calls on local input/auth/quota rejection; exact quota/isolation/persistence;
429/3000 ms routing and bounded cleanup; conservative cancellation/billing;
sanitized responses/logs; full native Task 4 pytest/Ruff and process cleanup.
Preserve c889236 approved logic/tests and Tasks 1/2. Document implementation choices
separately from R1-R7. No real vendor, HTTP provider guarantee, T4-006, commit/push.

## T4-005 local verification / review handoff - 2026-11-04 (America/Los_Angeles)

Implemented H1-H8, independent acceptance PENDING. Final native full suite E026:
427 passed in 40.81s (324 unchanged accepted + 74 HTTP/config/lifecycle + 29 real
wire), zero failures/skips/warnings/xfails; Ruff lint/format pass, 22 files. Runtime
Python 3.12.16/SQLite 3.53.1; Task 4 lock 27 packages, locked offline sync checked.
21 wire local rejection receipts have zero provider calls AND zero new reservations;
28 wire children reaped, 27 exit 0/one expected invalid-startup exit 3, zero forced.
15 storage children exit 0/zero live or forced; 43 total reaped. Separate processes
verify framing, primary 429/real timeout routing, conservative usage, concurrent
same/different tenants, durable process restart and disconnect. No accepted code
or test correction needed; initial harness fatal stdin-reader issue fixed in NEW
support code and recorded, with original expected-exit assertion preserved.

New app.py/settings.py and five HTTP test/support/child modules; Task 4 pyproject/
lock HTTP additions only. Relevant governance/README updated, root README changes
Task 4 status only. No Task 1/2 implementation/dependency/environment change; no
rerun or new pass claim for their suites. Existing R1-R7/P1-P4 remain unchanged.
ADR-020 records interface/auth/body/error/lifecycle/test choices separately.

No current test/lint blocker. Limits: Windows fixed local drive, trusted UTC,
registered key/identity provisioning, verified real-model bounds/caps and explicit
deployment budgets still required; stock provider fails closed. Only loopback
HTTP/1.1 verified; no semantic completion redaction proof, public TLS/ingress,
load/OS-crash final audit or arbitrary uncooperative-resource shutdown guarantee.
Next: independent engineering review of T4-005/source/tests/E026/ADR-020, preserve
uncommitted checkpoint. TASK-4 IN_PROGRESS; do not start T4-006, commit or push.

## T4-005 independent acceptance / Git checkpoint - 2026-11-04 (America/Los_Angeles)

User APPROVES T4-005; DONE/independently ACCEPTED. No blocking production defect
identified. TASK-4 remains IN_PROGRESS; T4-006 NOT_STARTED and not authorized.
Reported review: all 427 test cases passed independently across separate runs;
29 real HTTP wire cases passed in split groups. Authentication, quota rejection,
fallback, concurrency, persistence and error sanitization were reviewed. Linux
verification required review-only compatibility substitutions. ONE combined Linux
wire run STALLED DURING FIXTURE TEARDOWN: not a completed all-at-once pass. Do not
conflate split passes with a completed combined run or native Linux support.
E026 native Windows/Python 3.12.16/SQLite 3.53.1 full-suite result remains
AUTHORITATIVE for the supported environment; E027 records reported review provenance.

Latest authorization permits ONE descriptive approved T4-005 source/tests/support/
configuration/lock/README/governance commit. Preserve all code/tests/config/pins and
Tasks 1/2 unchanged; no reruns absent unexpected implementation changes. Initial
HEAD c889236, empty index, ahead 3/behind 0 recorded origin/main; ten tracked files
modified, seven new Python files and one review ZIP. Capture 82 hashes, retain/
locally exclude archive, inspect full diff/index and whitespace, commit once,
verify SHA/manifest/clean tree/branch counts and stop. No T4-006, Task 3 or push.

## T4-006 audit start - 2026-11-04 (America/Los_Angeles)

Accepted baseline 6eaccaf, initially clean, main ahead 4/behind 0 recorded origin.
Acceptance: fresh complete Task 1/2/4 suites and Ruff, Task 4 clean locked setup and
deterministic success/fallback reproduction, R1-R7 traceability distinct from P1-P4,
SQLite/concurrency/recovery/HTTP findings, current/reachable-history security audit,
README/submission checklist and justified READY/CHANGES REQUIRED recommendation.
Document actual evidence only. No accepted code/tests/dependency edits or features;
reproduce/document and stop for blocking production defect. No Task 3/commit/push;
T4-006/TASK-4 remain IN_PROGRESS until independent approval.

## T4-006 local audit handoff - 2026-11-04 (America/Los_Angeles)

Local audit complete, recommendation **READY within documented assessment scope**;
independent ChatGPT approval PENDING. T4-006 and TASK-4 remain IN_PROGRESS, not DONE.
R1-R7 PASS under approved P1-P4/H1-H8: docs/TASK4_FINAL_AUDIT.md, ADR-021, E028.
Fresh native full suites: Task 1 149, Task 2 452, Task 4 427 passes; six Ruff checks
pass, zero failures/skips/warnings/xfails. Tasks 1/2 remain DONE/preserved.
New clean locked Task 4 install/imports, six ASGI/seven wire fixture repeats and
stock CLI intended 503/start/exit verified. Full native Task 4 43 children reaped,
zero forced; 21 local rejection receipts zero provider calls/new reservations.
No blocking production defect or actual tracked/history credential leak found.

Not verified: real provider/tokenizer/billing-time cap/production deployment, abrupt
OS kill/power/disk/WAL faults, restore, load/public ingress, unsupported platforms.
Portable ignores do not globally exclude arbitrary DB/ZIP paths; explicit staging
required. Provider reliability/UTC/local filesystem remain assumptions. No new
source/tests/config/locks, Task 3, stage/commit/push. HEAD preserved 6eaccaf; docs-only
recoverable work pending review. Next authorized step: independent engineering
review of audit/E028, not new implementation or automatic final acceptance.

## T4-006 independent acceptance / final Git checkpoint - 2026-11-05

America/Los_Angeles. User confirms APPROVED: assessment-ready within documented
requirements, supported Windows/SQLite environment and trusted-adapter policies.
All seven traceability rows reviewed against previously submitted source/test
evidence; all named references verified. E028 results, documentation, limitations
and submission findings consistent. **T4-006 and TASK-4 DONE**, all mandatory
assessment criteria verified and independently accepted. E029 records reported
acceptance, not new tests; E028 actual 2026-11-04 149/452/427 and Ruff evidence
preserved. No architecture/limitation expansion, real vendor/tokenizer/production
deployment certification or reinterpretation of qualified Linux review.

One final documentation-only commit authorized. Initial HEAD 6eaccaf, main ahead
4/behind 0 recorded origin/main, empty index; eight modified docs/new final audit
and local review ZIP. All original non-doc bytes match audit baseline; no unexpected
implementation/config changes or reason for test reruns. Preserve Tasks 1/2 and
all accepted Task 4 source/tests/configuration/dependencies/locks. Retain/exclude ZIP,
inspect full nine-file documentation diff/index, staged whitespace and artifacts,
commit once and verify SHA/inventory/clean tree/branch counts. No push/Task 3 or
further implementation. Future work/publication requires separate authorization.

## T3-001 contract proposal / independent review handoff - 2026-11-05

America/Los_Angeles. Architecture APPROVED CONDITIONALLY per user: isolated
FastAPI/HTTPX, explicit SSE parser, per-channel incremental redaction, bounded
memory, pull-driven backpressure and cancellation ownership. Exact contract still
PROVISIONAL. Second bounded materials inspection finds no original Task 3 brief;
known T3-R1-R8 come from user high-level requirements. No inferred vendor/categories.

Mandatory T3-001 acceptance criteria / actual current status:

- [x] Record requirement provenance and distinguish requirements from assumptions.
- [x] Record architecture conditional acceptance and original-brief search evidence.
- [x] Propose exact PII grammar, normalization/replacement and safe-prefix argument.
- [x] Specify synthetic SSE/JSON/channel/metadata/terminal/error behavior.
- [x] Specify separate line/event/candidate/output/channel/stream/time budgets.
- [x] Define cancellation, backpressure and bounded cleanup/postheader failure policy.
- [x] Define pure T3-002 scope and T3-Q01-Q12 / later Q13-Q21 acceptance matrix.
- [ ] Independent approval of exact T3-P1-P8 / T3-L proposals and omissions.

TASK3_REQUIREMENTS.md / ADR-022 / E030 hold proposals and actual inspections.
T3-001/TASK-3 IN_PROGRESS, NOT DONE; T3-002 through T3-006 NOT_STARTED. No tests,
new project/env/dependencies/source, commit or push. Tasks 1/2/4 remain DONE;
existing evidence/qualified support unchanged. Next action: approve or revise
T3-U1-U5, especially omitted PII/ASCII scope, whole-token @ masking/256-char reject,
synthetic event profile/metadata loss and numeric budgets. No implementation yet.

## T3-001 acceptance / T3-002 local implementation handoff - 2026-11-05

America/Los_Angeles. User independently APPROVES T3-001 for the explicitly defined
synthetic profile and all documented engineering policies; T3-001 DONE. Original
vendor brief unavailable, no universal PII/vendor interoperability claim. Approval
resolves the exact streaming contract, not future HTTP authentication/client/API
choices. All seven additional mandatory rules are retained (requirements/ADR-022).

T3-002 implemented and locally verified, IN_PROGRESS/independent review PENDING.
E031 final native Python 3.12.16: **362 passed in 3.02s**, zero failures/errors/
skips/warnings/xfails/xpasses, Ruff lint/format pass (11 files). Isolated 8-package
lock/offline locked sync/imports pass. No FastAPI/HTTPX/network dependency/runtime.
Pure models/SSE/profile/redactor/Processor and T3-Q01-Q12 tests only; ADR-023.

Byte-counted lines/events, strict incremental UTF-8/JSON, exact four-channel
transitions, whole-candidate masking/no raw overflow or EOF flush, separate Unicode/
raw/escaped-byte output caps, bounded lazy ownership and fixed errors verified.
Every representative raw-byte/delta cut, short-candidate partitions, Unicode cuts,
32 random partition seeds, 16 adversarial-content/reference seeds, 5000-event and
four-full-hold/1000-empty-event bounded-state tests included. Terminal error/abandon
revokes success. Initial cache warning/style/import failures preserved in E031.

No current test/lint blocker. Limits remain narrow ASCII grammar, conservative @
overmasking/long-token rejection, synthetic schema and trusted library composition.
No real async backpressure/cancellation/wire/RSS/deadline/provider claim yet.
Tasks 1/2/4 stay DONE/preserved. Next: independent review of task3 source/tests/
requirements/ADR-023/E031, not T3-003 or a Git checkpoint. No commit/push.

## T3-002 independent acceptance / Git checkpoint - 2026-11-05

America/Los_Angeles. User APPROVES T3-002; DONE/independently ACCEPTED. Reported
review: 362 passes; 1200 randomized interleaved streams; 2961 channel-level reference
comparisons; 256 prefix withholding/character-257 rejection probes; 376 truncated
wire cuts without whole-value PII leakage; 24000-event retained-state test and
compilation passed. No blocking production defect identified.

Linux/Python 3.13.5/pytest 9.0.2 review recorded one configuration warning, details
not supplied. Outside project-pinned Python 3.12; E031 native Windows/Python 3.12.16
and Ruff remain authoritative. No compatibility changes/pin widening/filters or new
execution claims. Original vendor brief unavailable; synthetic profile limits kept.

One T3-001/T3-002 implementation/acceptance commit authorized. Initial HEAD 7e37045,
aligned 0 ahead/0 behind recorded origin/main, empty index; five tracked docs plus
new requirements/15 Task 3 files/local review ZIP. All 11 Python hashes match E031;
config/pins/lock inspected unchanged, no test rerun needed. Capture 99 file hashes,
retain ZIP locally excluded, inspect/stage only 21 approved paths, staged whitespace
check, one descriptive commit and SHA/manifest/clean-tree/branch verification.
Preserve Tasks 1/2/4; TASK-3 IN_PROGRESS/T3-003 NOT_STARTED. No push or further code.

## T3-006 local final audit / independent review handoff - 2026-11-05

America/Los_Angeles. Latest attachment authorizes audit/documentation over
6b768780ace49c984d105b5ce558f69904f1076a, superseding historical no-T3-006 gates.
**Local recommendation READY within approved synthetic/Windows scope; T3-006 and
TASK-3 remain IN_PROGRESS, independent acceptance PENDING.** No code defect found.

Mandatory acceptance evidence:

- [x] R1-R8/Q01-Q21 and complete P/L/I/H/W policy traceability; exact test references.
- [x] Fresh native Task1 149/Task2 452/Task4 427/Task3 637 passes, all8 Ruff checks0;
  zero failures/errors/skips/warnings/xfails/xpasses (E039, not reused evidence).
- [x] Clean locked25-package Task3 install, successful authenticated progressive
  synthetic TCP demos,401 rejection/zero forwarding/done/end/confirmed child exits.
- [x] Privacy/limits/deadlines/backpressure/cancellation/capacity and process receipts
  audited with deterministic/native/OS distinctions retained.
- [x] Current112-file/reachable19-commit/234-blob secret/artifact contextual screen:
  no actual disclosure or unresolved finding; explicit ignore limitations retained.
- [x] Accepted source/tests/config/dependencies/locks and Tasks1/2/4 unchanged;
  independent environments/no cross-task production imports; READMEs corrected.
- [ ] Independent ChatGPT acceptance and authorization of final Git checkpoint.

Affected: AGENTS, root/Task3 READMEs, requirements/ledger/ADR-027/build/E039 and
new docs/TASK3_FINAL_AUDIT.md. E039 records commands/versions/exits, ignored audit-
tool-only first-demo failure and corrected rerun without application changes.
No new original vendor brief or universal PII/provider/TLS/formalRSS/kernel10s
guarantee. E038 Linux split/stall/import-path qualifications preserved. No local
blocker; review required. Next: independently review final audit/E039/docs diff;
do not markDONE, start new work, stage, commit or push before authorization.

## T3-006 independent acceptance / final documentation Git checkpoint - 2026-11-05

America/Los_Angeles. User confirms independent ChatGPT engineering APPROVAL:
TASK-3 assessment-ready within accepted synthetic SSE/PII contract. T3-006 and
TASK-3 DONE. All eight high-level requirements/21 criteria covered;73 unique
named tests checked against prior source archive; implementation symbols/local
links and assessor-demo syntax passed inspection; E039 evidence consistent; no
blocking documentation/traceability discrepancy. Review did NOT rerun native
Windows regression, directly inspect unpublished local Git history or validate
unavailable vendor requirements. E040 reported review/Git inspection; E039 actual
149/452/427/637 passes and eight Ruff results remain unchanged, not rerun here.

One descriptive final nine-file documentation-only commit authorized. Preserve
accepted source/tests/config/dependencies/locks and Tasks1/2/4; retain original
brief/PII/production/RSS/TLS/socket/environment limitations and historical records.
Initial HEAD6b768780ace49c984d105b5ce558f69904f1076a, main ahead4/behind0 recorded
origin/main, index empty. New review ZIP retained via exact local exclude; no
tracked ignore/config change. Explicitly stage only AGENTS, root/Task3 READMEs,
requirements/ledger/decisions/build/evidence and new TASK3_FINAL_AUDIT.md. Inspect
complete diff/index, run staged whitespace check, commit once, verify SHA/inventory/
clean tree/branch counts and stop. No tests/install/compile/Ruff rerun, fetch or
push. No remaining blocking assessment work; future publication/changes require
separate authorization.


## T3-007 post-acceptance evaluator remediation start - 2026-11-06

America/Los_Angeles. User authorizes targeted streaming PAN correction, Task4
read-only verification/documentation and fresh native four-task suites/Ruff.
T3-007 IN_PROGRESS / PENDING INDEPENDENT ACCEPTANCE; preserve historical approvals.
Criteria: reproduce unmasked PAN; bounded incremental13-19-digit contiguous/hyphen/
space grammar and safe-prefix proof; pure/ASGI/real-wire adversarial tests/no raw
supported PAN output/diagnostics; original lifecycle preserved; Task4 quota,
persistence, concurrency,429/3000ms fallback, conservative accounting/default503
verification; complete actual evidence/report. Tasks1/2 and Task4 implementation/
tests/config/dependencies/lock frozen, no unrelated changes/dependencies/commit/push.
Baseline8d7a3c7, clean initial tree,113 tracked hashes captured. Named gap-audit MD
not found in attachment/repository/workspace searches, local path requested.
Original vendor brief unavailable; user confirms recovered PAN category. Exact
separator/boundary/false-positive grammar is an engineering policy, not inferred
vendor wording. Explicit user requirements permit proceeding while awaiting gap MD.

## T3-007 independent acceptance / Git checkpoint - 2026-11-06

America/Los_Angeles. User independently APPROVES within documented13-19-digit
synthetic PAN grammar; T3-007 DONE. Reported659 non-wire cases, all17 new PAN
real-HTTP cases with review-only Linux subprocess import-path adjustment,1200
random streams/8812 delta fragments and prefix-withholding/overflow/four-channel
bounded-state probes pass. No blocking production defect. Accepted SSE parser,
HTTPX service/FastAPI/transport architecture unchanged. E042 review provenance;
E041 native149/452/733/427 (1761) and eight Ruff NOT independently rerun in full.
No new local tests/dependencies/features in acceptance. Preserve294/channel
auxiliary policy, scoped boundaries and all historical environment/PII/RSS/TLS/
socket/provider qualifications. Task4 implementation/pins frozen; real providers
NOT VERIFIED/rubric-dependent, no unspecified adapter added.

One descriptive19-path remediation acceptance commit authorized. Initial HEAD8d7a3c7,
main0 ahead/0 behind recorded origin, index empty. New local review ZIP hashed/
retained/excluded via exact .git/info/exclude; no tracked config change. Review
complete diff including auxiliary policy; explicitly stage only approved source/
tests/docs, exclude ignored scripts/receipts/env/cache/credentials/archives. Run
staged whitespace check, commit once, verify fullSHA/manifest/clean tree/branch
counts and stop. No push/fetch or further implementation authorized.
