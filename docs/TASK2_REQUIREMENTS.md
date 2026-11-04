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
