# T2-006 final assessment audit

Date: 2026-11-04 (America/Los_Angeles). Audited baseline: `aa343b3`.
Final verdict: **APPROVED - assessment-ready within documented requirements**.
Independent ChatGPT engineering acceptance was confirmed by the user on 2026-11-04.
**T2-006 and TASK-2 are DONE.** All eight traceability rows, reviewed source/test
references, final evidence and submission documentation were found consistent.
E018 records this reported acceptance and authorized documentation-only commit;
no tests were rerun for acceptance. E017 remains the actual audit execution record.
No accepted production code, tests, dependencies or configuration changed.
Task 1 remains DONE. No push or Tasks 3/4 authorized.

## Source and evidence boundaries

The eight original requirements below are the user-supplied, approved wording in
[TASK2_REQUIREMENTS.md](TASK2_REQUIREMENTS.md). No separate original vendor brief
was supplied for this audit. Later checkpoint requirements and implementation
choices are identified separately; none is silently promoted to an original
assessment requirement. [CONTRACT.md](../task2/CONTRACT.md) preserves those choices
and the chronological checkpoint history. Current execution evidence is E017 in
[TEST_EVIDENCE.md](TEST_EVIDENCE.md); older E008-E016 remain historical evidence.

PASS means the listed current execution/inspection verified the stated scope.
It does not claim all possible protocol/deployment behavior or vendor MCP support.

## Original requirements traceability

Test paths below are relative to `task2/tests/`; function names are actual test
definitions, including their parameterized cases. All ran in the current full suite.

| ID / original assessment requirement | Implementation | Automated cases | Current evidence | Status |
| --- | --- | --- | --- | --- |
| R1: Lightweight Python HTTP/JSON-RPC reverse proxy | `app.create_app` / nested `mcp`; `upstream.UpstreamAdapter.forward` | `test_app.py::test_authorized_roles_and_literal_prefix_pass_through`; `test_http_wire.py::test_wire_authorized_calls_preserve_request_and_response_bytes` | 452 passes; separate Uvicorn CLI/peer smoke check over TCP | PASS |
| R2: Bearer tokens map callers to admin/viewer | `settings.load_settings`, `SecuritySettings`; `security.authenticate` | `test_settings.py::test_settings_are_immutable_redacted_and_allow_multiple_tokens`; `test_security.py::test_known_tokens_resolve_to_trusted_roles`; `test_http_wire.py::test_wire_authentication_rejections_have_zero_upstream_calls` | Unit/ASGI/wire cases passed; CLI missing-token 401 | PASS |
| R3: tools/list transparent, without discovery filtering | `rpc.inspect_request`; `UpstreamAdapter.forward` / `_receive`; `app.mcp` byte relay | `test_upstream.py::test_original_request_and_discovery_response_bytes_are_unchanged`; `test_app.py::test_discovery_request_response_and_admin_definitions_are_transparent`; `test_http_wire.py::test_wire_discovery_is_transparent_including_admin_tools` | Exact discovery bytes including admin definitions passed; CLI viewer discovery 200 | PASS |
| R4: Inspect params.name for tools/call | `rpc.inspect_request`; `security.authorize` | `test_rpc.py::test_invalid_tool_parameters`; `test_guards.py::test_body_claims_and_nested_names_cannot_override_policy`; `test_http_wire.py::test_wire_bypasses_malformed_rpc_and_batches_fail_closed` | Missing/invalid selector and bypass cases passed | PASS |
| R5: Literal case-sensitive admin_ prefix requires admin | `security.authorize`; `guard_request` | `test_security.py::test_admin_can_authorize_protected_tools`; `test_security.py::test_literal_prefix_does_not_expand_to_other_names`; `test_guards.py::test_encoded_names_and_selectors_cannot_bypass_viewer_policy` | Decoded-name enforcement, admin success and ordinary calls for both roles passed | PASS |
| R6: Viewer denial -32001 / Unauthorized Tool Call, applicable ID preserved | `security.authorize`; `RpcError.to_response`; `app._rpc_error` | `test_security.py::test_viewer_denial_has_exact_contract_and_id`; `test_app.py::test_viewer_denial_has_exact_code_message_and_id_without_upstream`; `test_http_wire.py::test_wire_viewer_denial_preserves_id_and_zero_journal` | Wire ID variants passed; CLI 403/-32001/exact message/id=audit-deny | PASS |
| R7: Denied calls never reach downstream | `guard_request`; `require_authorized_request`; `app.mcp` before `adapter.forward` | `test_upstream.py::test_forwarding_requires_a_guard_issued_unmodified_permit`; `test_upstream.py::test_copied_proof_cannot_authorize_modified_role_body_or_metadata`; local-rejection tests in `test_app.py` / `test_http_wire.py` | 33 dedicated wire rejection cases each assert zero journal entries; CLI two rejections also zero before four permitted calls | PASS |
| R8: Preserve Task 1 | Separate `task2/` package, environment, pyproject and lock | Complete root `tests/` suite | 149 passes; Task 1/root dependency/manual-lab diff against published 6056bc7 empty; audit-start hash preservation check | PASS |

## Later checkpoint requirements and chosen policies

These are approved engineering requirements/choices from T2-001 through T2-005,
not additional wording attributed to the original assessment brief.

| Contract area | Implementation / actual automated evidence | Current result |
| --- | --- | --- |
| Strict UTF-8, envelopes/IDs/params, decoded duplicate keys | `rpc.inspect_request`; `test_rpc.py` ID/duplicate/parse cases, `test_http_wire.py::test_wire_bypasses_malformed_rpc_and_batches_fail_closed` | PASS |
| Numeric range policy: Decimal overflow/nonfinite conversions -> -32700/null, preserve representable opaque bytes | `rpc._parse_decimal`, `inspect_request`; `test_rpc.py::test_unrepresentable_exponents_are_parse_errors`, `test_representable_numbers_preserve_raw_body` | PASS |
| Whole-batch rejection; no notification permit/no RPC reply | `inspect_request`, `guard_request`, `RpcError.to_response`; batch/notification guard, ASGI and wire tests | PASS |
| Fixed trusted upstream, separate credential, no client headers/cookies, no redirects/retries | `UpstreamSettings`, `load_upstream_settings`, `UpstreamAdapter`; upstream destination/credential/redirect tests; `test_wire_client_credentials_cookies_and_role_claims_do_not_reach_upstream` | PASS |
| Preserve authorized request bytes and correlated upstream result/error bytes/status | `forward`, `_validate_response`, `_receive`; upstream preservation tests; `test_wire_upstream_jsonrpc_errors_keep_bytes_and_status`, length/chunked tests | PASS |
| HTTP framing/media/encoding/bounds/deadlines before RPC, auth before body/inspection | `app._http_metadata`, `_read_body`, `mcp`; corresponding `test_app.py` cases and real-wire size/media/deadline/method cases | PASS |
| Controlled failures, ID correlation, cancellation/close | Adapter timeout/transport/response validation and app mappings; `test_total_deadline_and_cancellation_close_streams_without_retry`; real slow/refused/killed/drop/malformed/redirect peer cases | PASS |
| Concurrent roles and repeated IDs do not mix | Independent permit/request state; `test_wire_concurrent_roles_repeated_ids_and_separate_connections`, ASGI and adapter concurrency cases | PASS |
| Lifespan pooling, startup failures, shutdown and cleanup | `create_app.lifespan`, `UpstreamAdapter.aclose`; ASGI lifespan tests; wire cleanup/startup-failure cases | PASS; 12 children reaped, 0 forced cleanup/live readers; extra CLI pair both exit 0 |
| Full vendor MCP/Streamable HTTP/session/SSE, DNS/TLS/public deployment interoperability | Deliberately excluded; no supplied real service or deployment exercised | NOT VERIFIED / outside agreed scope |

## Fresh regression and tooling results

Both interpreters: CPython **3.12.16**, MSC v.1944, Windows AMD64.
Each command below actually ran during T2-006. Exit codes are zero for all six.

| Working directory | Command | Result |
| --- | --- | --- |
| Repository root | `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest --tb=short` | **149 passed in 38.44s** |
| Repository root | `.\.venv\Scripts\python.exe -m ruff check task1 tests` | All checks passed |
| Repository root | `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | 17 files already formatted |
| `task2/` | `.\.venv\Scripts\python.exe -m pytest -q --tb=short` | **452 passed in 13.87s** |
| `task2/` | `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed |
| `task2/` | `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 16 files already formatted |

Both suites: **0 failures, 0 skips, 0 warnings, 0 xfails**. Combined: 601 passes,
not one shared-environment suite. Task 1 required execution outside the Windows
sandbox for official SDK named-pipe access. No assertion or test marker changed.
Task 2's 52 wire cases are included in 452, not added again to that total.
The new README's selected wire-example command was also executed: 10 passed,
42 deselected in 1.51s, exit 0, no failures/skips/warnings. It does not change the
full-suite count. Matrix test references, local documentation links and embedded
README client syntax were checked successfully; the latter is a syntax check.

Wire process settings remain ADR-014: six peer/proxy pairs; 127.0.0.1 ephemeral
ports; Python/Uvicorn/h11, no reload, one worker, access logs/proxy headers off;
4096-byte fixture bound, 0.5s body/read deadlines (5s read for gated concurrency),
3s connect, 1s write/pool, 4s total (6s concurrency). Defaults are documented in
CONTRACT.md and differ intentionally from these bounded test settings.
Fresh cleanup summary: 12 children, 0 alive/forced cleanup/live reader threads;
ten exits 0, intentionally killed upstream 1 and invalid-config proxy 3.
The 33 zero-forwarding cases cover auth 7, protected IDs 5, bypass/malformed/batch
10, notifications 3, oversize 2, media/encoding 3, methods 2, body deadline 1.
Concurrency: 12 clients with repeated ID=1, two denials, ten held permitted calls;
each response/authentication context remains associated with its owner.

## Reproducibility and launch audit

- uv **0.13.7** installed all 27 locked Task 2 packages into fresh ignored
  `task2/.cache/t2006-venv` using `sync --locked --offline --project task2 --extra
  dev --extra serve --python 3.12.16`. UV_PROJECT_ENVIRONMENT selected that fresh
  environment; UV_CACHE_DIR selected `task2/.cache/uv`; the Task 1 environment
  and both lockfiles stayed unchanged. `uv pip check` passed for all 27 packages.
- Installed distribution versions exactly equal all 27 task2/uv.lock selections.
  Imports of task2_proxy.app/security/upstream succeed from task2/ in the fresh
  editable installation. No Task 1 distribution exists in either Task 2 environment.
- Initial attempts are not hidden: offline install with the root cache missed a
  wheel (exit 1); the correct Task 2 cache then hit Windows sandbox denial creating
  setuptools temporary egg-info (exit 1). Authorized execution outside that sandbox
  succeeded offline (exit 0). A pip-check probe initially used an inaccessible
  user-default cache; rerun with explicit writable cache exited 0. These were
  environment constraints, not production defects. A normal online first install
  is documented; this audit reused verified cached artifacts rather than downloading.
- Actual Uvicorn module CLI was exercised in the fresh environment with
  `task2_proxy.app:create_app --factory --host 127.0.0.1 --port 0 --no-access-log`.
  A transient Python stdin supervisor used runpy to execute the module entry point
  and raised SIGINT on a stop command for graceful hidden Windows cleanup; it did
  not wrap/replace the ASGI app or inject HTTPX transports/settings. Port 0 avoids
  collision; README uses user-selected port 8000. Startup was awaited from CLI
  output, then real HTTP requests went through default production settings.
- An independent stdlib fixture peer used a separate ephemeral loopback port.
  Four independent random synthetic credentials existed only in process memory/env;
  no values were printed or stored. Required role-token/upstream environment
  variables and separate upstream Bearer configuration were used as documented.
- Observed missing-token 401, viewer protected 403/-32001/exact ID/message and zero
  peer calls; viewer discovery 200 including admin definitions; admin protected 200;
  admin/viewer ordinary calls 200. Exactly four permitted journal entries matched
  original request and response bytes; upstream-only auth succeeded with no client
  token/cookie/role leakage. Startup and shutdown completed, both processes exited
  0, no forced cleanup or live reader threads; captured output contained no tokens.
  These six smoke probes are manual audit evidence, not extra pytest cases.

## Security and Git publication audit

Scope: all 53 baseline tracked files, current documentation, and **98 unique blobs
in nine commits reachable from all local refs**. Inspected source, tests, synthetic
fixtures, documentation, lock URLs, path inventory and ignore rules. Pattern scans
covered private-key blocks, common provider keys, literal Bearer values, credential
assignments and URLs with embedded credentials; candidates were reviewed in context.

- **No actual secret or sensitive customer-data finding** in the inspected scope.
  Sixteen path/rule/fingerprint candidates were harmless: descriptive phrases such
  as Bearer authentication/credentials, an intentionally invalid `wrong-token`
  fixture, and user/password on example.test in a rejected-destination test.
  Customer/refund records are explicitly synthetic; runtime test tokens are randomly
  generated. Hashes and dependency artifact URLs are not credentials.
- No tracked environments, caches, egg-info, ZIPs, .env files, private keys or
  compiled/generated artifacts, including historical path inventory. Origin URL
  contains no embedded credentials. No credential values were included in scan
  output/report. This is bounded inspection, not proof against every secret format
  or a dependency advisory scan; external/unreachable history was not inspected.
- Portable .gitignore covers environment/runtime/tool caches, bytecode, egg-info,
  build/dist and .env/.env.* (except the intentional .env.example exception).
  No .env.example is tracked. Existing review ZIPs are ignored through local
  `.git/info/exclude`, which **does not travel with a clone**. This is a publication
  hygiene risk for future review archives, not a current tracked-file leak.
  Keep explicit-path staging/review; portable ignore changes need a later authorized
  configuration checkpoint. Do not upload local archives/caches/history scan files.
- Ignored-tree inventory initially emitted Windows permission warnings for stale
  sandbox-created cache directories. They are ignored/untracked, not missing tracked
  audit coverage. No artifact was deleted or staged. Actual source/refs remained intact.
- App-generated errors/logging do not expose credentials or exception details;
  tests and CLI captured output passed token checks. Upstream JSON-RPC content is
  intentionally transparent, so the trusted upstream owns its payload confidentiality.

Audit-execution Git snapshot (before the final acceptance commit): HEAD
`aa343b367e81827b394dfd509f8e82f84a5533ac`; main was **ahead 4,
behind 0** against the existing local origin/main reference. No fetch was performed,
so that is not a claim about live GitHub state. Initial tree/index were clean;
final differences are this audit's documentation only; index remains empty.
No commit, push, source/test/dependency/configuration change or Task 3/4 work.

Final integrity assertions: 44 baseline files remain byte-identical; nine tracked
documentation files changed and one new report was created. Historical build log,
decisions, evidence and requirement prefixes are preserved. The later README-only
test subset reaped two more children with exits 0, no forced cleanup/live readers;
its regenerated cache summary is distinct from the full suite's 12-child record.

Documentation changes only:

- `AGENTS.md`: current audit authorization, evidence and independent-review gate.
- `README.md`: implemented Task 2 navigation/status/tree; Task 1 evidence retained.
- `docs/TASK_LEDGER.md`: verified audit, recovery and independent acceptance.
- `docs/DECISIONS.md`: ADR-015 verification/provenance gate, no architecture redesign.
- `docs/BUILD_LOG.md`: M027-M030 baseline, findings, acceptance and recoverable handoff.
- `docs/TEST_EVIDENCE.md`: E017 executions/diagnostics; E018 reported acceptance and Git checks.
- `docs/TASK2_REQUIREMENTS.md`: append this audit's authorization; original unchanged.
- `docs/TASK2_FINAL_AUDIT.md` (new): matrix, checklist, audit and version inventory.
- `task2/README.md`: current setup/status/configuration/examples and limits.
- `task2/CONTRACT.md`: current summary/history labels and audit link; policies retained.

## README / submission checklist

- [x] Root README identifies both independent tasks and links Task 2 setup/contract.
- [x] Task 1 install, STDIO architecture, 149-test evidence and limitations retained.
- [x] Task 2 setup uses its own environment, locked dev/serve extras and pinned Python.
- [x] Required role JSON/fixed URL/separate optional upstream token are documented.
- [x] FastAPI factory launch, POST /mcp and authenticated discovery/denial examples
  are documented without actual credentials; exact deterministic socket examples
  also run through the named real-wire tests.
- [x] HTTP statuses, IDs, transparent discovery, fail-closed batch/notification,
  resource bounds and unsupported protocol modes are linked to the contract.
- [x] Fresh test/lint/format/install/CLI evidence and security scope are recorded.
- [x] No secrets/artifacts staged; accepted implementation and Task 1 preserved.
- [x] Independent engineering acceptance of this final audit; T2-006/TASK-2 DONE.
- [x] Final documentation/Git checkpoint explicitly authorized; commit identity in Git.
- [ ] Separate push/publication authorization; no push performed.

## Defects, limitations and recommendation

No reproducible production defect was discovered. Stale public documentation about
Task 2's existence, HTTP status decisions and pending wire verification was corrected
only in documentation; historical milestone evidence remains intact.

Remaining contractual/operational limits: stateless single JSON POST exchanges,
no notifications/batches, SSE/session headers/full Streamable HTTP/OAuth/JWT;
viewer is a prefix-based role, not generally read-only; decoded names use literal
case-sensitive semantics and downstream must agree. Exact integer/string/null IDs
only; Decimal range/nesting/integer parser limits; bounded buffered JSON bodies.
No automatic retries/redirects/compression; TLS/DNS/vendor service, other operating
systems, HTTP/2, arbitrary smuggling/half-open cases and load qualification were
not verified. The operator supplies destination trust/DNS/egress, strong token
provisioning/rotation and public TLS/header/connection/rate protections. These
accepted limits are not new missing original requirements.

**APPROVED within the supplied assessment contract following independent review.**
No new architecture is needed. ADR-015 records accepted verification/provenance;
E018 distinguishes reported independent acceptance from actual E017 executions.
T2-006/TASK-2 are DONE. One final documentation-only commit is authorized; verify
its clean tree/branch status and stop. No implementation changes, push or Tasks 3/4.
The limitations above remain unchanged; acceptance does not extend their scope.

## Installed dependency versions

The following table was populated from current interpreter distribution metadata;
Task 2 selections also match the freshly installed lock exactly. Setuptools 82.0.1
is the isolated build requirement in both projects, not a runtime distribution.

| Distribution | Task 1 | Task 2 |
| --- | --- | --- |
| ai-solutions-engineer-assessment | 0.1.0 | not installed |
| annotated-doc | not installed | 0.0.5 |
| annotated-types | 0.8.0 | 0.8.0 |
| anyio | 4.16.0 | 4.16.0 |
| asgi-lifespan | not installed | 2.1.0 |
| assessment-task2-proxy | not installed | 0.1.0 |
| attrs | 26.1.0 | not installed |
| certifi | not installed | 2026.10.23 |
| cffi | 2.1.1 | not installed |
| click | 8.5.0 | 8.5.0 |
| colorama | 0.4.6 | 0.4.6 |
| cryptography | 50.0.2 | not installed |
| fastapi | not installed | 0.162.0 |
| h11 | 0.16.0 | 0.16.0 |
| httpcore | not installed | 1.0.9 |
| httpcore2 | 2.16.0 | not installed |
| httpx | not installed | 0.28.1 |
| httpx2 | 2.16.0 | not installed |
| idna | 3.20 | 3.20 |
| iniconfig | 2.3.1 | 2.3.1 |
| jsonschema | 4.26.0 | not installed |
| jsonschema-specifications | 2025.9.1 | not installed |
| mcp | 2.3.0 | not installed |
| mcp-types | 2.3.0 | not installed |
| opentelemetry-api | 1.45.2 | 1.45.2 |
| packaging | 26.3 | 26.3 |
| pluggy | 1.7.0 | 1.7.0 |
| pycparser | 3.12 | not installed |
| pydantic | 2.12.5 | 2.14.2 |
| pydantic-core | 2.41.5 | 2.50.2 |
| pygments | 2.21.0 | 2.21.0 |
| pyjwt | 2.15.1 | not installed |
| pytest | 9.2.0 | 9.2.0 |
| pytest-asyncio | 1.4.1.post1 | not installed |
| python-multipart | 0.0.33 | not installed |
| pywin32 | 312 | not installed |
| referencing | 0.37.0 | not installed |
| rpds-py | 2026.9.1 | not installed |
| ruff | 0.17.3 | 0.17.3 |
| sniffio | not installed | 1.3.1 |
| sse-starlette | 3.6.0 | not installed |
| starlette | 1.10.0 | 1.10.0 |
| truststore | 0.10.5 | not installed |
| typing-extensions | 4.16.0 | 4.16.0 |
| typing-inspection | 0.4.4 | 0.4.5 |
| uvicorn | 0.54.0 | 0.54.0 |
