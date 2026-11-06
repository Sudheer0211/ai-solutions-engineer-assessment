# Task 4: token accounting, SQLite storage and injectable LLM routing

## Current publication status

**Task 4 is DONE, independently accepted within its documented requirements,
supported Windows/SQLite environment and trusted-adapter policies, and published.**
Verified public baseline: `a3a2af2`; see [repository publication status](../README.md).
Latest documented E041 verification (2026-11-06 America/Los_Angeles): **427 passed**,
both Ruff checks passed; repository total **1,761**. The existing synthetic evaluator
demo also passed nine cases. No tests were rerun for this documentation cleanup.

The original full evaluator rubric/vendor specification is not fully available.
Real-provider/tokenizer interoperability remains **NOT VERIFIED / rubric-dependent**;
stock authenticated generation returns 503 without trusted adapters. The synthetic
demo below is reproducible evidence, not a real-model or production certification.
Earlier checkpoint records below are explicitly historical; their pending-work and
publication instructions no longer describe the completed, published project.

## Evaluator demo: synthetic success, fallback and quota rejection

The stock factory deliberately returns sanitized **503** for authenticated
generation when trusted provider/token-bound adapters are absent. It does not
guess a tokenizer or connect to a real LLM. Real-provider integration is **NOT
VERIFIED / rubric-dependent**, rather than an automatic failure or success.

After the documented locked `dev`/`serve` setup, run this one command from `task4/`
on the supported native Windows fixed-local-drive/SQLite environment:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py -k "content_length_chunked_and_success_privacy or routing_and_conservative_accounting or exact_quota_and_denial_never_dispatches" --tb=short
```

The nine cases use existing deterministic trusted adapters and independent
loopback provider/proxy processes: primary success; primary429 and real3000ms
timeout with exactly one backup; terminal backup failure/429; transport failure;
unknown-usage accounting; exactly50000 combined reservation; and50001 denial.
The quota case also repeats a request to prove local429 causes zero extra provider
calls. Fixtures generate ephemeral credentials/SQLite state, assert sanitized
responses/accounting and reap children. No real credential/API/vendor/tokenizer is
required, and no provider adapter is installed into production by this command.
These are executable assessment demonstrations, not real-model certification.
See E041 and [post-acceptance findings](../docs/TASK3_TASK4_EVALUATOR_REMEDIATION.md).

## Historical T4-006 independent acceptance

**TASK-4 and T4-006 are DONE and independently APPROVED**, confirmed by the user
2026-11-05 (America/Los_Angeles), within documented requirements, supported
Windows/SQLite storage and trusted-adapter policies. All seven traceability rows,
named test references, E028 results, documentation and limitations were reviewed
and found consistent. E029 records reported acceptance, not new test executions.
[Final audit](../docs/TASK4_FINAL_AUDIT.md) and E028 record actual 2026-11-04
native Windows/Python 3.12.16/SQLite 3.53.1 verification:
**427 passed in 40.44s**, zero failures/skips/warnings/xfails, Ruff lint/format
pass (22 files); fresh Task 1/2 regressions also pass 149/452 without changes.
A new locked 27-package installation/import check, six deterministic ASGI cases,
seven wire cases and the stock CLI's intended authenticated 503/graceful exit pass.
No accepted implementation/test/config/lock changes or real-provider certification.
This acceptance supersedes historical pending-review/no-T4-006 gates below; all
historical evidence/environment qualifications remain intact. One final docs-only
acceptance commit is authorized, no test rerun absent unexpected code/config changes.
Preserve source/tests/dependencies/configuration/lock; no Task 3 or push.

### Historical T4-005 verification and handoff

**T4-005 is independently ACCEPTED**, confirmed by the user 2026-11-04.
E026: **427 passed in 40.81s** (324 accepted + 74 ASGI/config/lifecycle + 29 wire),
zero failures/skips/warnings/xfails; Ruff lint/format pass (22 files). Native
Windows/Python 3.12.16/SQLite 3.53.1; storage remains fixed-local-drive only.
28 wire children reaped (27 exit 0, one EXPECTED invalid-startup exit 3), zero
forced cleanup; 15 storage children exit 0, total 43 reaped. 21 journal receipts
confirm zero provider calls AND zero new reservations for local rejections.

T4-001 through T4-004 are independently accepted (baseline c889236). E024 native
orchestration verification remains authoritative; E025's Linux compatibility review
does not add native Linux support. Accepted components/tests and Tasks 1/2 are
unchanged; only Task 4 HTTP dependencies/lock were extended. No real model/tokenizer
or vendor is supplied. TASK-4 IN_PROGRESS; one approved T4-005 milestone commit
only, no T4-006 implementation or push. E027 records qualified independent review:
427 cases across separate runs, 29 wire cases in split groups, using Linux review-
only compatibility substitutions. A combined Linux wire run stalled in fixture
teardown; it was NOT a completed all-at-once pass. No review substitutions ship,
no blocking production defect found; E026 native Windows full-suite result remains
authoritative. Historical limits below are superseded only by this checkpoint.

## Historical T4-001/T4-002 foundation

Isolated Python 3.12 project with standard-library-only runtime. Task 1/2 source,
tests, environments and dependency configurations are separate and unchanged.
Source contract: [TASK4_REQUIREMENTS.md](../docs/TASK4_REQUIREMENTS.md), finalized
engineering policies P1-P4; ADR-016. T4-001 architecture is independently approved
with conditions now finalized. **T4-002 is independently ACCEPTED**, confirmed by
the user on 2026-11-04: 169 existing tests, 12,000 randomized differential checks
and six targeted invariants passed; no blocking defect. These are reported review
results, not new local executions. E020 retains actual local pytest/Ruff evidence;
E021 records acceptance/Git inspection. Whole TASK-4 remains IN_PROGRESS.

From task4/, with uv installed:

```powershell
uv sync --locked --extra dev --extra serve --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Local verification E020 (2026-11-04 America/Los_Angeles): **169 passed in 0.12s**,
zero failures/skips/warnings/xfails, both Ruff checks pass (5 Python files).
Initial sandbox execution passed 169 with one cache-permission warning; the same
command outside the sandbox resolved it. No tests/markers/warning filters changed.
Runtime Python 3.12.16, pytest 9.2.0, Ruff 0.17.3; setuptools 82.0.1 isolated build.
The lock selects eight installed packages including this editable project.

## Historical T4-002 interface and trust boundary

- models.ModelTokenBounds: model alias, input/output bounds and counting-policy
  identifier. Requires exact nonnegative integers, positive total and signed-64-bit
  range. These are TRUSTED INTERNAL ADAPTER OUTPUTS, not client estimates. A name
  or successful construction cannot prove a tokenizer/output-cap guarantee.
- models.ReservationPlan: both typed model bounds required; total is the combined
  primary+backup reservation, checked for overflow. No missing-backup shortcut.
- models.SettledUsage / OutstandingReservation: immutable tenant-scoped entry ID,
  admission timestamp and token amount. Holds must be positive; settled zero is valid.
- accounting.calculate_usage(tenant_id, now_ms, settled, outstanding,
  last_observed_ms=None): sum settled entries in (now-60,000,now] plus ALL target-
  tenant holds, even old holds. Future entries, regressed watermark, wrong record
  types or duplicate identities (including both states) fail closed.
- accounting.assess_admission(..., clock=..., last_observed_ms=None): sample injected
  AccountingClock.now_ms once and return immutable AdmissionDecision. Allowed iff
  settled + outstanding + both new model bounds <= 50,000. Existing overage denies.
  Denied decisions leave reported remaining capacity unchanged, never negative.

Opaque tenant IDs are compared exactly, without normalization/case-folding. Raw
API-key authentication/HMAC identity resolution is not implemented in this checkpoint.
Future trusted adapters must establish model-specific token bounds/output enforcement
or reject before dispatch. No actual provider/tokenizer is selected or certified.

Each entry represents one attempt's accounting identity; future storage projects
its attempt rows into these records once. Settlement replaces an outstanding entry
at its original admission timestamp; it must not supply that ID in both collections.
T4-002 receives snapshots; it does not perform settlement, refunds or recovery.

## Historical T4-002 checkpoint limits

Pure decisions do not reserve tokens or mutate a store. Repeating an allowed
calculation can return allowed again: atomic concurrent admission belongs to
T4-003's SQLite transaction. Do not use these results as authorization permits.
Unresolved holds never expire in pure calculations; future recovery must supply
an explicit valid replacement rather than expecting automatic quota release.

No SQLite database/transactions, provider clients, timeout/fallback execution, HTTP
endpoints, crash-recovery infrastructure or Task 3 is implemented. P3's monotonic
3,000 ms primary/500 ms cleanup policy is documented only. Persistence, concurrency,
real token provenance, provider behavior and full Task 4 compliance remain unverified.
The accepted foundation is committed as 3d8d3e5 and unchanged. Historical pure-only
limits above describe T4-002; T4-003 adds storage below, with its own review gate.

## T4-003 storage API

`storage.SQLiteStore(StorageSettings(absolute_path, external_identity_secret),
clock=injected_UTC_clock)` bootstraps/validates a local SQLite store. The parent
directory must exist. Only Windows fixed local volumes are currently verified;
network volumes and other platforms fail closed. Runtime minimum SQLite 3.51.3;
this environment verifies 3.53.1. No database file or secret ships in the repository.

| Operation | Guarantee |
| --- | --- |
| admit(key_bytes, UUID, plan, reservation_ms=...) | Atomic read/pure decision/two reservations; return only after COMMIT |
| start_attempt(key_bytes, UUID, ordinal) | One durable dispatch intent; does not execute/select a provider |
| settle(..., actual_tokens=int or None) | Known charge or full unknown bound; same admission time; identical repeat no-op |
| release_unused(...) | Only never-started reservation; idempotent zero charge |
| usage(key_bytes) / request(key_bytes, UUID) | Tenant-scoped immutable accounting/state; persistent clock and lazy recovery |
| recover(key_bytes) | Convert due unresolved holds to full deadline charges once; no provider replay |

API keys are transient opaque bytes HMACed under the external 32-1024-byte identity
secret; only full digests/verifier/internal UUIDs/numeric states are persisted.
Actual key authentication/provisioning remains a future boundary. Raw prompts,
completions, model/counter strings and provider credentials are not stored. Reopening
with incompatible identity/configuration fails. Do not rotate the secret/delete the
DB to recover availability; use separately reviewed migration/restore procedures.

SQLite uses STRICT schema/PK/FK/check constraints, WAL/FULL, explicit 1,000 ms busy
policy (configurable 1-10,000), and short BEGIN IMMEDIATE transactions. Connections
are private to each synchronous operation/calling thread. Async callers must offload
whole calls and drain before close. No provider/network I/O belongs inside a store
operation. Existing-file calls use mode=rw; missing stores are not recreated silently.

All unresolved holds count beyond their original 60s window. At the explicitly
supplied finite reservation deadline, lazy recovery changes remaining holds to full
charges anchored at that deadline and marks the request abandoned. Those charges
expire exactly 60s later; settled earlier attempts keep original timestamps.
Duplicate IDs, stale/invalid transitions and clock regression fail; failed
transactions retain original state. Over-bound actual usage durably blocks further
tenant admission. Generic StorageError exposes only an internal failure kind, not
SQLite diagnostics/paths/credentials. No automatic retry, pruning or unblock API.

### Historical T4-003 verification and handoff

Six barrier-synchronized processes competed for the final 2,000 tokens: one winner,
five denials, durable total 50,000. Duplicate-ID and identical/conflicting settlement
races and two independent writer/reader processes pass. Full run reaped 15 children,
all exit 0, no live/forced cleanup. Sanitized `.cache/sqlite_process_summary.json`
contains only cleanup outcomes; databases and artifacts under .cache are ignored.

This is storage-level durability/concurrency, not provider fallback/timeout, HTTP,
remote billing recovery, cross-platform filesystem or power-loss/hardware audit.
No Task 1/2 rerun was needed: no shared code/env changed. See
[T4-003 contract](../docs/TASK4_REQUIREMENTS.md), ADR-018 and E022 for exact schema,
transaction/error/recovery policy, actual commands, initial lint correction and risks.
T4-003 is accepted with the qualification above; preserve implementation and stop
after the authorized milestone commit. No T4-004 implementation or push authorized.

## Historical T4-004 provider/service checkpoint (API retained)

`providers.Provider` is an injectable trusted adapter. Its pure `prepare(text)`
returns a request-scoped `PreparedAttempt` with model-specific `bounds`,
`async execute()` and `async aclose()`. It MUST reliably count every token category
and enforce the matching output cap, with no hidden retry or redirect. The service
checks typed/model/counter metadata; those checks do not prove real tokenizer
correctness. No vendor contract/tokenizer is invented, and no caller-supplied
bounds are accepted. Unavailable reliable bounds must fail before admission/send.
Test doubles implement a synthetic counting/cap contract only.

Create `LLMService(store, primary, backup, RoutingPolicy(backup_timeout_ms,
reservation_ms), clock=optional_monotonic_clock)` using an initialized supported
SQLiteStore and trusted adapters. There are deliberately no backup/overall budget
defaults: supply positive integer budgets, reservation_ms greater than
3000 + 500 + backup_timeout_ms + 500, plus sufficient DB/scheduling margin.
The 2000/10000 values in tests are fixtures, not deployment requirements.

`await service.generate(validated_key_bytes, text, request_id=optional_internal_UUID)`
returns controlled ServiceOutcome(code/message/text/used_backup/request_id).
The key is shape-checked and used only by storage, never passed to model adapters.
Actual key authentication/provisioning and HTTP schemas remain deferred. Success
text is preserved; errors never copy raw provider/SQL diagnostics.

- Atomic combined admission precedes any send; local quota denial has zero provider
  calls. Durable single-start guards and tenant separation remain in
  accepted storage; provider input is the prompt alone, not a tenant credential.
- Primary deadline is monotonic 3000 ms. At/after the deadline, content loses; late
  reliable usage can still settle. Primary 429 or that deadline triggers exactly
  one backup only after confirmed local termination AND resource close. Early
  adapter timeouts are terminal failures, not evidence of the 3000 ms threshold.
- One shared 500 ms cleanup grace covers termination and close; timeout's ceiling
  remains original deadline+500 even after delayed observation. No confirmed cleanup
  means unavailable/no backup, retained holds and quarantined service dispatch.
- Backup has the explicit finite deadline; failure/timeout has no third attempt.
  Known in-bound usage settles at admission time; unknown usage charges full bound.
  Unsent backup is released only after confirmed cleanup. Bound breaches fail closed.
- All DB calls and pure preparation are offloaded through one bounded lane. DB
  transactions do not enclose provider I/O. SQLite remains the atomic quota arbiter
  across independent service instances and processes.
- Cancelling generate signals an owned workflow and raises CancelledError to the
  caller; it does not cancel a DB thread or assert rollback. The workflow discovers
  actual completion, cleans/accounts and prevents new fallback. Ambiguous storage
  failures preserve durable holds for accepted deadline recovery, with no replay.
- Stop submissions, then `await service.aclose()` BEFORE closing store/event loop.
  It drains owners/DB work and bounds its remaining cleanup wait. False signals
  unconfirmed/failed cleanup; retain ownership and do not claim graceful shutdown.
  An arbitrary uncooperative adapter/blocked OS thread cannot be forcibly killed
  by asyncio. Local cancellation cannot guarantee remote execution/billing stopped.

New tests use real local SQLite plus controlled clocks/events/fake providers,
including 2999/3000/3001 primary and cleanup boundaries, late observation, failure,
cancellation during DB work, duplicate starts, independent concurrent service
owners and tenant isolation. Complete suite includes the unchanged storage process
fixtures (15 normal children/zero forced cleanup). No network/provider socket,
actual model-token bound, HTTP or final fault-injection audit is claimed. Supported
storage remains Windows fixed local drive/SQLite >=3.51.3, actual 3.53.1.
See requirements T4-004 contract, accepted ADR-019 and E024/E025. Preserve approved
implementation; no test rerun or T4-005. The approximately 3.020 s independent
probe is reported evidence, not a latency SLA or new local execution. Stop after
the one authorized milestone commit; no push.

## T4-005 HTTP API and execution (independently accepted)

From task4/, use the isolated lock/environment above. FastAPI 0.162.0 runtime,
HTTPX 0.28.1/asgi-lifespan 2.1.0 dev, Uvicorn 0.54.0 serve extra; actual locked
Starlette 1.10.0/Pydantic 2.14.2. Never install these into Tasks 1/2 environments.

Supply required values through your operator environment/secrets manager (no real
credentials, .env contents or database files belong in Git):

| Variable | Meaning |
| --- | --- |
| TASK4_DATABASE_PATH | Absolute on-disk path, existing trusted parent on supported Windows fixed local drive |
| TASK4_IDENTITY_SECRET_HEX | Stable external 32-1024-byte identity secret encoded as hex; strong random material, no default |
| TASK4_TENANT_KEYS_JSON | JSON array of 1-1024 distinct strong registered Bearer keys, 32-256 safe ASCII bytes each; no default |
| TASK4_BACKUP_TIMEOUT_MS | Explicit positive finite backup budget; no default |
| TASK4_RESERVATION_MS | Explicit lifetime >3000+500+backup_timeout_ms+500, with adequate DB/scheduling margin |
| TASK4_MAX_BODY_BYTES | Optional 1-1048576; default 65536 |
| TASK4_BODY_TIMEOUT_MS | Optional 1-60000; default 5000 total body read |

Keep the same identity secret and tenant key across restarts to preserve identity.
Do not delete the database or rotate identity to recover quota. Removing a key from
allowlist and controlled restart revokes access without removing usage. Key/identity
rotation or DB retention migrations are not implemented.

Launch from task4/ (with dependencies installed):

```powershell
./.venv/Scripts/python.exe -m uvicorn task4_limiter.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log --no-proxy-headers --log-level warning
```

**The stock factory deliberately returns 503 before admission when model bounds
are unavailable.** It does not pretend to provide a real LLM. A trusted deployment
module must call create_app(..., provider_resources=...) with an async context
manager yielding verified primary/backup Provider adapters. Its pure prepare must
establish model-specific reliable input bounds, install/enforce output caps and
cover billable categories. Credentials remain private to that adapter. No caller
model/URL/cap/token estimate override, guessed tokenizer, hidden retry or redirect.
Tests use synthetic counters/adapters, not real-model guarantees. Deploy the trusted
module's factory through Uvicorn once its provider contract is verified.

### Reproduce primary success and fallback without a real provider

After the locked `dev` AND `serve` setup above, run from `task4/` on supported
Windows fixed-local-drive storage with SQLite >=3.51.3:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_http.py::test_routing_status_accounting_and_no_prompt_or_secret_leak --tb=short
.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py::test_wire_content_length_chunked_and_success_privacy tests/test_http_wire.py::test_wire_routing_and_conservative_accounting --tb=short
```

The first selector runs six ASGI cases (success, unknown usage, primary 429,
primary failure, backup failure and missing bounds). The second runs seven cases
over actual loopback HTTP: primary success, primary 429 and real 3,000 ms timeout
fallback, backup failure/429, transport failure and unknown usage. Fixtures create
temporary strong credentials/SQLite files, inject trusted deterministic adapters,
start Uvicorn plus an independent synthetic upstream on dynamic loopback ports,
assert routing/accounting and reap their children. No manual key/provider setup or
external inference service is needed. These fixtures are test-only adapters, not
a vendor integration or a production launch factory. E028 repeats both selectors
in a NEW locked environment: six/seven passed; all 14 wire children exit 0.

### Authenticated stock request

With a registered key already supplied in your environment, an authenticated request
can be made without writing the key into an example file:

```powershell
$registeredKeys = ConvertFrom-Json $env:TASK4_TENANT_KEYS_JSON
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/generate -ContentType application/json -Headers @{ Authorization = "Bearer " + $registeredKeys[0] } -Body '{"prompt":"Example request"}'
```

POST /generate accepts ONLY a nonempty prompt string (<=16000 characters) in a
UTF-8 JSON object. Duplicate keys, malformed/invalid-Unicode/nonfinite JSON, unknown
fields (tenant IDs, token estimates, model/cap overrides), arrays and coerced types
are rejected. JSON content type only (optional UTF-8 charset); no Content-Encoding,
even identity. Actual streamed bytes are limited, including chunked requests.
One Authorization: Bearer <key> header is required. Scheme case-insensitive, token
exact/case-sensitive. Unknown/removed/malformed/duplicate/missing credentials get
identical 401. Cookies/query keys/X-Tenant-ID/X-Role never grant authority. Only
authenticated, validated calls reach accepted service; existing SQLite HMAC maps
the accepted raw bytes to stable tenant identity, no client ID authority.

Success: {request_id, result:{text,used_backup}}; error:
{error:{code,message,request_id}}. UUID is generated by server, also X-Request-ID.
Responses are JSON with Cache-Control:no-store and X-Content-Type-Options:nosniff.
For example (UUID/completion are synthetic placeholders):

```json
{"request_id":"<server-uuid>","result":{"text":"Synthetic completion","used_backup":false}}
```

```json
{"error":{"code":"tenant_quota_exceeded","message":"Tenant quota exceeded","request_id":"<server-uuid>"}}
```

No raw request prompt, credentials, SQL path or provider diagnostics are reflected
as metadata/error detail or logged. Success text is the trusted adapter completion;
real-model semantic redaction/privacy is not certified by synthetic tests.

| Status | Meaning / code |
| --- | --- |
| 200 | Primary or authorized backup completion |
| 400 | Invalid JSON/schema/framing visible to app / invalid_request |
| 401 | Invalid credentials, WWW-Authenticate Bearer challenge |
| 404 / 405 | Unknown path / unsupported method (Allow: POST) |
| 408 | Body-read deadline / request_timeout |
| 413 | Body-size limit / request_too_large |
| 415 | Unsupported media type/content encoding |
| 429 | tenant_quota_exceeded (NO provider call) OR provider_rate_limited (terminal backup 429) |
| 499 | Diagnostic client_disconnected if still deliverable; normally closed peer receives no response |
| 502 | model_unavailable, no unapproved fallback/third attempt |
| 503 | service_unavailable: missing reliable bounds, DB failure, quarantine/unavailable resources |
| 504 | model_timeout: terminal timeout |

Primary HTTP 429 is an internal event and normally yields a 200 backup success,
not a local quota 429. Primary 3000 ms deadline and shared 500 ms cleanup behavior
remain unchanged. Failed/unconfirmed cleanup launches no backup, retains holds and
quarantines dispatch. Unknown consumption is charged conservatively; only proven
unsent capacity is finalized unused. No provider work inside DB transactions.

Lifespan opens SQLite off-loop, owns provider resources and accepted LLMService,
drains service before closing provider pools/store. A post-body ASGI disconnect
watcher cancels the public generate call; accepted shielded workflow discovers DB
completion and settles/recoverably retains usage. Startup/shutdown cancellation
cannot silently discard workers/cleanup. Unconfirmed cleanup produces a generic
unclean-shutdown failure while retaining resource ownership. Arbitrary broken
adapters/blocked OS I/O cannot be forcibly killed by asyncio; supervisor recovery
may be necessary. Real remote execution/billing after cancellation is uncertain.

### Historical T4-005 wire verification and handoff

Run all tests (including wire) with the isolated dev AND serve extras installed.
Wire harness starts separate proxy and synthetic upstream processes on 127.0.0.1,
child-bound dynamic ports, HTTP readiness and explicit release synchronization.
No real vendor or external network is contacted. Journals contain only synthetic
attempt IDs, ordinal/phase/header-presence; usage DB stores approved accounting
metadata/HMACs. Receipts in ignored .cache/http_wire_summary.json record per-mode
provider calls/charges, 21 zero-call/zero-reservation rejections, process cleanup;
.cache/sqlite_process_summary.json records the 15 storage children. First invalid-
startup harness failed due to daemon stdin finalization; async stop-file control
fixed it without weakening assertions. E026 preserves both actual runs.

Malformed HTTP rejected before ASGI may receive Uvicorn/h11's HTTP 400 rather than
the application envelope; server normalization may erase redundant header syntax.
Only loopback HTTP/1.1 is verified, not arbitrary proxy/HTTP2/public deployment.
Outside loopback require TLS, safe ingress/logging, strong key provisioning and
verified provider accounting/caps. No access logs/untrusted proxy-header trust,
OAuth, streaming, Redis/distributed limiting, vendor support, rotation/unblock/
retention API or final fault/load audit. T4-005 is independently accepted (E027),
with split Linux review results and the combined-run teardown stall qualified above.
Preserve approved implementation; no test rerun absent unexpected changes. Stop
after the one authorized milestone commit; no T4-006 or push.
