# Task 1 — Customer/refund MCP server

Runnable assessment implementation using Python **3.12.16**, official
**mcp 2.3.0**, and **Pydantic 2.12.5**. Exactly two tools use the official STDIO
transport. All records and transactions are synthetic and process-local.

**Assessment status: BLOCKED.** The final regression run has **94 passed,
4 xfailed**. MCP 2.3.0 drops malformed STDIO JSON/envelopes without the required
-32700/-32600 response. Running the retained diagnostics with `--runxfail`
produces four failures. Task 1 is not fully compliant or DONE. See
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

The last run: 94 passed, 4 strict expected failures, no skips; lint and formatting
passed. Expected failures document unmet requirements rather than compliance.
To reproduce the outstanding failures directly:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short
```

That command exits 1: 4 failed, 94 deselected. The ordinary suite exits 0 because
those known failures are explicitly marked xfail; unexpected fixes become strict
XPASS failures so the limitation cannot silently disappear from the record.

`tests/test_integration.py` uses the real SDK in-process. `tests/test_wire.py`
starts real processes and exercises raw STDIO and the official SDK client.
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

## Verified error matrix and limitation

| Case | Required | Observed on STDIO |
| --- | --- | --- |
| Malformed JSON | -32700, null ID | **Missing response**, both lifecycle eras |
| Invalid request envelope | -32600, applicable ID | **Missing response**, both eras |
| Unknown protocol method | -32601 | Verified; integer/string IDs preserved |
| Invalid arguments / unknown tool | -32602 | Verified; IDs preserved |
| Unexpected injected service exception | -32603 | Verified; generic message, ID preserved |
| Missing customer / insufficient balance | Tool result isError=true | Verified; no failed-operation mutation |

Exact limitation: mcp 2.3.0's STDIO reader catches Pydantic JSON/envelope
validation exceptions and forwards them as stream exceptions. Its default
JSONRPCDispatcher drops those exceptions without emitting a JSON-RPC error.
The tests send a bad frame followed by a valid tools/list sentinel: the sentinel
succeeds, but no required error frame appears. No SDK monkeypatch or custom
framing/lifecycle was introduced. The next step is an official SDK/public
transport remedy followed by `--runxfail` and regression verification.
See [ADR-003](docs/DECISIONS.md) and the
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
    TASK_LEDGER.md
    DECISIONS.md
    BUILD_LOG.md
    TEST_EVIDENCE.md
  task1/
    __init__.py
    __main__.py
    schemas.py
    repository.py
    service.py
    server.py
  tests/
    __init__.py
    test_schemas.py
    test_service.py
    test_integration.py
    test_wire.py
    wire_support.py
    fault_server.py
```

Ignored local environments/caches are omitted. Read AGENTS.md and the ledger
at every session start. Tasks 2–4 have no supplied requirements and remain
untouched. FastAPI, HTTP proxies, OAuth/JWT, SQLite, rate limiting, inference APIs,
SSE, PII streaming, Docker/Kubernetes and optional CI/performance/property-testing
extras are intentionally excluded from this Task 1 implementation. Some HTTP
libraries are transitive SDK dependencies; this application does not start them.
