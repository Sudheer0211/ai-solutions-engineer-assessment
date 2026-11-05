# Test and verification evidence

Record only commands actually executed. Dates use America/Los_Angeles.
Environment probes and document checks are not application compliance tests.
Never include credentials, tokens, sensitive data or raw private records.

## E001 — 2026-11-02: Pre-implementation inspection (GOV-001, T1-001)

Working directory: `S:\2026 jobs`; shell: PowerShell.

| Actual command | Observed result |
| --- | --- |
| `git status --short` | Failed: not a Git repository |
| `git rev-parse --show-toplevel` | Failed: not a Git repository |
| `rg --files -g AGENTS.md -g TASK_LEDGER.md -g pyproject.toml -g README.md -g requirements.txt -g package.json -g '!node_modules' -g '!.venv' -g '!venv'` | Found unrelated project manifests/READMEs; no governance files in results |
| `py -0p` | Python 3.11 and Anaconda 3.9 listed; no 3.12 |
| `python --version` | Python 3.11.1 |
| `python -m pip show mcp pydantic pytest ruff` | MCP/Ruff absent; Pydantic 2.12.5; pytest 8.4.2 |
| `python -m pip index versions mcp` | Exit 1: no matching distribution found; investigate registry configuration/network |
| `Get-Command uv,git,winget -ErrorAction SilentlyContinue` (selected Name/Source) | Git and winget found; uv not found |

No application tests, lint checks or server startup checks executed in E001.
These results establish blockers, not passing acceptance criteria.

## E002 — 2026-11-02: Governance verification (GOV-001)

Working directory: project root.

- Executed `git init`: exit 0; empty repository initialized at the chosen path.
- Executed `Get-Content AGENTS.md` and `Get-Content docs/TASK_LEDGER.md`.
- Executed a `python -c` assertion checking all five required files exist and
  are nonempty and the source snapshot exactly equals the attachment: passed.
  Source SHA256: `440f1c903ebd9d5a72a9ae3660f7fc9b7a5855b5a72e87ab092d72cb39dddebd`.
- Executed `git status --short`: only new AGENTS.md and docs/ reported.
- Executed a process-environment presence probe: PIP_NO_INDEX set, no
  PIP_INDEX_URL. No environment values/secrets were printed.
- Executed `python -m pip index versions mcp --index-url https://pypi.org/simple
  --no-cache-dir`: exit 1; inherited PIP_NO_INDEX still prevented discovery.

G1–G5 verified by content/file inspection and source equality. These are
governance checks; no application-test or protocol-compliance claim is made.

## E003 — 2026-11-02: Local environment/public API verification (T1-001)

Working directory: project root, PowerShell. Network setup used escalated
execution approved by automatic review; registry settings affected that process
only. No global dependency installation was performed.

1. `python -m pip install --index-url https://pypi.org/simple --target .tools uv`
   with PIP_NO_INDEX=0: first attempt failed (inherited refusing proxy); retry
   with process-local proxy settings cleared succeeded, uv 0.13.7.
2. `.\.tools\bin\uv.exe python install 3.12` with UV_PYTHON_INSTALL_DIR=.runtime
   and UV_CACHE_DIR=.cache: exit 0, CPython 3.12.16 downloaded.
3. `.\.tools\bin\uv.exe venv --python 3.12 .venv`: exit 0.
4. `.\.tools\bin\uv.exe pip install --python .venv\Scripts\python.exe
   --index-url https://pypi.org/simple 'mcp==2.3.0' 'pydantic==2.12.5'
   pytest pytest-asyncio ruff`: exit 0; 37 packages installed.
5. Executed `.\.venv\Scripts\python.exe -c` introspection of sys.version,
   importlib.metadata.version and inspect.signature: Python 3.12.16;
   mcp 2.3.0; Pydantic 2.12.5; pytest 9.2.0; pytest-asyncio 1.4.1.post1;
   Ruff 0.17.3. Public Server accepts on_list_tools/on_call_tool; run accepts
   streams/options; MCPError takes code/message/data.
6. Executed `Get-Content`/`rg` inspection of installed stdio.py, runner.py,
   jsonrpc_dispatcher.py and client/session.py. Some initial guessed paths
   (shared/session.py and client/transports) did not exist; inspected actual
   paths instead. No SDK files modified. Malformed JSON is passed as an
   exception; the default dispatcher drops stream exceptions. Wire proof pending.

These are environment/API checks, not application test passes.

## E004 — 2026-11-02: Implementation checks and fixes (T1-002–T1-006)

Working directory: project root; runtime: E003 local Python 3.12.16.

| Actual command | Actual outcome |
| --- | --- |
| `.\.tools\bin\uv.exe pip install --python .venv\Scripts\python.exe --index-url https://pypi.org/simple -e '.[dev]'` | Exit 0; package built with pinned setuptools 82.0.1 and installed editable |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_schemas.py tests/test_service.py tests/test_integration.py` | 1 failed, 78 passed in 1.08s; schema advertised zero as valid; two sandbox pytest-cache warnings |
| `.\.venv\Scripts\python.exe -m ruff check .` | Exit 0; all checks passed, two filesystem-access warnings during broad discovery |
| `New-Item -ItemType Directory -Path '.cache\pytest\v\cache' -Force` | Created explicit pytest cache path to avoid sandbox temporary-directory rename warnings |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest` (sandbox) | Exit 1; 2 failed, 88 passed, 4 xfailed in 15.77s; official client subprocess startup denied Windows named-pipe access |
| `.\.venv\Scripts\python.exe -m ruff check task1 tests` | Exit 1; E501 in wire_support.py |
| `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | Exit 1; 6 files needed formatting |
| `.\.venv\Scripts\python.exe -m ruff format task1 tests` | Exit 0; 6 reformatted, 7 unchanged |
| `.\.venv\Scripts\python.exe -m ruff check task1 tests` | Exit 0; all checks passed |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest` (approved unsandboxed rerun) | Exit 0; 90 passed, 4 xfailed in 20.23s; no skips |
| `.\.tools\bin\uv.exe lock --python .venv\Scripts\python.exe --index-url https://pypi.org/simple` | Exit 0; resolved 39 lock packages |
| `.\.tools\bin\uv.exe sync --locked --extra dev --python .venv\Scripts\python.exe` | Exit 0; checked 38 installed packages |

Schema fix: put gt=0 on each numeric union branch rather than the union wrapper.
Wire tests verify actual processes, modern/legacy connectivity, both tools,
schema equality, integer/string IDs, -32601/-32602/-32603, business errors,
atomic failures, stdout JSON purity, stderr logs, EOF shutdown and state reset.
Internal fault is injected through a test repository, with no production fault
switch or SDK monkeypatch. Client responses and application logs omit the
synthetic private exception detail.

The four xfails are real unmet acceptance criteria, not passes: malformed JSON
(-32700) and malformed envelope (-32600 with ID preservation), in both eras.
The SDK's stdio reader passes validation exceptions downstream; the dispatcher
drops them without constructing a response. Subsequent valid requests succeed.

## E005 — 2026-11-02: Final verification and strict diagnostics (TASK-1, T1-001–006)

Working directory: `S:\2026 jobs\Projects\ai-solutions-engineer-assessment`.
Runtime: Python 3.12.16 / MCP 2.3.0 / Pydantic 2.12.5; Windows.

| Actual command | Actual result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m ruff format task1 tests` | Exit 0; 1 file reformatted, 12 unchanged (added nonfinite wire boundary cases) |
| `.\.venv\Scripts\python.exe -m ruff check task1 tests` | Exit 0; all checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | Exit 0; 13 files already formatted |
| `.\.tools\bin\uv.exe pip check --python .venv\Scripts\python.exe` (first attempt, no local cache setting) | Failed to initialize default user cache: sandbox access denied |
| Same `uv pip check` with UV_CACHE_DIR set to repository .cache | Exit 0; 38 packages checked, all compatible |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest` (approved unsandboxed execution for Windows pipes) | Exit 0; **94 passed, 4 xfailed in 19.45s; no skips** |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short` | Exit 1; **4 failed, 94 deselected in 4.50s** |
| `.\.tools\bin\uv.exe sync --locked --extra dev --python 3.12.16` (local runtime/cache directories configured) | Exit 0; resolved 39 lock packages; checked 38 installed packages |
| `git diff --check` | Exit 0; no tracked diff exists yet in this newly initialized repository; does not validate untracked file whitespace |
| `git status --short` and `rg --files --hidden` with runtime/cache/Git exclusions | Only assessment files enumerated; no unrelated project changes |

The strict diagnostic failures are exactly:

- Parse error required -32700, legacy: `Required -32700 response absent; observed []`.
- Parse error required -32700, modern: same missing response.
- Invalid envelope required -32600 with ID invalid-8, legacy: `Required -32600 response absent; observed []`.
- Invalid envelope required -32600 with ID invalid-8, modern: same missing response.

These cases are not skipped and do not count as passes. They establish B3.
All four added nonfinite wire cases (NaN, Infinity, -Infinity, 1e309) returned
-32602 without consuming the first refund ID or changing the available balance.
NaN/Infinity tokens are nonstandard JSON; the SDK accepts their lexical form
before application validation rejects them. This does not resolve malformed
transport parsing or imply general strict JSON lexical compliance.

Final STDIO evidence: actual module/console processes connected; modern discovery
and legacy initialization worked; every stdout frame parsed as JSON-RPC and
ended in a newline; diagnostics appeared on stderr; normal stdin-EOF termination
returned exit 0; restarting reset state. Monetary values and sequential IDs were
asserted, including failed-operation atomicity. Internal failure responses/logs
omitted injected private details. Test subprocesses were closed by their harnesses.

Two temporary pytest cache directories left by the sandbox's failed atomic
cache creation were removed using native PowerShell with checked absolute paths
inside this repository. No unrelated directories were deleted.

### Acceptance mapping

| Criteria | Evidence / outcome |
| --- | --- |
| A1–A6 | Runtime E003; unit/schema/integration and actual subprocess tests E005 |
| A7 | **UNMET** for -32700/-32600 and malformed-envelope ID; other categories verified |
| A8–A9 | Domain/integration/wire tests verify seeds, Decimal arithmetic, IDs, mutations and atomic failure |
| A10–A11 | Both raw lifecycle subprocess paths verify stdout purity and stderr diagnostics |
| A12–A13 | Connectivity/domain tests pass; full mandatory compliance remains unmet due to four diagnostics |
| A14 | Editable build/install E004; locked sync, lint/format and module/console entry checks E005 |
| A15 | README inspected for setup, examples, tree, matrix, lifecycle, state, exclusions and limitations |

Governance checks E002 are distinct from executable tests. TASK-1 remains BLOCKED.

Final governance verification: executed a PowerShell here-string Python assertion
script checking five nonempty requested files, byte-identical source snapshot,
one registry row per task ID, TASK-1 BLOCKED, unchanged reserved Tasks 2–4, and
presence of final actual results. Exit 0. Re-read the final ledger with
`Get-Content -LiteralPath docs/TASK_LEDGER.md -Encoding UTF8` and inspected
`git status --short`; only new assessment files appear. Corrected two range
labels degraded by Windows shell encoding to plain ASCII hyphens; source
requirements snapshot was not edited. No code changed after E005 test execution.

## E006 — 2026-11-03: Read-only blocker investigation (T1-007, TASK-1)

Working directory: project root; PowerShell; existing local environment. No
package installation, upgrade, source patch or new test file in this session.

| Actual command/action | Actual result |
| --- | --- |
| `Get-Content -LiteralPath AGENTS.md -Encoding UTF8`; same for docs/TASK_LEDGER.md, docs/DECISIONS.md, task1/__main__.py, tests/test_wire.py and pyproject.toml | Read governance and current code/test contract before investigation |
| `git status --short`; `rg --files --hidden` with AGENTS/manual-lab and environment exclusions | New repository files remain untracked; user manual lab files present; no existing commits to compare |
| PowerShell here-string piped to `.\.venv\Scripts\python.exe -`: hashlib/Path manifest plus importlib.metadata/inspect.signature | Baseline SHA256 captured for 18 files; mcp 2.3.0; Server.run has no dispatcher/observer parameter; JSONRPCDispatcher documents on_stream_exception |
| `Get-Content` and `rg -n` on installed mcp/server/{stdio.py,runner.py,lowlevel/server.py}, shared/{jsonrpc_dispatcher.py,message.py,_stream_protocols.py,_context_streams.py} and AnyIO _fileio.py | Confirmed forwarding/drop path, no driver observer injection, first-request era selection, SDK writer/isolation and file-wrapper ownership |
| Read-only Python stdin probe calling public jsonrpc_message_adapter.validate_json(raw, by_name=False) and ValidationError.errors(include_url=False) | Parse failure has json_invalid at root; malformed envelopes have schema errors; root input/ID sometimes available, sometimes absent; boolean ID request accepted as JSONRPCNotification |
| Read-only Python stdin probe comparing the report's original-A/original-B malformed requests | Different valid IDs yielded identical public error-detail lists; universal ID recovery from those lists is impossible |
| Same probe constructing public JSONRPCError/ ErrorData / PARSE_ERROR | Serialized `{"jsonrpc":"2.0","id":null,"error":{"code":-32700,"message":"Parse error"}}` successfully |
| Read-only Python inspect.signature of serve_connection, serve_dual_era_loop and serve_one | Custom dispatcher supported by serve_connection, not dual-era Server.run path; adopting it would require additional lifecycle driver composition |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest` (approved unsandboxed run for Windows named pipes) | Exit 0; **94 passed, 4 xfailed in 20.40s**, no skips |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short` | Exit 1; **4 failed, 94 deselected in 4.38s** |

All strict failures remain the exact missing -32700/-32600 error assertions in
tests/test_wire.py:138, in both legacy and modern modes. No assertions or markers
were changed. The prior E005 counts are historical; the above counts are today's
actual executions. No lint run was needed for documentation-only modifications.

Official web research (read-only): PyPI and GitHub release listings identify
2.3.0 as latest in the checked pages. Inspected current main STDIO/runner and
documented server/dispatcher/message interfaces, migration guide, AnyIO wrappers,
JSON-RPC specification and modern MCP STDIO cancellation. URLs and distinctions
between evidence/inference are in docs/STDIO_BLOCKER_INVESTIGATION.md. No claim
that a new release, private branch or unmerged fix has been tested.

These model/source diagnostics are not an implemented remediation and do not
verify the proposed adapter's cancellation, shutdown, correlation or stdout
behavior. New boundary tests and acceptance commands are a future plan only.

Final integrity verification executed: recomputed the same 18 SHA256 hashes using
a Python stdin script and compared them to the session-start manifest in tool
memory. All 18 matched. This includes all 13 task1/tests Python files, both manual
labs, pyproject.toml, uv.lock and the byte-preserved requirements snapshot.
In particular, tests/test_wire.py and its four XFAIL cases are byte-identical.

Executed a second read-only Python stdin script checking the five changed docs
for nonempty UTF-8 content and trailing whitespace, report A/B/C/--runxfail coverage,
TASK-1 BLOCKED, and unchanged reserved TASK-2/TASK-3/TASK-4 rows. Exit 0, all
assertions passed. Runtime metadata reconfirmed Python 3.12.16, mcp 2.3.0 and
Pydantic 2.12.5. Final `git status --short` remains consistent with the preexisting
untracked project/manual-lab state; hashes provide the implementation evidence.

Completed in this session: T1-007 research criteria R1-R5 only. No remediation
acceptance criterion changed to passing; B3 remains unresolved.

## E007 — 2026-11-03: Controlled Approach C implementation (T1-008)

Working directory: repository root. Python 3.12.16 / MCP 2.3.0 / Pydantic 2.12.5.
User authorized implementation, a recoverable Git baseline, and removal of only
obsolete XFAIL decorators after all assertions pass under --runxfail.

| Executed command/check | Actual result |
| --- | --- |
| `git add -- .gitignore .python-version AGENTS.md README.md docs manual_refund_lab.py manual_validation_lab.py pyproject.toml task1 tests uv.lock`, then `git -c user.name=Codex -c user.email=codex@openai.com commit -m 'Baseline Task 1 before controlled STDIO remediation'` | Exit 0; baseline dfb329b9e91620b3075710bb2466c11ba8703936; 27 existing files preserved; clean status before edits |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest -m sdk_limitation --runxfail --tb=short` | Exit 0; **4 passed, 94 deselected in 6.12s**; original test file untouched |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest tests/test_schemas.py tests/test_service.py tests/test_integration.py tests/test_wire.py -m 'not sdk_limitation'` (approved unsandboxed Windows pipe access) | Exit 0; **94 passed, 4 deselected in 18.81s** |
| Initial `.\.venv\Scripts\python.exe -m ruff check task1 tests` / `ruff format --check task1/stdio_boundary.py task1/__main__.py` | Both exit 0; all checks passed; 2 files formatted |
| `.\.venv\Scripts\python.exe -m ruff format task1/stdio_boundary.py tests/test_stdio_boundary.py tests/test_stdio_boundary_wire.py tests/boundary_server.py tests/wire_support.py` | Exit 0; 4 files reformatted, 1 unchanged; original test_wire.py excluded |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest tests/test_stdio_boundary.py tests/test_stdio_boundary_wire.py --tb=short` (initial sandbox run) | Exit 1; **45 passed, 4 failed, 1 warning in 35.57s** |
| Same new-test command after fixture corrections (approved unsandboxed execution) | Exit 0; **49 passed in 19.32s** |
| `.\.venv\Scripts\python.exe -m ruff format task1/stdio_boundary.py tests/test_stdio_boundary.py` after two added union-fallback cases | Exit 0; 2 files unchanged |
| `.\.venv\Scripts\python.exe -m ruff check task1 tests` and `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | Exit 0 each; all checks passed; 17 files formatted |
| Python stdin assertion comparing tests/test_wire.py to `git show dfb329b:tests/test_wire.py` before cleanup | Entire file byte-identical; SHA256 5e7cbf5f63ab7d79797727b07772b74ae0035365c65628642ba21c5e3916e3d8 |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest --runxfail --tb=short` (approved unsandboxed execution) | Exit 0; **149 passed in 37.19s**, no skips/xfails; original four cases still decorated |
| Code checkpoint commit: `git ... commit -m 'Implement SDK-preserving STDIO error recovery (T1-008)'` | Exit 0; 7b0c79fdda6949e9a18a8919910ae58e9d04360f; code/new tests checkpointed before cleanup |
| Separate cleanup: removed only the one parametrized `@pytest.mark.xfail(...)` decorator in tests/test_wire.py | Original four assertions/bodies unchanged; sdk_limitation marker retained for targeted regression selection |
| Python stdin source comparison / AST function-span comparison after cleanup | Current test_wire.py equals baseline with exactly that decorator removed; original test function bytes identical |
| Python stdin importlib.metadata RECORD/SHA256 verification | All **124 MCP 2.3.0 Python source files** match installed wheel RECORD; no SDK monkeypatch or source modification |
| Post-cleanup Ruff check / format --check | Both exit 0; all checks passed; 17 files formatted |

Initial new-test failures were test fixture issues, not regressions in the 94
ordinary tests: modern custom results include SDK resultType/_meta fields; the
child-output fixture needed explicit DEVNULL stdin/timeout in this Windows setup;
EOF teardown may answer outstanding work under SDK policy and is not an explicit
notifications/cancelled request. The broken-output test's communicate reader on a
closed pipe caused the warning; it was corrected without changing production.
The explicit cancellation tests continue to require no response for the cancelled
ID in either lifecycle mode. No test was skipped, xfailed or weakened to hide an
adapter failure. Production was additionally hardened against invalid-method
requests accepted by the SDK union as a response; two unit cases verify this.

New tests exercise 51 cases, including real SDK parsing with paused error output,
real OS-pipe backpressure (24 large error frames), exact ID/order correlation,
two-frame capture bound, no-opener recovery beyond eight frames, cancellation,
normal EOF with pending work, broken output bounded exit, UTF-8 fragmentation,
notification/response routing, and print/fd/child stdout isolation.

Final post-cleanup execution:

| Executed command/check | Actual result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest --tb=short` (approved unsandboxed Windows subprocess access) | Exit 0; **149 passed in 39.94s**, no failures, skips, XFAIL or XPASS |
| `git add -- tests/test_wire.py`, then cleanup commit | Exit 0; 93a861f7bfd6f49bf40a882753aa376ac4662d0f; exactly 1 file/1 deletion; separate from implementation checkpoint |

### Final TASK-1 acceptance mapping

| Mandatory criteria | Verified evidence |
| --- | --- |
| A1-A4 | Python 3.12 startup/module/console, official SDK, exactly two tools, successful calls and model-derived schemas in original suite, retained in all 149 passes |
| A5-A6 | Original strict schema/business tests and wire -32602/IDs pass unchanged |
| A7 | -32700/null and -32600/reliable IDs pass before/after legacy/modern opening; -32601/-32602/-32603 and business isError remain passing |
| A8-A9 | Deterministic records/refunds, exact Decimal updates, reset-on-restart and failure atomicity pass |
| A10-A11 | Every wire line is JSON-RPC; stderr diagnostics verified; new print/fd/child isolation passes |
| A12-A13 | All 149 unit, SDK integration and subprocess assertions pass normally, including cancellation, ordering, pipe backpressure, EOF and broken-output exit |
| A14 | Existing locked setup/pins retained; module/console still run; final lint and format checks pass |
| A15 | README and investigation/adoption report updated with tree, versions, commands, matrix, architecture and limitations |

Adoption decision: ACCEPT. B3 resolved; TASK-1/T1-003/T1-005/T1-008 DONE.
Initial new-fixture failures are preserved above and resolved; no existing
ordinary-suite regression occurred, so the requested prototype rollback was not
triggered. No SDK, business tools/schemas, dependency pins, manual labs or Tasks
2-4 requirements were changed. Remaining limits are documented in README/ADR-006:
MCP 2.3.0 correlation contract, two-frame (not byte) bound, explicit stdin handle,
existing SDK UTF-8/nonfinite handling and Windows-only verification. Broken-output
test uses communicate(), which closes stdin; bounded exit is verified for broken
stdout plus stdin EOF, not an arbitrary half-open transport. It may exit nonzero.
These do not leave a mandatory assessment criterion unmet.

Final integrity/documentation checks executed via a Python stdin assertion script:
protected business/schema/dependency/manual-lab/requirements paths have no diff
against dfb329b; test_wire.py equals the baseline minus exactly one decorator;
all A1-A15/C1-C7 criteria checked; Tasks 2-4 registry rows equal baseline; all six
changed documentation files are nonempty UTF-8 with no trailing whitespace.
All passed. `git diff --check` exited 0. No production or test code changed after
the 149-pass normal run; final edits were documentation only.

## E008 — 2026-11-04: Task 2 contract and pure guards (T2-001, T2-002)

Scope: task2 isolated project and pure unit-test checkpoint only. No HTTP endpoint,
forwarding, Streamable HTTP, SSE, OAuth/JWT issuance, Tasks 3/4, commit or push.
Task 1 historical entries E001-E007 above are preserved without alteration.

| Executed command/check | Actual result |
| --- | --- |
| Read AGENTS.md, ledger, root configuration, prior decisions/build/evidence; `git status --short`; `git log -3 --oneline` | Clean tree at 6056bc7 before work; protected-file hashes and historical documentation prefixes captured |
| `.\.tools\bin\uv.exe sync --project task2 --extra dev --python 3.12.16 --index-url https://pypi.org/simple` from root | Exit 0; created task2/.venv and task2/uv.lock; 8 isolated packages installed; runtime guards have no third-party dependencies |
| `.\.venv\Scripts\python.exe -m ruff format src tests` from task2 | Exit 0; 6 new files reformatted, 3 unchanged |
| `.\.venv\Scripts\python.exe -m ruff check src tests` from task2 | Exit 0; all checks passed |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2, first run | Exit 0; **156 passed, 1 cache warning in 0.27s**; sandbox denied pytest temporary cache-directory creation |
| `New-Item -ItemType Directory -Path '.cache\pytest\v\cache' -Force` from task2 | Created explicit ignored cache directories to avoid sandbox atomic-cache warning |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2, final run | Exit 0; **156 passed in 0.17s**, no warnings/failures/skips/xfails |
| `.\.venv\Scripts\python.exe -m ruff check src tests` from task2, final | Exit 0; all checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` from task2 | Exit 0; 9 files already formatted |
| Python -B metadata/import-path probe from task2 environment | Python 3.12.16; assessment-task2-proxy 0.1.0; pytest 9.2.0; Ruff 0.17.3; sys.prefix/task2_proxy import resolve exclusively to task2/.venv and task2/src |
| `.\.tools\bin\uv.exe sync --project task2 --locked --extra dev --python 3.12.16 --offline` with task2 cache | Exit 0; resolved/checked 8 packages; locked offline setup works |
| `.\.tools\bin\uv.exe pip check --python task2\.venv\Scripts\python.exe` | Exit 0; all 8 installed packages compatible |

Network installation used approved escalated execution to populate only the new
Task 2 environment/cache. No installation into Task 1's environment, and no
root pyproject.toml/uv.lock edits. FastAPI/HTTPX are intentionally not installed
as unused guard dependencies; their integration remains the later checkpoint.

Verified behavior: missing/invalid/duplicate Bearer credentials; case-insensitive
scheme with case-sensitive tokens; comparison of every candidate; validated,
immutable/redacted configuration; exact literal prefix and denial message/code;
IDs including zero/empty string/large integers/null; no bool/fraction coercion;
duplicate keys at all nesting levels (including escaped spellings); escaped tool
name/selector bypasses; spoofed role claims; strict JSON/UTF-8/nonfinite rejection;
opaque large numeric arguments/extensions and original body preservation;
unsupported batches; notifications inspected/authorized then rejected without
ordinary JSON-RPC replies or forwarding permits; authentication before parsing.

These are pure unit checks, not HTTP integration/wire evidence. There is no
networking code. Actual transparent discovery responses, upstream delivery and
non-delivery must be tested later when a forwarding implementation is authorized.
Task 1's 149-pass result remains historical; it was not rerun or rewritten here.

Preservation verification executed after the above checks: recomputed hashes for
all 31 previously tracked files and compared them with the session-start manifest.
All 27 files outside the four authorized governance records are byte-identical,
including every Task 1 source/test file, root pyproject.toml/uv.lock, README,
AGENTS.md, manual labs and source requirements. Historical decisions/build/evidence
prefixes and the complete Task 1 acceptance section are unchanged. TASK-1/3/4
registry rows and Git HEAD (6056bc7) are unchanged. No commit or push occurred.

Checkpoint acceptance: T2-C1-T2-C9 verified, T2-001/T2-002 DONE. Whole TASK-2
remains IN_PROGRESS. No remaining blocker for this checkpoint. Deferred HTTP
status/notification/upstream/response decisions remain explicitly listed in
task2/CONTRACT.md for review before any endpoint or forwarding implementation.

## E009 — 2026-11-04: Review numeric-exponent correction (T2-002)

Environment: existing isolated task2/.venv; Python 3.12.16. No install/upgrade.
E008's 156-pass baseline and Task 1's historical E007 evidence are unchanged.

| Executed command/check | Actual result |
| --- | --- |
| PowerShell Python stdin diagnostic via `.\.venv\Scripts\python.exe -B -` from task2: print sys.version; invoke inspect_request with the supplied tools/list/id=1/extra=1e999999999999999999999999999999999999999 input; inspect Decimal conversions and context traps | Python 3.12.16; reproduced decimal.InvalidOperation (caught/printed by diagnostic, process exit 0). Positive/negative extreme exponents and zero coefficient raise InvalidOperation; 1e9999 remains finite. This is a reproduction probe, not a passing test |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2 | Exit 0; **186 passed in 0.15s**; no warnings, failures, skips or xfails |
| `.\.venv\Scripts\python.exe -m ruff check src tests` from task2 | Exit 0; all checks passed |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` from task2 | Exit 0; 9 files already formatted |

Added 30 cases exercise unrepresentable positive/negative exponents, negative/zero
coefficients in tool arguments, opaque extensions and IDs, with InvalidOperation
traps both on and off; plus representable extreme/exact values retaining the same
raw-body object. Existing 156 cases remain passing, including strict ID checks,
decoded tool-name authorization and duplicate-key detection. Unrepresentable
numbers now return -32700 / Parse error, null ID; no decimal exception escapes.
Policy and tradeoffs: ADR-010 and task2/CONTRACT.md. No HTTP/wire claim is made.
Task 1 tests were not rerun. Independent re-verification of this fix is pending.

Final read-only preservation check: a Python stdin SHA256 comparison against the
47-file session-start manifest found exactly seven changed files (rpc.py,
test_rpc.py, CONTRACT.md and four governance records). All other 40 files,
including Task 1 and the existing review ZIP, are byte-identical. Session-start
code/test diffs were generated without staging untracked files. HEAD remains
6056bc7; nothing staged. `git diff --check` exited 0 (only Git line-ending
advisories). No commit or push occurred.

## E010 — 2026-11-04: Accepted foundation commit inspection (T2-001/T2-002)

The user confirms independent engineering acceptance, including the Decimal fix.
This records repository inspection, not a new automated test run. Latest test
evidence remains E009: 186 passing cases and both Ruff checks passing.

- Executed `git status --short --untracked-files=all`, `git diff --cached
  --name-status` and `git log -3 --oneline`: initial index empty; HEAD 6056bc7;
  five modified governance records, fifteen new foundation files and review ZIP.
- Added local-only Git info/exclude patterns for task2 review ZIP exports and
  credential-history report files. Executed `git check-ignore` for task2/.venv,
  task2/.cache, .cache, .env, task2/.env, task2_review.zip and the credential-history
  report path: all excluded. No environment/cache/artifact is staged or removed.
- Executed explicit-path `git add` for the 20-file foundation/governance allowlist;
  inspected `git diff --cached --stat`, `--name-status`, documentation diffs and
  `--check`. No unexpected paths or whitespace errors.
- Executed a Python stdin index-content/allowlist/SHA256 inspection: exactly 20
  authorized files; staged content matches the worktree (normalizing Git EOLs);
  targeted private-key/token/credential-URL patterns found no staged matches.
  Reviewed Task 2 source/tests/config/lock are unchanged since session start;
  Task 1 source/tests/root pins and prior evidence prefixes remain unchanged.
- Commit is authorized; no push or T2-003 implementation is authorized. The
  resulting foundation commit is identified by Git history and the session report.

## E011 — 2026-11-04: HTTPX upstream adapter (T2-003)

Baseline e828729b; existing Task 2 Python 3.12.16 environment. Scope is adapter
plus mock-transport integration; no endpoint, real upstream, Task 1 tests or commit.
Prior E001-E010 entries remain historical. No credentials or raw sensitive data
were used; fixtures generate ephemeral synthetic tokens.

| Actual command/check | Actual result |
| --- | --- |
| Read AGENTS/ledger/contract/accepted guards and inspect `git status --short`, `git log -1 --oneline`; Python stdin SHA256 baseline | Clean at e828729b; captured all 46 tracked file hashes |
| Python stdin importlib.metadata probes | HTTPX absent from Task 2; a separate read-only root metadata probe also failed with PackageNotFoundError; no root installation/change |
| `.\.tools\bin\uv.exe sync --project task2 --extra dev --python 3.12.16 --index-url https://pypi.org/simple --offline` from root, task2 UV cache | Exit 1: HTTPX not cached; no satisfiable offline resolution |
| Same sync without --offline, approved escalated network with process-local HTTP/HTTPS/ALL proxy variables cleared | Exit 0; resolved 15 packages; installed HTTPX/transitive dependencies only into task2/.venv; updated only Task 2 lock |
| `.\.venv\Scripts\python.exe -m ruff format src tests` from task2, initial | Exit 0; 2 files reformatted, 9 unchanged |
| `.\.venv\Scripts\python.exe -m ruff check src tests` from task2, initial | Exit 1; three B023 loop-variable captures in new test fixtures; fixed using bound default arguments |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2, first | Exit 1; **295 passed, 1 failed in 0.71s**; unsupported gzip fixture was decompressed during HTTPX Response construction before adapter validation |
| Ruff lint/format after loop-variable fixes | Exit 0 each; all checks passed, 11 files formatted |
| Python stdin inspect.signature/getsource probes of installed HTTPX public AsyncClient.send and Cookies constructor | Verified send-as-is behavior, timeout setup and CookieJar policy retention; no library code changed |
| `.\.venv\Scripts\python.exe -m ruff format src tests` after fixture/concurrency extensions | Exit 0; 1 reformatted, 10 unchanged |
| Full pytest after raw-stream gzip fixture correction and additional proof/concurrency tests | Exit 0; **299 passed in 0.73s**; no warnings/skips/xfails |
| Ruff lint/format at the 299-pass checkpoint | Exit 0 each; all checks passed, 11 files already formatted |
| Locked offline uv sync: `.\.tools\bin\uv.exe sync --project task2 --locked --extra dev --python 3.12.16 --offline` with isolated cache | Exit 0; resolved/checked 15 packages |
| `.\.tools\bin\uv.exe pip check --python task2\.venv\Scripts\python.exe` from root | Exit 0; all 15 installed packages compatible |
| Final `.\.venv\Scripts\python.exe -m pytest -q --tb=short` after timeout-overflow config regression | Exit 0; **300 passed in 0.55s**, no failures/warnings/skips/xfails |
| Final `.\.venv\Scripts\python.exe -m ruff check src tests` | Exit 0; all checks passed |
| Final `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Exit 0; 11 files already formatted |

Installed metadata: Python 3.12.16; HTTPX 0.28.1, httpcore 1.0.9, AnyIO 4.16.0,
certifi 2026.10.23, h11 0.16.0, idna 3.20, pytest 9.2.0, Ruff 0.17.3;
transitive versions are recorded in task2/uv.lock. Original 186 guard cases remain
unchanged and passing; test_upstream.py adds 114 cases.

New coverage: URL/credential/finite-limit configuration, exact request and result/
error bytes/IDs, unfiltered discovery, no inbound header/token leakage, upstream
cookie rejection and safe output headers, all 3xx without follow-up, no application
retry, phase-timeout metadata/failure handling, bounded raw streams, total deadline,
cancellation/close, size limits, malformed/duplicate/error envelopes, strict ID type
matching, fabricated/tampered permits, fixed URLs despite body claims, and concurrent
calls with distinct or repeated IDs across roles and separate upstream credentials.

The one failed test was a fixture-path mismatch: changed the gzip fixture to an
AsyncByteStream so the real adapter sees headers before body handling. No assertions
were weakened or existing guard tests edited. Adapter code additionally validates
extreme timeout configuration without leaking OverflowError. Policy/limits are
documented in ADR-011/012 and task2/CONTRACT.md. These mock checks do not verify
real DNS/TLS/OS socket pooling or real network timeout enforcement; no HTTP endpoint
or full MCP Streamable HTTP compatibility is claimed. Independent review pending.

Final read-only integrity inspection: `git diff --check` exited 0; inspected
`git status --short --untracked-files=all`, diff/stat and index inventory. Python
stdin SHA256 comparison against the 46-file baseline confirms 11 intended tracked
modifications, 35 byte-identical baseline files, and exactly two new adapter/test
files. All Task 1 source/tests/root pins, Task 2's original tests/rpc/settings,
Task 1/3/4 registry rows and historical decision/build/evidence prefixes preserved.
HEAD remains e828729b; nothing staged. No code changed after the 300-pass run;
final edits only document verified outcomes. No commit/push.

## E012 — 2026-11-04: Independently accepted T2-003 Git checkpoint

The user confirms independent engineering approval of T2-003. No tests or Ruff
commands were rerun: reviewed code/tests/dependencies have no unexpected changes.
E011 remains the actual 300-pass/Ruff execution evidence; this is Git inspection.

- Executed Git status, complete tracked diffs, new upstream.py/test_upstream.py
  inspection, index inventory, log and `git rev-list --left-right --count
  origin/main...HEAD`. Initial HEAD e828729b; ahead 1/behind 0; index empty;
  11 modified tracked files, two new code/test files and temporary review ZIP.
- Locally excluded /task2_t2003_review.zip in .git/info/exclude; preserved the
  archive. `git check-ignore` confirms environments, caches, .env paths, both
  review ZIP names and credential-history reports are excluded.
- Staged only the explicit 13-file T2-003 implementation/dependency/governance
  allowlist. Inspected `git diff --cached --stat`, `--name-status`, `--check` and
  protected Task 1 paths. No unexpected paths or whitespace errors; index matches
  worktree with Git EOL normalization. No environments/caches/archives staged.
- Python stdin index-content/allowlist/SHA256/AST inspection passed: reviewed
  source/tests/config/lock/archive byte-identical to session start; no Task 1 or
  original guard-test/rpc/settings changes; authenticate/authorize function bodies
  unchanged; historical governance prefixes preserved. Targeted private-key/token/
  credential-URL scan found no secret candidates, recognizing only the intentional
  invalid user:password URL on the reserved .test domain in a negative test.
- No architecture changes in this checkpoint; ADR-011/012 now ACCEPTED. One
  descriptive milestone commit is authorized, identified by Git history and the
  session report. No push or T2-004 implementation is authorized.

## E013 — 2026-11-04: FastAPI HTTP/ASGI integration (T2-004)

Baseline 0b2e0b7; isolated task2/.venv, Python 3.12.16. No actual socket server was
started, no T2-005 work, no Task 1 test rerun, no commit/push. Prior evidence intact.

| Actual command/check | Actual result |
| --- | --- |
| Read AGENTS/ledger/accepted modules/contracts; `git status --short --untracked-files=all`, `git log -2 --oneline`; Python stdin SHA256 baseline | Clean at 0b2e0b7; captured all 48 tracked file hashes |
| `.\.tools\bin\uv.exe sync --project task2 --extra dev --extra serve --python 3.12.16 --index-url https://pypi.org/simple` from root with isolated cache/runtime settings | Exit 0; approved isolated network install; resolved 27 packages, installed 13 including rebuilt project; no root environment/config changes |
| `.\.venv\Scripts\python.exe -m ruff format src tests` from task2, first | Exit 0; 2 new files reformatted, 11 unchanged |
| `.\.venv\Scripts\python.exe -m ruff check src tests` from task2, first | Exit 1; four new-test issues: two unused imports and two overlong byte literals. Corrected without changing test assertions |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2, first | Exit 0; **397 passed in 2.60s**, no failures/skips/warnings/xfails |
| Ruff lint and `format --check src tests` at first passing suite | Exit 0 each; all checks passed, 13 files already formatted |
| `.\.venv\Scripts\python.exe -m ruff format src tests` after extending distinct-client/ASGI disconnect/reader-failure coverage | Exit 0; 1 new test file reformatted, 12 unchanged |
| Ruff lint after coverage extensions | Exit 0; all checks passed |
| Final `.\.venv\Scripts\python.exe -m pytest -q --tb=short` | Exit 0; **400 passed in 1.88s**; **0 failures, 0 skips, 0 warnings**, no xfails |
| Final `.\.venv\Scripts\python.exe -m ruff check src tests` | Exit 0; all checks passed |
| Final `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Exit 0; 13 files already formatted |
| `.\.tools\bin\uv.exe sync --project task2 --locked --extra dev --extra serve --python 3.12.16 --offline` from root with isolated cache/runtime | Exit 0; resolved/checked 27 packages |
| `.\.tools\bin\uv.exe pip check --python task2\.venv\Scripts\python.exe` from root | Exit 0; all 27 installed packages compatible |
| Python stdin sys.version/importlib.metadata probe | Python 3.12.16, FastAPI 0.162.0, Starlette 1.10.0, HTTPX 0.28.1, asgi-lifespan 2.1.0, Uvicorn 0.54.0, Pydantic 2.14.2, pytest 9.2.0, Ruff 0.17.3 |

New test_app.py adds 100 cases to the unchanged original 300. Tests run actual
FastAPI/Starlette ASGI handling via HTTPX ASGITransport and explicit ASGI lifespan
events via LifespanManager, through the existing guards and adapter into an
instrumented MockTransport. They are ASGI integration, not socket/wire evidence.

Zero-upstream evidence: every local rejection test asserts recorder.requests is
empty: bad/ambiguous credentials, encoded protected names, duplicate JSON keys,
forged role claims, malformed RPC/batches/notifications, methods/paths, media and
encoding failures, framing/length errors, declared/streamed oversize, body deadline,
disconnect and unexpected body-read failure. No body reads occur on bad auth or
declared oversize. Exact-bound chunked requests pass unchanged; crossing the bound
never creates a permit/request. Decimal range failure remains 400/-32700/null.

Concurrent evidence: two ASGI clients with different default credentials send 24
concurrent requests sharing ID=1; 4 viewer admin_ calls return 403 and never reach
upstream, exactly 20 approved calls reach upstream, each returned owner matches its
caller. Accepted error/result bodies and unfiltered discovery retain exact bytes;
inbound cookies/auth/header claims do not replace separate upstream credentials.

Upstream failure tests intentionally record one authorized attempt, controlled
502/504 and -32603/caller ID, no retry or exception/credential disclosure. Unexpected
upstream exceptions produce generic 500/-32603; captured logs/stdout/stderr contain
no secrets. Lifecycle checks show no client before startup, one client across
requests, closure on exceptional exit, startup failure on missing configuration,
and 503 without a running lifespan. All standard service helper exits also verify
transport closure. HTTP contract/limits: task2/CONTRACT.md; decision ADR-013.

No pytest test failed during T2-004. Initial lint failures above are retained as
actual evidence and resolved. The optional Uvicorn local-run command is documented
from official settings; it was not executed to begin socket testing. Independent
engineering review remains PENDING.

Final read-only preservation checks: `git diff --check` exited 0; Git status/diff/
index inventory inspected. Python stdin SHA256/tomllib inspection confirmed exactly
10 intended tracked modifications and two new app/test files, with 38 baseline
files byte-identical. Task 1 source/tests/root pins, all original Task 2 modules/
tests and original locked package versions retained. Historical decision/build/
evidence prefixes and Task 1/3/4 registry rows unchanged; new files have no whitespace
errors or targeted private-key/token-pattern matches. HEAD 0b2e0b7 and empty index
unchanged. No code/test edits after the final 400-pass run; final changes are docs
only. No commit/push or T2-005 work.

## E014 — 2026-11-04: T2-004 independent acceptance and Git checkpoint

Independent evidence reported by the user: engineering review approved T2-004,
the reviewed suite passed 400 tests, and additional security probes confirmed
zero upstream calls for rejected requests. Probe commands/counts/timings were not
provided; these are reported results, not local executions in this checkpoint.
E013 retains the actual local pytest/Ruff record. No tests or Ruff rerun here.

- Read governance/ledger and inspected complete tracked diffs plus new app.py/
  test_app.py. Executed Git status/index inventory/log/ahead-behind checks: initial
  HEAD 0b2e0b7, empty index, 10 modified tracked files, two new app/test files and
  task2_t2004_review.zip; ahead 2/behind 0 versus the existing origin/main ref.
- Added local-only .git/info/exclude entry for task2_t2004_review.zip; archive
  retained. `git check-ignore` confirms virtual environments, caches, .egg-info,
  .env paths, review ZIPs and credential-history reports are excluded.
- Explicit-path staging contains exactly 12 approved implementation/dependency/
  documentation files. `git diff --cached --check` passes; inspected staged stat,
  name/status and protected-path inventory. No unexpected paths/whitespace errors.
- Python stdin allowlist/content/SHA256/tomllib inspection passed: staged content
  matches worktree with Git EOL normalization; accepted code/tests/dependencies and
  review ZIP unchanged since session start; Task 1 and all earlier Task 2 modules/
  tests preserved; original dependency pins and historical record prefixes intact.
  Targeted staged private-key/token/credential-URL scan found no secret candidates.
  No environment, cache, egg-info, credential or review archive is staged.
- Governance changes record acceptance only; ADR-013/HTTP policies and accepted
  implementation are unchanged. One descriptive T2-004 commit is authorized;
  its identity is recorded in Git history and the session report. No push or T2-005.

## E015 — 2026-11-04: Real loopback HTTP wire verification (T2-005)

Baseline be9ddd8, existing Task 2 Python 3.12.16 environment and already installed
Uvicorn 0.54.0/FastAPI 0.162.0/Starlette 1.10.0/HTTPX 0.28.1. No installs or
dependency/lock changes. Tests ran with real loopback TCP in the default sandbox;
no ASGI/HTTPX mock transport in the new wire matrix. No external RPC target.

| Actual command/check | Actual result |
| --- | --- |
| Read AGENTS/ledger/accepted HTTP modules/contracts; Git status/log; pinned-Python SHA256/signature probe | Clean at be9ddd8; 50 tracked hashes captured; public Server.run(sockets=...) confirmed |
| `.\.venv\Scripts\python.exe -m ruff format src tests` from task2, initial | Exit 0; 3 new files reformatted, 13 unchanged |
| `.\.venv\Scripts\python.exe -m ruff check src tests`, initial | Exit 1; one I001 import-order issue in new test file |
| `.\.venv\Scripts\python.exe -m ruff check --fix tests/test_http_wire.py` | Exit 0; one import-order issue fixed, no assertion changes |
| `.\.venv\Scripts\python.exe -m pytest tests/test_http_wire.py -q -x --tb=short`, first | Exit 1; **45 passed, 1 failed in 5.27s**; reserved non-listening endpoint produced 504 at the fixture's 0.5s connect deadline, rather than expected refusal/502 |
| Python stdin direct socket probe via `.\.venv\Scripts\python.exe -B -` | Exit 0; same owned loopback non-listener: 0.5s deadline -> TimeoutError; 3s deadline -> ConnectionRefusedError/WinError 10061, observed 2.032s. Diagnostic only; no duration assertion |
| Intermediate Ruff format/check after fixture connect deadline correction and concurrency gate | Exit 0 each; 16 files unchanged, all checks passed |
| Same wire-only pytest command after fixture correction | Exit 0; **49 passed in 10.98s**, no failures/skips/warnings |
| Ruff format/check after adding method/body-deadline coverage and cleanup summary | Exit 0 each; 2 files reformatted, 14 unchanged; all checks passed |
| Final `.\.venv\Scripts\python.exe -m pytest -q --tb=short` from task2 | Exit 0; **452 passed in 13.14s**, **0 failures, 0 skips, 0 warnings**, no xfails |
| Final `.\.venv\Scripts\python.exe -m ruff check src tests` | Exit 0; all checks passed |
| Final `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Exit 0; 16 files already formatted |
| `Get-Content -Encoding UTF8 .cache/http_wire_summary.json` | 12 children, 0 alive, 0 forced cleanups, 0 live reader threads; ten exits 0, deliberately killed upstream exit 1, invalid-config proxy exit 3 |

First failure was a fixture deadline mismatch, documented in M024 before changing
it. Windows reported actual refusal after about 2s; the production timeout/refusal
policy was correct. Only test configuration changed to 3s connect/4s total. No
production defect/fix, weakened assertion, skipped test or baseline regression.

Process configuration: six independent proxy/peer pairs (12 child processes) in the
full run; dynamic child-owned 127.0.0.1 ports; hidden subprocesses on Windows, clean
minimal child environments, no tokens in argv/files. Proxy runs actual create_app
through public Uvicorn Server.run with its own socket, worker=1, asyncio/h11,
lifespan=on, access_log=False, proxy_headers=False, no reload, 2s graceful shutdown,
1s keepalive. A non-mutating ASGI observer emits lifecycle/request-finished events.
Peer is independent stdlib ThreadingHTTPServer/HTTP1.1/backlog128. Parent clients
use http.client and raw sockets; no fake network transports. Trusted fixture limits
are 4096 bytes, 0.5s body/read (5s read for gated concurrency), 3s connect, 1s
write/pool, total 4s (6s concurrency). Readiness/events 10s, journal predicates 5s,
normal clients 5s/concurrency 7s, stop wait 6s then bounded 2s terminate/kill fallback.

Actual journal evidence:

- 33 dedicated rejection cases each assert exactly zero protocol receipts: auth 7,
  viewer IDs 5, bypass/malformed/invalid-ID/batch 10, notifications 3, oversize 2,
  media/encoding 3, methods 2, body deadline 1. Incomplete client disconnect also
  records zero before a successful recovery request records exactly one.
- Admin protected calls and both ordinary roles succeed; discovery still includes
  admin tools. Request and upstream response/error bytes/IDs/status remain intact;
  length/chunked bodies pass unchanged, forbidden headers/cookies are absent and
  safe downstream headers/framing are observed over TCP.
- Concurrent independent connections share ID=1: 12 requests, 2 viewer denials and
  exactly 10 approved entries simultaneously held in the peer journal, then released
  by control event. Every owner/result matches; upstream credential check succeeds
  and client-token/cookie/role-header flags remain false.
- Slow peer: observed receipt then configured 504 with caller ID, exactly one call
  after gate release. Drop/malformed/redirect: controlled 502 and one call, no retry.
  Process kill: one confirmed receipt before intentional peer termination, controlled
  502. Refusal: actual 502 from unavailable reserved endpoint, zero peer receipts.
- Partial-body disconnect waits for the handler-finished event (attempted 400,
  not a response received by the disconnected client). Body deadline produces actual
  408. Proxy recovers. Startup failure and raised test-body assertion clean up both
  children. Normal proxy teardown includes observed lifespan.shutdown.complete.

Peer control/health calls do not count as protocol requests. Journal bodies are
synthetic and stay in memory; raw auth values are never recorded, only booleans/
header names. Every harness checks child captured output against fixture tokens;
none leaked. The ignored summary contains only child outcome metadata.

Task 1 tests were not rerun: no shared code/environment changed. All prior 400 Task 2
cases remain passing. This is Windows loopback fixture interoperability, not vendor
MCP/TLS/DNS/HTTP2/load/full-session proof. Independent review PENDING; no T2-006,
commit or push. Full boundary/configuration details: task2/CONTRACT.md and ADR-014.

Final read-only integrity check: Python stdin SHA256/tomllib assertions confirm
9 intended tracked modifications, 41 byte-identical baseline files and exactly
3 new test files. Every production module, original Task 2 test, root/Task 1 code,
dependency configuration/lock and historical documentation prefix is preserved;
only pytest markers changed in Task 2 configuration. Task 1/3/4 ledger rows intact.
New files pass whitespace and targeted secret-pattern inspection. Sanitized cached
cleanup metadata matches 12 reaped children/zero live readers or forced cleanup.
`git diff --check` exited 0; HEAD be9ddd8 and empty index unchanged. No source/test
edits after the 452-pass run; final updates are documentation only. No commit/push.

## E016 — 2026-11-04: T2-005 independent acceptance and Git checkpoint

Reported independent evidence from the user: 400 existing tests and 52 wire tests
passed independently; 33 rejection cases enforce zero upstream forwarding; all
12 children reaped without forced cleanup; production/prior tests match T2-004's
review snapshot. Commands/timings were not provided; these are reported results,
not new local executions. E015 remains the actual local pytest/Ruff record. No
test, wire service, or Ruff command was rerun during this Git checkpoint.

- Read governance and inspected complete tracked diffs plus all three new wire
  files. Git status/index/log/ahead-behind initially showed HEAD be9ddd8, empty
  index, 9 modified tracked files, 3 new tests and task2_t2005_review.zip; ahead 3/
  behind 0 versus the local origin/main ref.
- Added local-only info/exclude entry for task2_t2005_review.zip, retaining the
  archive. `git check-ignore` confirms virtual environments, cached cleanup summary,
  egg-info, .env paths, review ZIPs and credential-history reports are excluded.
- Explicit-path staging includes exactly 12 approved wire-test/marker/governance
  files. `git diff --cached --check` passes; stat/name-status/protected-path checks
  show no unexpected paths or whitespace errors. No environment/cache/credentials/
  review archive is staged.
- Python stdin allowlist/content/SHA256/tomllib inspection passed: index matches
  worktree with Git EOL normalization; reviewed wire tests/marker, production/prior
  tests, lock and archive unchanged since session start. Task 1/root dependencies,
  Task 2 dependency/build configuration and historical record prefixes retained.
  Targeted staged private-key/token/credential-URL scan found no secret candidates.
- Only acceptance documentation changed this session; ADR-014's accepted design
  and limits are unchanged. One descriptive T2-005 commit is authorized; identity
  is recorded in Git history/session report. No push or T2-006 scope authorized.
