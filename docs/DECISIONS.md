# Architecture decisions

## ADR-001 — Isolate the assessment repository

- Date: 2026-11-02; status: ACCEPTED; tasks: GOV-001, TASK-1.
- Context: `S:\2026 jobs` is not a Git repository and contains unrelated work.
- Decision: Use `Projects/ai-solutions-engineer-assessment` as the project root,
  as explicitly selected by the user. Establish governance before source work.
- Alternatives: Modify the workspace root; reuse an unrelated existing project.
- Rationale: Clear repository ownership, scope and recoverable audit trail.
- Tradeoffs: A new project needs its own environment and Git initialization.
- Consequences: Preserve unrelated directories; all assessment files stay here.
- Affected files: AGENTS.md, docs/*.md, docs/TASK1_REQUIREMENTS.txt.

## ADR-002 — Evidence-gated completion and immutable task boundaries

- Date: 2026-11-02; status: ACCEPTED; tasks: GOV-001, TASK-1, TASK-2–TASK-4.
- Decision: Maintain explicit mandatory checklists, stable IDs and dated actual
  evidence. Keep supplied Task 1 brief as a source snapshot. Tasks 2–4 stay
  reserved until their requirements are supplied; do not define them here.
- Alternatives: Track progress only in chat; mark implementation as complete
  before verification; infer future-task requirements from Task 1 exclusions.
- Rationale: Sessions must resume from durable records without scope drift.
- Tradeoffs: Documentation must be maintained alongside meaningful changes.
- Consequences: SDK limitations remain visible; unmet criteria prevent DONE.
- Affected files: AGENTS.md and all docs/ governance records.

## ADR-003 — Official MCP 2.3.0 low-level server

- Date: 2026-11-02; status: ACCEPTED; tasks: T1-001, T1-003, T1-004.
- Decision: Official mcp==2.3.0, Pydantic 2.12.5, local Python 3.12.16.
  Use public Server constructor callbacks, model-derived schemas and
  MCPError(INVALID_PARAMS). Business failures return is_error tool results.
- Alternatives: High-level MCPServer returns validation errors as tool results;
  custom framing/lifecycle and SDK monkeypatches violate the contract.
- Rationale: Explicit protocol control while the SDK owns transport/lifecycle.
- Tradeoffs: Manual result construction. Source inspection indicates malformed
  STDIO frames become dropped exceptions; wire diagnostics must verify this.
- Consequences: Keep A7 unmet if confirmed. No private application SDK calls.
- Affected files: pyproject.toml, task1/server.py, task1/__main__.py.
- Sources: [versioned low-level docs](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/docs/advanced/low-level-server.md),
  [official release](https://pypi.org/project/mcp/2.3.0/), installed public
  signatures and STDIO/dispatcher source (E003).

## ADR-004 — Exact process-local mock state

- Date: 2026-11-02; status: ACCEPTED; tasks: T1-002, T1-003.
- Decision: Frozen synthetic records, per-server repository, sequential IDs,
  Decimal(str(amount)) arithmetic with enough subtraction precision to retain
  tiny valid amounts. Return monetary values as exact decimal strings.
- Alternatives: Float balances round; cent quantization adds an unauthorized
  restriction; databases and real payments are out of scope.
- Rationale: Deterministic mock behavior without extra infrastructure.
- Tradeoffs: State disappears on restart. Synchronous no-await updates are
  atomic relative to this event loop, with no cross-thread/distributed promise.
- Consequences: Validation precedes service calls; business failures precede
  commit. Fresh server instances reset records and refund identifiers.
- Affected files: task1/schemas.py, repository.py, service.py, server.py.

## ADR-005 — Preserve unmet SDK wire requirements as explicit diagnostics

- Date: 2026-11-02; status: ACCEPTED; tasks: TASK-1, T1-003, T1-005.
- Context: Both lifecycle modes consume malformed JSON and invalid envelopes
  without the required error frames. Strict wire diagnostics reproduce this.
- Decision: Retain four strict xfail cases and run them with --runxfail to
  expose the failures. TASK-1 remains BLOCKED and A7 remains unverified/unmet.
- Alternatives: Hand-roll a parser/frame bridge, patch the SDK, waive criteria,
  or hide the failures. These conflict with the assessment contract.
- Rationale: The brief explicitly requires honest failing/diagnostic wire tests
  when official transport cannot emit the required errors.
- Tradeoffs: Default regression suite exits 0 with four visible xfails;
  mandatory compliance diagnostics exit 1. A green default command is not DONE.
- Consequences: Seek an official public fix/version, then rerun strict probes
  and regression suite; update evidence rather than silently changing criteria.
- Affected files: tests/test_wire.py, README.md, docs/TASK_LEDGER.md,
  docs/TEST_EVIDENCE.md. No requirements of Tasks 2–4 are changed.

## ADR-006 — Minimal STDIO input-boundary composition

- Date: 2026-11-03; status: ACCEPTED after controlled implementation T1-008;
  originally PROPOSED during T1-007 research; B3 resolved by E007.
- Context: Current official release listings and inspected main sources do not
  provide a ready-made dual-era Server.run error-recovery option. The documented
  dispatcher observer is not injectable through that driver. Public Pydantic
  error details can be identical for different valid IDs, so an exception-only
  adapter cannot meet general ID preservation.
- Recommendation: Prefer a verified upstream fix. Local fallback: observe raw
  input through documented stdio_server(stdin=...) composition, correlate it
  losslessly with decoded items, emit SDK JSONRPCError/SessionMessage objects
  via the SDK write stream, and keep Server.run unchanged. Leave stdout at its
  SDK default to retain descriptor isolation. Full design and source references:
  [T1-007 investigation](STDIO_BLOCKER_INVESTIGATION.md).
- Alternatives: Retain the explicit limitation; wait for upstream; use decoded
  exception details; reconstruct the runner; copy/patch the transport. Waiting
  preserves compliance honesty but leaves B3 unresolved. Exception-only recovery
  loses IDs; recreating runner/transport increases maintenance and assessment risk.
- Rationale: The proposed composition may close the assessment gap while retaining
  official framing, writing, dispatch, cancellation and lifecycle machinery.
- Tradeoffs: Raw-frame correlation, backpressure, explicit stdin ownership,
  context propagation and shutdown races require dedicated tests. Supplying stdin
  skips SDK fd0 diversion; default stdout protection must remain. The input/item
  relationship is inspected behavior requiring a pinned-version contract test.
- Research-phase consequences: No code/dependency/test changes then. Original four XFAIL cases
  remain byte-identical. A real fix produces strict XPASS under the default command;
  use --runxfail to verify all original 98 assertions plus new tests. Do not remove
  markers, weaken tests, or mark TASK-1 DONE before all mandatory criteria pass.
- Proposed affected files: task1/stdio_boundary.py (new), task1/__main__.py,
  new boundary tests, optional test harness support, README and governance records.
- Research-phase affected files: docs only. Subsequent implementation is recorded
  below. Tasks 2-4 remain out of scope.

### Adoption after controlled implementation (T1-008)

- User explicitly authorized the candidate, retaining official MCP 2.3.0 and
  Server.run. Implemented public AnyIO AsyncFile observation, bounded two-frame
  FIFO and receive decoration; SDK stdout parameter remains omitted.
- SDK parser/runner/writer are unchanged; all 124 installed MCP Python files
  match wheel RECORD. Business tools/schemas, pins and manual labs are unchanged.
- Verified all original 98 assertions plus 51 new cases under --runxfail, then
  normal execution after the separately authorized cleanup: 149 passed each.
- Backpressure test withheld draining a real output pipe while 24 large error
  frames were pipelined; IDs/order preserved and capture high-water mark <=2.
  Both cancellation eras, EOF, broken output and print/fd/child isolation pass.
- Accepted tradeoffs: pinned one-line/item contract; explicit stdin bypasses fd0
  diversion while stdout protection stays active; two-frame bound is not a byte
  size limit; existing UTF-8 replacement/nonfinite lexical behavior is preserved.
- No architecture expansion into SDK internals. Adopt for this assessment;
  prefer a future verified upstream remedy and rerun this suite before upgrading.
- Supersedes the research-only/no-code consequences above for the authorized
  implementation. Prior research statements remain the historical decision trail.

## ADR-007 — Retire only the verified obsolete XFAIL decorator

- Date: 2026-11-03; status: ACCEPTED; tasks: T1-008, T1-005, TASK-1.
- Decision: After 149 passing assertions under --runxfail, remove only the single
  parametrized @pytest.mark.xfail decorator; keep the historical sdk_limitation
  marker and all four original bodies/assertions unchanged.
- Alternative: Keep strict XFAIL forever, causing XPASS failure after a real fix;
  weaken/remove the diagnostic assertions. User expressly authorized only the
  obsolete-decorator cleanup after verification, so assertions remain intact.
- Rationale: Normal suite now expresses real compliance without masking failures.
- Tradeoff/consequence: Historical records retain old failures and markers; the
  current suite has no expected failures. Baseline/implementation/cleanup commits
  isolate the change, and source comparison proves body preservation.
- Validation: E007: 149 passed under --runxfail; 149 normal passes after cleanup;
  Ruff passes. ADR-005's retained-XFAIL policy is superseded for the fixed cases.
- Affected file: tests/test_wire.py only for the cleanup itself; evidence/docs updated.

## ADR-008 — Isolated Task 2 guard checkpoint

- Date: 2026-11-04; status: ACCEPTED for T2-001/T2-002 only.
- Decision: Separate task2 project/environment/lock with standard-library pure
  guard runtime; pinned pytest/Ruff development tools. Approved FastAPI/HTTPX
  integration remains deferred until an HTTP checkpoint actually needs it.
- Alternatives: Add dependencies/tests to Task 1's root environment or build an
  HTTP application now. These risk changing verified Task 1 or exceed authorization.
- Rationale: Preserve Task 1 and make security decisions independently testable.
- Tradeoffs: Two environment/lock lifecycles; no HTTP compliance claim yet.
- Consequences: No Task 1 source/tests/dependency/lock edits; no commit/push.
  Full TASK-2 stays IN_PROGRESS. Source: docs/TASK2_REQUIREMENTS.md.
- Affected files: task2 project, new requirements, governance records.

## ADR-009 — Strict single-request guard policy and transport-neutral errors

- Date: 2026-11-04; status: ACCEPTED after independent engineering review,
  as confirmed by the user on 2026-11-04; tasks: T2-001/T2-002.
- Decision: Authenticate first; inspect immutable original UTF-8 bytes; reject
  all duplicate decoded keys and batches; preserve unique valid top-level IDs;
  compare decoded names with literal case-sensitive admin_. Viewer denial is
  exactly -32001 / Unauthorized Tool Call. No client role claims are trusted.
- Notifications: inspect/authorize identically, then reject as unsupported.
  Recognized notifications generate no JSON-RPC response and no permit; their
  future HTTP rejection status is deferred. Protected viewer notifications still
  carry the exact authorization error internally. Explicit null ID is a request.
- Alternatives: Coerce types/normalize names; silently forward unknown shapes;
  partially authorize batches; fabricate notification replies. These introduce
  parser disagreement/bypasses or conflict with JSON-RPC notification semantics.
- Rationale: No uninspected executable input can become a forwarding permit.
- Tradeoffs: Restricted batch/notification support; a later HTTP contract must
  define status/header policy. Integer/string/null IDs supported; no fractional IDs.
- Consequences: Preserve opaque arguments/extensions/raw bytes; no tool-result
  filtering. Settings are immutable, contain no defaults, hide tokens from repr
  and errors, and reject conflicting/unknown roles. Exact choices: task2/CONTRACT.md.
- Affected files: task2/src/task2_proxy/{settings,security,rpc}.py and focused tests.

## ADR-010 — Contain unrepresentable JSON numeric conversions

- Date: 2026-11-04 (America/Los_Angeles); task: T2-002; status: ACCEPTED after
  independent re-verification, confirmed by the user. Corrects ADR-009's baseline.
- Evidence: review input reproduced decimal.InvalidOperation on Python 3.12.16;
  Decimal can also return NaN for that input if its InvalidOperation trap is off.
- Decision: keep Decimal parsing; catch DecimalException at the JSON inspection
  boundary and reject nonfinite conversion results. Unrepresentable numbers yield
  -32700 / Parse error with null ID and no permit, even if their syntax is valid.
- Alternatives: catch InvalidOperation alone (narrower containment); use float
  (overflow/precision loss); replace all noninteger values with opaque markers
  (broader parser redesign). Retaining the current parser with a finite-result
  check and exception-family handler is the smallest correction robust to traps.
- Consequences: parser representation limits are an explicit input limitation;
  no partial envelope/ID recovery on conversion failure. Representable values,
  strict IDs, duplicate-key checks, decoded tool names and raw bytes are unchanged.
- Affected: task2/src/task2_proxy/rpc.py, task2/tests/test_rpc.py, task2/CONTRACT.md.
  Verification: E009, 186 passing tests and both Ruff checks. No HTTP/Task 1 changes.

## ADR-011 — Own the fixed upstream client and validate authorization issuance

- Date: 2026-11-04 (America/Los_Angeles); task: T2-003; status: ACCEPTED after
  independent engineering review, confirmed by the user. Baseline e828729b and
  existing guard behavior retained.
- Decision: add upstream.py with frozen trusted settings, fixed HTTPS/literal-loopback
  HTTP URL, separate optional Bearer credential and one owned HTTPX 0.28.1 AsyncClient.
  Use explicit public Request/send APIs, finite phase/deadline timeouts, connection
  limits, TLS verification, trust_env=False, retries=0 and follow_redirects=False.
  A public CookieJar rejection policy prevents shared upstream cookie state.
- Authorization: the prior public dataclass was not proof of guard issuance. Add a
  private process-local HMAC proof bound to role/body, verified/reinspected before
  sending. Existing guard tests remain unchanged; no inbound credential retention.
- Alternatives: accept raw bytes or any constructed role dataclass (bypasses guard);
  inject externally configured AsyncClient (shared mutable auth/cookie/env settings);
  new client per request (loses pooling); pass inbound headers (credential leakage).
- Rationale: fixed ownership and no client-header interface minimize credential
  confusion; local per-call bodies/IDs isolate concurrent work without a global ID map.
- Tradeoffs: asyncio/process-local permits; no hostile-Python sandbox or replay
  protection; injected transports are trusted test infrastructure. Trusted operators
  still own destination/DNS/egress configuration; private HTTPS endpoints are allowed.
- Affected: security.py, upstream.py, Task 2 dependency/lock, test_upstream.py.
  HTTPX public API/source and CookiePolicy documentation inspected; references in
  task2/CONTRACT.md. E011 records actual tests and preservation checks.

## ADR-012 — Bounded raw JSON responses and transport-neutral failures

- Date: 2026-11-04 (America/Los_Angeles); task: T2-003; status: ACCEPTED after
  independent engineering review, confirmed by the user.
- Decision: forward original authorized bytes. Buffer at most 2 MiB of raw identity
  response data; validate one unambiguous JSON-RPC response and exact ID type/value;
  return unchanged body and nonredirect status. Preserve result/error extensions,
  including opaque exponent tokens, without business schemas or discovery filtering.
  Reject compressed/SSE/batch/malformed/mismatched responses and all 3xx.
- Headers: discard all upstream headers; synthesize JSON Content-Type and no-store.
  Do not propagate cookies, challenges, hop-by-hop/nominated fields, MCP sessions,
  CORS, redirects or upstream lengths. T2-004 owns final HTTP framing/status mapping.
- Failures: typed generic UpstreamError kinds for timeout/transport/redirect/invalid
  response/ID mismatch/size/closed; no fabricated JSON-RPC code. Propagate caller
  cancellation and close acquired responses. No automatic retry of mutating calls.
- Alternatives: blindly relay responses/headers (misrouting, credential/framing
  hazards); deserialize/reserialize business payloads (changes precision/extensions);
  implement Streamable HTTP/session/SSE behavior now (out of authorized scope).
- Consequences: JSON-only/stateless upstream interoperability, bounded buffering
  and explicit response envelope/numeric limits; no real DNS/TLS/wire claim from
  mock tests. Endpoint error mapping and real upstream validation remain later work.
- Affected: upstream.py, test_upstream.py, Task 2 contract/README; evidence E011.

## ADR-013 — Thin FastAPI composition and explicit HTTP policy

- Date: 2026-11-04 (America/Los_Angeles); task: T2-004; status: ACCEPTED after
  independent engineering review, confirmed by the user. Baseline 0b2e0b7 components
  and the reviewed T2-004 implementation remain unchanged.
- Decision: create_app factory, exact POST /mcp and lifespan-owned existing adapter.
  Load trusted settings during startup, one client per app/event loop, cleanup in
  finally/async context. No import-time config/client, automatic docs or slash redirects.
- Order: HTTP metadata/framing -> existing authenticate -> bounded stream read ->
  existing guard_request -> existing adapter.forward. Deliberate second auth check
  inside the accepted guard avoids redesigning permit issuance; no parsing/role-rule
  duplication. request.stream plus byte count/EOF length check and total read deadline
  handle chunked/lengthless bodies. No framework JSON models/body deserialization.
- HTTP policy: 401 generic/challenge; 403 exact protected-call RPC denial; 400 existing
  RPC parse/envelope/parameter errors; 415 unsupported media/encoding; 413 size;
  408 body deadline. Recognized notifications get empty 400/403. Upstream failures
  use 502/503/504 plus -32603/caller ID; valid upstream bytes/statuses pass unchanged.
  Unexpected exceptions are sanitized without logging request/exception material;
  ASCII local RPC serialization preserves all existing string ID values.
- Alternatives: FastAPI HTTPBearer/body models (different duplicate-header/JSON
  coercion behavior); per-request client (loses pool); refactor accepted guards
  (unnecessary baseline risk); accept compressed/SSE bodies (outside contract).
- Tradeoffs: JSON-only service, repeated constant-time token comparisons, bounded
  buffering and generic diagnostics. ASGI server owns wire framing/draining/TLS and
  graceful request draining before shutdown. Trusted upstream payloads are unfiltered
  and must themselves avoid exposing secrets. Full HTTP contract: task2/CONTRACT.md.
- Dependencies: FastAPI 0.162.0 runtime; asgi-lifespan 2.1.0 dev; Uvicorn 0.54.0
  optional serve extra. Only Task 2 environment/lock changes; no sockets started.
- Evidence: E013, 400 passes and both Ruff checks; all prior 300 cases/modules retained.
  Affected: app.py/test_app.py, Task 2 config/lock/docs and governance records.

## ADR-014 — Independent loopback processes, redacted journal and event-driven faults

- Date: 2026-11-04 (America/Los_Angeles); task: T2-005; status: ACCEPTED after
  independent engineering review, confirmed by the user. Production baseline
  be9ddd8 and approved wire tests unchanged.
- Decision: test-only stdlib ThreadingHTTPServer peer and real Uvicorn/HTTPX proxy
  subprocesses, parent http.client/raw-socket clients. Each child binds 127.0.0.1:0;
  proxy supplies its socket to public Server.run. Existing create_app is wrapped
  only by a relaying ASGI event observer; no parser/runner/production monkeypatch.
- Synchronization: JSON stdout bound/lifespan/request-finished events, readiness
  HTTP probes, peer Condition/Event gates and bounded parent requests/waits. The
  concurrency test confirms 10 permitted receipts pending before releasing them;
  no sleep-duration assertions. Cleanup uses stdin graceful exit then bounded
  terminate/kill fallbacks, explicit waits/pipe closure and reader joins.
- Evidence: in-memory request/response byte journal with auth/cookie/role booleans
  and header names; no stored raw auth. Synthetic tokens are process-local/env only.
  Authenticated peer control/health operations do not count as protocol requests.
  Only sanitized child outcome metadata is persisted in an ignored cache artifact.
- Alternatives: ASGI/mock-only tests (cannot expose real framing/connect behavior),
  external MCP peer (uncontrolled/network scope), parent free-port probe then child
  rebind (race). Independent stdlib peer avoids using the same ingress framework.
- Tradeoffs: test-only mock protocol/tools, Windows/h11 evidence, OS-specific
  refused-connect delay and no TLS/DNS/HTTP2/session/load proof. Refusal probe showed
  0.5s was a timeout; raising only fixture connect timeout to 3s exposes actual
  WinError 10061. Production mapping already distinguished timeout/refusal correctly.
- Affected: tests/http_wire_server.py, http_wire_support.py, test_http_wire.py;
  pytest marker only in pyproject; no new dependency or production-source change.
- E015: 452 total passes/52 wire cases, Ruff pass; 33 local-rejection cases have
  zero protocol receipts. Cleanup: 12 children reaped, zero forced/live readers;
  two deliberate nonzero exits accounted for. Independent acceptance recorded in
  E016; T2-006 remains unauthorized.

## ADR-015 — Evidence provenance and final audit acceptance gate

- Date: 2026-11-04 (America/Los_Angeles); task: T2-006; status: ACCEPTED following
  independent ChatGPT engineering review, confirmed by the user. T2-006/TASK-2 DONE.
- Decision: preserve accepted architecture/code/tests/configuration at aa343b3;
  audit with fresh complete suites in separate environments, an isolated locked
  Task 2 installation, CLI/real-loopback smoke probes, current-file/reachable-Git
  inspection and an explicit requirements-to-test matrix. Original user-supplied
  requirements are distinct from approved implementation choices and excluded work.
- Alternatives: rely only on earlier passing counts (no fresh regression evidence);
  combine environments (hides task isolation/dependency drift); add features or
  redesign accepted components during audit (outside authorization).
- Consequences: no new production architecture. Documentation-only corrections
  remove stale current-status claims while preserving historical records. Pattern
  matches require context review; a clean scoped scan is not universal secret/CVE
  assurance. Local-only archive excludes are disclosed as publication hygiene risk.
- Accepted verdict: APPROVED, assessment-ready within documented requirements.
  Independent review confirmed eight traceability rows, source/test references and
  evidence/docs consistency. E018 records reported acceptance; E017 executions are
  unchanged and not rerun. Authorize one documentation-only final acceptance commit;
  no implementation/config changes, push or Tasks 3/4. No architecture redesign.
  Existing operational limits and bounded security-audit scope remain applicable.
- Affected: audit/traceability report, README/contract and governance documentation
  only. Evidence: E017; 452 Task 2/149 Task 1 passes, both Ruff checks per task,
  fresh locked install/imports, CLI startup/shutdown and bounded publication scan.

## ADR-016 — Task 4 transactional reservations and sequential provider fallback

- Date: 2026-11-04 (America/Los_Angeles); status: APPROVED WITH CONDITIONS following
  independent review, confirmed by the user; conditions finalized as P1-P4 below.
  Source: docs/TASK4_REQUIREMENTS.md R1-R7. T4-002 pure implementation authorized.
- Confirmed: primary HTTP 429 OR primary 3,000 ms timeout triggers backup; local
  tenant-quota 429 never does. No Retry-After comparison, retry loop or hedging.
  Tenant-key quota and SQLite usage survive concurrent requests/process restarts.
- Proposed architecture: isolated task4 package/environment/lock; tenant resolution,
  pure accounting/types, SQLite store, provider adapters, orchestration and HTTP
  boundary. Do not import/change Tasks 1/2. Provider APIs/tokenizers are unspecified.
- Accounting proposal A1-A5: input+output across both attempts; reliable model-specific
  bounds and enforced output caps; reserve primary+backup together before dispatch.
  Normal charges use admission-time rolling (now-60s,now], active holds stay counted.
  Reconcile known usage; unknown usage consumes the bound. This is conservative and
  can reject a primary-only request that would fit; original brief does not mandate
  this counting/reservation policy. Independent acceptance is required.
- Transactions: BEGIN IMMEDIATE for check-and-reserve; separate short expected-state
  transitions/settlement, no network inside transactions. A DB-owning worker per
  process, bounded busy waits, one on-disk store and tenant-scoped keys/queries.
  No SQLite-in-Python thread-safety shortcut or process-local-lock correctness claim.
- Runtime evidence E019: available CPython 3.12.16 uses SQLite 3.53.1/threadsafety 3;
  no DB opened. Propose WAL/FULL on verified local storage, rechecking the future
  Task 4 environment and PRAGMA results. SQLite documents the WAL-reset fix in
  3.51.3/later and patched backports; WAL still has one writer and is same-host only.
  Sources: [WAL](https://www.sqlite.org/wal.html),
  [transactions](https://www.sqlite.org/lang_transaction.html),
  [FULL synchronization](https://www.sqlite.org/pragma.html#pragma_synchronous).
- Fallback: durable single-owner phase change after primary 429 or total-exchange
  deadline; await cancellation/close primary before one backup. At most one call
  per model, no hidden retries/redirects/parallel local calls. Remote work/billing
  after timeout cannot be proven stopped; reservations cover uncertainty.
- Recovery: persistent holds/intent, finite overall reservation deadline, lazy
  abandoned-hold conversion to full conservative charges; never clear holds on
  another worker's startup or replay an uncertain remote call. Stable external
  identity secret/verifier prevents accidental tenant namespace reset. No broker,
  distributed lock/lease service, response cache or automatic billing reconciliation.
- Alternatives: post-response-only counting (oversubscription); reserve primary
  only then re-admit backup (can prevent required fallback); hedge/retry (duplicate
  execution); hold DB lock during LLM call (writer starvation); distributed services
  (unnecessary assessment scope). Rollback journaling remains an alternative if
  WAL prerequisites cannot be met; journal selection must be verified, not assumed.
- Tradeoffs/open decisions: conservative availability/overcharging, local writer
  throughput, trusted clock/storage; exact providers/token categories/output caps,
  API-key transport/rotation, HTTP schema and backup/overall deadlines need approval.
  No exactly-once provider execution or multi-host SQLite promise. A1-A10 are not
  silently promoted to assessment requirements. Proposed tests: T4-Q1 through Q12.
- Affected now: documentation/governance only. No application source/dependencies,
  T4-002, Task 3, commit/push. Preserve accepted Tasks 1/2 and stop for design review.

### Finalized conditional-approval policies / T4-002 authorization

- P1: reservation timestamp is the admission UTC sample; normal settlement replaces
  holds at that same timestamp. Settled interval (t-60,000,t], exact quota allowed;
  ALL unresolved holds count regardless of age. Reject future target-tenant entries/
  regressed clock/duplicate identities; do not double count settlement and holds.
- P2: reliable model-specific input bound + enforced output cap required for each
  model before dispatch; exact nonnegative signed-64-bit integers, positive model
  total, no overflowing combined total. No caller estimates or boolean attestations.
  Missing/unreliable bounds fail closed before I/O; pure internal record validation
  is arithmetic, not provider/tokenizer certification. Actual adapters deferred.
- P3: monotonic start+3,000 ms total primary exchange deadline, tie means timeout;
  one extra 500 ms total cancellation/close grace. Never wait indefinitely for a
  cancellation-resistant task. Backup only after confirmed primary termination/close;
  otherwise sanitized unavailable, no backup, conservative usage retained. The
  500 ms grace/measurement scope are engineering policies, not brief requirements.
- P4: one tenant-scoped identity/expected-state settlement; identical repeat no-op,
  conflicting/stale update fails closed. Unknown usage keeps its bound; only proven
  unsent capacity is released. Holds survive restart; lazy transactional conversion
  at/after overall deadline uses full bounds/deadline timestamp once. No silent
  release/replay or old-worker overwrite. No recovery execution in T4-002.
- These policies are engineering assumptions finalized under the user's request;
  only R1-R7/confirmed clarifications are the assessment contract. Prior proposed
  restrictions above are historical and superseded only for authorized T4-002.
- T4-002: independent project/environment/lock, immutable typed internal records,
  pure injected-clock snapshots/admission decisions and combined reservation math.
  No state mutation, SQLite/provider/HTTP/recovery execution or concurrent-permit
  guarantee. Preserve Tasks 1/2; verify new pytest/Ruff and stop for review.

## ADR-017 — Pure typed accounting snapshots before transactional admission

- Date: 2026-11-04 (America/Los_Angeles); task: T4-002; status: ACCEPTED following
  independent engineering review, confirmed by the user. Accepted Tasks 1/2 preserved.
- Decision: standard-library-only task4_limiter models/accounting package, isolated
  Python 3.12.16 project/lock/env. Pin tested pytest 9.2.0/Ruff 0.17.3 dev and
  setuptools 82.0.1 build; do not add unused HTTP/provider/database dependencies.
- Frozen typed model bounds and combined plan; settled/outstanding entries share
  tenant-scoped identity but cannot coexist under the same ID in a valid snapshot.
  Exact integer/range checks reject coercions/overflow; zero known usage is valid,
  zero bound is insufficient. Model and counting-policy metadata required, but
  metadata is not a proof that a tokenizer or output limit is trustworthy.
- calculate_usage implements P1's exact interval plus all holds. assess_admission
  samples an injected UTC clock once, rejects regression/future target entries,
  computes combined demand and denies existing overage. Records/inputs are immutable
  or unmodified; pure decisions are not admission permits or stored reservations.
- Alternatives: mutable in-process quota store (wrong checkpoint/concurrency claim),
  inspect tokens through a made-up tokenizer (unreliable provenance), auto-expire
  old holds (silent loss of uncertain usage), implement SQLite early (scope breach).
- Consequences: deterministic arithmetic and strict internal contracts now verified;
  T4-003 still must atomically sample/check/reserve with one persistent snapshot.
  Actual model/tokenizer enforcement, tenant key resolution, idempotent settlement,
  bounded cleanup and recovery remain future integration work, not passing claims.
- Affected: task4 config/lock/README, models.py/accounting.py and two focused test
  files; governance/status updates. Evidence E020: 169 passes, both Ruff checks,
  eight-package locked install/import/pip checks. E021 records reported independent
  approval: 169 tests, 12,000 differential checks and six invariants passed, no blocking
  defect. No new local tests/Ruff or architecture/logic changes. One foundation commit
  authorized; no T4-003, Task 3 or push. Preserve all pure-boundary limitations.

## ADR-018 - SQLite durable admission and conservative attempt settlement

- Date: 2026-11-04 (America/Los_Angeles); task T4-003; status ACCEPTED following
  independent engineering review within Windows fixed-local-drive/supported SQLite
  scope, confirmed by the user. Preserve accepted accounting/storage implementation.
- Decision: three STRICT tenant-scoped tables, integer amounts, composite PK/FK,
  terminal state/charge/source checks and tenant/time/deadline/block indexes. HMAC
  transient API keys under a stable external secret; persist only digest/verifier,
  UUIDs and accounting state. Check schema/policy/identity on every transaction.
- Verify SQLite >=3.51.3 and Windows fixed local storage before enabling WAL.
  Actual SQLite 3.53.1/S: DRIVE_FIXED=3; configure WAL/FULL/foreign_keys and explicit
  busy timeout. Current detector fails closed on other OS/network volumes; a future
  portable detector requires separate implementation/verification, not attestation.
- Admission writer transaction covers clock sampling/watermark, lazy tenant recovery,
  snapshot, existing pure assess_admission, both inserts and explicit SQL COMMIT.
  Success is returned only after COMMIT. Read-like APIs also transact to persist
  time/recovery. Global UTC regression fails; future/faulty clock assumptions remain.
- Storage-only start intent, known/unknown settlement and unsent release are separate
  short transactions. Identical finalization no-op; conflicting/stale updates fail.
  Normal charges keep admission timestamps; overdue holds become full deadline-
  anchored charges once. Unknown execution is never refunded or replayed. A bound
  breach durably blocks tenant admission pending operator investigation.
- Interface is synchronous with one private connection per operation/calling thread,
  rather than adding a permanently running DB worker now. Future async service can
  submit whole calls to its bounded worker/executor; close requires draining first.
  No network inside transaction, no Python lock as cross-process correctness tool.
- Alternatives: deferred SELECT then separate insert (race); shared thread-disabled
  connection (transaction interleaving); per-process memory lock (no process safety);
  guessed refunds/restart resets (quota bypass); unverified filesystem WAL (unsafe);
  extra distributed recovery components (outside assessment scope).
- Tradeoffs: SQLite single writer/connection overhead, strict global clock and
  trusted local filesystem, no automatic retries/retention/remote billing recovery.
  Store initialization is not restoration after deleted DB files. Provider execution,
  actual cleanup/deadlines and fallback selection remain T4-004, not storage proofs.
- Evidence E022: full 221 tests (169 accepted/52 new), Ruff pass; 15 spawned children
  reaped normally, admission/duplicate/settlement races and restart persistence pass.
  Transaction/commit fault tests are scoped storage tests, not final system audit.
- Affected: storage.py/four new fixture/test files, Task 4 README/requirements and
  governance records. No dependency/pure-code/accepted-test edits. One approved
  T4-003 milestone commit authorized; no T4-004/provider/HTTP work or push.
- Review provenance E023: 221 passes/15 normally reaped children and three further
  scenarios reported in an isolated Linux copy using test-only platform/SQLite gate
  shims. This is not native Linux support or native Windows gate evidence. E022's
  native Windows/SQLite 3.53.1 execution remains authoritative. No source defect,
  architecture/gate modification, local test/Ruff rerun or shipped shim.

## ADR-019 - Owned asynchronous attempts over durable SQLite intent

- Date: 2026-11-04 (America/Los_Angeles); T4-004; status ACCEPTED following
  independent engineering review, confirmed by the user. Accepted ADR-016/017/018
  and ebc226a are preserved; no architecture or implementation change.
- Decision: resource-free trusted Provider.prepare creates a one-shot bounded/cap-
  enforcing handle; separate execute and aclose. Controlled typed status/usage,
  no invented vendor/tokenizer/endpoint, credentials external. Matching metadata
  is necessary, not proof of a real accounting guarantee. No caller estimates.
- Require explicit backup and overall lifetimes; no numeric deployment defaults.
  Combined reservation covers both attempts. One bounded offload lane calls whole
  synchronous store APIs; SQLite transactions, not that lane, enforce concurrency.
  Durable start before send, recheck budget/cancellation after DB completion and
  at execution entry. Success is returned only after known/unknown settlement and
  release of provably unused backup. Late reliable usage can settle, never win
  the response deadline. Total bound breach uses storage's durable block; an
  in-total category/cap breach charges full bound and quarantines this instance.
- Primary monotonic 3000 ms / original deadline+500 ms cleanup ceiling, one shared
  termination+close grace; boundary ties fail closed. Only primary 429/owned
  deadline expiry trigger one backup after confirmed termination/close. Early
  adapter timeouts do not prove deadline expiry and do not trigger fallback.
  Backup uses explicit finite timeout and no third attempt. No retries/hedging.
- One shielded request workflow remains owned after caller cancellation. Signal
  cancellation, discover actual DB completion, finalize provably unsent intent or
  charge known/unknown dispatched usage. Never infer DB rollback from coroutine
  cancellation. Ambiguous commits leave holds, not automatic retries/refunds.
  Owner drains before store/loop close. Failed/unconfirmed cleanup stops further
  dispatch, retains strong task references and durable holds, returns sanitized
  unavailable; aclose can explicitly report unclean shutdown. Remote cancellation
  and billing are not proven by local task termination.
- Alternatives rejected: cancel-and-forget to_thread (false rollback), unbounded
  wait_for cancellation (may exceed deadline), overlapping fallback (duplicate
  owned execution), refund 429/timeout as zero (unproven billing), implicit backup
  timeout/vendor tokenizer (unspecified contract), production SQLite changes
  (unnecessary accepted-baseline risk). Official Python 3.12
  [asyncio tasks/cancellation](https://docs.python.org/3.12/library/asyncio-task.html)
  documents shield, to_thread and wait semantics used here.
- Tradeoffs: conservative combined reservation/unknown billing may reject early;
  one offload lane per service limits DB submission concurrency but is not a
  cross-process lock. An uncooperative adapter cannot be forcibly terminated by
  asyncio; quarantine and explicit unclean shutdown are required. Blocking OS DB
  I/O cannot be cancelled safely; drain can wait on it. Trusted UTC/local Windows
  storage and externally authenticated key/model adapters remain prerequisites.
- Affected: new providers.py/service.py and three test/support files; Task 4
  README/requirements/governance. No accepted code/test/config/lock changes or
  installations. E024: full native 324 passes and Ruff checks; independent review
  accepted (E025). One approved milestone commit only; HTTP/T4-005, real vendor
  integration, final audit and push remain excluded.

### T4-004 acceptance provenance / scope

- User APPROVES T4-004 on 2026-11-04 (America/Los_Angeles), no blocking production
  defect. Reported isolated Linux review used review-only platform/SQLite changes:
  324 passes, additional category-cap/total-bound adversarial checks and a real
  monotonic fallback probe at approximately 3.020 seconds with one backup and
  conservative accounting. Commands/versions beyond that report were not supplied.
- E024 native Windows/Python 3.12.16/SQLite 3.53.1 evidence remains authoritative;
  Linux compatibility runs do not establish native Linux support or shipped gate
  correctness. No compatibility change is included. Timed probe is not a latency
  SLA, real-provider integration or proof of remote termination/billing semantics.
- Accepted design/tradeoffs above remain intact. E025 records reported acceptance
  and inspection, not new tests. One descriptive approved-source/test/doc commit;
  preserve implementation/pins/Tasks 1/2, no T4-005 or push. TASK-4 remains incomplete.

## ADR-020 - Authenticated bounded HTTP around accepted orchestration

- Date: 2026-11-04 (America/Los_Angeles); T4-005; status ACCEPTED following
  independent engineering review, confirmed by the user with qualification below.
  Preserve accepted c889236 modules/tests and Tasks 1/2; no architecture change.
- Decision: isolated FastAPI factory; POST /generate prompt-only strict JSON;
  manual bounded streaming read and explicit validation/error envelope avoid raw
  input in automatic validation responses. Require registered external Bearer keys,
  keep allowlist digests, derive stable identity through existing SQLite HMAC only.
  No client tenant/model/token estimate authority or cookie/role forwarding.
- Lifespan offloads store initialization, owns provider context and accepted service,
  drains service before provider/store close. Retain startup worker/shutdown task
  after cancellation; quarantine resources on unconfirmed close, never false success.
  Single post-body disconnect consumer cancels the public service call, preserving
  accepted request-owner/DB accounting. No duplicate storage/routing logic or changes
  to accepted modules. Default adapters fail BoundsUnavailable before admission;
  no invented vendor/tokenizer. Deployment injects trusted Python resources only.
- HTTP choices (not original R1-R7): 64 KiB/5 s default body limits, UTF-8 JSON only,
  no compression, prompt <=16000 chars, one Bearer header/32-256-byte registered key,
  opaque server UUID; 400/401/404/405/408/413/415/429/499/502/503/504 mappings in
  requirements. Distinguish tenant_quota_exceeded from provider_rate_limited.
  Uvicorn/h11 owns transport parsing and may reject framing before JSON envelope.
- Dependencies: FastAPI 0.162.0 runtime; HTTPX 0.28.1/asgi-lifespan 2.1.0 dev;
  Uvicorn 0.54.0 serve extra. Existing pytest/Ruff/build pins preserved, isolated
  lock resolves 27 packages. No Task 1/2 dependency/environment change. Resolved
  Starlette 1.10.0/Pydantic 2.14.2 are tested in Task 4, not silently assumed from
  Task 2. Official [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)
  and [Starlette request streams](https://starlette.dev/requests/) consulted.
- Real-wire design: independent proxy/synthetic upstream processes, loopback only,
  child-bound dynamic ports/HTTP readiness, trusted fixture counters/caps, SQLite
  journals and bounded state polling/release events. No production vendor contract.
  Native invalid-startup harness exposed daemon stdin reader finalization failure;
  replace with async stop-file control, preserving expected failure assertion.
- Alternatives: caller estimates/tenant IDs (quota bypass), permissive reflected
  validation/debug errors (secret/prompt leak), DB calls on event loop (blocking),
  guess production tokenizer/vendor (unsupported), mock-only verification (misses
  framing/disconnect/process behavior), cancel-and-discard workers (false rollback).
- Tradeoffs: immutable allowlist needs controlled restart for revocation, no rotation
  migration, conservative reservation may reject early; no semantic completion
  redaction guarantee, TLS/public deployment/load/final fault audit deferred. Broken
  trusted adapters/OS I/O can prevent clean shutdown; retain ownership and surface
  controlled failure. Access/proxy logging must be configured safely at deployment.
  All accepted local Windows/runtime restrictions remain. E026 records actual
  verification/initial failures; E027 records independent acceptance. One approved
  milestone commit only; no T4-006 or push.

### T4-005 independent acceptance provenance

- User APPROVES T4-005 on 2026-11-04 (America/Los_Angeles), no blocking production
  defect. All 427 cases passed independently across separate review runs; 29 wire
  cases passed in split groups. Authentication, quota rejection, fallback,
  concurrency, persistence and sanitization were reviewed.
- Linux review used review-only compatibility substitutions. One combined Linux
  wire run stalled during fixture teardown; it was NOT a completed all-at-once
  pass. Split results must not be presented as that combined run, proof of native
  Linux support, or a new local execution. No review substitutions ship.
- E026 native Windows/Python 3.12.16/SQLite 3.53.1 full-suite verification remains
  authoritative. No new review commands/versions/cleanup counts were supplied;
  E027 records only the provided evidence and Git/source inspection. Accepted
  design/tradeoffs unchanged. One approved T4-005 commit; no code/test/config edits,
  test rerun absent unexpected implementation changes, T4-006 or push.

## ADR-021 - 2026-11-04: T4-006 scoped assessment-readiness evidence

- Status: **independently ACCEPTED**, user confirmation 2026-11-05; provenance below.
  T4-001 through T4-006 accepted; TASK-4/T4-006 DONE. No production
  architecture change. Affects AGENTS/root README, Task 4 README, requirements,
  final audit, ledger, build log and E028/E029 only.
- Context: user authorizes verification/documentation over 6eaccaf, not feature
  development. R1-R7 come from the user's recovered original brief; P1-P4 and H1-H8
  are independently approved choices. Stock factory intentionally has no real
  provider/tokenizer. Earlier Linux compatibility review is qualified and must
  not become native Linux support or an invented combined wire pass.
- Decision: recommend READY within approved accounting and supported Windows/local
  SQLite/trusted-adapter contract, pending independent review. Execute all three
  complete suites and six Ruff commands fresh; new lockfile environment/imports,
  deterministic ASGI/socket selectors and stock Uvicorn CLI 503/start/exit probe.
  Add explicit deterministic reproduction commands to README rather than invent a
  vendor integration to make stock execution appear successful.
- Alternatives: reuse prior evidence as fresh (invalid); require an unstated real
  vendor/production deployment or add crash infrastructure during audit (scope
  expansion); label all crash recovery verified from WAL/FULL/restart tests alone
  (unsupported). Keep current code and evidence gaps visible instead.
- Tradeoffs/consequences: local quota is the approved admission-time invariant,
  conditional on trustworthy model bounds/caps and UTC clock. Upfront combined
  reservation can deny early. Real vendor billing/tokenization, abrupt OS kill,
  physical power/disk/WAL faults, load/public ingress/TLS and arbitrary resistant
  resources remain unverified; graceful restart and injected fault tests are
  narrower evidence. Local-only archive ignores require explicit future staging.
- Evidence: E028 actual 149/452/427 fresh passes, all Ruff checks, clean 27-package
  install, 6/7 selector passes and controlled stock CLI. Current/reachable-history
  review found no actual secret/tracked runtime artifact, with scan limits stated.
  No code/tests/config/locks modified; no new feature, commit/push or DONE claim.
  Next: independent review of TASK4_FINAL_AUDIT.md/E028; separately authorize any
  corrective work or final acceptance/Git checkpoint.

### T4-006 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User reports final independent engineering APPROVAL: Task 4
assessment-ready within documented requirements, supported Windows/SQLite and
trusted-adapter policies. All seven traceability rows reviewed against previously
submitted source/test evidence, all named automated references verified; E028,
documentation, limitations and submission findings consistent. No new review
command lines, runtime versions, test counts/timings or extra executions supplied;
this is acceptance provenance, not a new test pass. E028 native audit evidence
and all earlier Linux review-only/split-run/stalled-teardown qualifications remain
unchanged. No new provider/tokenizer/production-deployment or physical-crash claim.

TASK-4/T4-006 DONE. Accepted architecture/tradeoffs unchanged. Latest user authorizes
one final documentation-only acceptance commit, exact nine-file allowlist, staged
whitespace/artifact/secret inspection and final SHA/status verification. Preserve
all implementation/tests/config/dependencies/locks and Tasks 1/2. E029 records
reported acceptance and actual Git/document inspections; no tests/Ruff rerun absent
unexpected implementation/config changes. No Task 3/push; stop at Git checkpoint.

## ADR-022 - 2026-11-05: Task 3 conditional architecture and provisional streaming contract

- Status: T3-001 independently APPROVED for the explicitly defined synthetic
  profile, user confirmation 2026-11-05; acceptance provenance below. T3-P1-P8 /
  T3-L are accepted engineering policies, not original vendor requirements.
  T3-001 DONE; TASK-3 IN_PROGRESS. Original proposal history below is retained.
- Provenance: no original Task 3 brief recovered after second repository/reachable
  filename/attachment inspection. Available T3-R1-R8 are high-level user requirements,
  not inferred PII categories/provider APIs. Preserve distinction in requirements.
- Accepted architecture: isolated project/env/lock; explicit UTF-8/SSE parser,
  validated payload adapter, request/channel-local redactor, one pull-driven async
  chain, bounded memory and owned cancellation. Future FastAPI/Starlette handles
  HTTP/lifespan, HTTPX owns pooled upstream streaming; neither supplies the PII proof.
- Proposed security simplification: K = ASCII alnum plus ._%+@-. Withhold complete
  maximal K-run (cap 256); all proposed EMAIL/PHONE/SSN forms lie within K. Real
  delimiter or validated channel-done proves candidate complete, then classify
  and replace whole candidate with [REDACTED] if any rule matches. Any @ candidate
  is conservatively masked even if malformed. Before character 257 fail closed;
  never release an unfinished prefix. Errors/transport EOF are not safe finalizers.
  This yields a partition-invariant proof under the explicit grammar, not broad
  semantic/Unicode/obfuscated PII recognition. Phone forms/normalization exclusions
  in T3-P1/P2 need explicit review, not silent implementation assumptions.
- Proposed wire semantics: synthetic JSON delta(channel,text), done(channel),
  global end({}) and fixed upstream error. Four channel identities, no state reset
  at event/delta boundaries. Rechunk generated safe output, preserve per-channel
  order, drop comments/id/retry/unknown fields and reject unrecognized payload/event
  shapes. No arbitrary metadata passthrough, provider sentinel or success-on-EOF.
- Limits proposed separately: 4 KiB processing chunks, 8 KiB lines, 16 KiB events,
  4096-scalar deltas, 256-char candidate/channel, 1024-scalar/8 KiB pending output,
  four channels and 16 concurrent streams/process. Explicit monotonic upstream/
  send/overall/cleanup budgets; all numeric choices provisional, not brief wording.
- Cancellation/failure: no read-ahead queue, await downstream send; close response
  in finally with one bounded cleanup budget, retain/quarantine uncertain resources.
  Fixed postheader SSE error or connection close; never echo raw buffers/diagnostics,
  fabricate success termination or retry/replay a generation automatically.
- Alternatives: independent chunk regexes/guessed overlap (cross-boundary leak),
  buffer complete stream (violates progressive bounded operation), general semantic
  PII claim (unsupported), unbounded ambiguous token (memory risk), forward opaque
  metadata (privacy bypass), invent a vendor API (missing contract). More permissive
  bounded automata remain possible after an approved grammar/correctness argument.
- Tradeoffs: harmless @ strings overmasked, punctuation within candidate removed,
  long harmless identifiers/URLs rejected, formatted/international/obfuscated PII
  outside the narrow profile not certified. No fixed content latency for an endless
  candidate; deadlines terminate instead of raw flush. Rechunking/metadata loss
  requires approval. Python/transport/OS memory copies require measurement, not a
  false RSS sum from logical counters. Real provider/API/browser/auth contract
  remains a later explicit approval item before HTTP integration.
- T3-002 boundary: isolated foundation plus pure models/SSE/profile/redaction and
  T3-Q01-Q12 tests only AFTER approval and authorization; no HTTPX/FastAPI/client/
  service/provider/network code yet. Full matrix T3-Q01-Q21 in requirements.
  No completed task changes, source/install/test execution/commit/push this session.
  E030 records actual inspections only. Next: independent exact-contract review.

### T3-001 final acceptance / T3-002 authorization - 2026-11-05

User APPROVES the documented synthetic profile, narrow ASCII email/phone/SSN,
whole-candidate [REDACTED], exact alphabet/256 cap/four channels, JSON-over-SSE
delta/done/end/fixed-error, dropped metadata and rechunked per-channel order.
Resource caps/deadlines are approved engineering policies, not original brief
wording. Original Task 3 vendor brief remains unavailable; no universal PII or
vendor-specific interoperability claim. T3-001 DONE and independently accepted.

Mandatory rules explicitly preserved: only valid done finalizes; unexpected EOF/
malformed termination cannot flush tails; independent byte/scalar/serialized limits;
no raw threshold-prefix release; no data after done/duplicate done/early global end;
reject duplicate/ambiguous payloads; every supported pattern character lies in K.
User authorizes T3-002 isolated pinned pure implementation/tests and governance,
not HTTPX/network, FastAPI, wire, T3-003 or commit/push. E031 records actual local
verification; this approval itself is not a new test execution.

## ADR-023 - 2026-11-05: bounded pure Task 3 pipeline and fail-latched ownership

- Status: T3-002 independently ACCEPTED, user confirmation 2026-11-05; review
  provenance below. Accepted implementation/architecture unchanged.
  Applies only to task3 pure source/tests/config/lock/README and governance.
- Decision: five small modules (package init plus models/sse/payloads/redaction),
  standard-library runtime; Processor is a synchronous pull generator, not an
  async service/network adapter. Typed frozen events/private payload repr, bounded
  tightened-only Limits, fixed generic errors; immutable shared default limits.
- SSE: raw byte counters before retained growth, incremental strict utf-8-sig,
  deferred CR to count split CRLF before event dispatch, bounded line/data storage,
  lazy event iteration. Metadata drops without output/authority. Resource lexical
  JSON precheck precedes stdlib syntax/escape decoding; strict exact schemas.
- Redaction: request-local four-channel state, <=256 ASCII hold/channel, classify
  on real delimiter/done only. Closed channels never reused, global end only after
  all opened channels done, fixed upstream error clears tails. No full-stream
  buffering, output fragment <=256 scalars, independent scalar/UTF-8/JSON frame
  checks before retained encoding buffer extension. Encoder is shape-only; only
  Processor/redactor composition is the privacy path, not arbitrary encoder calls.
- Ownership: fully consume/close each iterator. Failure/abandonment clears tails,
  latches unusable state and revokes success; terminal stops reading trailing
  upstream bytes. Success is pure protocol completion, not downstream delivery.
  Real disconnect/deadline/backpressure ownership remains later work.
- Alternatives: mutate completed projects/shared environments (baseline risk),
  per-chunk regex or premature-tail flush (leak), queue/list all events (unbounded
  flow), custom full JSON parser (unnecessary), implicit EOF completion (leak),
  add FastAPI/HTTPX now (outside T3-002). Chosen bounded lexical precheck does not
  replace the JSON syntax parser. No arbitrary metadata/extension passthrough.
- Tradeoffs: byte-wise incremental decoding is deliberately simple and bounded,
  not throughput-optimized; Python objects/encoding scratch add overhead beyond
  logical counters. Conservative masking/long-token rejection and narrow scope
  remain accepted. Pure tests do not certify RSS/HTTP async behavior/real providers.
- Evidence E031: final 362 passes, zero failures/skips/warnings/xfails; both Ruff
  checks pass (11 files). Initial cache warning, B008 findings and missing test
  import collection failure retained as actual outcomes. New terminal-failure
  regression ensures failed/abandoned end encoding cannot leave success asserted.
  No accepted Task 1/2/4 implementation/test/pin changes. Next: independent review,
  not T3-003, commit or push.

### T3-002 independent acceptance provenance - 2026-11-05

User reports APPROVED: complete independent 362-pass suite, additional 1200
randomized interleaved SSE streams and 2961 channel-reference comparisons, 256
candidate-prefix withholding probes plus character-257 fail-closed check, 376
truncated-wire cuts without whole-value PII leakage, 24000-event retained-state
test and Python compilation passed. No blocking production defect identified.

Independent review ran Linux/Python 3.13.5/pytest 9.0.2 with ONE pytest configuration
warning; specific warning text, commands/timings and extra Ruff results not supplied.
This environment is outside project-pinned Python 3.12. Do not reinterpret it as
supported Python 3.13 installation or change pins/config/filters. Native E031
Windows/Python 3.12.16/pytest 9.2.0/Ruff 0.17.3 remains authoritative. E032 records
reported review and Git inspection, not fresh test execution. Original brief still
unavailable; approved synthetic/narrow PII scope and all limitations remain intact.

T3-002 DONE/independently accepted; TASK-3 IN_PROGRESS. No architecture/source/test
change. One accepted foundation commit authorized, exact source/test/config/pin/
lock/README/requirements/governance inventory only. Preserve Tasks 1/2/4; no test
rerun absent unexpected implementation changes, T3-003 or push. Verify Git and stop.

## ADR-024 - 2026-11-05: T3-003 owned raw HTTPX streams and demand-driven sessions

- Status: independently ACCEPTED, user confirmation 2026-11-05; T3-003 DONE.
  TASK-3 IN_PROGRESS; T3-004 NOT_STARTED/not authorized. Pure baseline 0a75587 unchanged.
- Decision: add only upstream.py/service.py and four async test/support files.
  UpstreamSettings fixed trusted HTTPS/literal-loopback URL and optional private
  credential; frozen 1-65536-byte request body, fixed POST/application-json without
  invented provider schema. One owned HTTPX pool, no retry/redirect/env proxies/
  cookies/decompression. Strict status/media validation before any body read.
- Raw lifetime: use public response AsyncByteStream and explicit response.aclose
  under owned close work. HTTPX 0.28.1 aiter_raw auto-closes at EOF; Response.aclose
  marks is_closed before awaiting actual stream close. Reading/closing separately
  avoids treating an interrupted hidden EOF close/flag as confirmed resource release.
  No SDK internals patched or runner rewritten. Inspected native pinned HTTP/1.1
  read size 65536; cap raw block there and lazily split <=4096 for accepted Processor.
  Avoid aiter_raw(chunk_size=4096) coalescing small events and harming early delivery.
- Service: async-with session, sequential anext, per-session Processor and one raw
  reader, no producer queue. Atomic process-global 16 cap with synchronous brief
  lock/no admission queue across service instances/loops. Reject before send.
  Await demand between frames; only timer watchdogs can run while paused.
  Final review removed the optional per-instance test capacity override to make
  this invariant unconditional. Only new async test modules isolate the global
  counter through a test fixture; no production bypass/SDK/pure monkeypatch.
- Time/ownership: first-valid 15 s from admission, read idle 15 s only during reads,
  overall monotonic 120 s even paused; HTTPX owns 5 s pool/connect/write phases.
  First event inferred from accepted Processor's validated channel/terminal state,
  no duplicate SSE/payload parsing. Record acceptance before timer observation;
  delayed watchdog cannot retroactively fail a timely event. This race was exposed
  by the new test and corrected without changing its failing assertion.
- Cleanup: one shielded 1 s grace from close initiation for cancellation/discovery
  and response close. Retain late workers/resources/slots, quarantine new admissions,
  no pool close under uncertainty. Late confirmed release does not clear quarantine.
  One separate bounded pool-close task after request owners drain. Cancellation of
  a public cleanup waiter does not cancel/discard owned work. Client must retain
  service ownership on False shutdown; arbitrary resistant Python/OS I/O cannot
  be forcibly killed. No automatic retries or reset of uncertain close flags.
- Privacy: only Processor frames, fixed StreamError/CapacityExceeded metadata.
  Known error frame remains accepted pure behavior; other failures raise fixed
  codes for future HTTP mapping. Context-scoped logging filters suppress owned
  HTTPX/httpcore HTTP/1.1 records (untrusted reason phrases included), without
  suppressing unrelated requests. No inbound header/body debug logging or telemetry.
- Alternatives: background reader/list (unbounded read-ahead), async semaphore
  waiting queue (violates immediate cap), per-service-only count (process cap bypass),
  new client per request (no pool), wait_for alone (can await resistant cancellation
  indefinitely), cancel/drop close work (false ownership release), change pure parser
  to add first-event observer (unnecessary baseline change), pretend generator sends
  completed socket writes (unsupported). Framework timers/gates are trusted inputs.
- Tradeoffs: one raw block/processing slice/accepted parser state plus HTTPX buffers,
  no RSS ceiling; mocked phase errors/settings are not native socket timing proof.
  T3-004 must enforce actual send min(10 s, remaining overall), cancel blocked sends
  on disconnect/deadline and retain session cleanup ownership. Cooperative processing
  checkpoints are not preemptive interruption. No endpoints/wire/vendor integration.
- Dependency: isolated HTTPX 0.28.1 runtime, httpcore 1.0.9 and 15-package lock;
  pytest/Ruff/build/Python pins retained. Source references: official
  [HTTPX async](https://www.python-httpx.org/async/),
  [timeouts](https://www.python-httpx.org/advanced/timeouts/),
  [transports](https://www.python-httpx.org/advanced/transports/); installed public
  response/byte-stream implementation inspected read-only. Private httpcore read
  constant inspected diagnostically, not imported/depended on as an application API.
- E033 actual final 457 passes/95 new async cases, both Ruff checks (17 files),
  read-count/gated deadline/cancellation/quarantine evidence. All 11 accepted pure
  files/362 tests and Tasks 1/2/4 unchanged. Next independent review, no commit/push.

### ADR-024 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User confirms independent engineering APPROVAL, no blocking
production defect. Reported complete suite 457 passes, additional 240 randomized
HTTPX fragmentation cases, resistant cancellation/ownership/quarantine/confirmed
release, concurrent shutdown with admission blocked/shared transport closed once,
11 pure files byte-identical and compilation pass. Review Linux/Python 3.13.5
produced one nonfatal pytest configuration warning; warning text/pytest version/
exact commands and timings not supplied. E033 native Windows/Python 3.12.16 and
Ruff remain authoritative; no real-socket/ASGI/vendor or widened-runtime claim.
E034 records reported review and inspection only, not a fresh test execution.
No architecture or accepted implementation change. Supersedes pending/no-commit
handoff above only for one descriptive T3-003 acceptance commit with exact approved
source/tests/dependency/lock/README/governance inventory. Preserve all limitations
and completed Tasks 1/2/4; no T3-004 or push; stop after Git verification.

## ADR-025 - 2026-11-05: T3-004 HTTP boundary and owned ASGI send operations

- Status: independently ACCEPTED, user confirmation 2026-11-05; T3-004 DONE.
  TASK-3 IN_PROGRESS; e4bd001 components unchanged. T3-005 NOT_STARTED/not authorized.
- Contract: T3-H1-H9 document implementation policies, not recovered assessment
  wording: POST /stream exact bounded prompt JSON, one operator-configured opaque
  Bearer distinct from upstream optional credential, no caller routing/extra fields,
  queries/docs/CORS/resume. Validate config at lifespan, auth before body, strict
  framing/raw bytes/scalars/JSON duplicates. Existing pure PII/profile unchanged;
  original vendor brief unavailable. No roles/tenant/OAuth/vendor schema invented.
- Response choice: a small Starlette Response subclass uses the public ASGI
  scope/receive/send protocol. Installed Response/StreamingResponse/init_headers
  source inspected read-only. Ordinary StreamingResponse does not expose the
  required shared send-deadline/retained-resistant-worker controls; framework
  version-dependent disconnect behavior is not our ownership protocol. No framework
  internals patched. Admission and upstream header validation precede response.start,
  body parsing remains the accepted service/Processor. Never await another anext
  until the current send completes, no queue/background reader.
- Deadlines: admitted start/body/final-empty send gets min(now+10s, session.deadline),
  checked with injected monotonic clock/timer tasks, not cancellation-resistant
  wait_for. Request upload has independent 10s/16384-byte budget. Timely sends
  cannot renew overall120. Postheader local failure uses connection closure, not a
  locally encoded SSE frame bypass. Only accepted Processor frames reach SSE;
  known upstream error remains fixed. Best-effort empty close uses existing send
  budget. Never retry a response.start, send an error after disconnect or invent end.
- Capacity: reuse accepted Capacity primitive for a separate unconditional global
  HTTP cap16 through terminal send/cleanup. Upstream service can release its slot
  before HTTP sends finish; counting only service.active would permit unbounded
  stalled terminal response owners. Cross-app tests prove zero 17th upstream call.
  Admission is immediate, not a semaphore waiting queue. No production cap override;
  only new HTTP test fixture isolates its new counter.
- Lifespan/ownership: one service/client, no await between validated construction
  and retention; config failure opens no transport. After body completion one
  receive monitor races open/read/send with disconnect/shutdown/deadline. Cleanup
  starts accepted session close and HTTP worker joins under one anchored additional
  1s, without renewing service grace. Shields retain resistant workers on repeated
  caller cancellation. Unconfirmed close quarantines admissions/retains HTTP owner
  and slot; never close pool under that owner. Late confirmed work releases; explicit
  aclose may recheck public session.cleaned if late service confirmation followed
  false guard result, without new close/retry. app.state.runtime retains handles,
  unclean_shutdown remains true on cancelled/failed shutdown; fixed failure only.
  Shared pool's accepted one-time 1s budget follows drained request owners.
- Alternatives: ordinary unbounded StreamingResponse/send await (no required send
  enforcement), async producer queue (read-ahead), service-only cap (terminal-send
  bypass), replay/retry/resume (out of scope), raw encoder for local SSE errors
  (unnecessary bypass), provider-specific request adapter (brief unavailable).
- Tradeoffs: close-after-header failures require clients to verify SSE end, even
  with status200. Preflight validates headers only, not entire stream. HTTP canonical
  prompt JSON changes inbound whitespace/escapes but adapter preserves formed bytes.
  Nonadmitted JSON response connection lifetime/header allocation relies on ASGI
  server, not streaming cap. Server receive is trusted/cancellation-cooperative;
  bytes offered to ASGI cannot be retracted. Resistant sends may later finish only
  the already-offered sanitized frame; no new output/success claim follows failure.
  No socket acknowledgment/real proxy buffering/RSS/provider termination guarantee.
- Dependencies: Task 3 only FastAPI0.162.0/Starlette1.10.0, optional serve extra
  Uvicorn0.54.0; existing HTTPX/Python/dev pins preserved; 25-package locked env.
  No completed project imports/environment changes or accepted source/test edits.
- Verification E035: final native Windows/Python3.12.16, 580 passes (457 unchanged
  +123 HTTP/settings), Ruff lint/format22. Controlled ASGI read counts1 whileblocked,
  then2 afterrelease; exact10/overall120/sharedcleanup/cancel/quarantine/lifespan
  gates. One HTTPX ASGITransport smoke is NOT socket-backpressure evidence. Initial
  fixture deadline-race and coalesced-frame failures retained, no weakened assertions.
- References: [FastAPI custom responses](https://fastapi.tiangolo.com/advanced/custom-response/)
  and [ASGI HTTP send/receive/disconnect specification](https://asgi.readthedocs.io/en/latest/specs/www.html).
  Public installed source inspection supplements these; a failed Starlette website
  fetch is not treated as retrieved documentation. Next independent T3-004 review,
  no wire/T3-005, deployment/vendor/final audit, commit or push.

### ADR-025 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User confirms independent APPROVAL, no blocking source defect.
Reported complete suite580 passes;180 additional randomized interleaved two-channel
ASGI scenarios/4613 upstream reads; five fail-closed scenarios (candidate overflow,
unexpected EOF, duplicate done, premature end, malformed payload) pass. All17 prior
Task3 Python files byte-identical to T3-003 review archive. Review Linux/Python3.13.5
had one nonfatal pytest configuration warning; exact warning/pytest version/
commands/timings not supplied. E035 native Windows/Python3.12.16 tests/Ruff remain
authoritative, not a new local execution or supported-runtime/pin change. E036
records reported review and Git inspection. No architecture/implementation change,
real socket/RSS/vendor/deployment certification or universal PII claim. Original
brief unavailable; all historical evidence/tradeoffs retained. Supersedes pending/
no-commit handoff above only for one T3-004 acceptance commit of approved source/
tests/config/lock/README/governance. Preserve Tasks1/2/4; no T3-005 or push; stop.

## ADR-026 - 2026-11-05: T3-005 independent native-wire verification harness

- Status: independently ACCEPTED, user confirmation 2026-11-05; T3-005 DONE,
  TASK-3 IN_PROGRESS. Accepted ecbd61c source/580 tests unchanged, T3-006 not authorized.
- Decision: add only three tests/http_wire_* files and strict pytest marker plus
  evidence/docs. Separate native Python processes run synthetic provider and the
  accepted factory under Uvicorn; pytest client uses actual http.client sockets.
  Child binds loopback port0/exclusive Windows address before reporting, then real
  HTTP readiness. No parent bind-close/rebind race, external provider or public bind.
- Synchronization: bounded stdin plan/release commands and sanitized stdout
  receipts; generation is explicitly gated, not asserted from final-body equality.
  Independent provider-side counter journal cross-checks native proxy attempts for
  rejection evidence. No raw body/token/customer data persists in journals. Child
  env allowlist, distinct ephemeral tokens, hidden Windows process windows, no
  credential CLI arguments. Event/log/control queues bounded, fixture plans capped.
- Measurement seam: public AsyncBaseTransport/AsyncByteStream delegates to actual
  HTTPX AsyncHTTPTransport with approved pool/retry/env/TLS settings/request-phase
  timeouts. Preserve bytes and partition; do not replace source parser/redactor or
  generation runner. Test outer ASGI wrapper awaits actual Uvicorn send, counts
  bytes/suspensions and reads public state high-water counters; no producer queue
  or detached reader. Instrumentation overhead/settings are test-specific.
- Backpressure: bounded control round trips prove identical suspended send/read
  counter while real client pauses; do not infer TCP-read partitions from writes,
  actual buffer occupancy from cumulative byte totals, universal OS tuning or a
  kernel-stall deadline from ASGI tests. Client4096/listener16384 byte buffer requests
  aid reproducibility, not production settings or measured accepted-socket buffers.
  Exact10/120s remains deterministic ASGI evidence; representative real first/read
  inactivity waits run once each per complete suite. Native confirmed cleanup is
  distinguished from deterministic resistant/quarantined-owner tests.
- Memory: independent streamed digest/text/control checks and fixed high-water
  counters for1000/5000-event streams, Windows working-set/peak snapshots through
  GetProcessMemoryInfo, optional unavailable observations on non-Windows.64MiB
  growth guard is empirical only, no RSS/kernel/proxy allocation proof. Python,
  framework/native buffers and instrumentation contribute to working set.
- Process lifetime: explicit client sockets/pipes/readers closed; bounded child
  drain/exit7s, termination2s/kill2s as last resort, classified receipts for each PID.
  Expected startup-invalid2 is a negative test, not an unexpected crash or passing
  startup. Ordered runtime drain tested during active request; stock signals and
  deployment shutdown excluded. Failed fixture still reaps both children.
- Alternatives: in-process ASGI mocks only (cannot prove real progression/transport
  behavior), fixed ports or reserve-release ports (collision), arbitrary sleep
  assertions (timing races), subprocess hard-kill-only cleanup (no graceful proof),
  production instrumentation/features (unneeded baseline change), repeated120s
  boundary waits (unneeded; accepted deterministic proof retained), raw journals
  (privacy risk), vendor integration (brief unavailable/out of scope).
- E037 actual native final:637 passes in53.46s,57 new wire/580 unchanged, Ruff25;
  one client frame before gated provider completion,23 HTTP/body/auth rejection
  cases plus capacity zero-forwarding,16/17 occupancy/reuse/isolated safe-sensitive
  states, first15.016/read15.047s closure, sampled read117 frozen through3 control
  barriers and empirical working set. Final10 test children9 normal0/1 expected2;
  all three runs30 children27 normal/3 expected2, zero forced/killed/alive readers/
  private diagnostic matches. No accepted implementation defect/correction found.
- Source/API provenance: pinned Uvicorn Server.serve(sockets=...), Config,
  FlowControl.drain and RequestResponseCycle.send inspected read-only; actual send
  awaits writable drain when paused. Official website fetch timed out; do not claim
  retrieved documentation or wire behavior based on that failure. Public HTTPX/
  ASGI seams already established ADR-024/025. No monkeypatch/import of private
  SDK internals in accepted code. Next independent review; no T3-006/commit/push.

### ADR-026 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User APPROVES T3-005, no blocking defect/production correction.
Reported580 existing passes, all57 wire cases with passing assertions across split
executions,40 extra randomized real-socket fragmentation passes. SSE progression/
redaction/auth/concurrency/disconnect/timeout/cleanup reviewed;22 prior Python files
byte-identical to T3-004 archive. Linux/Python3.13.5 import-path change was ONLY in
extracted review harness, not shipped source. Combined Linux wire run stalled
after50 completed cases;19-case split printed passing summary but did not return
promptly to enclosing command. NOT a clean combined637-test Linux execution or
new process/exit guarantee. Native E037 Windows/Python3.12.16 full637/exit0/Ruff
authoritative; E038 reported review/docs/Git inspection, no new tests. Preserve
actual kernel10s/TLS/formal RSS/real-provider and synthetic-profile limitations.
No architecture/code/marker/dependency/lock change in acceptance. Supersedes prior
pending/no-commit handoff only for one descriptive T3-005 wire/marker/README/
governance commit. Preserve Tasks1/2/4, exclude archives/generated receipts; verify
Git status and stop. No T3-006 or push; TASK-3 remains IN_PROGRESS.


## ADR-027 - T3-006 final audit evidence boundary - 2026-11-05

America/Los_Angeles. Status: adopted audit policy; local READY, independent final
acceptance pending. No architecture/production behavior changes. Affected:
docs/TASK3_FINAL_AUDIT.md, requirements/ledger/build/E039, AGENTS and root/Task3
READMEs only. Baseline6b768780ace49c984d105b5ce558f69904f1076a.

Decision: assess the approved synthetic R/P/L/I/H/W contract with an R/Q/policy
traceability matrix, fresh native Windows suites in all four independent pinned
environments, clean locked Task3 reproduction, contextual current/history security
screen and accepted-file SHA/import checks. READY is restricted to that scope;
T3-006/TASK-3 stay IN_PROGRESS pending independent review. Do not infer unavailable
vendor requirements from our approved engineering choices.

Rationale/evidence: E039 actual149/452/427/637 passes (1665), all8 Ruff checks0,
zero failures/skips/warnings/xfails; clean25-package install and two real-TCP
synthetic demos pass,401/401/200, progressive safe text, redaction/done/end and
confirmed cleanup. Native wire proves representative progression/inactivity/
flow control, deterministic tests prove exact10/120/1s budgets and resistant
ownership. No blocking source defect; no accepted implementation/test/pin edit.
History19 commits/234 blobs contextual screen finds no actual disclosure; synthetic
matches and token-count false positives are not recorded as real secrets.

Alternatives rejected: repeating historical test results as fresh evidence;
claiming a clean637 Linux run from split assertion results; adding vendor adapters,
config ignore changes or production instrumentation during an audit; declaring
whole-process RSS/kernel send/TLS/remote execution guarantees from bounded
application state or ASGI simulation; markingDONE before independent acceptance.

Tradeoffs/consequences: exact supported PII grammar can overmask/reject benign
long candidates and misses out-of-profile PII. Quarantine retains uncertain work
and may need supervisor intervention. Arbitrary ZIP/DB paths are not universally
ignored; explicit-path staging remains mandatory. Heuristic history screening is
not exhaustive secret/PII/advisory certification. README now supplies an executable
synthetic fixture recipe and fixes stale unimplemented status. Historical E038
Linux import-path/split/stall qualifications remain; native Windows authoritative.
No new feature, staging/commit/push or Task1/2/4 change. Next independent final review.


### ADR-027 independent final acceptance provenance - 2026-11-05

America/Los_Angeles. User independently APPROVES T3-006/TASK-3; DONE and
assessment-ready within accepted synthetic SSE/PII contract. Reported documentation
review covers8 requirements/21 criteria,73 unique named tests checked against
previous source archive, implementation-symbol/local-link validation, demo syntax
and E039 consistency. No blocking documentation/traceability discrepancy. The
review did NOT rerun native Windows tests, directly audit unpublished local Git
history or validate unavailable vendor instructions. E039 actual local1665 passes/
eight Ruff remain evidence, not newly executed here or independently rerun claims.
No architecture change. Preserve original decisions/limits/environment and E038
Linux split/stall qualifications. One final documentation-only acceptance commit
authorized; preserve source/tests/config/deps/locks. E040 records review and actual
Git inspection. No new tests/features/push; stop after SHA/inventory/status check.
