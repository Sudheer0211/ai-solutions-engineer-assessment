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
