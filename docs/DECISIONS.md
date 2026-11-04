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

## ADR-006 — Proposed minimal STDIO input-boundary composition

- Date: 2026-11-03; status: PROPOSED (research only; no architecture change
  implemented); tasks: T1-007, TASK-1, T1-003, T1-005; blocker: B3.
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
- Consequences: No code/dependency/test changes now. Original four XFAIL cases
  remain byte-identical. A real fix produces strict XPASS under the default command;
  use --runxfail to verify all original 98 assertions plus new tests. Do not remove
  markers, weaken tests, or mark TASK-1 DONE before all mandatory criteria pass.
- Proposed affected files: task1/stdio_boundary.py (new), task1/__main__.py,
  new boundary tests, optional test harness support, README and governance records.
- Actual affected files this session: docs only. Tasks 2-4 remain out of scope.
