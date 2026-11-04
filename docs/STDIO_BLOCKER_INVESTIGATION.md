# T1-007: MCP STDIO protocol blocker investigation

Date: 2026-11-03 (America/Los_Angeles). Current status: Approach C IMPLEMENTED,
VERIFIED and ADOPTED under T1-008. B3 is resolved; TASK-1 mandatory criteria pass.

## Controlled implementation and adoption

The user subsequently authorized Approach C, a recoverable Git baseline, and
removal of only obsolete XFAIL decorators after full --runxfail verification.
The research-phase analysis below is preserved as history; its proposal-only
and retained-XFAIL statements are superseded by this verified adoption record.

- Baseline: dfb329b9e91620b3075710bb2466c11ba8703936 preserves all existing
  files and manual labs. Implementation: 7b0c79fdda6949e9a18a8919910ae58e9d04360f.
- task1/stdio_boundary.py uses a public AnyIO AsyncFile observer with one SDK
  stdin reader, a fail-closed two-frame FIFO, and an ObjectReceiveStream adapter.
  Each SDK item consumes its corresponding original line, including malformed
  frames. No secondary stdin reader, newline splitter, runner or serializer exists.
- task1/__main__.py composes validated_stdio() and retains Server.run(). The
  SDK still parses every frame and owns stdout serialization/fd1 isolation.
  All 124 installed MCP 2.3.0 Python files match the installed wheel RECORD.
- Malformed JSON produces -32700/null. Invalid request envelopes produce -32600
  with reliable top-level string/integer ID, otherwise null. Both eras recover
  before/after opening. Invalid request methods cannot escape through SDK
  notification/response union fallback. Raw input and ValidationError objects
  are released before output backpressure; logs contain only generic codes.
- Valid requests pass unchanged, with metadata/context. Notifications and
  responses retain SDK handling; malformed response-shaped frames are not
  answered, avoiding error-reply loops. No tool schema/business behavior changed.
- New unit/wire tests and tests/boundary_server.py exercise the matrix;
  tests/wire_support.py gained an optional module argument for test fixtures.
  Production advertises two tools. Cases cover cancellation in both modes,
  EOF/pending work, broken output, actual pipe backpressure, ordering,
  UTF-8 fragmentation and print/fd/child stdout isolation.
- Verification: 94 original ordinary passes; original four diagnostic passes with
  --runxfail; 149 complete passes with --runxfail before marker cleanup;
  149 normal passes after cleanup. Ruff passes. Exact results in E007.
- Cleanup commit 93a861f7bfd6f49bf40a882753aa376ac4662d0f removes only the
  obsolete parametrized XFAIL decorator. Original four test bodies/assertions
  are byte-identical; the historical regression marker remains selectable.
- Recommendation: adopt. No original-suite regression occurred; rollback was
  not triggered. Baseline remains recoverable.

Accepted limitations: correlation is pinned to MCP 2.3.0's one-item-per-line,
rendezvous input contract; upgrades must rerun boundary tests. The bound is two
frames, not bytes. Explicit stdin owns a duplicate handle and bypasses fd0
diversion; SDK stdout protection remains. Existing UTF-8 replacement and
nonstandard NaN/Infinity handling remain (-32602 at tool validation).
Only Windows was executed. Normal EOF exits cleanly; broken stdout with stdin EOF
exits within the tested bound and may exit nonzero. EOF settlement is SDK-owned, distinct from explicit
cancellation, which sends no later reply for the cancelled ID.

## Original research recommendation (T1-007)

Prefer an official SDK transport fix once published and verified. No newer
compatible release or ready-made server option was found in the sources checked
today. For a local remediation, propose approach C: a small lossless input
observation/error adapter composed around the documented `stdio_server(stdin=...)`
and `Server.run(read_stream, write_stream, ...)` interfaces. Keep SDK parsing,
framing, stdout writing, dispatch and both lifecycle implementations.

This is an application adaptation using documented interfaces, not an SDK-provided
error-recovery feature or a verified fix. Do not replace the transport or copy
the runner. A prototype must prove the ownership/correlation invariants below
before changing completion status. Under an assessment interpretation forbidding
even this boundary adaptation, the honest result remains BLOCKED pending upstream.

No implementation, tests, dependencies, requirements snapshot or manual lab
files were edited during this investigation. No upstream issue/comment was sent.

## Read-only findings

1. Installed runtime remains Python 3.12.16, mcp 2.3.0, Pydantic 2.12.5. PyPI and
   the official GitHub release list still identify 2.3.0 as latest. The checked
   main-branch STDIO parser and dual-era runner also retain the missing recovery
   path. This is the result of today's inspection, not a guarantee about future
   releases or every unmerged branch. [S1, S2, S3]
2. The installed STDIO reader catches `validate_json()` failures at lines
   189-192, sends the exception to its read stream, then continues. Runner
   dispatcher constructions at 489, 728 and 764 omit `on_stream_exception`.
   The dispatcher drops those exceptions when no observer is installed. [S3, S4]
3. `JSONRPCDispatcher(on_stream_exception=...)` is documented. However,
   `Server.run()` and `serve_dual_era_loop()` expose no observer or injected
   dispatcher parameter. `serve_connection()` can consume a supplied dispatcher,
   but that entry alone does not reproduce the dual-era driver's selection,
   per-request modern connection construction and era enforcement. [S4, S5]
4. Server middleware sees decoded requests/notifications. It cannot catch JSON
   parsing/envelope errors that never become a request. Its before-validation
   wording concerns method/parameter validation after wire decoding. [S6]
5. The SDK already supports `JSONRPCError(id=None)`. A direct public-model probe
   serialized an explicit `"id":null` with code -32700. Thus error representation
   and the official stdout serializer are usable; the missing piece is generating
   the error at the input boundary. [S7; actual probe in E006]
6. Pydantic `errors()` is insufficient for universal request-ID recovery. The two
   inputs below yield identical public error details: their valid IDs do not
   occur in any failed field. Do not scrape exception text or choose an arbitrary
   nested `input` dictionary. E006 records the executed comparison.

   ```json
   {"jsonrpc":"2.0","id":"original-A","method":7,"params":[],"result":[],"error":[]}
   {"jsonrpc":"2.0","id":"original-B","method":7,"params":[],"result":[],"error":[]}
   ```

7. An additional direct model probe found `id:true` on a request-like object
   accepted as `JSONRPCNotification` through union fallback. An exception-only
   bridge will not see that case. It is an adjacent diagnostic, not a newly
   implemented fix or an alteration of the four existing tests.
8. The driver waits for its first decoded request to choose a lifecycle and
   retains at most eight earlier items. A dispatcher observer alone may not run
   promptly for malformed input before any valid opening request. Recovery should
   occur before that opening-request selection, without choosing an era itself.
   Source inspection supports this inference; no new pre-opening wire test was
   added or run in this session. [S5]

## A: Supported SDK options or a newer release

**Result:** Preferred long-term solution; no ready-made remedy found today.

- **-32700/null:** The SDK model can represent it, but current default STDIO does
  not create it. A supported upstream fix at the STDIO reader could do so before
  raw input is lost and before lifecycle selection.
- **-32600/ID:** A transport fix with the original input can preserve a valid
  string/integer ID. An observer receiving only a lossy ValidationError cannot
  guarantee that, even if the runner later exposes the observer.
- **Legacy/modern:** Keep the dual-era `Server.run()` path. Downgrading to 1.x or
  switching to the handshake-only loop is not a compatible remediation.
- **Cancellation/shutdown/stdout:** A fix confined to official input handling
  should retain SDK cancellation, stream ownership and isolated stdout. These are
  test requirements, not properties assumed from a version number.
- **Risk:** Lowest application maintenance once upstream tests verify behavior;
  release availability is unresolved. A new observer parameter alone is not
  sufficient if it lacks raw input or does not cover pre-opening errors.

Do not use `raise_exceptions=True` as a fix: the migration guide states that
transport exceptions remain dropped; the flag governs handler exceptions. [S7]
Do not take ownership of `JSONRPCDispatcher` merely to set the documented hook:
recreating the dual-era driver introduces lifecycle and cancellation maintenance.

## B: Application adapter at the decoded stream boundary

**Result:** Technically partial, not a complete remediation.

- **-32700/null:** A read-stream decorator could recognize Pydantic `json_invalid`
  errors and send `SessionMessage(JSONRPCError(...))` to the SDK write stream.
  It must distinguish parser failures from I/O exceptions and cancellation.
- **-32600/ID:** Some errors happen to include the root input; arbitrary requests
  do not. The identical-error probe proves the limitation. No documented public
  property on ValidationError guarantees the complete original JSON document.
- **Legacy/modern:** A stream decorator before `Server.run()` can retain both
  modes and handle failures before era selection. Server middleware cannot.
- **Cancellation/shutdown/stdout:** Forward valid messages and metadata unchanged;
  retain cancellation and closure semantics; use only the SDK write stream. A slow
  error sender adds backpressure. Do not turn EOF or task cancellation into errors.
- **Risk:** Moderate plumbing maintenance plus an unavoidable ID correctness gap;
  scraping union branch names/messages is brittle. It also misses invalid IDs
  accepted via notification fallback. Passing the current four cases alone would
  not establish correct general request semantics.

**Decision:** Reject an exception-only/Pydantic-error-scraping adapter as the fix.

## C: Minimal input-boundary observation plus SDK error emission

**Result:** Recommended local candidate, subject to implementation verification.

The following is a design, not code added to the repository:

1. Supply an owned UTF-8 text input through the documented `stdin` argument,
   using AnyIO's public file-wrapper interface with a recording file-like reader.
   Observe whole lines as the SDK consumes them; do not implement another newline
   splitter, lifecycle, JSON-RPC dispatcher or stdout serializer. [S3, S8]
2. Correlate original lines with decoded SDK items using a bounded, lossless FIFO.
   A single mutable `last_line` is unsafe because the reader can advance while an
   error is being written. No raw input should be logged or retained after use.
   One line/item correlation is an inspected 2.3.0 implementation property, not
   a documented cross-version promise: pin it and require a contract test.
3. Interpose a receive adapter before `Server.run()`. Pass valid SessionMessage
   instances through with metadata/context and cancellation notifications intact.
   For parsing failures emit -32700 with explicit null ID. For invalid request
   envelopes inspect the original JSON object for its top-level ID: preserve a
   valid string or integer (including zero); exclude bool, fractional values,
   lists and objects. If ID cannot be established, use null. Never recover an ID
   by regex from syntactically broken JSON or from nested fields. [S9]
4. Validate only the necessary request-envelope boundary, including a request
   with an invalid ID that the union accepted as a notification. Leave method
   lookup, argument schemas and business execution to the existing SDK/server.
   Do not recategorize missing tools/call arguments from -32602 to -32600.
   Preserve valid notifications' no-response behavior, and do not manufacture
   error replies to incoming response/error frames, which could cause reply loops.
   Legacy response routing remains SDK-owned; modern message-direction rules
   must not be replaced by a new application dispatcher.
5. Construct public `JSONRPCError`, `ErrorData` and `SessionMessage` objects with
   generic messages; send them through the existing SDK write stream. That
   stream feeds the SDK's single stdout writer. No direct sys.stdout/fd writes,
   competing text writers, private descriptor claims or private dispatcher access.
6. Leave `stdout=None`: supplying a custom stdout skips the SDK's descriptor
   protection. Supplying only stdin leaves the default stdout isolation intact,
   according to the inspected branch structure. Explicit stdin does skip the
   SDK's fd0 diversion; input-handle ownership must therefore be explicit. [S3]
7. Keep one structured lifetime around input observation, receive filtering and
   `Server.run()`. Emit accepted input errors before forwarding EOF; do not close
   the output while an error is pending, block a worker on an abandoned capture
   queue, shield a write indefinitely, or swallow CancelledError. On a vanished
   client, settle/close tasks within a bound instead of inventing a protocol reply.

**Assessment:** -32700/null and -32600/valid ID become feasible without information
loss. Legacy/modern selection and in-flight cancellation remain SDK-owned.
Ownership/backpressure/context propagation need dedicated tests. Costs are extra
input observation, a second JSON inspection for rejected envelopes, and a narrow
version-sensitive correlation contract. Avoid changing the SDK's existing treatment
of nonfinite tool amounts: all four current wire tests must still get -32602.

This candidate is preferable to permanently retaining B3 because it can close the
required wire-response gap while preserving the official writer and runner. It is
preferable to copying stdio.py because it avoids taking over descriptor isolation
and transport shutdown. It is not preferable to a tested official upstream fix.
If the necessary composition cannot satisfy these invariants through public APIs,
stop at the documented limitation instead of expanding into SDK internals.

## Proposed affected files

| File | Proposed purpose; no implementation edits made now |
| --- | --- |
| task1/stdio_boundary.py (new) | Input observation, safe envelope/error classification and stream composition |
| task1/__main__.py | Compose the boundary with official stdio_server and unchanged Server.run |
| tests/test_stdio_boundary.py (new) | Classifier, correlation, ownership and cancellation tests |
| tests/test_stdio_boundary_wire.py (new) | New real-process boundary and lifecycle tests |
| tests/wire_support.py (only if needed) | Test-only raw pre-connect/slow-handler lifecycle support |
| README.md and engineering records | Explain the adaptation, actual results and remaining limits |

Keep task1/server.py, schemas.py, repository.py, service.py, both manual labs,
pyproject.toml and uv.lock unchanged for the local candidate unless evidence
establishes a separate need. An eventual upstream upgrade would instead require
reviewed dependency/lock updates and the same tests. Leave tests/test_wire.py and
its four XFAIL cases byte-for-byte unchanged. Tasks 2-4 are out of scope.

## Exact validation plan for a future implementation

All proposed boundary cases run in legacy and modern modes where applicable.
Tests listed below are proposed; they were not added or executed today.

| Proposed test | Required assertion |
| --- | --- |
| test_parse_error_before_and_after_opening | Send `{"jsonrpc":` plus newline; exactly one -32700/null reply even before initialize/discover; then connect/call successfully |
| test_invalid_request_id_preserved | Method=7 with IDs 0, 42, empty string and a normal string; one -32600 with exact ID/type, no result or mutation |
| test_original_id_survives_lossy_validation_error | Use both original-A/B examples above; each error carries its own ID |
| test_unusable_id_and_nonobject_envelopes | Invalid bool/fraction/list/object/null IDs and scalar/array roots produce correct -32600/null policy without being silently retyped as notifications |
| test_malformed_json_never_recovers_partial_id | Broken JSON containing an apparent id still returns null |
| test_input_correlation_under_backpressure | Pipeline distinct malformed and valid requests while delaying output; no swapped IDs, duplicate replies or unbounded raw-input retention |
| test_recovery_does_not_choose_protocol_era | More than eight bad pre-opening frames each get one reply; a following modern or legacy opening still chooses the requested era |
| test_valid_notification_and_response_routing | No replies to valid notifications; no error-reply loop for response/error frames; legacy routing preserved |
| test_cancellation_survives_malformed_input | Test-only slow request, bad frame, notifications/cancelled, then sentinel; handler stops and no post-cancellation response for the cancelled ID |
| test_eof_and_broken_output_are_bounded | EOF with no opener, after bad input and during pending work closes resources; normal EOF exits 0; broken output/cancellation cannot hang |
| test_stdout_isolation_with_stray_output | Test-only print, os.write(1, ...) and child stdout during serving land off wire; every stdout frame is newline-delimited JSON-RPC; stderr diagnostics have no raw inputs |
| test_utf8_input_and_no_argument_regressions | UTF-8 split reads/escaped newlines remain correctly framed; original numeric/NaN/Infinity/-32602 and business-error/state behavior remains intact |

Cancellation uses public SDK handlers in a test-only process, never a third
advertised production tool. Use synchronization/sentinels rather than timing-only
absence assertions. Don't promise payment rollback for a request already committed.

From the repository root, exact acceptance commands after implementation:

```powershell
# The 94 existing ordinary cases must remain passing.
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest tests/test_schemas.py tests/test_service.py tests/test_integration.py tests/test_wire.py -m "not sdk_limitation"

# The original four assertions must pass without editing their XFAIL markers.
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short

# Run original 98 cases plus new tests as actual tests, with no XFAIL masking.
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest --runxfail
.\.venv\Scripts\python.exe -m ruff check task1 tests
.\.venv\Scripts\python.exe -m ruff format --check task1 tests
```

Success targets: 94 original ordinary passes; 4 original diagnostic passes under
--runxfail; 98 original passes plus new tests under full --runxfail, with no skips
or unexpected failures. Keeping strict XFAIL markers means the normal command
will report four XPASS failures after a real fix. That is expected marker behavior,
not a failure of the previously passing 94 tests. Do not weaken the assertions or
remove markers to hide it; use --runxfail for the remediation acceptance run.

## Original read-only session verification (E006)

- Existing suite unchanged: **94 passed, 4 xfailed in 20.40s**, exit 0.
- Existing strict diagnostics: **4 failed, 94 deselected in 4.38s**, exit 1;
  both modes still omit the -32700/-32600 frames.
- Public-model probes demonstrated nullable-ID error serialization, lossy ID
  details and invalid-ID notification fallback. These are diagnostics, not a
  passing implementation of the proposed boundary.
- Source/requirements/manual-lab integrity is checked by hashes, since this new
  repository still has untracked files and Git diff alone cannot prove integrity.
- No remediation, lint changes, dependency upgrade, new tests or task completion
  is claimed. E006 records commands and final integrity verification.

## Primary sources checked

- S1: [PyPI MCP release listing](https://pypi.org/project/mcp/) and
  [official GitHub releases](https://github.com/modelcontextprotocol/python-sdk/releases).
- S2: [current main STDIO reader](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/stdio.py)
  and [main runner](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/server/runner.py).
- S3: [documented stdio_server input/output parameters and isolation](https://py.sdk.modelcontextprotocol.io/api/mcp/server/stdio/),
  checked against installed 2.3.0 source.
- S4: [documented JSONRPCDispatcher observer](https://py.sdk.modelcontextprotocol.io/api/mcp/shared/jsonrpc_dispatcher/).
- S5: [Server.run API](https://py.sdk.modelcontextprotocol.io/api/mcp/server/lowlevel/server/)
  and [runner API](https://py.sdk.modelcontextprotocol.io/api/mcp/server/runner/).
- S6: [versioned middleware documentation](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/docs/advanced/middleware.md).
- S7: [SDK migration guide: nullable error IDs, transport exceptions and stream isolation](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md).
- S8: [AnyIO public file wrapping](https://anyio.readthedocs.io/en/stable/fileio.html)
  and [SDK SessionMessage API](https://py.sdk.modelcontextprotocol.io/api/mcp/shared/message/).
- S9: [JSON-RPC 2.0 errors/IDs](https://www.jsonrpc.org/specification) and
  [MCP 2026-07-28 STDIO cancellation/framing](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio).
- Related upstream evidence, not a verified fix:
  [open issue #2751](https://github.com/modelcontextprotocol/python-sdk/issues/2751)
  describes deeply nested STDIO requests left pending while shallow requests work.
