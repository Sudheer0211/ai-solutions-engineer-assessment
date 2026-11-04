# Task 2 guard checkpoint

This project implements T2-001/T2-002 only: configuration and pure security/
JSON-RPC guards. There is no HTTP endpoint, application launcher or forwarding.
FastAPI + HTTPX integration belongs to the next authorized checkpoint.
See [CONTRACT.md](CONTRACT.md) for exact requirements, choices and deferred work.

Checkpoint verification (2026-11-04): 186 unit cases passed; Ruff lint and format
checks passed. See root docs/TEST_EVIDENCE.md entries E008/E009 for actual results.
Independent engineering review accepted T2-001/T2-002, including the Decimal fix,
as confirmed by the user on 2026-11-04. Whole Task 2 remains incomplete; T2-003
implementation awaits explicit authorization. No HTTP endpoint or forwarding exists.

From task2/ with uv installed:

```powershell
uv sync --locked --extra dev --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Use this project's environment; do not install into the root Task 1 environment.
Runtime guards use only the standard library. Dev/build versions are pinned;
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
