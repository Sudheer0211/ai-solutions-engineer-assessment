# TASK-4 / T4-001: Multi-Tenant LLM Rate Limiter contract and design

Date: 2026-11-04 (America/Los_Angeles). Source: user-recovered original assessment
requirements and explicit clarifications supplied in this session. No separate
verbatim original Task 4 document/provider specification was attached. This record
preserves the confirmed requirements separately from proposed engineering choices.

Current status (2026-11-04 America/Los_Angeles): T4-001 through T4-005 are
independently ACCEPTED; TASK-4 remains IN_PROGRESS. E026 native Windows/Python
3.12.16/SQLite 3.53.1 full-suite verification remains authoritative. E027 records
qualified independent review: 427 cases across separate runs, 29 wire cases in
split groups with review-only Linux compatibility substitutions. One combined
Linux wire run stalled during fixture teardown, NOT a completed all-at-once pass.
No blocking production defect; no new native Linux support or shipped substitution.
One descriptive approved T4-005 Git commit is authorized; preserve code/tests/
configuration/lock and Tasks 1/2. No tests absent unexpected implementation changes,
T4-006, Task 3, new vendor/HTTP features or push. Original R1-R7/P1-P4 and HTTP
implementation choices below are unchanged.

## Finalized engineering policies after conditional approval

The user independently accepts the architecture, combined primary+backup reservation,
transactional admission, conservative recovery and controlled fallback. P1-P4 below
complete the requested conditions. These are explicit ENGINEERING ASSUMPTIONS,
not additional original assessment requirements R1-R7. Earlier proposed wording
is retained as design history; P1-P4 supersede ambiguity in A2/A4/A5/A6/recovery.

- P1 (timestamps/invariant): sample UTC accounting time once inside future admission
  transaction. Stamp both attempt reservations with that admission time. Normal
  settlement REPLACES the corresponding hold with actual/conservative charge at the
  SAME admission timestamp; never insert an extra counted copy. At time t, count
  settled entries with t-60,000 < timestamp <= t, plus ALL outstanding reservations
  regardless of age/deadline. Exactly 50,000 is permitted; greater is denied. At
  exactly timestamp+60,000 a settled charge expires, but an unresolved hold does not.
  Reject target-tenant future timestamps or a clock behind the persisted watermark;
  do not silently ignore evidence of clock regression. Clock drift assumptions remain.
- P2 (bounds): trusted model-specific accounting must establish input upper bound
  and an enforceable output cap including all counted token categories for EACH
  model. Counts must be exact nonnegative integers within signed-64-bit storage
  range, with positive per-model total and nonoverflowing combined total. No bool,
  float, string, missing bound, caller estimate, character heuristic or `verified`
  client flag is sufficient. Missing/unreliable/model-mismatched bounds cause a
  sanitized service-unavailable rejection BEFORE reservation/provider dispatch;
  invalid caller parameters map separately to invalid_request. A valid combined
  demand over quota is a local quota rejection. T4-002 takes trusted internal bound
  records only: its arithmetic cannot certify tokenizer/provider provenance. Future
  model adapters MUST create them from verified counting/output enforcement or fail
  closed; no real provider/tokenizer is selected or implemented here.
- P3 (deadline/cleanup): primary deadline is start_monotonic+3,000 ms, measured
  immediately before send through complete bounded response receipt; pool/connect/
  write/read share that single budget. A response observed at/after deadline loses
  the race. After timeout/primary 429, cancellation plus local resource cleanup has
  ONE additional 500 ms grace budget, not a fresh allowance per cleanup step.
  Use a bounded wait that does not indefinitely await cancellation-resistant tasks.
  Backup dispatch requires primary task terminal and resources closed, durable
  state transition and valid overall reservation deadline. If cleanup cannot be
  confirmed within grace, return sanitized service_unavailable, retain conservative
  accounting and launch NO backup/orphaned retry. Normal cooperative timeout/429
  automatically falls back once after cleanup. Total response time need not be
  exactly 3,000 ms. Local cancellation cannot guarantee remote execution stopped.
  Deadline/routing execution is T4-004, not implemented in T4-002.
- P4 (settlement/recovery): future storage updates one tenant-scoped attempt identity
  transactionally by expected state. Repeating identical settlement is a no-op;
  conflicting/stale settlement fails closed, never an extra charge/refund. Known
  usage cannot exceed its bound; unknown dispatched usage retains the full bound.
  Only provably unsent capacity can be released. Restart alone never releases or
  replays an unresolved attempt. Until future transactional recovery converts a
  hold, it counts even after its deadline. At/after a finite overall deadline,
  lazy recovery may convert remaining holds once to full charges anchored at that
  deadline, a conservative extension of P1, then expire normally after 60 seconds.
  Old workers cannot dispatch/overwrite recovered entries. No automatic provider
  replay/query or distributed recovery infrastructure. T4-002 only calculates
  snapshots; it neither settles nor recovers records.

T4-002 pure calculations are NOT concurrent admission permits: repeated evaluation
does not mutate state. T4-003 must enforce check+reserve atomically. Snapshots reject
duplicate target-tenant entry identities, including identities present as both
settled and outstanding. Known existing overage must fail closed for new admission.

## Confirmed assessment requirements

| ID | Confirmed requirement |
| --- | --- |
| T4-R1 | Token-aware sliding-window rate limiter |
| T4-R2 | Maximum 50,000 tokens per minute per tenant API key |
| T4-R3 | Persistent usage tracking using on-disk SQLite |
| T4-R4 | Safe handling of concurrent requests |
| T4-R5 | Primary HTTP 429 automatically triggers secondary backup |
| T4-R6 | Primary timeout after 3,000 ms automatically triggers secondary backup |
| T4-R7 | Standardized, sanitized error responses |

Confirmed clarifications: local tenant-quota 429 MUST NOT bypass quota through
fallback; 3,000 ms is the primary timeout, not a Retry-After comparison; fallback
must be a controlled transition without unintended retries/concurrent duplicate
executions; preserve tenant isolation across concurrency/restarts; identify accounting
assumptions; verify actual SQLite runtime before selecting WAL; keep recovery
proportional without distributed infrastructure.

## Accounting choices and remaining adapter decisions

The brief does not specify the counting source, accounting timestamp, output cap,
charge treatment of failed attempts or fallback-budget admission. The architecture
review accepts the conservative reservation design; P1-P4 finalize its conditions.
The following engineering choices are distinct from assessment wording; provider,
HTTP and other deferred details remain future checkpoint inputs:

| ID | Engineering choice / unresolved dependency |
| --- | --- |
| T4-A1 | Count input plus output across BOTH provider attempts under the same tenant-key budget. Do not count characters or accept caller-reported usage as authoritative. Provider-specific tokenizer/usage fields remain unspecified. |
| T4-A2 | Each attempt needs a reliable bound B = accounted input tokens + enforced maximum output tokens, including any provider-specific billable categories. Both model tokenizers/caps must support the bound; otherwise reject before dispatch. A final provider count alone cannot enforce a hard concurrent cap. |
| T4-A3 | Atomically reserve B_primary + B_backup before primary dispatch. This ensures required fallback does not later need unreserved quota. Conservative consequence: requests can be rejected even though primary alone would fit. A combined reservation exceeding 50,000 is rejected, not split across models. |
| T4-A4 | Attribute normally finalized charges to logical-request admission time. Sliding interval is (now - 60,000 ms, now]; exactly 50,000 is allowed. Outstanding reservations count independently of age until finalized/recovered. These boundary/timestamp choices are not original brief wording. |
| T4-A5 | Reconcile known usage down to actual values; release a provably unsent backup reservation after primary success. Unknown primary usage after timeout is conservatively charged at its bound; a 429 is not automatically assumed unbilled. Trust zero only when the provider contract reliably establishes it. |
| T4-A6 | Primary has a monotonic 3,000 ms total exchange deadline beginning immediately before the send operation; excludes prior quota/DB work, includes pool/connect/write/read and complete bounded response receipt. Completion observed at/after deadline is timeout. P3 finalizes the measurement/tie rule and bounded 500 ms cleanup grace. |
| T4-A7 | Backup has its own finite deadline; its numeric value and an overall reservation deadline remain to be approved. No inherited unlimited timeout or assumed second 3,000 ms requirement. |
| T4-A8 | Resolve an externally validated API key to HMAC-SHA256(identity_secret, api_key_bytes). Store the full pseudonymous identifier, never raw keys. Same key/secret maps identically after restart. Header name, key provisioning and key/identity-secret rotation remain unspecified; rotation must not silently reset usage. |
| T4-A9 | Nonstreaming, one logical request per call; candidate POST /generate with typed JSON, not Task 2 JSON-RPC. Exact path/request/success/error schemas and streaming expectations need approval. |
| T4-A10 | Only primary 429 and the primary deadline trigger fallback. No automatic retries/redirects, hedging, 5xx/connection-error fallback or recursive backup fallback. Other errors return sanitized failures. |

The strict-cap guarantee is conditional on reliable per-model bounds, correctly
enforced output limits and the accepted accounting convention. Unknown usage is
not zero. A provider exceeding its promised bound is an invariant breach: fail
closed for further admission of that tenant, persist uncertainty and investigate;
do not claim that a retrospective correction can undo an already exceeded cap.

## Approved architecture and current implementation boundary

task4/ now has its own pyproject, lock, environment, pure tests and README;
no imports from Task 1/2 and no changes to their dependency configurations.

| Module | Responsibility |
| --- | --- |
| settings.py | Validate external identity secret, fixed primary/backup configuration, DB path and finite deadlines; no secret defaults or import-time I/O |
| tenant.py | Resolve validated opaque API keys to stable tenant identifiers; no caller-controlled tenant override |
| models.py | Immutable request, reservation, attempt, usage, outcome and sanitized error types |
| accounting.py | Pure token-bound policy and exact sliding-window calculations with injected clocks |
| storage.py | Explicit schema initialization/versioning, transactional admission, phase transitions, settlement and bounded recovery |
| providers.py | Typed asynchronous provider interface and separate primary/backup adapters; tokenizer/HTTP mapping selected after provider clarification |
| service.py | One owner per request; orchestrate reservation, primary deadline, one fallback and final settlement |
| app.py | Candidate HTTP factory/lifespan, strict request validation and standardized public errors; no provider/accounting duplication |

T4-002 uses Python 3.12.16 with a standard-library-only runtime, setuptools 82.0.1
for builds, pytest 9.2.0/Ruff 0.17.3 for development and its own eight-package lock.
FastAPI/Uvicorn/HTTPX and sqlite3 operations remain later-checkpoint candidates;
no HTTP/provider dependency was installed.
No provider SDK or tokenizer is invented. HTTPX transports would disable retries
and redirects; endpoints/credentials are operator-configured, never supplied by
callers. Tenant API keys are never forwarded as model-provider credentials.

## SQLite schema and transactions

Proposed minimal tables (design only, no migration/source created):

- requests: composite primary key (tenant_id, request_id), admission_ms,
  reservation_deadline_ms, phase and updated_ms. request_id is an internal unique
  identifier; it does not promise client retry deduplication or response replay.
- attempts: composite primary key (tenant_id, request_id, ordinal), ordinal 1/2,
  bound_tokens, charged_tokens, state, usage_source, accounting_ms. Composite foreign
  key to requests prevents cross-tenant association. No prompt/completion/raw error.
- store_meta: singleton schema version, last-observed UTC timestamp and a verifier
  derived from the external identity secret (never the secret). On existing stores,
  missing/mismatched identity configuration fails startup; it cannot create a new
  tenant namespace silently. Initialize only on a genuinely new store; secret
  rotation requires an explicit migration, not an automatic quota reset.
  Integer/nonnegative/check constraints and
  finite validated inputs; application rejects bool/float/overflow token counts.

Indexes: tenant/time for settled usage; tenant/state for pending holds. SQL queries
always include tenant_id. Attempts are the sole quota source; requests do not add
a second copy of their totals. Settled and held states are mutually exclusive.

Within BEGIN IMMEDIATE: sample/check accounting clock, recover expired holds,
sum settled tokens in the window plus all outstanding bounds, test combined demand,
insert request/two held attempts and COMMIT. If demand exceeds remaining capacity,
return a local 429 with zero provider I/O. Rejections do not create usage charges.
Each dispatch-intent/phase change and settlement is another short transaction with
expected-state conditional updates; duplicate callbacks cannot settle/fallback twice.
Never hold a SQLite transaction during network I/O, cancellation cleanup or waits.

All processes use the same DB admission rule; Python locks are not the cross-process
correctness mechanism. One bounded DB worker per process owns its connection/thread,
with explicit transaction handling, rollback/error cleanup and bounded busy waits.
No unguarded connection sharing or synchronous DB blocking in the async event loop.
Cancellation while a DB operation runs requires discovering its actual outcome;
coroutine cancellation alone does not imply a rollback.

Available runtime probe (E019): Python 3.12.16, SQLite 3.53.1, threadsafety=3.
T4-002 isolated runtime metadata (E020) also reports SQLite 3.53.1; no DB opened.
It exceeds SQLite's documented WAL-reset fix version 3.51.3. Therefore PROPOSE WAL
with synchronous=FULL/foreign_keys enabled, bounded busy timeout and verified PRAGMA
results on local storage. This was metadata inspection only: no DB opened, WAL
enabled or concurrency verified. Re-probe in the eventual isolated Task 4 runtime
and verify the configured filesystem is local; do not assume the workspace's S:
drive is suitable. Fail startup on incompatible runtime/storage/configuration.

SQLite serializes writers even with WAL; WAL is not multi-host/network-filesystem
coordination. FULL is a durability/performance tradeoff, not a guarantee against
faulty storage. No new database service, Redis, queue broker or distributed lock.
Sources: [transactions](https://www.sqlite.org/lang_transaction.html),
[WAL and runtime fix](https://www.sqlite.org/wal.html),
[synchronization](https://www.sqlite.org/pragma.html#pragma_synchronous).

## Primary/backup state machine

VALIDATED -> RESERVED -> PRIMARY_RUNNING -> either FINAL or BACKUP_READY ->
BACKUP_RUNNING -> FINAL. Terminal uncertainty/recovery uses ABANDONED; no replay.

| Event | Required/proposed transition | Outbound attempts |
| --- | --- | --- |
| Local quota exceeds capacity | Return local 429; never enter RESERVED | 0 |
| Primary succeeds before deadline | Settle primary, release unsent backup hold; FINAL | Primary 1, backup 0 |
| Primary returns 429 | Close primary exchange; durable BACKUP_READY; automatic backup from reserved capacity | Primary 1, backup 1 |
| Primary reaches 3,000 ms deadline | Cancel/await/close owned primary exchange; durable BACKUP_READY; automatic backup | Primary 1, backup 1 |
| Response/deadline race | Single expected-state transition chooses one outcome; no second fallback | At most 1 of each |
| Other primary failure | Sanitized terminal failure under A10 | Primary 1, backup 0 |
| Backup succeeds | Settle known usage plus conservative unknown primary charge; FINAL | At most 1 of each |
| Backup 429/timeout/failure | Standardized sanitized failure; no retry/third model | At most 1 of each |
| Client disconnect/cancel | Cancel/await owned work; account known/uncertain usage; do not start new fallback | No new attempt |
| DB failure before dispatch intent commits | Fail closed; no corresponding provider send | 0 additional |

No Retry-After sleep/threshold comparison, primary retry, parallel task hedging or
provider-SDK hidden retry. Secondary starts only after the owned primary task is
terminal and its local transport resources are closed; cleanup failure stops new
dispatch rather than launching an orphaned concurrent task. A finite overall
reservation deadline also gates dispatch, preventing stale workers using freed
capacity. Cleanup/DB failure or client cancellation can prevent dispatch; this is
fail-closed failure handling, not an alternative quota/fallback path.

Cancelling an HTTP exchange cannot prove a remote provider stopped execution or
billing. The no-duplicate guarantee is one deliberate local call per model, no
overlapping owned calls/retries. Remote execution after timeout remains uncertain,
covered by the primary reservation. Exactly-once remote execution would require
provider guarantees absent from the brief; it is not claimed.

## Proportional crash recovery and time

Persist reservations and dispatch intent before I/O. Normal completion atomically
replaces holds with known charges or conservative bounds and releases only provably
unused capacity. Return success only after accounting commits; failed settlement
keeps durable reservations rather than opening quota invisibly.

Outstanding holds survive restart and remain counted, including older-than-window
holds; starting a new process never clears them. Each request has a bounded overall
reservation deadline established at admission. Once that deadline passes, the next
transaction may atomically mark it ABANDONED and convert remaining holds to full
bound charges anchored at the reservation deadline (deliberately conservative).
Those charges then age out after 60 seconds. Finalized charges need no replay.
Never reclaim a still-valid reservation just because another process starts;
expected-state guards prevent stale completions overwriting recovered state.

This lazy recovery needs no provider queries, background reconciliation service,
distributed leases or client-response cache. It may overcharge after a crash or
unknown failure; exact billing recovery is not promised. Request deadlines and this
conservative timestamp shift are engineering policies finalized in P4; actual
recovery execution and numeric overall deadlines remain deferred.

UTC integer milliseconds persist window positions; monotonic time measures the
3,000 ms deadline. Reject accounting-clock regression against the stored watermark;
trusted host time/no unexplained large forward jumps is an explicit operational
assumption. No persisted process-monotonic timestamp. Prune only expired terminal
entries; retention must not delete active holds or reset another tenant's budget.

## Standardized sanitized failures (proposed HTTP contract)

One local envelope: error {code, message, request_id}, with stable public codes and
messages and an opaque internal request correlation ID. Exact field names/path and
success schema remain T4-A9 decisions. No raw exceptions, provider payloads/URLs,
tenant keys, identity secret, credentials or SQL paths in responses/logs.

| Condition | Proposed HTTP / public code |
| --- | --- |
| Local quota exhausted | 429 / tenant_quota_exceeded; never fallback |
| Primary provider 429 | Internal routing event, not local quota exhaustion |
| Backup provider 429 | 429 / provider_rate_limited; no retry/fallback loop |
| Backup timeout | 504 / model_timeout |
| Other provider/protocol failure | 502 / model_unavailable |
| Database/config/runtime unavailable | 503 / service_unavailable |
| Invalid request / missing-invalid tenant credential | 400 / invalid_request; 401 / invalid_credentials respectively |

Retry-After is optional pending API approval. Never copy an untrusted provider
header or promise an exact retry time while reservations have unknown outcomes.

## Full Task 4 acceptance test matrix

T4-002 verifies the pure arithmetic parts of Q1/Q2/Q3/Q9 only (E020), including
tenant-ID separation, not key authentication/restart identity resolution. Remaining
SQLite, concurrency, provider/fallback, HTTP/recovery cases are NOT EXECUTED.

| IDs / requirement | Acceptance evidence planned |
| --- | --- |
| T4-Q1 / R1,R2 | Exact integer token validation, 49,999/50,000/50,001 totals, combined primary/backup demand and no admitted overage |
| T4-Q2 / R1,R2 | 59,999/60,000/60,001 ms expiry, weighted expirations, no fixed-minute boundary burst; held versus settled sums never double-count |
| T4-Q3 / R2,R4 | Independent keys isolated; same key stable after restart; missing/changed identity secret fails rather than silently resetting quota |
| T4-Q4 / R3,R4 | Barrier-synchronized threads/processes sharing on-disk SQLite contend for final tokens; durable admissions never exceed capacity; busy deadline fails closed |
| T4-Q5 / R3 | Close/reopen, two live processes, crash after admission/dispatch/before settlement; other process startup does not clear active holds; bounded lazy recovery |
| T4-Q6 / R5 | Primary 429 causes exactly one backup; local 429 causes zero primary/backup calls; no Retry-After dependency |
| T4-Q7 / R6 | Injected monotonic clock/events at 2,999/3,000/3,001 ms, complete-exchange deadline and response race; primary cleanup precedes single backup |
| T4-Q8 / R4-R6 | Concurrent tenants/requests, cancellation, repeated callbacks, failed state commit; no cross-tenant response or double dispatch/settlement |
| T4-Q9 / R1-R6 | Both attempts charged, primary-success backup refund, unknown timeout/429 usage never zeroed, bound violation fails closed; no third attempt |
| T4-Q10 / R7 | Exact public errors, provider 429 distinct from local 429, timeouts/storage failures, output/log secret canaries absent |
| T4-Q11 / R3,R4 | Isolated runtime version/PRAGMAs verified; local temporary file DB; rollback/write failure/clock regression/restart/cleanup |
| T4-Q12 / all | Later real-loopback provider/proxy processes, startup/shutdown, request journals/timeout handling; full suite/Ruff/traceability and independent final audit |

Use injected clocks and explicit barriers/events, not sleep-duration assertions.
Provider interfaces/HTTP mock transports precede real sockets. No real credentials
or external LLM calls are required unless the assessment later explicitly asks.

## Milestones and review gate

T4-001: independently APPROVED WITH CONDITIONS; P1-P4 finalized, DONE.
T4-002: isolated project/typed records/pure tests implemented and independently
ACCEPTED; actual local results E020, reported independent acceptance E021.
T4-003: SQLite transactional admission/persistence/concurrency/recovery independently
ACCEPTED in supported Windows/SQLite scope; E022 native results/E023 qualified review.
T4-004: provider adapters and 3,000 ms/429 fallback state machine.
T4-005: HTTP/real-wire integration and fault/tenant-isolation verification.
T4-006: complete regression, traceability/security/reproducibility audit and acceptance.
Later milestones are proposed only and stop for independent review individually.

Before future provider/HTTP checkpoints: supply provider/model/tokenizer/output-cap
details, backup/overall deadlines, tenant credential transport/provisioning/rotation
and exact HTTP schemas. These do not block pure arithmetic with trusted synthetic
bound records; no such records are claimed to verify real model behavior.
T4-003 acceptance and one milestone commit are recorded below. T4-004, push and
provider/HTTP execution are not authorized by the current checkpoint.

## T4-003 SQLite storage contract (2026-11-04)

User authorizes storage.py, durable atomic admission/settlement/recovery and actual
SQLite/process verification against accepted 3d8d3e5/169 tests. Preserve all accepted
models/calculations/tests/configuration/dependencies/locks and Tasks 1/2. No provider
calls, primary timeout/fallback execution, HTTP, final fault audit, Task 3/T4-004,
commit or push. Earlier no-storage scope statements are historical.

### Storage API and schema

SQLiteStore(StorageSettings(absolute_path, external_identity_secret,
busy_timeout_ms=1000), clock=injected_UTC_clock) initializes an empty, unowned on-disk
store or verifies existing metadata. Current implementation validates Windows fixed
local volumes with Win32 GetVolumePathNameW/GetDriveTypeW; other platforms/network
volumes fail closed. Actual runtime is SQLite 3.53.1, with minimum 3.51.3 enforced
before connecting/enabling WAL. Parent directory must exist and remain trusted.
The implementation does not claim physically verified storage hardware or hostile
filesystem/symlink-race protection. Runtime/storage assumptions must hold thereafter.

Three STRICT tables: store_meta (version, identity verifier, DB-wide last UTC sample,
50,000/60,000 constants); requests (tenant HMAC, internal UUID, admission/deadline,
phase, durable bound-breach block); attempts (composite tenant/UUID/ordinal key,
positive bound, state, charge/source/timestamp). Composite FK/unique/check constraints
enforce tenant association and valid held versus finalized representations, including
explicit NOT NULL terminal checks. Tenant/state/time, deadline and block indexes.
Only integers, controlled states, HMAC-derived identifiers/verifier and internal UUIDs
are persisted: no plaintext API keys, model/provider credentials, prompts/completions
or raw exception text. Model aliases/counter strings are not persisted either.

Identity secret is mandatory external bytes (32-1024 bytes; operator supplies strong
random material). API keys are opaque nonempty bytes, HMACed transiently with a
separate domain label; same key/secret remains stable across restarts. No key
authentication/provisioning/rotation or default secret is added. Incorrect verifier,
schema/application version or policy metadata fails safely, including rechecks on
each operation. Never silently initialize a nonempty unrelated DB or reset metadata.

- admit(key, UUID, plan, reservation_ms=positive_finite_integer): BEGIN IMMEDIATE;
  verify identity/policy, sample UTC clock once AFTER writer acquisition, check/update
  watermark, lazily recover this tenant's due holds, read its usage, call accepted
  assess_admission and insert BOTH reservations iff allowed; explicit SQL COMMIT
  precedes a returned result. Valid quota denial commits clock/recovery but no request.
  Duplicate admitted UUIDs fail, including finalized historical UUIDs; distinct
  tenant keys may use the same UUID. No successful idempotent replay of admission.
- start_attempt(key, UUID, ordinal): persist one dispatch intent, not a provider
  call/routing decision. Primary needs both reservations intact; backup needs primary
  settled and its own reservation intact. Repeated starts/conflicting transitions
  fail. Future routing MUST also confirm owned task termination/cleanup and deadline
  immediately before actual send; DB state cannot prove remote cancellation.
- settle(..., actual_tokens=int|None): started only; known value up to bound replaces
  hold at original admission time; None conservatively charges the bound. Identical
  repeat no-op; different value/source or invalid/stale state rejected. Over-bound
  measurement durably blocks future tenant admissions and retains the unresolved
  bound, then reports BOUND_EXCEEDED; no automatic unblock/admin endpoint is added.
- release_unused(...): only never-started capacity, finalized as zero/unused at
  original admission time; identical repeat no-op. A started/unknown attempt cannot
  be released. This is not a provider cancellation mechanism.
- usage(key), request(key, UUID), recover(key): short writer transactions to enforce
  the persisted clock and lazy recovery, returning immutable snapshots or recovered
  request count. Unresolved bounds survive window expiration and restart. At/after
  explicit admission+reservation_ms deadline, remaining holds convert exactly once
  to full deadline-anchored charges and request becomes abandoned. Known prior
  charges retain their original timestamp; old workers cannot overwrite recovered
  rows. Deadline charges leave the window exactly 60s later. No provider replay.

No overall duration default is invented: the trusted future service must supply
reservation_ms and coordinate it with primary/backup/cleanup budgets. It must not
dispatch using expired/abandoned intent. Delayed recovery may find the deadline
charge already aged out, but full historical charge/abandoned state remains stored;
this is the accepted finite-deadline accounting policy, not proof of remote billing.

### Transaction, error and deployment boundaries

Each synchronous operation owns/closes a connection in its calling thread; future
async owners must offload the WHOLE operation, optionally through their DB worker,
and drain in-flight operations before close. No shared connection/asyncio-lock
correctness shortcut; SQLite serializes writers across threads/processes. No network
or provider work occurs inside a transaction. No permanent worker/thread pool was
added in this storage-only checkpoint.

Explicit Python 3.12 autocommit=True plus SQL BEGIN IMMEDIATE/COMMIT/ROLLBACK avoids
implicit transaction ambiguity. Initial schema/identity transaction uses EXTRA,
then enables/verifies WAL/FULL; operational connections recheck WAL/FULL/foreign_keys.
busy_timeout is explicit, integer 1-10,000 ms (default 1,000); no whole-operation
automatic retry. An existing store opens mode=rw, never silently recreating a missing
file. Initial empty-store creation is trusted operator bootstrap, not backup recovery.
Concurrent first initialization can report controlled BUSY; initialize before workers.

SQLite errors map to generic StorageError with internal failure kind, no paths/keys/
SQL diagnostics in its public string. Failed transactions roll back all tentative
rows/watermark/recovery; a failed transition may leave holds for a later successful
recovery transaction. Bound-breach blocking is the deliberate committed-error case.
An ambiguous COMMIT failure returns failure, never success; do not automatically
replay it. Filesystem/OS failures after a successful FULL commit and faulty hardware
are not exhaustively audited. No rows are pruned automatically: retaining duplicate-ID
history can grow the DB; later retention needs a reviewed policy.

No real model bound provenance, public HTTP sanitization, provider fallback/timeout,
Linux/macOS storage detector, distributed execution or final fault audit is verified.
Pure entry records/policies remain unchanged; storage is their transactional owner.
Actual commands/results, concurrency receipts and process cleanup: E022/ADR-018.

## T4-002 independent acceptance and foundation commit (2026-11-04)

The user reports independent engineering APPROVAL, 169 existing tests/12,000
randomized differential checks/six targeted invariants passed and no blocking
finding. Ruff remains supported by E020's actual pinned-environment checks.
One descriptive T4-001/T4-002 project/requirements/governance commit is authorized,
superseding historical no-commit gates for this checkpoint only. Preserve accounting
logic/tests/configuration/lock and Tasks 1/2. No new local tests/installations,
SQLite/provider/HTTP/recovery implementation, T4-003, Task 3 or push. Whole Task 4
is not complete; accepted pure arithmetic is not transactional admission.

## T4-003 independent acceptance and commit authorization (2026-11-04)

User APPROVES the storage implementation within documented Windows fixed-local-
drive/supported SQLite scope. Reported independent evidence: isolated Linux review
copy with test-only compatibility shim bypassing unsupported platform/SQLite gates;
all 221 tests and 15 normal child exits/zero forced cleanup, plus ten-thread
admission, tenant isolation and exact deadline-recovery scenarios passed; no source
defect identified. Review commands/runtime details were not supplied. This does
not establish native Linux support or native Windows gate correctness: E022's
native Windows/SQLite 3.53.1 run remains authoritative. No shim/gate change is shipped.

T4-003 DONE/ACCEPTED; whole TASK-4 IN_PROGRESS. One descriptive commit of approved
SQLite source/tests/support/requirements/governance is authorized, superseding only
this checkpoint's earlier no-commit gate. Preserve accounting/storage/tests/pins
and Tasks 1/2. No local test/Ruff rerun, new features, T4-004, Task 3 or push.

## T4-004 injectable orchestration contract (2026-11-04)

Independently ACCEPTED, confirmed by user 2026-11-04; E024/E025. No design change.
Original R1-R7 remain the assessment requirements. The following interface and
routing choices operationalize accepted P1-P4; they do not invent vendor contracts.

### Adapter and configuration trust boundary

- providers.Provider.prepare(text) is trusted, pure, resource-free model-specific
  counting/cap preparation, offloaded from the event loop. It returns a one-shot
  PreparedAttempt with immutable ModelTokenBounds and execute()/aclose(). Bounds
  must match the provider's configured model_id and counter_id. Both providers
  must prepare successfully before admission. No caller estimate or verified flag.
- The prepared handle MUST enforce its output cap and cover all billable token
  categories, use the prepared input exactly, and disable retries/hedging/redirects.
  The service cannot certify a tokenizer/provider by inspecting its metadata. No
  actual model, tokenizer, endpoint or provider credentials are selected. Synthetic
  fake counters/caps verify orchestration, not real LLM enforcement. An unverified
  real adapter must raise BoundsUnavailable before admission or execution.
- ProviderResult has a controlled status (success, rate_limited, timeout or
  transport_failure), optional reliable TokenUsage(input_tokens, output_tokens)
  and success-only text. Unknown usage is None, never implicit zero. Raw provider
  exceptions are sanitized, not exposed/logged. Tenant keys are never passed to
  providers; credentials belong to a future externally configured adapter.
- LLMService(store, primary, backup, RoutingPolicy(backup_timeout_ms,
  reservation_ms), clock=...) exposes async generate(validated_key_bytes, text,
  request_id=optional_internal_UUID). Key shape/length is checked; provisioning,
  authentication and HTTP credential transport remain T4-005 contract decisions.
  No caller-controlled tenant override or external response replay is provided.
- Backup and overall budgets are REQUIRED positive signed-64-bit integer
  configuration, with no invented defaults. reservation_ms must EXCEED
  3000 + 500 + backup_timeout_ms + 500; the operator supplies DB/scheduling margin.
  Test-only examples use 2000/10000 ms, not a newly approved deployment policy.

### Dispatch, deadlines and fallback

1. Offload whole synchronous store operations through a bounded lane. SQLite
   BEGIN IMMEDIATE remains the cross-thread/process quota authority. Commit the
   combined primary+backup admission before any send. Quota denial returns
   tenant_quota_exceeded, with zero provider executions and no fallback.
2. Commit start_attempt before the corresponding execute. Duplicate UUID/attempt
   state fails closed, with no replay. Before intent, after DB completion and at
   the owned execution task's entry, check cancellation/quarantine/time budget.
   A monotonic reservation deadline sampled BEFORE admission is conservative for
   elapsed time; storage separately checks persisted UTC/deadline/recovery state.
   Trusted UTC/no large unexplained clock jumps remains an operational assumption.
3. Primary gets one monotonic 3000 ms complete-exchange budget. Task scheduling
   after dispatch intent is included conservatively. A response observed at 2999
   ms may succeed; at/after 3000 it loses the content race. Late reliable usage
   can still settle the primary; late success content cannot suppress fallback.
4. Primary HTTP 429 or expiry of that owned primary deadline authorizes exactly
   one backup, AFTER confirmed primary termination and local resource close.
   Adapter-reported/raised early timeouts do not establish the required 3000 ms
   deadline: returned TIMEOUT is a sanitized terminal model_timeout; raised
   exceptions are terminal model_unavailable. Neither triggers early fallback.
5. After completion/timeout/cancellation, one shared 500 ms grace covers task
   cancellation/termination AND aclose. For timeout its ceiling is the ORIGINAL
   attempt deadline+500, even if observation is delayed. At the grace boundary,
   unconfirmed cleanup fails closed. No fresh allowance per cleanup step.
6. On unconfirmed/failed cleanup return service_unavailable, retain ALL unresolved
   holds for accepted deadline recovery, launch no backup, and quarantine further
   dispatch on that service instance. Strong task references retain eventual local
   cleanup; no retry task is started. asyncio cannot forcibly kill arbitrary
   cancellation-resistant or event-loop-blocking adapters. Adapters must be async
   cooperative; remote execution/billing after local cancellation remains uncertain.
7. Backup has the explicit configured finite deadline, equivalent cleanup rules,
   and no fallback/retry. Other primary failures have no fallback. No provider I/O
   runs inside a DB transaction. used_backup reflects actual local backup execute
   invocation, not merely durable intent.

### Settlement, cancellation and lifecycle

Reliable in-bound usage replaces its hold once at admission time; unknown usage
charges the whole bound. A success can have unknown billing and is conservatively
charged. Only never-sent backup capacity is released after confirmed primary
cleanup. If intent committed but the owner proves execute was never invoked,
known zero can settle that started intent; this is not a guessed rollback/refund.
Total usage above the reserved bound invokes accepted storage's durable tenant
block and keeps unresolved holds. A category/output-cap breach within total bound
charges the full bound, quarantines this service and fails; it does not falsely
claim that the storage total-bound block fired. Real-adapter correctness remains
a prerequisite for a hard real-provider token bound.

A cancelled caller sets an event and receives CancelledError. Its shielded owned
workflow remains referenced: in-flight offloaded DB work finishes and its actual
outcome is discovered. No cancellation implies rollback. After a successful
cancelled admission, provably unsent holds are finalized; after actual dispatch,
terminate/close and settle reliable or unknown usage; never launch new fallback
once cancellation is observed. Ambiguous/failed DB operations are not retried,
replayed or refunded; durable holds remain for P4 recovery. Provider close must
confirm cleanup before settlement or fallback. Late completions do not overwrite
recovered rows; storage expected-state/deadline guards remain unchanged.

Owner must stop submissions and await service.aclose()/drain BEFORE closing store
or event loop. aclose drains request owners/DB completion and bounds its wait for
quarantined cleanup; False explicitly means cleanup remains unconfirmed or failed.
This is not a thread-kill, a DB I/O cancellation deadline or a guarantee of graceful
shutdown for a permanently broken adapter/filesystem. Pending cleanup handles must
not be silently discarded. No provider replay or new recovery infrastructure.

Structured outcomes contain internal UUID, controlled code/message, success-only
text and used_backup. Codes: invalid_request, invalid_credentials,
tenant_quota_exceeded, provider_rate_limited, model_timeout, model_unavailable,
service_unavailable. They contain no raw diagnostics/keys/SQL paths/provider URLs.
No HTTP status/schema is newly implemented: T4-005 will map this existing contract.

### Local verification and independent acceptance

E024: native Python 3.12.16/SQLite 3.53.1, 324 passes (221 accepted + 103 new),
zero failures/skips/warnings/xfails, Ruff lint/format pass (15 files). Controlled
clock tests include 2999/3000/3001, 499/500/501 cleanup, split termination/close
budget and late observation, unknown/late usage, actual SQLite commits and
multiple independent service owners, tenant isolation, duplicate IDs, cancellation
at offloaded DB boundaries, storage failures and deadline recovery. All 15 existing
storage-process children exit normally, zero forced/live children. No external
LLM/network calls, real tokenizer certification, HTTP, final fault audit or
cross-platform storage support. Tasks 1/2 and accepted Task 4 files/pins unchanged.
Independent acceptance is recorded below; one approved milestone commit only.
Do not begin T4-005 or push.

### T4-004 independent acceptance and commit authorization

On 2026-11-04 (America/Los_Angeles), user APPROVES T4-004 with no blocking
production defect. Reported independent evidence: 324 tests passed in an isolated
Linux review copy using review-only platform/SQLite compatibility changes;
additional output-category cap and total reservation-bound adversarial checks
passed; a real monotonic-clock test observed successful fallback after approximately
3.020 seconds with exactly one backup execution and conservative usage accounting.
Commands/runtime details beyond the supplied report were not provided. E024 native
Windows/Python 3.12.16/SQLite 3.53.1 evidence remains authoritative. The review
changes are not shipped and do not establish native Linux/storage-gate support,
a real model/tokenizer guarantee or a response-time SLA. No new local runs.

T4-004 DONE/ACCEPTED; TASK-4 remains IN_PROGRESS. Latest authorization permits
one descriptive approved-source/tests/support/README/requirements/governance commit
only, superseding historical no-commit gates for this checkpoint. Preserve approved
provider/service/accounting/storage/tests/config/locks and Tasks 1/2. No test rerun
absent unexpected implementation changes, no T4-005, new vendor/HTTP work or push.

## T4-005 authenticated HTTP checkpoint (2026-11-04)

Source: latest user attachment, "Authenticated HTTP Integration and Real HTTP Wire
Verification". Independently ACCEPTED, user confirmation 2026-11-04 (E027).
These checkpoint requirements supplement R1-R7; the specific route/schema/auth choices below are
engineering policies where the original assessment brief was silent.

| ID | Mandatory checkpoint criterion |
| --- | --- |
| T4-H1 | FastAPI factory/lifespan around accepted modules; bounded strict HTTP input and no blocking SQLite in event loop |
| T4-H2 | External tenant-key authentication; reject missing/malformed/duplicate/unknown/unauthorized keys; stable approved identity; no client tenant authority |
| T4-H3 | Trusted model-specific bounds/enforced caps only; no caller estimates, invented production tokenizer or unspecified vendor support |
| T4-H4 | Local 429 zero calls; primary success/429/3000 ms timeout/500 ms cleanup and backup failures preserve accepted routing/accounting |
| T4-H5 | Quota boundaries, isolation/persistence, concurrent atomic admission and conservative client cancellation |
| T4-H6 | Standardized controlled responses/logs without raw keys, secrets, request prompts or exception diagnostics |
| T4-H7 | Independent loopback processes, dynamic ports, real client/framing, journaled actual calls/durable state and bounded reliable cleanup |
| T4-H8 | Full supported native Task 4 suite/Ruff, actual evidence/governance; preserve Tasks 1/2/accepted components; stop for review, no T4-006/commit/push |

### HTTP and authentication contract (implementation choices)

- POST /generate only; no redirect, docs/redoc/OpenAPI, streaming or public status/
  journal/control endpoint. Other methods 405 (Allow: POST), unknown paths 404.
  The wire fixture's upstream control/readiness endpoints are TEST ONLY.
- Authenticate one Authorization: Bearer <key> header before body reading/JSON/
  bounds/admission. Scheme case-insensitive, token exact/case-sensitive ASCII RFC
  Bearer characters, 32-256 bytes total. Missing/malformed/duplicate/unknown or
  removed/not-allowlisted keys all return identical 401 + Bearer realm="task4".
  No default credentials, JWT/OAuth, roles, query/cookie authentication or key CRUD.
- External TASK4_TENANT_KEYS_JSON is an immutable allowlist (1-1024 distinct keys).
  Retain SHA256 digests for authentication, visit all with constant-time digest
  comparisons. Hand accepted bytes transiently to existing SQLiteStore for HMAC
  identity under unchanged external identity secret/domain. Header/body tenant
  overrides never become authority; extra JSON fields are rejected. Keys must be
  generated strongly/provisioned by operator; syntax cannot prove entropy. Removing
  a key revokes HTTP access without deleting stored usage. Rotation/migration is
  not implemented and must not silently reset accounting identity.
- Body must be application/json, optionally charset=utf-8 (case-insensitive), with
  no Content-Encoding (including identity). Reject unsupported media/encoding 415.
  Validate visible duplicate/ambiguous length/transfer headers; HTTP/1.1 chunked
  is supported. Count actual bytes while streaming, not only Content-Length.
  Default max 65536 (configurable 1-1048576), total body-read timeout 5000 ms
  (configurable 1-60000): too large 413, read deadline 408. Length mismatch 400.
- Strict UTF-8 JSON object with ONLY prompt: nonempty string, <=16000 characters,
  valid Unicode (no unpaired surrogates). Reject duplicate JSON keys at every
  object level, nonfinite constants, malformed JSON, arrays/scalars, wrong types,
  unknown keys (including tenant IDs/token estimates/model overrides) with 400.
  Validation details/input are never reflected or logged.
- Server generates UUID correlation ID, never trusts client-supplied IDs. Success
  200: {request_id, result:{text, used_backup}}. Error:
  {error:{code,message,request_id}} with fixed public message. All application
  responses include X-Request-ID, Cache-Control:no-store, X-Content-Type-Options:
  nosniff and JSON media type. No inbound header/cookie/role forwarding.
- Local quota: 429/tenant_quota_exceeded, zero provider calls/reservations. Primary
  provider 429 is INTERNAL routing, normally successful backup -> 200; terminal
  backup 429 -> 429/provider_rate_limited (distinct from tenant quota). Typed model
  failure -> 502/model_unavailable; timeout -> 504/model_timeout; unreliable bounds,
  storage failure/quarantine/unavailable -> 503/service_unavailable. Invalid request
  400/invalid_request; invalid credentials 401/invalid_credentials. Entity failures
  use request_too_large/unsupported_media_type/unsupported_content_encoding/
  request_timeout with the statuses above. Disconnect is diagnostic 499 if a
  response is still deliverable; a closed socket normally receives nothing.
- Malformed transport framing rejected by Uvicorn/h11 BEFORE ASGI may receive a
  server-generated HTTP 400 rather than the application JSON envelope. Server
  normalization can erase redundant identical header syntax; the boundary checks
  what ASGI actually exposes. Do not claim byte-level HTTP parsing ownership or
  unrestricted reverse-proxy/HTTP2 deployment compatibility.

### Trusted resources and failure/cancellation ownership

HTTPSettings/load_settings require absolute TASK4_DATABASE_PATH, external
TASK4_IDENTITY_SECRET_HEX, TASK4_TENANT_KEYS_JSON, TASK4_BACKUP_TIMEOUT_MS and
TASK4_RESERVATION_MS. Optional TASK4_MAX_BODY_BYTES/TASK4_BODY_TIMEOUT_MS configure
HTTP budgets. No secret/backup/overall defaults. Existing RoutingPolicy validates
combined budgets; test values are not deployment requirements. Storage runtime/
filesystem/identity checks are unchanged. Read configuration at startup, no import-
time DB/network I/O. Invalid configuration fails startup with generic diagnostics.

Trusted Python deployment code injects provider_resources(), an async context
manager yielding primary/backup adapters, into create_app. The default factory
uses bounds-unavailable adapters: requests authenticate/validate then fail 503
BEFORE reservation/dispatch, not a fictional vendor/tokenizer. Actual adapters
must establish reliable model-specific counters/caps under accepted Protocols.
Clients cannot choose providers, URLs, bounds or caps. Success contains only the
trusted adapter completion and controlled metadata; no raw prompt/debug echo.
A real completion's semantic privacy/redaction is not certified by synthetic tests.

Initialize SQLiteStore off-loop during lifespan; accepted LLMService offloads all
subsequent DB operations. No HTTP code duplicates admission/settlement/recovery.
Providers are owned by lifespan, closed AFTER service work drains; close store last
(flag only, all DB work already drained). Startup cancellation discovers the actual
initialization worker outcome before close. Shutdown owns a shielded cleanup task;
caller cancellation cannot discard DB/provider cleanup. Failed/unconfirmed attempt
cleanup retains resources and raises a generic unclean-shutdown signal rather than
closing a pool under a live owned attempt. Blocking OS I/O or a permanently broken
trusted resource context cannot be forcibly killed by asyncio; supervisor/operational
recovery remains necessary. No new replay or distributed recovery system.

Read request body with one consumer, then watch ASGI disconnect alongside the public
service call. On disconnect/cancellation, cancel that public coroutine so accepted
service signals its retained workflow; never assume cancelled DB work rolled back.
No new fallback after observed cancellation. Known/unknown usage, admission-time
settlement, deadline-anchored recovery and reserved primary+backup policy are exactly
those already accepted. No accepted production correction was needed.

### Wire evidence, supported scope and operational limits

E026 records actual native Windows/Python 3.12.16/SQLite 3.53.1 executions. New ASGI
and wire tests supplement the unchanged 324 tests. Wire harness starts independent
Uvicorn proxy and deterministic synthetic HTTP upstream processes, both 127.0.0.1,
OS-bound port 0 with reported ports, HTTP readiness checks, bounded deadlines,
per-request journal counts and on-disk SQLite state. Fixed fixture counting/caps
are not a real tokenizer/provider guarantee. No external service contacts. Upstream
fixture has no tenant credentials in its environment or incoming headers. Explicit
release events coordinate concurrency/remote timeout work; cleanup reaps all children,
including expected invalid-startup failures, with receipts under ignored .cache.

No raw API keys/identity secrets/prompts/completions are persisted in usage/journals;
journals contain synthetic UUID/ordinal/state/header-presence only. Do not enable
access logs or forward untrusted proxy headers. HTTP over loopback is the verified
scope; non-loopback deployment needs TLS, trusted ingress/logging, key provisioning,
verified real-model adapters/caps, appropriate explicit execution budgets and reviewed
filesystem/clock operations. No load-saturation/slow-header/OS-crash final audit,
full streaming, public model integration, administrative unblock/rotation/retention
API or multi-host SQLite support. T4-005 is independently accepted as recorded
below; TASK-4 is not DONE. No T4-006 implementation or push.

### T4-005 independent acceptance and Git authorization

User APPROVES T4-005, 2026-11-04 (America/Los_Angeles), no blocking production
defect identified. All 427 cases passed independently across separate review runs;
29 real wire cases passed in split groups. Authentication/quota rejection/fallback/
concurrency/persistence/error sanitization reviewed. Linux verification required
review-only compatibility substitutions. One COMBINED Linux wire run stalled during
fixture teardown; do not describe it as a completed all-at-once pass. Native E026
Windows/Python 3.12.16/SQLite 3.53.1 full-suite result remains authoritative.
Reported review commands/versions and child cleanup counts were not supplied;
no new local execution or native Linux support is claimed. No substitutions ship.

T4-005 DONE/ACCEPTED, TASK-4 IN_PROGRESS. Latest user authorization supersedes only
this checkpoint's historical no-commit gate: one descriptive approved source/tests/
support/config/lock/README/governance commit, preserving implementation unchanged.
Exclude envs/DB/WAL/caches/credentials/archives, inspect exact staged content and
whitespace, verify resulting commit/clean status/branch counts and stop. No reruns
absent unexpected implementation changes, T4-006, Task 3 or push. E027 records
review provenance and Git inspection; accepted engineering choices are unchanged.
