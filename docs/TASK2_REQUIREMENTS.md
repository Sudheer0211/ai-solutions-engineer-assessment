# Task 2 supplied requirements

Source: user-approved requirements and checkpoint authorization, 2026-11-04
(America/Los_Angeles). These requirements are independent of Task 1.

## Explicit assessment requirements

- Lightweight HTTP/JSON-RPC reverse proxy in Python.
- Authenticate callers using Bearer tokens mapped to `admin` and `viewer` roles.
- Forward `tools/list` transparently without filtering discovery results.
- For `tools/call`, inspect `params.name`.
- Tool names beginning with the literal, case-sensitive prefix `admin_` require
  the `admin` role.
- A viewer invoking `admin_*` must receive JSON-RPC error code `-32001` with
  message `Unauthorized Tool Call`, preserving the applicable request ID.
- Denied calls must never reach the downstream server.
- Task 1 must remain unchanged.

## Authorized checkpoint: T2-001 and T2-002 only

1. Create a separate task2/ project with isolated dependency configuration.
2. Record the exact acceptance contract, separating requirements from choices.
3. Load role-token configuration without hardcoded production credentials.
4. Implement pure Bearer authentication and authorization.
5. Implement strict JSON-RPC inspection and error construction.
6. Reject ambiguous duplicate keys and prevent encoded-name authorization bypasses.
7. Define/test batches, notifications, missing parameters and malformed envelopes;
   never silently forward uninspected executable requests.
8. Write focused unit tests for authentication, roles, IDs, malformed requests
   and bypass attempts.
9. Update governance records without altering Task 1 evidence.

## Constraints and completion boundary

- FastAPI + HTTPX architecture is approved for the later HTTP implementation.
- No HTTP endpoint or HTTPX forwarding in this checkpoint.
- No full MCP Streamable HTTP, SSE, OAuth, JWT issuance, Tasks 3 or 4.
- Do not modify Task 1 source, tests, dependencies or lockfile.
- Do not commit or push. Execute new checkpoint tests and Ruff checks.
- Stop at the checkpoint for independent review. Whole TASK-2 is not complete
  until later HTTP forwarding/discovery/denial acceptance tests are verified.

## Subsequent acceptance and commit authorization (2026-11-04)

The user confirms independent engineering acceptance of T2-001/T2-002, including
the Decimal correction, and authorizes one foundation commit with relevant
governance documentation. This supersedes only the original no-commit restriction
above. No push, HTTP implementation or T2-003 work is authorized by this checkpoint.

## Subsequent T2-003 authorization (2026-11-04)

The user authorizes an HTTPX upstream adapter only, preserving e828729b:

- Implement task2/src/task2_proxy/upstream.py with a minimal typed async interface.
- Use pooled httpx.AsyncClient with explicit timeouts; a fixed validated upstream
  destination, never a client-supplied URL; no automatic redirects or retries.
- Accept only previously inspected/authorized request objects. Forward original
  bytes without rewriting methods, IDs, arguments or extensions.
- Never forward inbound Bearer tokens, cookies or unapproved auth headers.
  Configure upstream credentials separately.
- Preserve legitimate JSON-RPC responses/error objects; document failures for
  connections, timeouts, malformed responses, ID mismatches and unsafe headers.
- Isolate concurrent response bodies and authentication contexts.
- Use HTTPX mock transports for unit/integration tests of bodies, IDs, credentials,
  failures, redirects, concurrency and rejection without valid permits.
- Execute the full Task 2 suite and Ruff; record exact results. Mark T2-003 DONE
  only after acceptance tests pass, then stop for independent review.
- No FastAPI endpoint (T2-004), SSE, OAuth, Tasks 3/4, Task 1 changes, commit or push.

Detailed implementation choices and limits are in task2/CONTRACT.md, not implied
assessment requirements. Earlier checkpoint authorization restrictions are historical.

## T2-003 independent acceptance and commit authorization (2026-11-04)

The user confirms independent engineering approval of T2-003 and authorizes one
descriptive milestone commit containing only its approved implementation, tests,
dependency updates and related governance records. This supersedes the preceding
no-commit restriction only. No push or T2-004 implementation is authorized.

## Subsequent T2-004 authorization (2026-11-04)

User authorizes FastAPI HTTP integration against accepted e828729b/0b2e0b7:

- app.py application factory, documented POST /mcp, and pooled adapter lifespan.
- Reuse existing settings/security/rpc/upstream components without duplicating
  their functionality or unnecessarily redesigning accepted behavior.
- Apply method/media/encoding/size policies before RPC; bound streamed/chunked
  bodies; authenticate Bearer credentials before application-level RPC processing.
- Inspect/authorize tools/call before any outbound request; forward only existing
  permits through the adapter, preserving request/response bytes and IDs.
- Document HTTP statuses for authentication/authorization/malformed/upstream
  failures; preserve applicable local-error IDs and fail-closed batches/notifications.
- Do not disclose tokens, internal exceptions or upstream credentials in responses
  or logs. Test missing/malformed/duplicate/invalid credentials, roles, zero denied
  upstream delivery, transparent discovery, encoded names/duplicate keys, malformed/
  oversized/compressed bodies, concurrency, failures and startup/shutdown.
- Inject ASGI/HTTPX transports for integration. Actual sockets belong to T2-005.
- Run full Task 2 pytest and both Ruff checks; record actual evidence and update
  governance. Stop for independent review; no Task 1 changes, SSE, OAuth/JWT, Tasks
  3/4, T2-005, commit or push. Prior no-endpoint restrictions are historical.

## T2-004 independent acceptance and commit authorization (2026-11-04)

The user confirms independent approval of T2-004, a reviewed 400-test pass and
additional security probes confirming zero upstream calls on rejection. Authorize
one descriptive commit of approved T2-004 source/tests/dependencies and relevant
documentation only. Exclude environments, caches, egg-info, credentials and ZIP
review artifacts. Do not alter the accepted implementation, push or begin T2-005.
This supersedes only the preceding no-commit restriction for this Git checkpoint.

## Subsequent T2-005 authorization (2026-11-04)

User authorizes real HTTP wire verification against accepted be9ddd8/400 tests:

- Launch existing proxy through Uvicorn and an independent mock HTTP/JSON-RPC peer
  in separate processes; use real loopback TCP clients, dynamic ports, deterministic
  fixtures, explicit readiness, bounded startup and reliable cleanup. No public
  listeners or external RPC services.
- Verify missing/invalid/malformed/duplicate Bearer credentials, viewer protected
  denial HTTP 403/-32001/exact message/applicable ID, zero journaled upstream calls
  for local rejection, admin access, ordinary calls for both roles and transparent
  discovery including admin definitions. Verify escaped names/duplicate keys and
  isolation of inbound tokens/cookies/spoofed role headers from upstream.
- Verify original request/response/error bytes and IDs; Content-Length/chunked,
  oversize/media/encoding, malformed RPC/IDs, notifications/batches, statuses/headers.
- Test concurrent independent clients/repeated IDs, slow-peer deadlines, refusal,
  unexpected process termination, disconnects, startup/shutdown and failed-test
  cleanup using synchronization/bounded waits, not unreliable sleep assertions.
- Prefer test fixtures/harness over production edits; reproduce and document any
  defect before a narrow correction. Preserve Task 1/accepted Task 2 behavior.
- Run full Task 2 suite and Ruff; Task 1 regressions only if shared code/environment
  changes. Record actual counts, journal/process outcomes/failures/limits/docs.
- Stop for independent review; do not claim acceptance, commit/push, start T2-006,
  implement full MCP sessions/SSE/OAuth or Tasks 3/4. Earlier no-wire restrictions
  are historical; new architecture choices are documented separately in the contract.

## T2-005 independent acceptance and commit authorization (2026-11-04)

User confirms independent acceptance: 400 prior/52 wire tests passed, 33 rejection
cases prevent upstream delivery, 12 children reaped without forced cleanup, and
production/prior tests match the T2-004 review snapshot. Authorize one descriptive
commit of approved wire tests, pytest marker and related engineering docs only.
Exclude environments/caches/credentials/review ZIPs. Do not push, begin T2-006 or
change Task 1/accepted implementation. This supersedes only the prior no-commit
restriction for this Git checkpoint; no additional implementation scope is granted.

## Subsequent T2-006 final audit authorization (2026-11-04)

User authorizes an evidence-based verification/documentation checkpoint against
accepted aa343b3: trace original requirements separately from choices; execute
complete Task 2/Task 1 suites and both Ruff checks in their own environments;
verify locked Task 2 setup/imports/CLI/config/examples/lifespan; inspect current
files/relevant Git history, secrets/artifacts/ignore rules and public documentation.
Deliver traceability, actual counts/versions/commands/exits, publication audit,
submission checklist, limitations and READY/CHANGES REQUIRED recommendation.
Documentation-only corrections are allowed. Reproduce/document a production defect
then stop for review; no accepted code changes, new features, Tasks 3/4, commit or
push. TASK-2 must remain IN_PROGRESS until independent final audit acceptance.

## T2-006 independent acceptance and final documentation commit (2026-11-04)

User confirms independent verdict APPROVED: Task 2 assessment-ready within its
documented requirements; eight traceability rows, test references and final evidence/
submission docs consistent. Mark T2-006/TASK-2 DONE and authorize one final docs-only
acceptance commit, after complete diff/staging/preservation/whitespace inspection.
This supersedes the earlier review/no-commit gate for this checkpoint only. Preserve
all implementation/tests/dependencies/locks; no test reruns unless an unexpected
code/config change appears, no push or Tasks 3/4. No assessment requirement changes.
