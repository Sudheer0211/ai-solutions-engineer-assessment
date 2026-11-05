# TASK-4 / T4-006 final assessment audit

Date: 2026-11-04 (America/Los_Angeles). Baseline: `6eaccaf`.
Final verdict: **APPROVED / assessment-ready within the documented assessment
contract, supported Windows/SQLite environment and trusted-adapter policies**.
Independent ChatGPT engineering acceptance confirmed by user on 2026-11-05
(America/Los_Angeles). **T4-006 and TASK-4 are DONE.** All seven traceability rows
were reviewed against previously submitted source/test evidence; all named test
references verified, E028/documentation/limitations/submission findings consistent.
E029 records reported acceptance and the authorized final documentation-only Git
checkpoint, not new test executions. No production/test/config/dependency/lockfile
changes; one final documentation commit authorized, no push.
Actual commands, versions, unsuccessful setup attempt and results: **E028** in
[TEST_EVIDENCE.md](TEST_EVIDENCE.md). Audit scope decision: ADR-021.

## Requirement provenance and interpretation

The available original pasted attachment concerns Task 1, not a separate Task 4
vendor brief. The user's recovered original requirements and clarifications are
preserved as **T4-R1 through T4-R7** in
[TASK4_REQUIREMENTS.md](TASK4_REQUIREMENTS.md). Those seven requirements are the
assessment source of truth. P1-P4 are independently approved engineering policies;
A1-A10 and H1-H8 record choices and adapter/deployment dependencies, not additional
verbatim assessment requirements. No unstated vendor API/tokenizer is inferred.

PASS below means verified against that contract and its approved accounting/trust
boundary. It does not certify real-provider integration or a production deployment.
All test paths in the matrix are relative to `task4/tests/`; all were executed in
the fresh 427-case suite, not merely inspected. The suite reports zero skips/xfails.

## Requirements traceability matrix

| ID / explicit assessment requirement | Implementing modules/functions | Automated tests (file::function) | Fresh evidence | Status |
| --- | --- | --- | --- | --- |
| T4-R1: Token-aware sliding-window limiter | `models.ModelTokenBounds`, `ReservationPlan`; `accounting.calculate_usage`, `assess_admission`; `SQLiteStore._entries` | `test_accounting.py::test_weighted_sliding_expiration_keeps_old_holds`, `test_exact_lower_boundary_excluded_upper_boundary_included`, `test_minute_boundary_does_not_reset_usage`; `test_models.py::test_zero_or_overflowing_bounds_cannot_authorize_work` | E028: full 427 pass; exact interval and integer/trusted-bound checks | PASS, under P1/P2 |
| T4-R2: Maximum 50,000 tokens/minute per tenant API key | `accounting.assess_admission`; `SQLiteStore.admit`, `_tenant`; `TenantCredentials.authenticate`; `LLMService.generate` | `test_accounting.py::test_combined_reservation_obeys_exact_49999_50000_50001_boundary`; `test_storage.py::test_atomic_49999_50000_50001_boundary`; `test_http.py::test_combined_admission_boundaries_and_quota_rejection`; `test_http_wire.py::test_wire_exact_quota_and_denial_never_dispatches` | E028: exactly 50,000 admitted; 50,001 rejected; wire overquota mode has zero provider calls/reservations | PASS, admission-time convention |
| T4-R3: Persistent on-disk SQLite usage | `SQLiteStore._initialize`, `_transaction`, `admit`, `settle`, `_recover` | `test_storage.py::test_reopen_keeps_holds_identity_and_clock_and_never_clears_live_owners`; `test_storage_processes.py::test_committed_settlement_and_hold_survive_independent_process_restart`; `test_http_wire.py::test_wire_concurrent_tenants_atomic_quota_and_persistence_across_process_restart` | E028: native SQLite 3.53.1, WAL/FULL, reopen and independent process restart tests pass | PASS, Windows fixed local drive |
| T4-R4: Safe concurrent requests | `SQLiteStore._transaction` / `admit` (`BEGIN IMMEDIATE`); tenant-scoped constraints; `LLMService._offload` | `test_storage_processes.py::test_barrier_processes_compete_for_final_capacity`, `test_duplicate_request_race_has_one_durable_reservation`, `test_process_settlement_race_is_idempotent_or_rejects_conflict`; `test_service.py::test_concurrent_admission_shared_budget_and_tenant_isolation`; wire concurrent-tenants test above | E028: six competitors for last 2,000 tokens, one admission/five denials; 15 storage children exit 0; no shared Python-lock dependency | PASS, single supported local DB |
| T4-R5: Primary HTTP 429 automatically uses secondary | `providers.ProviderStatus.RATE_LIMITED`; `LLMService._run`, `_exchange`; durable `SQLiteStore.start_attempt` | `test_service.py::test_primary_429_exactly_one_backup_after_cleanup`, `test_local_quota_denial_zero_provider_calls`, `test_backup_failure_is_terminal_no_third_attempt`; `test_http_wire.py::test_wire_routing_and_conservative_accounting` | E028: wire 429 mode one primary/one backup, charge 25; local rejection journal has zero calls; clean-install routing repeats pass | PASS, after confirmed cleanup |
| T4-R6: Primary timeout after 3,000 ms automatically uses secondary | `RoutingPolicy`, `LoopClock`; `LLMService._wait`, `_exchange`, `_run` | `test_service.py::test_primary_monotonic_timeout_boundaries`, `test_cleanup_shared_grace_and_no_concurrent_backup`, `test_cancellation_and_close_share_one_grace_budget`, `test_late_timeout_observation_does_not_renew_cleanup_budget`; wire routing timeout case | E028: controlled 2,999/3,000/3,001 ms and 499/500/501 ms cases pass; real socket timeout mode one primary/one backup; unconfirmed cleanup prevents fallback | PASS, P3 safety exception applies |
| T4-R7: Standardized sanitized errors | `ServiceOutcome`; `StorageError`; `ConfigurationError`; `app._error`, `create_app` error/route handlers, `_body` | `test_service.py::test_primary_exceptions_do_not_trigger_fallback_or_leak`; `test_http.py::test_routing_status_accounting_and_no_prompt_or_secret_leak`, `test_database_failure_is_sanitized_and_unconfigured_provider_fails_closed`; `test_http_wire.py::test_wire_authentication_rejection_zero_calls_and_rows`, `test_wire_entity_rejection_zero_calls_and_rows`, `test_wire_database_unavailability_fails_safely` | E028: generic errors, no credentials/prompt/internal diagnostics; ASGI and real HTTP status/header assertions pass | PASS, app-visible HTTP requests |

## Fresh regression, lint and runtime evidence

All commands ran on native Windows, CPython **3.12.16**, MSC v.1944 AMD64.
SQLite runtime **3.53.1** in all three interpreters; only Task 4 uses it for storage.
Each project used its own existing environment. No Linux gate substitutions used.

| Project / cwd | Complete pytest | Fail / skip / warning / xfail | Ruff lint | Ruff format |
| --- | --- | --- | --- | --- |
| Task 1 / repository root | **149 passed in 36.06s**, exit 0 | 0 / 0 / 0 / 0 | PASS, exit 0 | PASS, 17 files, exit 0 |
| Task 2 / `task2/` | **452 passed in 13.26s**, exit 0 | 0 / 0 / 0 / 0 | PASS, exit 0 | PASS, 16 files, exit 0 |
| Task 4 / `task4/` | **427 passed in 40.44s**, exit 0 | 0 / 0 / 0 / 0 | PASS, exit 0 | PASS, 22 files, exit 0 |

Task 4 includes the unchanged accepted 324 accounting/storage/orchestration tests,
74 ASGI/config/lifecycle cases and 29 real wire cases. Full-suite receipts: 28 wire
children reaped (27 exit 0, one expected invalid-startup exit 3), 15 storage children
exit 0; **43 reaped, zero forced cleanup/live children**. Task 2 receipt: 12 reaped,
zero live/forced cleanup/reader threads; deliberate upstream termination and failed
startup cases yield nonzero child codes while their assertions pass.

Dependencies: Task 1 MCP 2.3.0/Pydantic 2.12.5/pytest-asyncio 1.4.1.post1;
Tasks 2/4 FastAPI 0.162.0, Starlette 1.10.0, Pydantic 2.14.2, HTTPX 0.28.1,
Uvicorn 0.54.0/asgi-lifespan 2.1.0. All use pytest 9.2.0/Ruff 0.17.3.
E028 records exact commands and full inspected package inventories.

Earlier independent Linux review used review-only compatibility substitutions.
T4-005's 427 cases passed across separate runs/29 wire cases in split groups;
one combined Linux wire run stalled during teardown. That is **not** a completed
combined pass or native Linux support. This audit's native full run completed.

## SQLite/accounting and recovery findings

- **Atomicity:** on-disk STRICT `store_meta`, `requests`, `attempts`; composite
  tenant/request/ordinal keys, FK/check constraints, tenant/state/time and deadline
  indexes. `BEGIN IMMEDIATE` encloses watermark verification, lazy recovery, usage
  read, approved pure quota decision and both reservation inserts. Return of success
  follows SQL COMMIT. Each operation has its own connection; no provider I/O occurs
  in a transaction. Async operations are offloaded, not guarded solely by asyncio.
- **Consistency:** exact integer bounds, primary+backup reservation, 50,000 inclusive.
  Settled charges at admission time count in `(now-60000, now]`. Outstanding holds
  count regardless of age. Settlement replaces each hold once, preserves timestamps,
  releases only proven unused capacity; duplicate identical settlements are no-ops,
  conflicting transitions fail. Tenant HMAC and metadata survive reopen; mismatched
  identity config or regressed UTC watermark fail closed. UTC forward jumps remain
  a trusted-clock operational risk; monotonic time separately governs execution.
- **Durability/concurrency:** supported runtime/filesystem gates precede use. WAL,
  synchronous=FULL, explicit busy timeout (default 1,000 ms) verified. Six process
  contenders cannot oversubscribe the final capacity. Duplicate/start/settlement
  races, threads, independent service owners and separate tenant budgets pass.
- **Recovery:** uncertain dispatched usage charges its full bound; unresolved holds
  survive restart/window expiration. Lazy transactional recovery at/after stored
  finite deadline converts remaining holds to full charges at that deadline, once;
  charges then expire 60 seconds later. Previously settled attempts are not charged
  again. No provider replay, implicit uncertain release or distributed recovery.
  Actual bound breaches durably block further tenant admission.
- **Executed fault tests:** second-insert abort rolls back request/first hold and
  watermark; denied COMMIT cannot return admission success; settlement abort keeps
  holds and permits identical retry. Busy contention, removed DB, invalid config,
  clock rollback, storage-worker cancellation and before/after-commit API failure
  probes preserve conservative state. Exact recovery deadline, stale workers,
  partial settlement/recovery and graceful process restart are covered.

### Recovery scenarios NOT VERIFIED

No abrupt OS kill at every admission/dispatch/COMMIT/settlement/recovery instruction;
no power-cut, disk-full, hardware/fsync failure, DB/WAL corruption, backup restore or
deleted-database reconstruction experiment. The COMMIT-denial test fails before
COMMIT; after-commit probes simulate API ambiguity, not real power-loss acknowledgement
loss. Recovery transaction rollback at every intermediate write has not been
fault-injected separately. SQLite WAL/FULL is an inspected/tested durability policy,
not a physical crash-survival certification. No remote billing reconciliation or
provider exactly-once guarantee; uncertain remote execution cannot be undone.
These are explicitly bounded assessment limitations, not invented passing tests.

## Primary/backup and accounting findings

Prepare trusted per-model bounds/caps, atomically reserve both attempts, durably
start primary, then execute. No trustworthy bounds means 503/no admission or send.
Local quota exhaustion means 429/no provider. Primary success settles in-bound
usage and releases unused backup; unknown consumption charges full bound.

Primary 429 or primary-owned monotonic 3,000 ms deadline authorizes exactly one
backup only after terminal primary task AND confirmed resource close. A result
observed at the deadline loses. Cancellation/close share 500 ms; delayed timeout
observation cannot renew it. Unconfirmed cleanup quarantines dispatch and retains
conservative accounting, returning controlled failure instead of unsafe fallback.
Other failures have no fallback; backup failure/timeout has no third attempt.
Cancellation discovers DB-worker completion rather than assuming rollback.

Wire mode journals: success two primary/zero backup calls (two framed requests);
429 and timeout each one primary/one backup, charge 25; backup failure/backup 429
each one/one, charge 40; transport failure and unknown success each one/zero,
charge 20. Tenant credentials never reach upstream. Late remote work is explicitly
released by fixtures; local cancellation is not proof of remote billing cessation.
No real vendor input counting/output-cap enforcement or token-billing-time sliding
quota has been validated. The verified quota is the approved P1 admission-time
accounting invariant with reliable adapter bounds as a prerequisite.

## HTTP and clean reproducibility

A NEW ignored environment `.cache/t4006-clean-env` was created from the unchanged
Task 4 lock using uv 0.13.7 and the installed Python 3.12.16. Offline setup initially
failed for missing cached Ruff; the online locked retry installed all 27 packages,
exit 0. Imports of installed app/service/storage and runtime versions passed.
The environment is new; the package installation is editable from this checkout,
not a wheel/distribution portability certification.

In that clean environment, documented deterministic adapter selectors passed:
**6 ASGI routing cases in 0.81s** and **7 real HTTP cases in 16.61s**, exits 0,
zero failures/skips/warnings/xfails. The latter exercise primary success plus six
routing modes; all **14 children exit 0, zero forced cleanup**. Fixtures inject
trusted synthetic bounds/caps and private temporary credentials; no real keys,
real LLM, vendor tokenizer or external inference endpoint is required.
Reproduction commands are in [Task 4 README](../task4/README.md).

The documented `uvicorn task4_limiter.app:create_app --factory` CLI was also
launched in the clean environment on loopback port 61736, with temporary generated
configuration. An authenticated request received the intended **503
service_unavailable** from stock bounds-unavailable adapters. A one-request server
budget allowed graceful exit 0; stdout/stderr empty, no forced cleanup. Successful
primary/fallback reproduction uses the injected fixtures, not the stock factory.

HTTP policies pass at ASGI and wire levels: registered single Bearer credentials,
strict prompt-only UTF-8 JSON, duplicate/invalid-envelope rejection, streamed body
size and total body-read deadline, no compression/tenant/model overrides. Defaults
are 65,536 bytes/5,000 ms, prompt 16,000 characters; fixtures use smaller explicit
budgets. 21 native wire rejection receipts show **zero provider AND reservation
deltas**, including auth/body/quota/concurrency/DB/framing cases. Concurrent tenants
and graceful process restart preserve identities and budget. Lifespan startup,
failed startup, cancellation, draining and cleanup assertions pass.

Response policy: 200 success; 400 invalid input; 401 credentials; 404/405 route or
method; 408 read timeout; 413 too large; 415 encoding/media; 429 local quota or
terminal backup rate limit (distinct codes); 499 disconnect diagnostic if deliverable;
502 provider failure; 503 unavailable/bounds/storage/unclean cleanup; 504 terminal
model timeout. Controlled JSON error envelope, server request UUID, no-store/nosniff.
Uvicorn/h11 may emit HTTP 400 before ASGI for malformed transport framing.

## Security and Git publication inspection

Inspected all 81 initially tracked files and all local reachable history: **14
commits, 238 objects, 163 unique text blobs**, no binary blobs. No tracked current
or historical DB/WAL/SHM, ZIP, environment, cache, egg-info or credential file found.
Origin URL has no embedded credential. Private-key/common provider-key patterns,
Bearer literals, quoted credential assignments and credentialed URLs were examined
with redacted contexts/fingerprints. **No actual credential/security leak found.**

141 historical candidate occurrences were manually classified: 139 Bearer grammar,
documentation/RFC link/invalid-test references; one frozen-settings mutation sentinel;
one deliberately rejected credentialed `.test` URL. None is a production credential.
Runtime fixture keys/identity secrets are generated, not hardcoded. Usage rows store
HMAC tenant IDs, verifier, UUIDs and numeric states; no raw keys/prompts/completions.
HTTP/private-error markers are synthetic negative-test data.

Limits: heuristic/context scan is not proof against all secret formats, unreachable
objects/reflogs/remote-only branches, external CI/hosting logs, dependency CVEs or
real-model semantic leaks. Local ignored artifacts may contain temporary test keys
and DBs and must remain outside publication.

Portable `.gitignore` excludes environment/cache/egg-info/.env paths, but review ZIP
exclusions live in local `.git/info/exclude`; arbitrary SQLite files outside ignored
cache paths are not globally excluded. **Publication hygiene risk**, not an actual
tracked leak. Do not blanket-stage generated files; inspect exact staged inventory.
No ignore/config changes are authorized or made in this audit. No TLS/ingress/public
listener, multi-host/network filesystem, native Linux, load/slow-header, production
provider or deployment certification is claimed. Bind loopback as documented.

## Submission checklist and adoption decision

- [x] R1-R7 implementation/test traceability established; policies distinguished.
- [x] Fresh complete 149/452/427 suites and six Ruff commands pass in separate envs.
- [x] Clean locked Task 4 install/imports, stock CLI 503/start/exit and deterministic
  primary/fallback reproduction verified; instructions supplied.
- [x] Accounting boundaries/concurrency/persistence/routing/sanitization checked;
  crash/fault coverage gaps explicitly recorded.
- [x] Reachable Git history/current tracked artifact/secret inspection completed;
  no accepted implementation changes or accidental stage/commit/push.
- [x] README/contract/ledger/ADR/build/evidence updated; known deployment limits clear.
- [x] Independent ChatGPT review of T4-006 and authorization to mark TASK-4 DONE,
  confirmed 2026-11-05; E029 records supplied acceptance, not new tests.
- [x] Final documentation-only Git checkpoint authorized with explicit inventory,
  staged-content/secret/artifact/whitespace checks; no implementation changes.
- [ ] Any GitHub push/publication requires separate user authorization.

**APPROVED / assessment-ready**, within the documented approved policies,
trusted adapter seam and supported Windows/SQLite/local-storage scope. No blocking
implementation defect identified. Real LLM/provider/tokenizer and production
deployment remain NOT VERIFIED and deliberately excluded. Next action: complete
the one authorized final documentation-only Git checkpoint, verify SHA/inventory/
clean tree/branch status and stop. No test rerun unless unexpected implementation
or configuration changes are discovered; no Task 3 or push.
