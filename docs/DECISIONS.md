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
