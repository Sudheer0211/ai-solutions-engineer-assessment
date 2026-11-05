# T2-001 / T2-002 acceptance contract

Date: 2026-11-04 (America/Los_Angeles). Source:
[supplied requirements](../docs/TASK2_REQUIREMENTS.md). IDs below distinguish
mandatory requirements from chosen behavior; none relaxes the supplied prefix rule.

## Explicit requirements and checkpoint acceptance

| ID | Requirement / verification |
| --- | --- |
| T2-C1 | Separate project, environment and lock; original Task 1 files unchanged |
| T2-C2 | No default/production credentials; configuration maps tokens to only admin/viewer |
| T2-C3 | Pure Bearer authentication; reject missing/invalid/ambiguous credentials |
| T2-C4 | Inspect decoded params.name; literal case-sensitive admin_ requires admin |
| T2-C5 | Viewer denial: -32001, exact Unauthorized Tool Call message, applicable ID preserved |
| T2-C6 | Strict envelopes/IDs/params; duplicate keys and encoded-name bypass tests |
| T2-C7 | Explicit safe batch/notification policy; guard returns no permit for denied/unsupported inputs |
| T2-C8 | Focused tests and Ruff executed with actual results; governance/evidence updated |
| T2-C9 | No HTTP route/forwarder/network client; no Tasks 3/4; no commit/push |

Checkpoint status: T2-C1 through T2-C9 verified; T2-001/T2-002 DONE for review.
Actual evidence: E008 in [TEST_EVIDENCE.md](../docs/TEST_EVIDENCE.md).
156 unit cases pass; Ruff lint/format, locked setup and preservation checks pass.
Review correction evidence E009 supersedes the test count: 186 passed; both Ruff
checks pass. The user confirmed independent engineering acceptance of T2-001/
T2-002, including the numeric-range fix, on 2026-11-04. One foundation commit is
now authorized; this supersedes the original checkpoint's no-commit restriction.
No push or T2-003 implementation is authorized.

Whole Task 2 still requires real HTTP forwarding, unfiltered discovery, and wire
proof that denied requests never reach downstream. This checkpoint contains no
networking and claims only guard correctness, not end-to-end proxy compliance.

## Implementation choices for review

- Python 3.12; standard-library-only guards. Separate task2/pyproject.toml,
  task2/uv.lock and task2/.venv. Dev dependencies pin pytest/Ruff. FastAPI/HTTPX
  are deferred until used by the later HTTP checkpoint, avoiding unused runtime
  dependencies and changes to the Task 1 environment.
- Environment variable TASK2_ROLE_TOKENS holds a JSON object whose exact keys
  are admin and viewer, each mapped to a nonempty list of opaque token strings.
  Both roles are required; multiple tokens per role allowed; duplicates anywhere,
  unknown roles, empty tokens and malformed configuration fail closed. There are
  no defaults. Settings are immutable and token values are omitted from repr/errors.
- Bearer scheme is case-insensitive; opaque token values are case-sensitive.
  One header only, supplied as a sequence so duplicate headers can be rejected.
  Header outer HTTP whitespace and one-or-more spaces after the scheme are
  accepted; token follows RFC 6750's ASCII bearer-token grammar. No query/body/
  cookie/role-claim fallback. All configured candidates use compare_digest.
- Guard order: authenticate -> inspect JSON/envelope -> authorize -> reject
  unsupported notification -> return an immutable permit. No guard accepts a
  forwarding callback or performs network I/O.
- JSON must be UTF-8; malformed syntax/encoding/nonstandard NaN or Infinity tokens
  yield -32700/null. Decimal parsing preserves valid large/exact numeric values
  in opaque arguments; the original immutable body bytes are retained unchanged.
  Syntactically valid numbers outside Decimal's representable range also fail
  at the parsing boundary with -32700 / Parse error and null ID. No partial ID
  recovery, rounding, infinity/NaN substitution or permit is produced. Decimal
  exceptions are contained; nonfinite conversion results are rejected even when
  the InvalidOperation trap is disabled. Representable numbers remain opaque.
- One object per request. Batches (including empty/mixed arrays) are unsupported:
  reject the whole batch with -32600/null; never return partial permits.
- jsonrpc must be exactly string 2.0; method must be a string. Top-level result/
  error fields are rejected on request inputs. Unknown extension fields remain
  allowed, opaque and present in original bytes; no business schemas are applied.
- IDs: string, integer or explicit null; bool/fraction/list/object rejected.
  Missing ID is distinct from explicit null: it identifies a notification.
  Invalid envelopes preserve a unique valid top-level ID; duplicate top-level
  id makes recovery unreliable and produces null. Nested IDs are never used.
- Duplicate decoded keys at ANY nesting level, including escaped spellings,
  yield -32600. Parsing retains the root ID independently of duplicate detection.
- params, when present, must be an object or array. tools/call additionally
  requires object params with a nonempty string name. tools/list allows omitted
  or object params. Invalid/missing method parameters yield -32602 with valid ID.
- Names are decoded once by the JSON parser and compared with startswith(admin_).
  No trimming/case-folding/URL decoding/Unicode normalization. Other spellings
  refer to other opaque names; future downstream must use the same semantics.
- Notifications are inspected and authorized with the SAME prefix rule; then
  all are rejected as unsupported for this checkpoint. No notification can
  produce a permit. Viewer protected notifications carry the exact authorization
  denial internally; other notifications carry an unsupported-request rejection.
  Errors for recognized notifications construct no JSON-RPC response, respecting
  JSON-RPC no-reply semantics. Later HTTP rejection status remains to be selected.
- Auth failures are generic AuthenticationError values, not invented JSON-RPC
  authentication codes. Transport status/challenge/body mapping is deferred.
- Viewer is not assumed read-only: non-admin_ tools pass this role policy even
  when mutating. tools/list gets no discovery-filter logic; no response processing
  exists at this checkpoint. Unknown protocol methods remain inspectable for
  later downstream dispatch rather than a new local method allowlist.

## Deferred decisions / next checkpoint

HTTP path/status mappings, notification transport reporting, upstream auth,
header/body consistency, size/time limits, upstream failures and response relay
remain for T2-003 onward. No compatibility with full MCP Streamable HTTP is
claimed. No completion claim for transparent discovery or zero denied HTTP calls
will be made before actual integration/wire tests exist.

Primary references: [JSON-RPC 2.0](https://www.jsonrpc.org/specification),
[Python JSON decoder hooks](https://docs.python.org/3.12/library/json.html),
[constant-time comparisons](https://docs.python.org/3.12/library/secrets.html),
[Bearer grammar](https://www.rfc-editor.org/rfc/rfc6750.html#section-2.1).

## T2-003 — HTTPX upstream adapter (2026-11-04)

The user authorizes adapter implementation only, preserving accepted foundation
e828729b. The earlier checkpoint's no-forwarder restriction is superseded for
this module; no FastAPI endpoint, SSE, OAuth, Tasks 3/4, commit or push is authorized.
T2-004 owns the future inbound HTTP contract. Acceptance U1-U8 is in the ledger.

### Interface and security contract

- `load_upstream_settings(environment=None)` reads only trusted startup settings:
  required TASK2_UPSTREAM_URL and optional TASK2_UPSTREAM_BEARER_TOKEN. No default
  destination/credential, inbound fallback, arbitrary auth headers or per-call URL.
- Frozen UpstreamSettings validates an absolute HTTPS endpoint or HTTP to a
  literal loopback IP only. Reject URL userinfo (including empty userinfo), query,
  fragment, whitespace/control characters, backslashes and invalid ports. Optional
  Bearer credentials use the existing strict token grammar and are repr-redacted.
  Private HTTPS destinations remain valid: the operator owns destination/DNS/egress
  trust; this is not a general SSRF-resistant URL fetcher.
- `async with UpstreamAdapter(settings)` owns/reuses one AsyncClient; `await
  adapter.forward(permit)` returns a frozen UpstreamResponse(status_code, body,
  headers). `aclose()` is idempotent. One adapter belongs to one asyncio event loop
  and upstream configuration; its lifespan owner drains/cancels work before closing.
- Guard-issued permits now carry a private process-local HMAC proof bound to role
  and original body. require_authorized_request verifies it, reinspects bytes,
  checks metadata consistency and authorization before transport. Public dataclass
  construction/replacement or copied proofs with modified role/body/metadata cannot
  authorize I/O. Existing auth/JSON-RPC policies and original tests are retained.
  Permits are reusable in-process values, not replay prevention, cross-process
  credentials or a sandbox against malicious Python with access to module internals.
- POST original bytes using explicit public httpx.Request plus AsyncClient.send;
  no JSON serialization, method/ID/argument/extension rewriting or discovery filter.
  Only fixed Content-Type/Accept application/json, Accept-Encoding identity and
  optional separately configured upstream Authorization are supplied, plus HTTPX's
  Host/Content-Length. No inbound header/cookie/token input exists. trust_env=False,
  auth=None, TLS verification enabled, no environment proxies/netrc/CA overrides.
  A public CookieJar policy refuses response cookies; headers are never merged
  from shared client state. Custom transport injection is trusted test setup only.
- Default pool: 20 connections/10 keepalive. Explicit connect/read/write/pool
  timeouts: 5/15/15/5 seconds, plus 30-second asyncio I/O deadline. Positive finite
  values are configurable via settings. Request bytes are limited to 1 MiB before
  sending; streamed raw responses to 2 MiB before parsing. Future inbound HTTP must
  bound bodies before guard parsing. No automatic retries (transport retries=0) or
  redirect following; callers must not blindly retry mutating tools.

### Response and failure policy

- Require one application/json Content-Type, UTF-8 JSON and absent/identity
  Content-Encoding. Compressed bodies, SSE, batches, duplicates at any nesting,
  nonstandard constants and malformed responses are rejected. Require jsonrpc=2.0,
  one result/error, no method, and a valid ID matching both type and value.
  Error objects require integer code and string message; data/extensions stay opaque.
  Noninteger response numbers use parser markers solely for envelope checks;
  arbitrary valid exponents/exact values in opaque data remain original bytes.
  Python integer conversion and nesting limits still apply.
- Valid correlated results/errors retain exact body bytes and original 2xx/4xx/5xx
  status. Null upstream error IDs do not match a non-null caller ID. All 3xx are
  rejected without follow-up. No result/discovery/schema filtering occurs.
- Discard every upstream response header, including cookies, hop-by-hop/nominated
  fields, credentials/challenges, CORS, redirects, lengths and cache policy. Return
  only locally generated content-type application/json and cache-control no-store.
  T2-004 must compute its own framing; upstream MCP session headers are not relayed.

| Condition | Adapter outcome |
| --- | --- |
| Forged/non-issued permit | AuthenticationError before any transport call |
| Connect/read/write/protocol failure | UpstreamError(TRANSPORT), generic diagnostic |
| HTTPX timeout or asyncio deadline | UpstreamError(TIMEOUT) |
| Any 3xx | UpstreamError(REDIRECT), no follow-up |
| Unsupported media/encoding or invalid response | UpstreamError(INVALID_RESPONSE) |
| Valid envelope with different ID/type | UpstreamError(ID_MISMATCH) |
| Body bounds exceeded | UpstreamError(REQUEST_TOO_LARGE/RESPONSE_TOO_LARGE) |
| Adapter closed | UpstreamError(CLOSED) |
| Caller cancellation | CancelledError propagated; acquired response closed |

Responses are closed on successful reads, validation failures, stream failures,
deadline and cancellation. Typed adapter failures do not invent JSON-RPC codes or
HTTP statuses: mapping belongs to T2-004. Transport exception details, URLs, tokens
and bodies are not exposed in adapter error messages.

Verification E011: 300 total Task 2 cases passed, both Ruff checks passed; 114 new
cases use the real AsyncClient with MockTransport and controlled async streams.
This verifies adapter behavior, not real DNS/TLS/socket pooling/timeout enforcement
or inbound HTTP security. Independent engineering approval of T2-003 was confirmed
by the user on 2026-11-04. One milestone commit is now authorized, superseding only
the implementation checkpoint's no-commit restriction. No push or T2-004 work. The
upstream must support stateless single-JSON POST exchanges; MCP sessions, streaming
HTTP, compression and arbitrary protocol headers require a separately reviewed scope.

Primary APIs: [HTTPX AsyncClient/send](https://www.python-httpx.org/api/),
[transports/retries](https://www.python-httpx.org/advanced/transports/),
[timeouts](https://www.python-httpx.org/advanced/timeouts/),
[CookiePolicy](https://docs.python.org/3.12/library/http.cookiejar.html#http.cookiejar.CookiePolicy.set_ok).

## T2-004 — FastAPI HTTP integration (2026-11-04)

Authorized scope: app.py factory/lifespan/POST /mcp and injected ASGI integration;
accepted modules/settings/guards/adapter and all original tests remain unchanged.
The earlier no-endpoint restriction is superseded for this checkpoint only. No
T2-005 sockets, SSE, OAuth/JWT issuance, Tasks 3/4, commit or push.

### Startup and request flow

- `create_app(security_settings=None, upstream_settings=None, *,
  upstream_transport=None, body_timeout=10.0)` returns FastAPI without reading
  credentials or constructing HTTPX resources. Injected settings/transport are
  trusted application/test setup, never request data. Configuration loads through
  existing load_settings/load_upstream_settings during lifespan startup; invalid
  configuration aborts startup. A single existing UpstreamAdapter owns the client
  for each app/event-loop lifespan and closes on normal/exceptional exit. The ASGI
  server must drain/cancel active requests before lifespan shutdown.
- Only POST /mcp exists. No trailing-slash redirects, Swagger/ReDoc/OpenAPI routes,
  CORS middleware, cookies/session authentication or query-token fallback.
- Order: routing/method -> HTTP metadata/framing -> existing authenticate ->
  bounded stream read -> existing guard_request -> existing adapter.forward.
  No automatic framework JSON body/model parsing. The guard deliberately rechecks
  the same credentials after the body read before issuing its proof-bound permit;
  authentication/inspection/authorization logic is not reimplemented in app.py.
- Require one application/json Content-Type, optionally a single UTF-8 charset
  parameter (quoted/unquoted, case-insensitive). Require absent/identity content
  encoding; never decompress. Duplicate Content-Type/Content-Encoding/Content-Length/
  Transfer-Encoding headers fail closed. Authentication header ambiguity remains
  the accepted Bearer guard's 401 policy.
- Accept absent length or one ASCII unsigned Content-Length; reject malformed,
  duplicate or conflicting length/transfer framing. Transfer-Encoding, if exposed
  by the ASGI server, must be exactly chunked and have no Content-Length. Compare
  declared length to the existing upstream max_request_bytes before reading;
  independently count every received body chunk before retaining it, then verify
  declared/actual length at EOF. No permit or outbound request until the full body
  passes. The same limit applies to chunked/lengthless streams (default 1 MiB).
  A positive finite body_timeout (default 10 seconds) bounds async body reads.

### HTTP response contract

Pre-RPC rejections use only a generic HTTP `{"detail": ...}` body, with no partial
ID recovery. After guard inspection, use RpcError.to_response for the accepted
codes/IDs; local serialization uses ASCII escaping to retain all accepted string
IDs, including surrogate escapes. Recognized notifications always have empty bodies.

| Condition | HTTP status | Body |
| --- | --- | --- |
| Unknown path (including /mcp/) | 404 | Generic HTTP detail; no redirect |
| Non-POST /mcp | 405 | Generic HTTP detail; Allow: POST |
| Ambiguous HTTP metadata/framing, invalid/mismatched length, incomplete body | 400 | Generic HTTP detail |
| Unsupported/missing Content-Type or nonidentity Content-Encoding | 415 | Generic HTTP detail |
| Missing/malformed/duplicate/invalid Bearer credentials | 401 | Invalid Bearer credentials; WWW-Authenticate: Bearer realm="mcp" |
| Body over limit | 413 | Generic HTTP detail; no JSON parsing/ID recovery |
| Body read deadline | 408 | Generic HTTP detail |
| JSON parse error (including Decimal range failure) | 400 | -32700 / Parse error; id=null |
| Invalid envelope/batch/duplicate JSON keys | 400 | -32600 / Invalid Request; reliable ID or null |
| Invalid/missing parameters | 400 | -32602 / Invalid params; applicable ID |
| Viewer protected tool call | 403 | -32001 / Unauthorized Tool Call; applicable ID |
| Recognized unsupported notification | 400, or 403 for protected viewer call | Empty body; no permit or RPC reply |
| Valid upstream result/error | Original nonredirect status | Exact upstream bytes, no discovery filtering |
| Upstream timeout | 504 | -32603 / Upstream timeout; caller ID |
| Upstream transport/redirect/malformed/ID mismatch/response-size failure | 502 | -32603 / Upstream request failed; caller ID |
| Closed upstream after inspection | 503 | -32603 / Upstream unavailable; caller ID |
| Adapter request-size rejection (defense in depth) | 413 | -32603 / Request body too large; caller ID |
| Request before startup/after shutdown | 503 | Service unavailable HTTP detail; no parsing |
| Unexpected failure after permit | 500 | -32603 / Internal error; caller ID |
| Unexpected failure before permit | 500 | Internal Server Error HTTP detail |

All local responses have no-store/nosniff headers. Successful relay uses the existing
adapter's safe metadata plus nosniff; Starlette computes framing for returned bytes.
No raw client/upstream authentication headers/cookies are reflected or forwarded.
The service does not log request material, exception text or tracebacks; debug is
disabled. Unknown local exception details are suppressed; caller cancellation is
not converted to a success/error response. Legitimate upstream JSON-RPC bodies are
intentionally unchanged: the trusted upstream must keep its payloads free of secrets.

### Evidence and remaining boundary

E013: 400 passing Task 2 cases, no failures/skips/warnings; both Ruff checks pass.
ASGITransport + LifespanManager exercise actual app/guard/adapter composition with
MockTransport upstream; the 100 new cases assert zero outbound calls on local
rejection. One concurrent test sends 24 requests through two clients with different
default credentials and repeated IDs: 4 viewer denials and exactly 20 upstream calls,
with owner-specific responses preserved. Upstream failure tests intentionally
observe one permitted attempt, not zero; no retries. Lifecycle tests verify no
client before startup, one pooled client during requests and closure on exit.

No HTTP listener or real upstream connection was started for validation. ASGI
tests do not prove HTTP parser/smuggling
behavior, real chunked-wire decoding, keepalive/draining, DNS/TLS, access-log behavior
or deployment limits; these are T2-005/operational boundaries, not passing wire claims.
An ASGI-provided chunk is already allocated before app limits apply. Deployment
must bound headers/connections and protect transport; the supplied local-run command
binds loopback and disables access logs. Full MCP Streamable HTTP/session/SSE and
OAuth remain excluded. Independent engineering approval of T2-004 was confirmed
by the user on 2026-11-04, including a reviewed 400-test pass and additional
zero-upstream rejection probes. One approved milestone commit is now authorized,
superseding only this checkpoint's no-commit restriction. No implementation change,
push or T2-005 work is authorized. E014 distinguishes reported from local evidence.

Primary references: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/),
[ASGI tests](https://fastapi.tiangolo.com/advanced/async-tests/),
[Starlette request streaming](https://starlette.dev/requests/).

## T2-005 — Real HTTP wire verification (2026-11-04)

Scope: test-only loopback TCP harness against accepted be9ddd8. No production
module, dependency version, prior test, HTTP policy or lifecycle redesign. Only
pytest marker metadata changes in pyproject.toml. No T2-006, sessions/SSE/OAuth,
Tasks 3/4 or push. Independent acceptance of T2-005 was confirmed by the user on
2026-11-04; one approved milestone commit is now authorized. No test or production
implementation changes are authorized by this Git checkpoint.

### Reproduction and process configuration

Use the existing dev + serve extras and run the full suite from task2/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

`tests/http_wire_server.py` launches either a stdlib ThreadingHTTPServer fixture
or Uvicorn serving the real create_app. `http_wire_support.py` owns subprocesses,
event readers, TCP clients/control and cleanup; `test_http_wire.py` supplies 52
wire cases, marked http_wire. No ASGITransport/MockTransport is used by these cases.

- Every listener is 127.0.0.1 with child-owned port 0. The proxy passes its bound
  socket to public uvicorn.Server.run(sockets=...), avoiding positive-service
  free-port probe/rebind races. There are no public listeners/external RPC targets.
- Proxy process: pinned Python 3.12.16/Uvicorn 0.54.0, one worker, no reload,
  asyncio loop, h11 HTTP, lifespan on, access logs off, proxy headers off,
  2-second graceful shutdown, 1-second keepalive. The observer only relays ASGI
  messages and emits lifecycle/completion events; app headers/body remain unchanged.
- Trusted test settings: 4096-byte input bound, 0.5s body deadline, 3s connect,
  1s write/pool, normally 0.5s read/4s total. The dedicated concurrency pair uses
  5s read/6s total to hold all ten approved requests until explicit release.
- Independent peer: stdlib HTTP/1.1 ThreadingHTTPServer, loopback, backlog 128;
  deterministic synthetic discovery/results/errors. Protocol calls are journaled
  in memory before responding. Token-protected control/reset/wait/release operations
  and health requests are excluded from the protocol-call count.
- Fresh synthetic tokens exist only in process memory/environment. Journal header
  fields are booleans/names (expected upstream auth, forbidden client token seen,
  cookie/spoofed-header presence); raw credentials are never journaled. Synthetic
  request/response bytes are available in memory for exact comparisons, not files.
  Child output is checked against all fixture secrets before cleanup completes.
- Readiness: bounded child bound/startup events plus real GET /health or /mcp
  probes. Event/startup deadlines are 10s; readiness poll waits are not timing
  assertions. Test request deadlines are 5s (7s for concurrency); journal wait/
  completion uses a Condition and 5s predicate deadline. No sleep-based assertions.
- Cleanup sends stdin stop/EOF, waits up to 6s per child, with terminate/kill
  fallbacks bounded at 2s each; process waits, pipe closure and reader joins are
  explicit. Failure during enter and exceptions inside a test use the same finally
  path. Proxy stdin shutdown exercises actual lifespan cleanup; no worker descendants.

### Observed results and boundaries

E015: full suite **452 passed in 13.14s**, 0 failures/skips/warnings; Ruff passes,
16 Python files formatted. Existing 400 cases unchanged. All production modules,
dependency versions and Task 1 are unchanged; Task 1 tests were not rerun.

- 33 dedicated local-rejection cases each record exactly zero upstream calls:
  Bearer failures (7), viewer protected IDs (5), encoded-name/duplicate/malformed/
  invalid-ID/batch cases (10), notifications (3), oversize length/chunked (2),
  media/encoding (3), non-POST methods (2) and incomplete-body deadline (1).
- Independent connections concurrently reuse ID=1: 12 calls, 2 viewer denials,
  exactly 10 permitted calls held simultaneously in the peer journal before gate
  release. Each result matches its owner and upstream auth context; no client
  tokens/cookies/spoofed role headers reach the peer.
- Admin/ordinary calls, unfiltered discovery, raw length/chunked bytes, response
  bodies/errors/IDs/status and safe headers pass. Slow peer gives 504 and one
  attempted/journaled call; drop/malformed/redirect gives 502 with one call/no retry.
  Peer kill after confirmed receipt gives controlled 502. Connection refusal uses
  a reserved bound non-listening loopback socket, yielding controlled 502 and no
  peer protocol receipt; this differs from a pre-forward authorization rejection.
- A partial-body client disconnect completes the observed app handler with an
  attempted 400 and zero upstream delivery; the disconnected client cannot receive
  that response. A subsequent normal request succeeds. Body deadline returns 408.
- Sanitized .cache/http_wire_summary.json reports 12 child processes (6 pairs),
  0 alive, 0 forced cleanups, 0 live reader threads. Ten normal exits are 0; the
  intentionally killed peer exits 1 and invalid-config proxy exits 3 on Windows.
  The artifact is ignored and contains no journal bodies or credentials.
- Initial refusal test expected 502 with only 0.5s connect timeout and got a valid
  504 instead. Direct Windows probing produced timeout at 0.5s, actual refusal
  WinError 10061 at a 3s deadline (about 2.03s). Only test settings were corrected;
  no production defect, assertion weakening or exception-policy change.

Verified on this Windows/Python/Uvicorn/h11 loopback setup only. This is independent
fixture interoperability, not a real vendor MCP service, TLS/DNS, HTTP/2, load/rate
qualification or full Streamable HTTP/session support. Application-rejected requests
and controlled failures are covered; arbitrary malformed-wire/smuggling behavior or
all disconnect/OS half-open cases are not exhaustively proven. The user reports
independent passes for the 400 existing and 52 wire tests, 33 zero-forwarding cases,
and all 12 children reaped without forced cleanup. E016 distinguishes this reported
independent evidence from local E015 executions. T2-005 is ACCEPTED; T2-006 still
requires separate authorization. No push is authorized.
