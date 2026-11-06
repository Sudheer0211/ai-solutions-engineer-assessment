# Task 2 HTTP/JSON-RPC proxy

## Current publication status

**Task 2 is DONE, independently accepted within its documented requirements, and
published.** Verified public baseline: `a3a2af2`; see the
[repository publication status](../README.md). This separate Python project
integrates the security guards, HTTPX adapter and FastAPI POST /mcp endpoint.
See [CONTRACT.md](CONTRACT.md) for requirements, policies and exclusions.

Latest documented verification is E041 (2026-11-06 America/Los_Angeles):
**452 passed**, including 52 real loopback wire cases; both Ruff checks passed.
The repository total is **1,761** across four independent environments. No tests
were rerun for this publication documentation cleanup. See
[test evidence](../docs/TEST_EVIDENCE.md) and
[final audit / traceability](../docs/TASK2_FINAL_AUDIT.md).

Historical T2-006 acceptance: user-confirmed 2026-11-04, with E017 execution and
E018 independent acceptance/Git inspection. That checkpoint is complete; its
historical restrictions on future tasks/publication are not current project status.

From task2/ with uv installed:

```powershell
uv sync --locked --extra dev --extra serve --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Use this project's environment; do not install into the root Task 1 environment.
Guards use the standard library; the adapter pins HTTPX 0.28.1 and HTTP integration
pins FastAPI 0.162.0. The optional serve extra pins Uvicorn 0.54.0; dev includes
asgi-lifespan 2.1.0. Dev/build versions are pinned;
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
Pure authentication errors are transport-neutral; the HTTP endpoint maps them to
401 with a Bearer challenge, as specified below and in CONTRACT.md.

Task 1 source/tests/dependencies/lockfile and historical evidence are preserved.
Guard unit tests are supplemented by accepted ASGI integration and real-wire
verification of transparent discovery and zero delivery on local rejection.

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

No redirects/retries, SSE, compressed requests/responses, OAuth or MCP session
negotiation. ASGI/mock integration verifies endpoint/guard/adapter composition;
actual loopback socket verification is now recorded in T2-005/E015.

HTTP application: create_app() loads trusted settings during lifespan startup and
owns one pooled adapter per app/event loop. Optional settings/transport arguments
are for trusted setup/tests. It uses existing role-token/upstream environment keys;
no credentials ship or are loaded at import time. Once configured externally, the
documented local launch command from task2/ is:

```powershell
.\.venv\Scripts\python.exe -m uvicorn task2_proxy.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

T2-006 exercised the Uvicorn module CLI entry point with these options and port 0
for an ephemeral loopback audit listener; startup/shutdown and authenticated calls
passed against an independent local fixture. See E017 for the Windows supervisor
and exact evidence boundary. POST raw UTF-8 JSON
to /mcp with application/json and one Bearer Authorization header. Default body
limit is 1 MiB, enforced while reading; body deadline is 10 seconds. Auth failures
return 401, viewer admin_ denials return 403/-32001 with the exact Unauthorized Tool
Call message and request ID. Malformed RPC returns 400 with existing RPC codes;
HTTP media/size/deadline failures return 415/413/408 before parsing. Batches fail
closed; recognized notifications get empty 400/403 responses. Upstream failures
map to generic 502/503/504 and -32603 with caller ID; valid upstream bodies/statuses
are unchanged. See CONTRACT.md for the complete status/header/lifecycle matrix.

T2-005 wire tests launch the exact factory through Uvicorn in a subprocess plus an
independent stdlib HTTP peer, both on child-owned ephemeral 127.0.0.1 ports. Parent
clients use real TCP; gates/events/journal counts coordinate faults and concurrency.
Run only these cases with `python -m pytest -m http_wire -q`; full-suite setup above
requires both dev and serve extras, without skips for unavailable Uvicorn/loopback.
The peer journal remains in memory and redacts auth values. The ignored sanitized
.cache/http_wire_summary.json records child cleanup outcomes. All 12 children were
reaped with zero forced cleanups/live readers. No real external service is contacted.
Production modules, prior 400 tests and dependency versions remain unchanged.
See CONTRACT.md for exact process settings, journal results and Windows-only limits.

## Configuration and authenticated examples

Required **server** environment variables, provided by the trusted operator:

| Variable | Meaning |
| --- | --- |
| TASK2_ROLE_TOKENS | JSON object with exact admin/viewer keys, each a nonempty list of distinct opaque Bearer tokens |
| TASK2_UPSTREAM_URL | Fixed absolute HTTPS URL, or HTTP to a literal loopback IP such as 127.0.0.1; no userinfo, query or fragment |
| TASK2_UPSTREAM_BEARER_TOKEN | Optional separate upstream credential; never an inbound token fallback |

The service loads these during startup, not import. No .env loader, default
credentials, dynamic upstream selection or public TLS listener is supplied. Keep
credentials in the process environment/approved secret provisioning, outside Git,
command arguments and logs. The launch command above binds loopback; use Ctrl+C
for graceful shutdown. A compatible upstream must accept stateless single-JSON POST
requests; this does not implement full MCP Streamable HTTP/session negotiation.

For an entirely local, deterministic reviewer check with temporary random credentials,
run these existing examples from task2/ (each launches and cleans up its own real
proxy/fixture peer; no manual secrets or external service required):

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py -k 'authorized_calls_preserve_request_and_response_bytes or discovery_is_transparent_including_admin_tools or viewer_denial_preserves_id_and_zero_journal'
```

For a separately configured running service, this client example reads the same
operator-provided role configuration in a client shell; it does not print tokens.
Use a service-owned admin_ tool name in place of admin_reset when checking against
another compatible upstream. Discovery must expose protected definitions to both roles.

```powershell
@'
import json, os
import httpx

roles = json.loads(os.environ["TASK2_ROLE_TOKENS"])
headers = {"Authorization": "Bearer " + roles["viewer"][0]}
with httpx.Client(base_url="http://127.0.0.1:8000", trust_env=False) as client:
    discovery = client.post("/mcp", headers=headers,
        json={"jsonrpc": "2.0", "id": "list-1", "method": "tools/list"})
    assert discovery.status_code == 200
    denial = client.post("/mcp", headers=headers,
        json={"jsonrpc": "2.0", "id": "deny-1", "method": "tools/call",
              "params": {"name": "admin_reset"}})
    assert denial.status_code == 403
    assert denial.json() == {"jsonrpc": "2.0", "id": "deny-1",
        "error": {"code": -32001, "message": "Unauthorized Tool Call"}}
    print("Discovery HTTP 200; protected viewer call HTTP 403 / -32001")
'@ | .\.venv\Scripts\python.exe -
```

JSON errors and IDs are preserved according to CONTRACT.md. Notifications and whole
batches are rejected; viewer does not mean read-only for non-admin_ tools. No SSE,
OAuth/JWT, compression or retries. Windows/h11 loopback is verified; real vendor MCP,
TLS/DNS/public deployment, other OSes and load qualification are not. Review archives
are locally ignored only; explicitly inspect staged files before any later publication.
