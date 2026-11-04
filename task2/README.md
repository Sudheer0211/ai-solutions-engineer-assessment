# Task 2 guards and upstream adapter

This project implements accepted T2-001/T2-002 guards and the T2-003 HTTPX upstream
adapter. There is no FastAPI endpoint or application launcher; that is T2-004.
See [CONTRACT.md](CONTRACT.md) for exact requirements, choices and deferred work.

Checkpoint verification (2026-11-04): 300 Task 2 cases passed; Ruff lint and format
checks passed. See root docs/TEST_EVIDENCE.md entries E008/E009/E011 for actual results.
Independent engineering review accepted T2-001/T2-002, including the Decimal fix,
as confirmed by the user on 2026-11-04. The user also confirmed independent
acceptance of T2-003 on 2026-11-04. Whole Task 2 remains incomplete; T2-004 awaits
explicit authorization. One T2-003 milestone commit is authorized; no push.

From task2/ with uv installed:

```powershell
uv sync --locked --extra dev --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Use this project's environment; do not install into the root Task 1 environment.
Guards use the standard library; the adapter pins HTTPX 0.28.1. Dev/build versions are pinned;
uv.lock records their tested transitive selection. No secrets/default tokens ship.

TASK2_ROLE_TOKENS is configured externally as JSON: admin and viewer keys each
hold a nonempty list of tokens. load_settings() reads it explicitly when called;
importing the library neither reads credentials nor starts a process/service.
Missing/conflicting configuration fails closed. Do not print the configuration.

Pure entry points:

- settings.load_settings(environment=None): immutable role-token configuration.
- security.authenticate(header_values, settings): one Bearer header -> trusted role.
- rpc.inspect_request(raw_bytes): strict request inspection with original bytes.
- security.authorize(role, request): enforce literal admin_ prefix restriction.
- security.guard_request(header_values, raw_bytes, settings): ordered checks;
  returns an immutable permit only for supported, authorized request objects.
- RpcError.to_response(): fresh JSON-RPC error dictionary, or None when a
  recognized notification must not receive a JSON-RPC reply.

Viewer protected requests receive code -32001, message Unauthorized Tool Call
and their original ID. Batches are rejected entirely. Notifications cannot return
permits; their names are still inspected/authorized and no RPC reply is fabricated.
Authentication errors remain transport-neutral pending HTTP status decisions.

Task 1 source/tests/dependencies/lockfile and historical evidence are preserved.
Passing these unit tests does not prove transparent HTTP forwarding or downstream
non-delivery: those require the later independent HTTP integration/wire checkpoint.

Upstream API (asyncio):

```python
from task2_proxy.upstream import UpstreamAdapter, load_upstream_settings

# permit is obtained from security.guard_request using trusted caller settings.
async with UpstreamAdapter(load_upstream_settings()) as adapter:
    response = await adapter.forward(permit)
```

Configure TASK2_UPSTREAM_URL separately from inbound role tokens. Optional
TASK2_UPSTREAM_BEARER_TOKEN is an independent upstream credential. URLs must be
HTTPS or literal-loopback HTTP, with no userinfo/query/fragment. No caller header,
cookie or URL is accepted by forward(). Original request/response bytes are retained.
Only unambiguous correlated JSON-RPC JSON responses are supported; all upstream
headers are replaced with safe local metadata. See CONTRACT.md for precise limits,
failure kinds, credential isolation, cookie rejection and lifecycle responsibilities.

No redirects/retries, SSE, compressed responses, OAuth or MCP session negotiation.
Mock integration verifies forwarding and denied-permit non-delivery at the adapter;
real upstream interoperability and inbound endpoint wire tests remain future work.
