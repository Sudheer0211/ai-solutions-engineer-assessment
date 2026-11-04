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
