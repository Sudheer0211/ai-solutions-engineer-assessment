# AI Solutions Engineer assessment

This repository contains independently executable Python assessment projects:

- **Task 1: DONE.** Official MCP STDIO customer/refund server; setup and architecture
  are documented below. Fresh T2-006 regression: 149 passing tests.
- **Task 2: DONE; independently approved, assessment-ready within documented
  requirements.** Secure HTTP/JSON-RPC
  reverse proxy with FastAPI and HTTPX; isolated environment and lockfile. Start with
  [Task 2 setup and examples](task2/README.md), [contract](task2/CONTRACT.md), and
  [final audit / requirements traceability](docs/TASK2_FINAL_AUDIT.md).
  T2-006 evidence: 452 passing tests, including 52 real HTTP wire cases; final
  independent approval confirmed 2026-11-04. No tests rerun for the acceptance commit.
- **Task 3: IN_PROGRESS.** T3-001 through T3-004 independently accepted, user
  confirmation 2026-11-05; qualified review recorded in [E036](docs/TEST_EVIDENCE.md).
  Native Task 3 suite: 580 passing tests/Ruff ([E035](docs/TEST_EVIDENCE.md)). See
  [Task 3 setup and synthetic HTTP contract](task3/README.md). Original vendor
  brief unavailable; real sockets/RSS unverified, no vendor/deployment claim.
- **Task 4: DONE; independently approved, assessment-ready within its documented
  requirements, supported Windows/SQLite environment and trusted-adapter policies.**
  Native Windows full-suite evidence remains authoritative; Linux review used
  split runs/compatibility substitutions, with a combined wire teardown stall
  explicitly recorded. See [Task 4 setup/contract](task4/README.md).
  T4-006 independent approval confirmed 2026-11-05 (America/Los_Angeles).
  See [final audit / requirements traceability](docs/TASK4_FINAL_AUDIT.md).
  E028 native audit suites (2026-11-04): Task 1 **149**, Task 2 **452**, Task 4 **427** passing
  tests; all Ruff lint/format checks pass ([E028](docs/TEST_EVIDENCE.md)).
  Clean locked Task 4 setup and deterministic primary/fallback fixtures verified.
  Stock Task 4 intentionally returns 503 without trusted provider/bounds adapters;
  no real LLM/tokenizer or production deployment is certified.
  E029 records independent acceptance and the documentation-only Git checkpoint;
  tests were not rerun for acceptance. No GitHub push is authorized.

Tasks 1 and 2 passed Ruff lint and formatting checks on 2026-11-04
(America/Los_Angeles). [E017](docs/TEST_EVIDENCE.md) records actual commands/results.
Use each task's own environment; Task 2 does not run through Task 1's STDIO server.

## Task 1 — Customer/refund MCP server

Runnable assessment implementation using Python **3.12.16**, official
**mcp 2.3.0**, and **Pydantic 2.12.5**. Exactly two tools use the official STDIO
transport. All records and transactions are synthetic and process-local.

**Assessment status: DONE (2026-11-03).** The final normal suite has **149 passed**,
with no skips or expected failures. A controlled input-boundary adapter resolves
the SDK's missing -32700/-32600 responses while preserving its parser, dual-era
runner, protocol writer and stdout protection. The original four diagnostic bodies
passed under --runxfail before their obsolete XFAIL decorator was removed. See
[task ledger](docs/TASK_LEDGER.md) and [actual evidence](docs/TEST_EVIDENCE.md).

## Install and run

From this repository root, with [uv](https://docs.astral.sh/uv/getting-started/installation/)
installed (tested uv 0.13.7):

```powershell
uv python install 3.12.16
uv sync --locked --extra dev --python 3.12.16
.\.venv\Scripts\python.exe -m task1
```

An alternative installed executable is `.\.venv\Scripts\task1-mcp.exe`.
The server waits for newline-delimited JSON-RPC on stdin. Connect an MCP client;
there is no HTTP listener or TCP port. Closing stdin shuts the process down.

On this workspace, uv/runtime are already local and ignored by Git:

```powershell
Set-Location 'S:\2026 jobs\Projects\ai-solutions-engineer-assessment'
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.runtime'
.\.tools\bin\uv.exe sync --locked --extra dev --python 3.12.16
.\.venv\Scripts\python.exe -m task1
```

`pyproject.toml` pins direct/build/dev dependencies; `uv.lock` records transitive
versions and artifact hashes. A standard Python 3.12 environment can also install
the package with `python -m pip install -e '.[dev]'`; use uv's locked setup for
the exact tested transitive selection. Linux/macOS use `.venv/bin/python` and
`.venv/bin/task1-mcp`. Only Windows execution was verified in this session.

## Verify

Run from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest
.\.venv\Scripts\python.exe -m ruff check task1 tests
.\.venv\Scripts\python.exe -m ruff format --check task1 tests
```

The final run: 149 passed, no skips or expected failures; lint and formatting pass.
The historical `sdk_limitation` marker now selects four ordinary regression tests:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short
```

All original 98 assertions plus 51 boundary cases passed together under
`--runxfail` before cleanup (149 passed), then again under the normal command
after cleanup. Only the obsolete XFAIL decorator was removed; the test function
and all four parametrized assertions remain byte-identical to the baseline.

`tests/test_integration.py` uses the real SDK in-process. `tests/test_wire.py` and
`tests/test_stdio_boundary_wire.py` start real processes. Boundary tests cover
pre-opening recovery, ID/order correlation, actual pipe backpressure, bounded
capture, cancellation, EOF, broken output, UTF-8 and print/fd/child isolation.
The SDK async client requires Windows named-pipe access; this environment's
sandbox denied it, so the final full suite ran with approved unsandboxed access.
No tests were skipped to hide that restriction.

## Tool calls

`get_customer_record` accepts only `customer_id`, matching `^CUST-[0-9]{5}$`.
Seed IDs: CUST-00001 (100.00), CUST-00002 (250.00), CUST-00003 (50.00).

`trigger_refund` requires that ID, a finite positive JSON numeric `amount`, and
a string `reason` of at least 10 characters containing a non-whitespace character.
Unknown fields, missing/null values, strings as amounts, booleans, NaN and
infinities are rejected. Amounts such as 10, 10.5, 10.25 and 0.001 are accepted;
there is no cent-precision restriction. Monetary output uses exact decimal strings.

These are individual JSON-RPC frames, sent after lifecycle connectivity:

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_customer_record","arguments":{"customer_id":"CUST-00001"}}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"trigger_refund","arguments":{"customer_id":"CUST-00001","amount":10.25,"reason":"Synthetic refund request"}}}
```

The lookup returns structured data containing customer_id, customer_name,
account_status and refundable_balance. The first refund returns structured data
equivalent to:

```json
{"refund_id":"REF-000001","status":"completed","customer_id":"CUST-00001","amount":"10.25","refundable_balance":"89.75"}
```

A protocol failure example:

```json
{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"trigger_refund","arguments":{"customer_id":"CUST-00001","amount":"10","reason":"Synthetic request"}}}
```

Returns `{"jsonrpc":"2.0","id":4,"error":{"code":-32602,"message":"Invalid tool arguments"}}`.
A lookup of CUST-99999 or a refund above the available balance returns a normal
JSON-RPC result containing `isError: true`, with a safe business-error message.
Neither failure changes balances, transaction history or the next refund ID.

## Lifecycle, dispatch and state

The SDK owns both supported lifecycle paths. Modern clients use `server/discover`
and the 2026-07-28 metadata envelope. Legacy clients send `initialize` proposing
2025-11-25, then `notifications/initialized`. For manual legacy STDIO testing,
send these before the example frames:

```json
{"jsonrpc":"2.0","id":"init","method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"manual-client","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
```

The SDK dispatches tools/list to the registered list handler and tools/call to
the call handler. Advertised schemas come directly from the same strict Pydantic
models used for validation. Validation errors and unknown tool names raise the
public MCPError with INVALID_PARAMS, which the SDK serializes as -32602 while
preserving IDs. Business errors return is_error tool results. Unexpected service
exceptions become a generic -32603 without private details.

Application logging is explicitly configured to stderr, with no print/banner
calls. The SDK owns all stdout serialization and, on the tested Windows transport,
isolates its protocol writer from ordinary stdout. Wire tests parse every captured
stdout line and check stderr startup/shutdown/execution/failure messages.

Refunds validate before service invocation, check existence/balance, then commit
synchronously without awaits. Decimal(str(amount)) and a locally sized arithmetic
context avoid binary float balance calculations and rounding away tiny amounts.
Frozen records prevent external balance mutation. Each server instance owns its
repository. A process restart resets balances, transactions and sequential IDs;
there is no persistence, payment integration or cross-thread/distributed guarantee.

## Verified error matrix and boundary adaptation

| Case | Required | Observed on STDIO |
| --- | --- | --- |
| Malformed JSON | -32700, null ID | Verified before/after opening, both lifecycle eras |
| Invalid request envelope | -32600, applicable ID | Verified; string/integer IDs preserved, unusable IDs become null |
| Unknown protocol method | -32601 | Verified; integer/string IDs preserved |
| Invalid arguments / unknown tool | -32602 | Verified; IDs preserved |
| Unexpected injected service exception | -32603 | Verified; generic message, ID preserved |
| Missing customer / insufficient balance | Tool result isError=true | Verified; no failed-operation mutation |

The SDK itself still drops malformed-frame exceptions. `task1/stdio_boundary.py`
supplies an observed public AnyIO AsyncFile as `stdio_server(stdin=...)`. The SDK
remains the sole input reader/parser. A two-frame FIFO associates each SDK item
with its original line; a receive decorator emits public JSONRPCError objects
through the SDK's existing writer before `Server.run()` sees valid messages.
Only rejected envelopes and notification/response union fallback need secondary
JSON inspection. No new newline splitter, dispatcher or protocol serializer exists.

Default stdout is retained so SDK descriptor protection remains active. The
adapter owns a duplicate input handle; explicit stdin does skip the SDK's fd0
diversion. Valid notifications and responses retain SDK routing, malformed
response-shaped frames are not answered, and errors/logs omit raw input details.
Explicit notification cancellation stops in-flight work without a reply. EOF
teardown remains SDK-owned and can settle outstanding work before exiting.

Maintenance limit: the two-frame correlation contract depends on pinned SDK
2.3.0's one-item-per-line rendezvous reader. A changed contract fails closed;
rerun all boundary tests before an SDK upgrade. The bound is in frames, not bytes;
the SDK's existing per-line size and UTF-8 replacement behavior remain unchanged.
Nonstandard NaN/Infinity tool-amount tokens still reach strict validation and
are rejected with -32602, preserving the original behavior. Normal EOF exits
cleanly; broken stdout combined with stdin EOF exits within the tested bound and
may exit nonzero. No broader half-open transport shutdown guarantee is claimed.
See [adopted ADR-006/007](docs/DECISIONS.md),
[investigation and adoption](docs/STDIO_BLOCKER_INVESTIGATION.md), and the
[versioned SDK documentation](https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/docs/advanced/low-level-server.md).

## Project tree

```text
ai-solutions-engineer-assessment/
  AGENTS.md
  README.md
  .gitignore
  .python-version
  pyproject.toml
  uv.lock
  docs/
    TASK1_REQUIREMENTS.txt
    TASK2_REQUIREMENTS.md
    TASK2_FINAL_AUDIT.md
    TASK4_REQUIREMENTS.md
    TASK4_FINAL_AUDIT.md
    TASK_LEDGER.md
    DECISIONS.md
    BUILD_LOG.md
    TEST_EVIDENCE.md
    STDIO_BLOCKER_INVESTIGATION.md
  task1/
    __init__.py
    __main__.py
    schemas.py
    repository.py
    service.py
    server.py
    stdio_boundary.py
  tests/
    __init__.py
    test_schemas.py
    test_service.py
    test_integration.py
    test_wire.py
    wire_support.py
    fault_server.py
    boundary_server.py
    test_stdio_boundary.py
    test_stdio_boundary_wire.py
  task2/
    README.md
    CONTRACT.md
    pyproject.toml
    uv.lock
    src/task2_proxy/
    tests/
  task4/
    README.md
    pyproject.toml
    uv.lock
    src/task4_limiter/
    tests/
  manual_validation_lab.py
  manual_refund_lab.py
```

Ignored local environments/caches are omitted. Read AGENTS.md and the ledger
at every session start.
Task 2 is implemented separately under `task2/`. Task 3 remains unimplemented;
Task 4 has its own isolated project under `task4/` (status and review gate above).
FastAPI, HTTP proxies, OAuth/JWT, SQLite, rate limiting, inference APIs,
SSE, PII streaming, Docker/Kubernetes and optional CI/performance/property-testing
extras are intentionally excluded from this Task 1 implementation. Some HTTP
libraries are transitive SDK dependencies; this application does not start them.
