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

## E017 — 2026-11-04: T2-006 final audit, fresh local execution

Date/timezone: America/Los_Angeles. Baseline aa343b3, main initially clean/index
empty, ahead 4/behind 0 versus existing local origin/main; no fetch. These are
fresh executions, not the user's earlier independent review results.

Both task interpreters report Python 3.12.16, MSC v.1944 64-bit AMD64. Full
installed version inventory and traceability: [TASK2_FINAL_AUDIT.md](TASK2_FINAL_AUDIT.md).
Task 1 MCP 2.3.0/Pydantic 2.12.5; Task 2 HTTPX 0.28.1/FastAPI 0.162.0/Pydantic
2.14.2/Uvicorn 0.54.0. Both pytest 9.2.0/Ruff 0.17.3. Task 2 dev asgi-lifespan
2.1.0; separate root pytest-asyncio 1.4.1.post1. uv 0.13.7.

### Complete regression and static checks

| Cwd | Exact command | Actual result / exit |
| --- | --- | --- |
| Repository root | `.\.venv\Scripts\python.exe -m pytest -q -o cache_dir=.cache/pytest --tb=short` | 149 passed in 38.44s; exit 0 |
| Repository root | `.\.venv\Scripts\python.exe -m ruff check task1 tests` | All checks passed; exit 0 |
| Repository root | `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | 17 files already formatted; exit 0 |
| task2/ | `.\.venv\Scripts\python.exe -m pytest -q --tb=short` | 452 passed in 13.87s; exit 0 |
| task2/ | `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed; exit 0 |
| task2/ | `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 16 files already formatted; exit 0 |

Both suites: zero failures/skips/warnings/xfails. Task 1 executes outside the
Windows sandbox for official MCP named-pipe access. Task 2 includes all 400 prior
and 52 wire cases, not 452 plus another 52. No tests/markers/assertions changed.

Read-only Python/JSON inspection of task2/.cache/http_wire_summary.json: 12 child
processes, zero alive/forced cleanups/live reader threads; ten normal exits 0,
intentional killed peer 1, invalid-config proxy 3. All 33 dedicated local rejection
cases journal zero protocol calls. Concurrent repeated IDs remain isolated: two
denials, ten approved held calls across 12 independent clients. Process settings,
failure/journal assertions and exclusions remain ADR-014/CONTRACT.md.

### Installation/import and CLI probes (not additional pytest passes)

From repository root, actual successful clean-install command and environment:

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) 'task2/.cache/uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.runtime'
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) 'task2/.cache/t2006-venv'
.\.tools\bin\uv.exe sync --locked --offline --project task2 --extra dev --extra serve --python 3.12.16
```

Exit 0; built editable assessment-task2-proxy and installed 27 packages into this
new ignored environment, not either accepted task environment. Python stdin
importlib.metadata/tomllib assertions with `.\.cache\t2006-venv\Scripts\python.exe -`
from task2/: all 27 versions exactly match uv.lock; app/security/upstream imports
succeed; Task 1 distribution absent. The original task2/.venv import probe also
passes and has no Task 1 distribution. Root-cwd metadata initially sees root local
egg-info through sys.path; checking from task2/ resolves this harmless cwd artifact.

```powershell
# From task2/
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache/uv'
..\.tools\bin\uv.exe pip check --python .cache/t2006-venv/Scripts/python.exe
```

Exit 0; 27 packages checked, all compatible. Initial setup diagnostics: `Get-Command
uv` found no global uv; repository `.tools/bin/uv.exe --version` succeeded. First
offline sync using root .cache exited 1 (missing cached Pydantic wheel); second
using task2/.cache/uv exited 1 (Windows sandbox denied setuptools temporary egg-info).
Same sync outside sandbox succeeded offline. Initial pip check with default user
cache printed access-denied; explicit writable cache rerun above exited 0. These
are recorded setup/environment failures, not passing tests or production defects.

Python stdin audit probe through fresh `.\.cache\t2006-venv\Scripts\python.exe -`
executes Uvicorn module CLI using runpy and arguments:
`task2_proxy.app:create_app --factory --host 127.0.0.1 --port 0 --no-access-log`.
A daemon stdin supervisor raises SIGINT for graceful hidden Windows shutdown;
no ASGI app wrapper/injected transport/settings. Actual defaults/environment loaders
run. Separate existing stdlib test peer binds 127.0.0.1:0. Ephemeral random inbound,
upstream and peer-control credentials exist only in process env/memory.

- Missing credential 401 and protected viewer 403 preserve expected challenge and
  -32001/exact Unauthorized Tool Call/id=audit-deny. Journal remains exactly empty.
- Viewer tools/list (including admin definitions), admin admin_reset, admin/viewer
  read each 200; exactly four entries match original request/response bytes and
  upstream auth, with no client-token/cookie/spoofed-role presence.
- Startup/shutdown complete; CLI and peer exit 0, zero forced cleanup/live readers,
  zero captured credential leaks. Probe exit 0. Six manual smoke cases are not added
  to the 452 pytest count. Port 0 replaces documented port 8000 only for isolation.
- Sanitized probe summaries/version metadata remain ignored cache artifacts, not
  required submission evidence or stored journals/credentials.

### Security/publication and preservation inspection

Python stdin subprocess/regex scan of `git rev-list --objects --all` and `git
cat-file` inspected 98 unique reachable blobs across nine commits, plus current
tracked files. Private-key/provider-token/credential-assignment/Bearer/credential-URL
patterns produced 16 path/rule/fingerprint groups; context review classified all
as descriptive text or invalid synthetic test credentials/URLs. No actual secret
or sensitive customer-data finding. No raw secret candidates printed. This is a
scoped inspection, not an external secret-scanner/CVE certification.

`git ls-files`, historical path inventory, `git status --short --ignored`, `git
check-ignore -v` and remote URL inspection show no tracked environment/cache/egg-info/
ZIP/.env/private-key/generated artifact or embedded remote credential. ZIP/report
rules are local info/exclude, not portable .gitignore; publication precaution is
documented. Ignored-tree enumeration warned about inaccessible stale sandbox cache
directories; all tracked files/reachable blobs were still inspected. No deletion.

Read-only SHA256 baseline and `git diff --exit-code 6056bc7 HEAD -- task1 tests
pyproject.toml uv.lock .python-version manual_refund_lab.py manual_validation_lab.py`
exit 0 verify published Task 1 preservation. Final tracked hash/diff/index checks
are required after documentation updates. No source/test/dependency/configuration
change, commit/push or Task 3/4 work; Task 2 final independent audit review PENDING.

New README reviewer command executed after the full run, from task2/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py -k 'authorized_calls_preserve_request_and_response_bytes or discovery_is_transparent_including_admin_tools or viewer_denial_preserves_id_and_zero_journal'
```

Exit 0: **10 passed, 42 deselected in 1.51s**, no failures/skips/warnings. This
subset verifies the newly documented command, not a replacement for the 452-case
full run; deselected cases are not skips. The cached summary is regenerated by
each invocation, so the 12-child full-run result above was read before this subset.
Python stdin documentation checks exit 0: local Markdown links resolve; every
explicit matrix test reference exists in AST; embedded README client code compiles
(syntax check, not a second execution of that exact client snippet). CLI smoke
evidence above exercises the same discovery/denial behavior with an ephemeral port.
`git diff --check` exits 0; Git emits only LF/CRLF conversion advisories, distinct
from the zero pytest warnings. No accepted implementation/test changes followed.

Final Python stdin SHA256/allowlist/history-prefix assertions exit 0: 44 of 53
baseline files byte-identical; exactly nine tracked documentation modifications
and one new docs/TASK2_FINAL_AUDIT.md. Every accepted source/test/configuration/
dependency/lock/manual-lab file is unchanged; historical build/decision/evidence/
requirements prefixes retained. HEAD aa343b3 unchanged, index empty, ahead 4/behind
0 local origin/main. Current 54 submission files pass targeted provider-key/private-
key rescan. Full tracked diff reviewed; local-link/test-reference checks passed.
Latest README subset cleanup separately reports two children, both exit 0, zero
alive/forced cleanup/live readers; this does not replace the full run's 12-child
evidence. No production defect or unresolved implementation blocker discovered.

## E018 — 2026-11-04: T2-006 independent acceptance and final Git checkpoint

Reported independent evidence from the user: final verdict APPROVED; Task 2 is
assessment-ready within documented requirements. All eight traceability rows,
references to previously reviewed source/tests, final evidence and submission
documentation were reviewed and found consistent. No new execution commands,
versions or timings were supplied with this review; none are invented here.
E017 remains the actual local 452 Task 2/149 Task 1 and Ruff execution record.
No pytest/Ruff/install/service probes rerun during this documentation checkpoint.

- Read governance, ledger, audit report and current docs. Initial Git status/diff/
  index/log/count inspection: HEAD aa343b3, nine modified tracked docs, new audit
  report, untracked task2_final_audit_review.zip, empty index, ahead 4/behind 0 local
  origin/main. No fetch or live remote-state claim.
- Python stdin SHA256/allowlist assertions confirm only the expected documentation
  differs from HEAD; captured 53 tracked-file hashes, new report and archive hash.
  Added local-only info/exclude entry for the review ZIP; retained its bytes.
- Record independent acceptance and DONE statuses in current docs; preserve actual
  E017 commands/results, original requirements and accepted architecture/limitations.
  Stage only ten approved documentation files; no implementation/tests/configuration/
  dependencies/lockfiles or local environments/caches/credentials/generated artifacts.
- One descriptive final documentation/acceptance commit authorized; no push, test
  rerun or Tasks 3/4. Staged inspection and resulting commit identity are recorded
  below/in Git history, separately from historical automated verification.
- Actual staged inspections: Python stdin SHA256/allowlist/history-prefix/link/
  status assertions pass; exactly ten documentation files, staged bytes match
  worktree with Git EOL normalization. All protected source/tests/config/dependency/
  lockfiles and retained review ZIP unchanged. Targeted staged private-key/provider-
  token/credential-URL patterns find zero candidates; no local artifacts staged.
- git diff --cached --check exits 0. Reviewed complete diff, staged stat/name-status
  and final audit report; no unexpected changes. No test/Ruff rerun needed or made.
  Proceed with the one approved documentation commit; resulting identity/inventory
  is the Git source-of-truth record and final session report. No push.

## E019 — 2026-11-04: T4-001 design/runtime inspection, not test verification

Date/timezone: America/Los_Angeles. Read governance/ledger/decisions, inspected
clean Git state at 6904b1f; captured 54 tracked-file hashes before documentation
edits. User authorizes T4-001 docs/design only; no implementation or installations.

Actual metadata probe from repository root:

```powershell
@'
import sys,sqlite3,json
print(json.dumps({'python':sys.version,'sqlite_runtime':sqlite3.sqlite_version,'threadsafety':sqlite3.threadsafety,'probe':'import metadata only; no database opened'},indent=2))
'@ | .\.venv\Scripts\python.exe -
```

Exit 0: CPython 3.12.16 (MSC v.1944 Windows AMD64); SQLite runtime **3.53.1**;
threadsafety **3**. No sqlite3.connect call, database file, WAL PRAGMA, transaction
or concurrency test. The interpreter belongs to existing Task 1; it was not changed
and is not a new Task 4 environment. Re-probe the eventual isolated environment.

Read official SQLite transaction/WAL/synchronization documentation, including the
documented WAL-reset fix in 3.51.3/later and backports. These support proposed
WAL/FULL on verified local storage, not a claimed DB runtime verification pass.
References and chosen/alternative designs: ADR-016 and TASK4_REQUIREMENTS.md.

No pytest/Ruff/install/provider/service command executed. Task 1's 149 and Task 2's
452 passing counts remain historical E017 evidence, not rerun T4 results. Planned
T4-Q1-Q12 cases are NOT EXECUTED. T4-001 independent design review PENDING.

Actual documentation verification: Python stdin SHA256/allowlist/history-prefix/
ledger-row/local-link/contract-ID assertions exited 0. Exactly five tracked docs
changed and one new docs/TASK4_REQUIREMENTS.md; 49 of 54 baseline files byte-identical.
All Task 1/2 source/tests/dependencies/locks and Task 1/2/3 ledger rows preserved;
prior decision/build/evidence content retained as exact text prefixes. No task4/
source directory created. HEAD 6904b1f unchanged; index empty. git diff --check
exited 0. These are read-only documentation checks, not application test results.

## E020 — 2026-11-04: T4-002 isolated project and pure accounting verification

Date/timezone: America/Los_Angeles; HEAD 6904b1f. User reports independent T4-001
architecture APPROVED WITH CONDITIONS and authorizes T4-002 after finalizing P1-P4.
That review is reported evidence, not a new execution. Policies/ADR-016 now distinguish
engineering assumptions from R1-R7; ADR-017 records the pure implementation boundary.
Captured 55 existing file hashes including untracked prior Task 4 requirements.

### Locked installation and environment probes

Actual commands from repository root (uv 0.13.7):

```powershell
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path (Get-Location) '.runtime'
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location) 'task4/.venv'
.\.tools\bin\uv.exe --version
.\.tools\bin\uv.exe lock --offline --project task4 --python 3.12.16
.\.tools\bin\uv.exe sync --locked --offline --project task4 --extra dev --python 3.12.16
```

Exit 0 for each: eight packages resolved/installed, editable project built. Sync
executed outside Windows sandbox due the previously observed setuptools temporary
directory permission constraint; no installation failure occurred this checkpoint.
No root/Task 2 environment sync or dependency/lock change.

Task 4 interpreter: Python 3.12.16 (MSC v.1944 64-bit AMD64). importlib.metadata/
tomllib stdin assertions through `.\.venv\Scripts\python.exe -` from task4 exit 0:
all eight installed distribution versions exactly equal task4/uv.lock selections;
models/accounting import from task4/src/task4_limiter. No mcp/httpx/FastAPI installed.
sqlite3.sqlite_version is 3.53.1 (metadata only; no DB connection/operation).

| Installed distribution | Version |
| --- | --- |
| assessment-task4-accounting | 0.1.0 |
| colorama | 0.4.6 |
| iniconfig | 2.3.1 |
| packaging | 26.3 |
| pluggy | 1.7.0 |
| pygments | 2.21.0 |
| pytest | 9.2.0 |
| ruff | 0.17.3 |

Setuptools 82.0.1 is pinned isolated build tooling, not a runtime distribution.
From task4, `$env:UV_CACHE_DIR = Join-Path (Get-Location) '../.cache'` then
`..\.tools\bin\uv.exe pip check --python .venv/Scripts/python.exe`: exit 0,
eight packages checked, all compatible.

### Actual tests and Ruff (cwd task4/)

| Command / context | Actual outcome | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m ruff format src tests` | Two test files reformatted, three files unchanged | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short` (sandbox) | 169 passed in 0.13s; ONE PytestCacheWarning, WinError 5 creating nodeids cache temporary directory | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Five files already formatted | 0 |
| Same pytest command outside sandbox | **169 passed in 0.12s**, zero failures/skips/warnings/xfails | 0 |

The warning justified the identical rerun; no test assertions, markers, cache
configuration or warning filters were changed. No implementation/test changes
after Ruff checks/final test run; subsequent edits are documentation only.

### Verified scope and limits

- T4-Q1/Q2 arithmetic: 49,999/50,000/50,001 combined capacity, weighted expiration,
  exact lower-excluded/upper-included 60s boundary, no fixed-minute reset, immutable
  primary+backup plans, invalid/missing/zero/overflow bounds and exact integer checks.
- T4-Q3 pure tenant-ID isolation only: exact opaque IDs, independent same entry names;
  no API-key authenticator/HMAC resolver, secret provisioning or restart verification.
- Conservative reservations: all old holds remain counted, both-state/duplicate IDs
  rejected (even expired settled IDs), future target timestamps/watermark regression
  fail closed, known zero differs from unknown holds, existing overage denies new work.
- Pure snapshot projections demonstrate original timestamp after settlement and
  conservative unknown charges; no settlement/recovery operation is implemented.
  Generators/permutations/repeated evaluations preserve input state and make no
  concurrent-admission guarantee. Model/counter names do not prove real token bounds.
- No SQLite persistence/transactions/concurrency, provider APIs/fallback/timeout
  execution, HTTP endpoints or crash-recovery infrastructure tested or implemented.
  Those remain later checkpoints; no new Task 1/2 pass claim or rerun.

T4-002 independent review PENDING. TASK-4 IN_PROGRESS, no T4-003, commit or push.

Final read-only integrity checks: Python stdin SHA256/allowlist/AST/link assertions
exit 0; 49 of 55 existing-file baselines unchanged, six intended governance/contract
docs modified, nine new Task 4 project/source/test files. All accepted Task 1/2
source/tests/configuration/dependency/lock files and completed-task ledger rows
remain byte-identical/unchanged; historical build/test evidence prefixes retained.
Source imports are limited to dataclasses, enum, collections.abc, typing and the
local models module. Targeted new-file private-key/provider-token/credential-URL
inspection finds no candidates. git diff --check exits 0; check-ignore confirms
Task 4 environment/cache/egg-info excluded. HEAD 6904b1f and empty index unchanged;
only intended docs/task4 paths are uncommitted. No application changes after checks.

## E021 - 2026-11-04: T4-002 independent acceptance and foundation Git checkpoint

Reported independent evidence supplied by the user: T4-002 APPROVED; 169 existing
unit tests, 12,000 additional randomized differential accounting checks and six
additional targeted invariants passed; no blocking defect. Review commands/seeds/
versions/timings were not supplied and are not invented. Ruff checks are supported
by previously recorded Codex E020 pinned-environment results, not a new reported
independent execution. No pytest/Ruff/install/provider/DB commands run here.

- Read AGENTS/ledger/decisions/contract/project README and inspect status/diff/index/
  log/counts. Initial HEAD 6904b1f, empty index, five modified tracked docs, new
  requirements/nine project files and review ZIP; ahead 0/behind 0 local origin/main.
- Capture SHA256 baseline for 65 existing tracked/untracked files, retaining the
  archive. Add local-only info/exclude rule for task4_t4002_review.zip; no deletion.
- Update acceptance records only. T4-001 and T4-002 are DONE/accepted; whole TASK-4
  IN_PROGRESS. Original acceptance contract, P1-P4, approved accounting logic/tests/
  project configuration/lock and Tasks 1/2 remain unchanged. No T4-003 authorization.
- One descriptive commit of exactly 15 approved Task 4/project/requirements/governance
  files is authorized. Exclude environments/cache/bytecode/egg-info/credentials/ZIPs.
  Staged preservation/content/whitespace evidence follows; identity is recorded by
  Git and the final session report. No push or new implementation.
- Actual Python stdin SHA256/allowlist/link/history-prefix/tomllib checks exit 0:
  seven acceptance docs changed this session, 58 baseline files (including all
  accepted code/tests/config/locks and ZIP) unchanged; eight lock selections retained.
  Completed-task rows and historical execution prefixes preserved; local links valid.
- Explicit staging yields exactly 15 approved paths (five modified tracked docs,
  new requirements and nine Task 4 files). Staged content matches worktree after
  Git EOL normalization. Full content/diff/stat/name-status inspected; no unignored
  leftovers, unexpected paths or targeted private-key/provider-token/credential-URL
  candidates. check-ignore confirms environments, bytecode, egg-info, cache, .env,
  credential-history reports and retained review ZIP excluded.
- git diff --cached --check exits 0. LF/CRLF conversion advisories are Git notices,
  not test results or source edits. No tests/Ruff rerun. Create the one authorized
  foundation commit, then verify its parent/inventory/clean status/branch counts;
  identity is recorded in Git history and final report. No push/T4-003.

## E022 - 2026-11-04: T4-003 atomic SQLite storage verification

Timezone America/Los_Angeles; accepted HEAD 3d8d3e5. Initial clean working tree,
ahead 1/behind 0 local origin/main. Captured SHA256 of 64 tracked files before
edits. User authorizes SQLite storage/concurrency only, preserving 169 accepted
tests/models/accounting and Tasks 1/2. No provider/HTTP or T4-004, commit/push.

### Runtime/storage inspection (not tests)

Root Python stdin probe of sys.version/sqlite3.sqlite_version and Win32
GetVolumePathNameW/GetDriveTypeW exited 0: Python 3.12.16, SQLite 3.53.1, workspace
volume S: type 3 (DRIVE_FIXED). Task 4 interpreter independently reports Python
3.12.16 (MSC v.1944 AMD64)/SQLite 3.53.1/pytest 9.2.0/Ruff 0.17.3. Standard-library
sqlite3 only; no dependency installation or pyproject/lock/environment change.
Official SQLite transaction/WAL and Python 3.12 autocommit documentation inspected;
source enforces runtime/local-volume checks before WAL and verifies connection
PRAGMAs. Other operating systems/network volumes fail closed, not claimed supported.

### Actual commands (cwd task4/)

| Command / stage | Actual outcome | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m ruff format src/task4_limiter/storage.py tests/storage_support.py tests/test_storage.py tests/test_storage_processes.py` | Four new files formatted | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` initial | 26 new-test fixture-shadowing/import/unused-import errors; no accepted-source changes | 1 |
| `.\.venv\Scripts\python.exe -m ruff check --fix src/task4_limiter/storage.py tests/conftest.py tests/storage_support.py tests/test_storage.py tests/test_storage_processes.py` after explicit fixture correction | Two remaining import issues fixed, zero remaining | 0 |
| `.\.venv\Scripts\python.exe -m ruff format src/task4_limiter/storage.py tests/conftest.py tests/storage_support.py tests/test_storage.py tests/test_storage_processes.py` | Five files unchanged | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4003-01` | 214 passed in 2.47s; zero failures/skips/warnings/xfails | 0 |
| Same scoped Ruff format command after adding transaction/race coverage | Three files formatted, two unchanged | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` after additional tests | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4003-02` expanded coverage | 221 passed in 3.46s, zero failures/skips/warnings/xfails | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` final | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` final | 10 files already formatted | 0 |
| Same two Ruff check commands after direct FK/PK assertions | All lint checks pass; 10 files already formatted | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4003-03` final | **221 passed in 3.37s**, **zero failures/skips/warnings/xfails** | 0 |

All three pytest invocations execute outside Windows sandbox for actual local SQLite
WAL/temp-file locks and spawned-process operation. All DBs stay in dedicated ignored
task4/.cache/t4003-01, t4003-02 or t4003-03 directories, never external services. Initial
lint-only failure was corrected in new test setup/imports; no tests were weakened,
skipped or warnings hidden. All actual pytest runs passed. Final total includes
169 accepted cases plus 52 new storage/process cases; no code/test edits afterward.

### Transaction, persistence and process evidence

- Runtime unit guards reject old SQLite/local-storage verification failure before
  file creation; actual connections show WAL, synchronous=2/FULL, foreign_keys=1,
  busy_timeout=1000. Strict integer/terminal-null/FK/unique constraints and indexes
  inspected/exercised; no raw tenant key or identity secret found in fixture DB/WAL
  bytes. Only HMAC identities/verifier/internal UUIDs/accounting fields are persisted.
- 49,999/50,000 admit and 50,001 rejects without inserted request/attempt rows;
  primary+backup demand and separate tenant budgets verified. Weighted actual DB
  expiration at 59,999/60,000/60,001 and later boundaries matches accepted pure math.
  Unknown/old holds stay counted; late known settlement keeps original admission time.
- Writer-lock observation from independent observer connections proves both injected
  clock sample and accepted pure decision execute while BEGIN IMMEDIATE is held:
  observer BEGIN IMMEDIATE returns SQLITE_BUSY, reads no uncommitted reservations;
  after successful return observer sees one committed request/two attempts.
- SQLite trigger abort on backup insert rolls back request/first attempt/watermark.
  Public SQLite authorizer denial of COMMIT returns controlled failure and no rows.
  Settlement abort preserves original started hold; later identical retry charges
  once. Held writer lock gives controlled BUSY with 20 ms configured policy and no
  timing-based assertion; after rollback the same UUID can be admitted safely.
- Known/unknown settlement and unused-release idempotence/conflicts tested; repeated
  starts/parallel-intent ordering/stale recovered rows rejected. Missing DB is not
  recreated by an existing store. Bound breach persists a tenant block and retains
  quota across reopen. Raw input never appears in generic StorageError strings.
- Reopen preserves unresolved holds beyond original 60s window and does not clear
  another owner's reservations. Identity/schema/policy verifier is checked before
  work; wrong identity and clock rollback fail. Deadline recovery occurs once,
  keeps full remaining bounds at deadline timestamp, preserves already settled
  timestamps, rejects old workers and expires those explicit charges 60s later.
- Five synchronized threads compete for final 2,000 tokens after 48,000: one win,
  four denials; usage 50,000. No process-local lock guards admission.
- Six real spawn processes (context Barrier, bounded 20/25s waits, one shared local
  DB) compete for that final 2,000: **one win/five denials**, committed **two requests,
  four attempts and 50,000 bound tokens** including seed. No successful admission
  without committed rows. Duplicate-ID race: three processes, one insert/two
  DUPLICATE results, one request/two attempts/2,000 reserved.
- Two same-settlement processes both acknowledge 123 but charge once (1,123 including
  backup hold). Two conflicting settlements yield one winning charge/one CONFLICT,
  no second charge. Independent writer process commits primary 123/backup hold 1,000;
  exits; separate reader process sees 1,123 and parent reopen sees same states.
- Read sanitized .cache/sqlite_process_summary.json after the final run: **15 children, zero alive,
  zero forced cleanup, every exit 0**. Processes are joined/closed in finally,
  queue closed/joined; summary contains no keys/journals/customer data. No reliable-
  sleep timing assertions or provider/network calls.

### Scope and remaining verification boundaries

Storage APIs only persist intent/accounting, not provider routing or cancellation.
Clock/local storage/identity provisioning are trusted operational inputs. Windows
fixed-local-volume detector only; single-writer overhead, initial bootstrap BUSY,
no pruning/unblock API and ambiguous commit/remote billing limits are documented.
Synchronous APIs require future async offload/drain. No public HTTP error behavior,
actual model/tokenizer proof, provider/fallback/timeout, power-loss/hardware or final
system fault-audit claim. Accepted Task 1/2/Task 4 pure source/tests/pins unchanged;
Task 1/2 suites not rerun because shared code/environment were not affected.
T4-003 independent acceptance PENDING, TASK-4 IN_PROGRESS. Stop before T4-004.

Final constraint review added direct foreign-key and duplicate-primary-key rejection
assertions to the existing schema test, then reran both Ruff checks/full suite above.
No accepted file changed; no assertion was removed/weakened. Cached process summaries
are regenerated per pytest invocation; the reported 15-child result is the final
221-case run, not a sum across repeated runs. Final edits afterward are docs only.

Final Python stdin SHA256/allowlist/ledger-row/history-prefix/link assertions exit 0:
57 of 64 existing tracked files byte-identical; exactly seven intended docs modified
and five new storage/test files. All accepted models/calculations/tests, Task 1/2
source/tests/configuration/dependencies/locks and accepted-task ledger rows unchanged.
Prior decisions/build/test records retained as exact prefixes. Local links valid,
targeted new-file private-key/provider-token scan clear. git diff --check exits 0;
test DB/process artifacts ignored. HEAD 3d8d3e5 unchanged, empty index, no commit/push.
Final process summary rechecked: 15 children/all exit 0/zero alive or forced cleanup.
No application/test edits after the final 221-pass run. Stop for independent review.

## E023 - 2026-11-04: T4-003 qualified independent acceptance and Git checkpoint

Reported independent evidence supplied by the user: T4-003 APPROVED within the
documented Windows fixed-local-drive/supported SQLite runtime. All 221 tests passed
in an isolated Linux review copy using a TEST-ONLY compatibility shim for unsupported
platform/SQLite gates. All 15 spawned children exited normally, zero forced cleanup.
Three additional scenarios passed: ten-thread admission, tenant isolation, exact
deadline-anchored recovery boundaries. No blocking source defect identified.

This is reported review, NOT new local execution or native Windows verification.
Review commands, Python/SQLite versions, shim implementation and timings were not
supplied and are not invented. No native Linux support/gate validation is claimed.
E022 native Windows/SQLite 3.53.1 test/Ruff evidence remains authoritative for the
supported platform. No compatibility shim, gate bypass or implementation change
is introduced in this repository. No pytest/Ruff/install/DB/provider command run here.

- Read governance/ledger/current contract/decisions/README; inspect status/diff/index/
  log/counts. Initial HEAD 3d8d3e5, empty index, seven tracked docs/five new Python
  source/test files and review ZIP; ahead 1/behind 0 existing local origin/main.
- Capture SHA256 of 70 tracked/untracked files. Retain review ZIP byte-for-byte and
  add local-only info/exclude entry; no deletion or global ignore/configuration edits.
- Record qualified acceptance without replacing E022. T4-003 DONE/ACCEPTED, TASK-4
  IN_PROGRESS; T4-004 not authorized. Preserve all accepted accounting/storage,
  tests/dependencies/locks, original policies and Tasks 1/2. One descriptive storage
  milestone commit authorized, no push. Actual staged inspection evidence follows.
- Actual read-only SHA256/allowlist/link/prefix/ledger-policy checks pass: seven
  acceptance docs changed this session, 63 baseline files including accepted source/
  tests/pins/archive unchanged. Original P1-P4/requirements and prior task rows remain
  intact; E022/build history prefix hashes preserved with EOL normalization. Source
  runtime/Windows gates unchanged; no review compatibility shim added.
- An initial optional cached-DB inventory probe raised StopIteration because no
  cached .sqlite3 remained at that location. Corrected inventory checks ignore rules
  for DB/WAL/SHM paths without creating/opening a database; final checks exit 0.
  This was an inspection-helper issue, not a source/test failure or new execution.
- Explicit staging contains exactly 12 approved paths: seven documentation files,
  storage.py and four test/support files. Full content/diff/stat/name-status reviewed;
  index matches worktree, no unexpected/unstaged/unignored leftovers. Targeted staged
  private-key/provider-token/credential-URL scan finds zero candidates. check-ignore
  verifies DB/WAL/SHM, environments, cache and retained archive exclusions.
- git diff --cached --check exits 0. Git LF/CRLF advisories are not source changes
  or test warnings. No test/Ruff/native/shim run performed. Create one descriptive
  milestone commit; verify parent/manifest/clean tree/branch status. Git history and
  final report record identity. No push, Tasks 1/2 changes or T4-004 implementation.

## E024 - 2026-11-04: T4-004 native orchestration verification

America/Los_Angeles (clock probe 2026-11-05 04:29:22 UTC = Nov 4 locally).
Starting HEAD ebc226a5eda6f9bb31927eb760abf7cd3b04a6e1, clean tree, empty index;
main ahead 2/behind 0 recorded origin/main. Captured SHA256 of 69 tracked files
in ignored .cache/t4004_baseline.json. Only seven relevant docs may change among
those files; all accepted code/tests/configuration/locks must remain identical.
No dependency installation, commit, push, HTTP or T4-005 implementation.

### Runtime inspection (not tests)

Task 4 interpreter command (cwd task4/):

```powershell
.\.venv\Scripts\python.exe -c "import sys,sqlite3,importlib.metadata as m; print(sys.version); print('SQLite',sqlite3.sqlite_version); print('pytest',m.version('pytest')); print('ruff',m.version('ruff'))"
```

Exit 0: Python 3.12.16 (main, Oct 26 2026, 14:10:56), MSC v.1944 64-bit AMD64;
SQLite 3.53.1; pytest 9.2.0; Ruff 0.17.3. Existing standard-library runtime and
pinned dev environment reused unchanged. Native Windows fixed-local-drive gates
remain enabled in unchanged storage.py; no Linux/platform compatibility shim.

### Commands actually executed (cwd task4/)

| Command / stage | Actual outcome | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m ruff format src/task4_limiter/providers.py src/task4_limiter/service.py tests/orchestration_support.py tests/test_service.py tests/test_providers.py` initial | Four files formatted; one unchanged | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` initial | Two new-test issues: default-constructor B008 and unused-import F401; corrected without touching accepted files | 1 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_service.py tests/test_providers.py --tb=short --basetemp=.cache/t4004-dev` sandbox | Setup errors and session-finish WinError 5 on pytest temp-directory access; aborted, no valid passing-suite summary claimed | 1 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_service.py tests/test_providers.py --tb=short --basetemp=.cache/t4004-dev-native` native | 85 passed in 2.03s | 0 |
| Same scoped Ruff format command after additional tests | Two formatted, three unchanged | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` expanded | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4004-full-01` native | 318 passed in 6.74s | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4004-full-02` native | 323 passed in 7.24s | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` expanded final candidates | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` expanded final candidates | One new test file needed formatting; 14 already formatted | 1 |
| Same scoped Ruff format command after final review refinement | Two formatted, three unchanged | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4004-final` earlier final candidate | 323 passed in 7.28s | 0 |
| `.\.venv\Scripts\python.exe -m ruff format src/task4_limiter/service.py tests/test_service.py` after close-failure ownership refinement | One formatted, one unchanged | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4004-final-ownership` final native | **324 passed in 7.24s**, zero failures/skips/warnings/xfails | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` final | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` final | **15 files already formatted** | 0 |

Native pytest calls used authorized execution outside sandbox restrictions for
actual local SQLite files/locks and spawned Windows processes, as E022 did. No
tests were weakened, filtered or skipped to obtain the final results. Earlier
failures are inspection/environment/format findings above, not hidden passes.
No accepted source/test was edited. All 221 accepted tests plus 103 new pass.

### Verified behavior / test references

- Q6/Q9: test_primary_success_releases_backup_and_preserves_admission,
  test_primary_429_exactly_one_backup_after_cleanup (known/unknown/zero usage),
  test_local_quota_denial_zero_provider_calls: no quota-bypassing fallback,
  exactly one authorized backup after primary 429, ordered primary finish/close
  before backup start, exact charge and admission timestamps.
- Q7: test_primary_monotonic_timeout_boundaries (2999/3000/3001),
  test_cleanup_shared_grace_and_no_concurrent_backup (499/500/501),
  test_cancellation_and_close_share_one_grace_budget,
  test_late_timeout_observation_does_not_renew_cleanup_budget,
  test_429_resource_close_also_has_one_bounded_grace,
  test_timeout_unknown_usage_is_full_primary_charge. Manual monotonic clock/events
  assert exact boundaries, not elapsed-wall-time sleeps. Late reliable usage can
  settle, late content cannot win; missing usage charges the full bound.
- Q6-Q10: test_backup_failure_is_terminal_no_third_attempt,
  test_backup_real_deadline_no_third_attempt,
  test_nonfallback_primary_failures and
  test_primary_exceptions_do_not_trigger_fallback_or_leak: backup 429/timeout/
  transport failure are terminal; early adapter timeouts do not authorize fallback.
  The "real_deadline" test name refers to the orchestration's owned deadline with
  an injected clock, not a real network request or three-second wall-clock wait.
- Q8/Q9: test_concurrent_admission_shared_budget_and_tenant_isolation (five 10000
  token reservations fit; sixth denies; another tenant admits independently),
  test_independent_service_owners_share_sqlite_quota_without_shared_python_lock
  (two 30000-token demands, one winner),
  test_repeated_uuid_across_tenants_does_not_mix_results_or_usage (eight tenants),
  test_duplicate_request_has_one_dispatch_and_one_settlement. Exact ownership,
  tenant budget and duplicate protection use real SQLite, not an in-memory store.
- Q8/Q11: test_durable_intent_visible_before_execution_and_no_transaction_held,
  test_storage_failure_no_unauthorized_send_or_replay (before/after committed
  faults), test_cancelled_db_worker_completion_discovered (eight controlled DB
  boundaries), test_db_delay_exhausts_overall_send_budget_without_dispatch,
  test_expired_sqlite_reservation_prevents_dispatch_and_keeps_deadline_charges.
  Database operations execute on non-event-loop threads; cancellation signals
  do not discard worker completion or falsely assert rollback. No network work
  is inside SQLite transactions; independent writer acquisition confirms this.
- Q8-Q10: client cancellation of primary, backup, resistant cleanup and preparation;
  test_shutdown_reports_unconfirmed_cleanup_without_unbounded_wait and
  test_failed_close_retains_resource_handle_and_reports_unclean_shutdown;
  test_adapter_bound_breach_fails_closed; unreliable/model-mismatched bounds,
  strict typed usage/budgets/overflow and invalid inputs fail safely. Public errors
  and captured logs exclude injected private diagnostics; prompt/success text is
  excluded from outcome repr. Provider API receives text, never the tenant key.

### Process, preservation and scope evidence

After final suite, parsed task4/.cache/sqlite_process_summary.json: children=15,
alive=0, forced=0; each exitcode=0. These are the accepted storage-process tests
rerun in this full native checkpoint. New orchestration uses controlled fake
providers and real SQLite in-process/offloaded threads, not external services.

Baseline SHA256 comparison verified accepted files unchanged; only permitted
engineering docs differ. Newly added providers.py/service.py and three test/support
files are the implementation delta. No accepted models/accounting/storage/tests,
Task 1/2 implementation/dependencies, lockfiles or shared environment changed.
Therefore no Task 1/2 tests were rerun or newly claimed passing in this checkpoint.
Final Git/whitespace and fixture-secret inspection are recorded below as inspections,
not tests. Index remains empty; ignored DB/WAL/cache/archives are not staged.

Remaining: independent engineering review of T4-004. No current test/lint failure.
No real vendor/tokenizer/output-cap certification, provider socket interoperability,
HTTP/auth provisioning, production backup/overall budget approval or final fault
analysis is claimed. Windows-local-drive/supported-runtime limitations and trusted
UTC assumptions remain. A permanently uncooperative adapter or blocked filesystem
cannot be forcibly cancelled by asyncio; quarantine/explicit unclean close and
owner drain are required. See ADR-019 and current T4-004 requirements contract.

Final inspection (not tests): Python baseline/manifest script exited 0: 62 original
tracked files byte-identical, exactly seven authorized docs modified and five new
Python files; original R1-R7/P1-P4 and Task 1/2 ledger rows unchanged. Accepted
source/tests/pins are identical. Final native process receipt: 15 children/all exit
0/zero alive/forced. Targeted private-key/provider-token/credential-URL patterns
found no candidates in changed/new files; tracked artifact inventory contains no
virtual environments/caches/SQLite databases/ZIPs. Existing ignore rules cover
actual test cache/DB/WAL/SHM paths, environment and local review ZIP. Exact new
file allowlist, empty index and unchanged ebc226a HEAD verified; source verification
hashes retained only in ignored .cache/t4004_verified_code.json. git diff --check
exited 0. main remains ahead 2/behind 0 recorded origin/main; no fetch/push/commit.
T4-004 is ready for independent review, not independently accepted or TASK-4 DONE.

## E025 - 2026-11-04: T4-004 independent acceptance / Git inspection

America/Los_Angeles; user reports independent engineering APPROVAL, no blocking
production defect. Reported evidence (NOT commands executed by Codex this session):

- All 324 tests passed in an isolated Linux review copy with review-only platform/
  SQLite compatibility changes. Review interpreter/SQLite versions and exact
  commands were not supplied; do not invent them or claim native Linux support.
- Additional adversarial output-category cap violations and total reservation-bound
  breaches passed. No numerical count beyond the supplied scenarios is asserted.
- A real monotonic-clock test observed successful fallback after approximately
  3.020 seconds with exactly one backup execution and conservative usage accounting.
  This is reported probe evidence, not a new local test, latency SLA, provider socket
  interoperability claim, or real-model/tokenizer/cancellation-billing guarantee.
- E024 native Windows/Python 3.12.16/SQLite 3.53.1 full 324-pass/Ruff verification
  remains authoritative for the documented supported environment. No review-only
  compatibility code/gate change is included. Earlier evidence remains unchanged.

T4-004 DONE/independently ACCEPTED; TASK-4 remains IN_PROGRESS. One descriptive
approved T4-004 commit authorized; no T4-005, push or implementation modifications.
No pytest/Ruff/install/provider/SQLite execution in this Git checkpoint. Subsequent
checks below are source/index/Git inspections, not new test results.

Initial inspections: git status --short --branch, git diff --stat, git diff --cached
--name-status, git rev-parse HEAD and git rev-list --left-right --count
HEAD...origin/main all exit 0. HEAD ebc226a5eda6f9bb31927eb760abf7cd3b04a6e1,
main ahead 2/behind 0 recorded origin/main; index empty. Seven modified engineering
docs, five approved new Python files and untracked task4_t4004_review.zip. Captured
75 initial SHA256 hashes in ignored .cache/t4004_acceptance_baseline.json. Verified
all 15 Python files against .cache/t4004_verified_code.json: exact E024 snapshot,
no unexpected implementation changes. Retained ZIP excluded locally via
.git/info/exclude; tracked ignore rules and all accepted code/pins unchanged.

Docs record reported qualified acceptance without new executions. Inspect full
tracked diff/new source/tests and exact staged inventory, exclude environments/
SQLite DB/WAL/cache/credentials/archives, run git diff --cached --check, commit once
and verify SHA/parent/manifest/clean status/branch counts. Preserve Tasks 1/2.

Completed staged inspections (not tests): full tracked diff and all five new
source/test/support files reviewed. Explicit git add -- with the 12-file allowlist
staged seven docs/README/requirements plus providers.py/service.py and three test/
support files. git diff --cached --name-status/--stat inspected: exactly 12 entries,
no dependency/config/lock/Task 1/2 or unexpected file. Staged blobs match reviewed
working files after Git EOL normalization; no unstaged or unignored leftovers.
All 68 captured non-document files, including source/tests/pins/archive, unchanged.
Targeted private-key/provider-token/credential-URL and staged artifact scans found
zero candidates; check-ignore confirms actual cache DB/WAL/SHM/environment/pycache/
review ZIP exclusions. git diff --cached --check exits 0. Git LF-to-CRLF advisories
are not implementation changes or test warnings. No test/Ruff rerun or new feature.
Proceed with one authorized commit; Git history/final report record SHA and final
clean-tree/branch verification. No fetch/push or T4-005.

## E026 - 2026-11-04: T4-005 authenticated HTTP and native wire verification

America/Los_Angeles (clock probes Nov 5 UTC, Nov 4 locally). User attachment
explicitly authorizes T4-005 only. Starting c889236a83978f72330dc937b68ad249ea71027f,
clean tree, main ahead 3/behind 0 recorded origin/main. Captured 74 tracked SHA256
hashes in ignored .cache/t4005_baseline.json. No commit, push, T4-006, Task 3 or
accepted production correction. Task 1/2 source/tests/dependencies/environments
remain unchanged; no new execution/pass claim for their suites.

### Environment/dependencies (actual inspection and installation, not tests)

Task 4 interpreter probe: Python 3.12.16 (main, Oct 26 2026, 14:10:56), MSC v.1944
64-bit AMD64; SQLite 3.53.1. Native Windows fixed-local-drive gate remains enabled
in unchanged storage.py; no compatibility shim. importlib.metadata reports FastAPI
0.162.0, Starlette 1.10.0, Pydantic 2.14.2, HTTPX 0.28.1, Uvicorn 0.54.0, pytest
9.2.0, Ruff 0.17.3, asgi-lifespan 2.1.0. Standard-library SQLite only. Task 4's
isolated pyproject/lock extended, no Task 1/2 pin/environment change.

uv was absent from PATH; used existing ../.tools/bin/uv.exe. With cwd task4/ and
UV_CACHE_DIR=../.cache/uv, executed:

| Actual command | Result | Exit |
| --- | --- | --- |
| `../.tools/bin/uv.exe lock --python .venv/Scripts/python.exe --offline` | Failed: FastAPI metadata absent from cache | 1 |
| `../.tools/bin/uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe --offline` initial | Same offline resolution failure; no install | 1 |
| `../.tools/bin/uv.exe lock --python .venv/Scripts/python.exe` authorized online | Resolved 27 packages in 1.10s; Task 4 lock updated | 0 |
| `../.tools/bin/uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe` | Resolved 27; prepared/installed 20 including editable Task 4 rebuild, isolated environment only | 0 |
| Same locked sync with `--offline`, final | Resolved 27 in 1ms; checked 27 in 2ms, no further installation | 0 |

Official FastAPI lifespan/Starlette request-stream docs consulted (ADR-020).
`python -m uvicorn --help` in Task 4 environment exited 0; factory, host/port,
no-access-log and no-proxy-headers flags confirmed. No real LLM/vendor contacted;
package downloads are separate from loopback-only integration verification.

### Actual verification commands (cwd task4/)

All commands below use the pinned Task 4 executable .\.venv\Scripts\python.exe; no other interpreter.

| Command / stage | Actual result | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m ruff format src/task4_limiter/app.py src/task4_limiter/settings.py tests/http_support.py tests/test_http.py` | Four new files formatted | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` initial | Two new-test issues I001/B023; corrected scoped import/closure binding | 1 |
| `.\.venv\Scripts\python.exe -m ruff check --fix tests/test_http.py` | One import fixed, zero remaining | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_http.py --tb=short --basetemp=.cache/t4005-asgi-01` | 71 passed in 2.68s | 0 |
| `.\.venv\Scripts\python.exe -m ruff format tests/http_wire_child.py tests/http_wire_support.py tests/test_http_wire.py` | Three new files formatted | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` wire initial | One unused-import F401; corrected only new support file | 1 |
| `.\.venv\Scripts\python.exe -m ruff check --fix tests/http_wire_support.py` | One issue fixed, zero remaining | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py --tb=short --basetemp=.cache/t4005-wire-01` | 26 passed, 1 failed in 36.08s; harness invalid-startup exit mismatch, described below | 1 |
| Scoped Ruff format over all seven new Python files after harness/lifecycle additions | Four formatted, three unchanged | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` expanded | One new nested import I001; scoped fix made | 1 |
| `.\.venv\Scripts\python.exe -m ruff check --fix tests/test_http.py` | One import fixed, zero remaining | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4005-full-01` | 427 passed in 40.60s, zero failures/skips/warnings/xfails | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` / `.\.venv\Scripts\python.exe -m ruff format --check src tests` | Both pass; 22 files already formatted | 0 / 0 |
| `.\.venv\Scripts\python.exe -m ruff format tests/http_wire_support.py` after receipt/upstream-env refinement | One formatted | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` before final full run | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4005-final` FINAL | **427 passed in 40.81s; zero failures/skips/warnings/xfails** | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` FINAL | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` FINAL | **22 files already formatted** | 0 |

All pytest invocations execute outside sandbox restrictions for native local SQLite
files/locks and Windows subprocesses, consistent with E022/E024. Read-only sandbox
access to a native pytest temp directory was denied; native diagnostic inspection
then succeeded. This did not require changing permissions/gates or weakening tests.

### Initial wire harness failure and correction (new support code only)

test_wire_bad_startup_reaps_process_without_forced_cleanup expected exit 3 for
invalid tenant configuration but observed Windows 3221225477. Native stderr
confirmed generic configuration rejection followed by Python _enter_buffered_busy:
a daemon stdin-reading thread held a BufferedReader lock during interpreter
finalization. Initial receipt still reaped all 28 children, zero forced; 27 normal
exit 0 and the erroneous invalid-startup exit. Replaced proxy daemon stdin control
with asynchronous stop-file polling, no reader thread at interpreter shutdown;
kept the expected-exit assertion. Harness cleanup continues through other children
after an assertion. Final complete suites above pass with expected exit 3 and zero
forced cleanup. No accepted app/service/storage correction, no bypass/shim introduced.

### Test coverage / native wire receipts

427 = 324 unchanged accepted + 74 new ASGI/config/lifecycle tests + 29 real HTTP
wire tests. H1-H8 map to test_http.py/test_http_wire.py, settings.py/app.py and the
unchanged accepted tests. Key named cases:

- H1/H2/H6: test_authentication_rejection_zero_reservations_and_calls,
  test_valid_duplicate_credentials_and_nonascii_headers_reject_without_reading_body,
  test_invalid_external_configuration_is_generic, wire authentication matrix.
  Only registered credentials authenticate; not-allowlisted keys use the unknown-
  credential path (no separate revocation interface). Missing/malformed/duplicate/
  cookie/spoof headers cannot grant identity.
- H1/H3/H6: strict input/header/size matrices, streamed exact 64/65-byte boundary,
  body deadline, wire Content-Length/chunked/compressed/malformed/schema/framing
  tests. No estimated tokens/tenant/model overrides; missing trusted bounds 503
  before admission/dispatch. Safe errors/logs exclude private diagnostic/prompt/
  credential/path canaries; completion is fixed synthetic content, not prompt echo.
- H4/H5: test_routing_status_accounting_and_no_prompt_or_secret_leak,
  test_combined_admission_boundaries_and_quota_rejection (49999/50000/50001),
  test_http_primary_timeout_and_unconfirmed_cleanup, wire routing/conservative accounting.
  Cooperative primary expiry uses REAL monotonic clock/HTTPX/TCP in wire tests;
  exact 3000/500 boundary and unconfirmed cleanup remain controlled-clock tests.
- H5/H7: test_http_concurrency_tenant_isolation_and_restart_persistence,
  test_wire_concurrent_tenants_atomic_quota_and_persistence_across_process_restart,
  test_wire_disconnect_accounts_primary_and_does_not_launch_backup. Five held 10000-
  token demands fill a tenant, sixth denied, separate key allowed; closed/restarted
  proxy retains HMAC identity/charges. Disconnect charges uncertain primary bound
  without starting backup. No false DB rollback inference on caller cancellation.
- H1/H5/H6: test_http_cancellation_preserves_dispatched_accounting,
  test_startup_cancel_discovers_initialized_worker_before_closing,
  test_shutdown_cancellation_drains_owned_provider_context,
  test_failed_attempt_close_quarantines_resources_instead_of_claiming_shutdown,
  test_database_failure_is_sanitized_and_unconfigured_provider_fails_closed.
  Owned cleanup/state are retained; no provider pool close under uncertain execution.

Real harness: 13 configured fixture modes; independent synthetic upstream and
Uvicorn proxy processes per mode, one proxy restart plus one expected invalid-
configuration startup. Both bind 127.0.0.1 on child-selected port 0, publish ports
and require bounded HTTP readiness (no preselect/release port race). Every HTTP
client disables environment proxies. No external LLM/vendor contacts. Upstream is
a TEST-ONLY fixed protocol/counter/cap fixture, receives no tenant configuration
or credential headers. Trusted adapters, not incoming prompts, choose bounds.
Journals persist only synthetic UUID/ordinal/phase/header-presence, never secrets,
prompts or completions. Explicit release events and bounded polling coordinate
requests/disconnect; arbitrary wall-sleep timing assertions are not used.

Final .cache/http_wire_summary.json was parsed/asserted (inspection, exit 0):
28 children/reaped 28/forced 0; 27 exit 0, one EXPECTED invalid-startup exit 3.
All 21 local rejection receipts have provider_delta=0 AND reservation_delta=0:
5 credential, 8 body/schema, 2 chunked-size/body-deadline, 2 quota, 1 concurrent
quota, 1 database-unavailable, 2 pre-ASGI framing. Non-admitted paths leave no new
request rows. Separate .cache/sqlite_process_summary.json: 15 storage children
all exit 0, zero alive/forced. Total **43 children reaped**, no forced cleanup.

Actual final per-mode journal/SQLite aggregates (distinct synthetic tenants):

| Wire mode | Primary calls | Backup calls | Complete requests | Charged tokens |
| --- | --- | --- | --- | --- |
| success (length + chunked) | 2 | 0 | 2 | 10 |
| primary 429 | 1 | 1 | 1 | 25 |
| primary real timeout | 1 | 1 | 1 | 25 |
| backup failure | 1 | 1 | 1 | 40 |
| backup 429 | 1 | 1 | 1 | 40 |
| transport failure | 1 | 0 | 1 | 20 |
| unknown success usage | 1 | 0 | 1 | 20 |
| exact quota | 1 | 0 | 1 | 25000 |
| excessive quota | 0 | 0 | 0 | 0 |
| concurrent tenants + restart | 7 | 0 | 7 | 35000 |
| client disconnect | 1 | 0 | 1 | 20 |
| database unavailable | 0 | 0 | 0 | 0 |
| startup fixture | 0 | 0 | 0 | 0 |

All modes: credential_headers_forwarded=0, held_tokens=0 after cooperative wire
completion/cleanup. Unconfirmed cleanup is verified separately in ASGI tests with
full holds retained. No third attempt. Raw journals/DB/WAL/logs/ports are ignored
.cache artifacts, not committed credentials/test fixtures.

### Preservation, current status and limitations

New runtime app.py/settings.py reuse accepted modules unchanged. Five new test/
support/child files, Task 4 pyproject/lock updates, relevant governance/Task 4 README
and root README Task 4 status correction. No accepted logic/test correction or
Task 1/2 dependency change needed; no Task 1/2 rerun claimed. R1-R7/P1-P4 unchanged.
Final source-hash/diff/artifact/index checks below are inspections, not tests.

T4-005 IMPLEMENTED/locally VERIFIED, independent acceptance PENDING; TASK-4 remains
IN_PROGRESS. No current test/lint failure; first harness/lint/cache failures above
are preserved. Stock provider rejects without trustworthy bounds. No real-model
counter/cap or semantic completion-privacy certification, public TLS/ingress/load/
OS-crash audit, unsupported filesystem/platform guarantee, OAuth/streaming/Redis
or arbitrary uncooperative-resource shutdown guarantee. Deployment needs strong
external keys/identity, verified adapters/caps, explicit execution budgets and safe
logging/clock/filesystem operations. Next: independent review, no T4-006/commit/push.

Final inspections (not tests): git diff --check exits 0; index empty, HEAD unchanged
c889236, main ahead 3/behind 0 recorded origin/main. SHA256 manifest comparison:
64 original tracked files byte-identical (all accepted Task 4 modules/tests and
Task 1/2 source/tests/pins included); exactly eight relevant docs/README plus
Task 4 pyproject/lock modified, seven new HTTP Python files. R1-R7/P1-P4 and prior
AGENTS/build/decision/evidence history intact. Root README corrects only Task 4
status/project count and clarifies unchanged Task 1/2 verification scope. New code
hashes (22 files) retained only in ignored .cache/t4005_verified_code.json; targeted
private-key/provider-token/credential-URL scan found zero candidates in changes.
Git LF/CRLF advisory on lockfile is not a test warning/implementation change.
No virtual environments/DB/WAL/cache/credentials/archive staged; no commit/push.

## E027 - 2026-11-04: T4-005 independent acceptance / Git inspection

America/Los_Angeles (clock probe 2026-11-05 06:00:12 UTC = Nov 4 locally).
User reports independent engineering APPROVAL, no blocking production defect.
Reported evidence, NOT new Codex executions:

- All 427 test cases passed independently across separate review runs.
- The 29 real HTTP wire cases passed in split groups. Authentication, quota
  rejection, fallback, concurrency, persistence and sanitization were reviewed.
- Linux verification required review-only compatibility substitutions. One combined
  Linux wire run STALLED DURING FIXTURE TEARDOWN; it is NOT a completed all-at-once
  pass. Do not represent aggregate split passes as a completed combined run.
- E026 native Windows/Python 3.12.16/SQLite 3.53.1 full-suite result remains
  authoritative for supported deployment. No review substitutions are shipped or
  native Linux support claimed. Review command lines, interpreter/SQLite versions,
  per-run timing/counts and Linux child-cleanup totals were not supplied.

T4-005 DONE/independently ACCEPTED; TASK-4 remains IN_PROGRESS. One descriptive
approved-source/test/support/config/lock/README/governance commit authorized.
No pytest/Ruff/install/provider/SQLite execution in this Git checkpoint. No T4-006,
Task 3, feature modification or push. Earlier E026 native evidence stays unchanged.

Initial inspections: git status --short --branch, git diff --stat, git diff --cached
--name-status, git rev-parse HEAD and git rev-list --left-right --count
HEAD...origin/main exited 0. HEAD c889236a83978f72330dc937b68ad249ea71027f;
ahead 3/behind 0 recorded origin/main, empty index. Ten tracked changes, seven
approved new Python files and untracked task4_t4005_review.zip. Captured 82 hashes
in ignored .cache/t4005_acceptance_baseline.json. All 22 Python files match the
final native verification snapshot in .cache/t4005_verified_code.json: no unexpected
implementation changes or need for tests. Retained archive locally excluded via
.git/info/exclude; no tracked ignore/config/source/test changes made this session.

Following source/index checks are inspections, not new test passes. Inspect full
diff/new approved files, exact 17-file index, exclude envs/DB/WAL/cache/credentials/
archives, run git diff --cached --check, create one descriptive commit and verify
SHA/parent/inventory/clean status/branch counts. Preserve Tasks 1/2 and T4-006 gate.

Completed staged inspection (not tests): full tracked diff/config/lock and all seven
new approved Python files reviewed. Explicit git add -- staged exactly 17 approved
paths (eight docs/README, two configuration/lock, seven Python). No Task 1/2 files,
environments/DB/WAL/caches/credentials/archives or review substitutions staged.
Staged blobs match reviewed working files after Git EOL normalization; no unstaged
or unignored leftovers. All 74 captured non-document files, including approved
code/tests/config/lock/archive, unchanged. Targeted private-key/provider-token/
credential-URL and artifact scans found zero candidates. Existing ignore rules
cover actual cache/DB/WAL/SHM/env/pycache and locally retained ZIP. Earlier E026
history is intact. git diff --cached --check exits 0; LF/CRLF advisories do not
represent implementation changes/test warnings. No tests/Ruff/install rerun.
Proceed with one authorized commit; Git history/final report record identity and
clean-tree/branch verification. No fetch/push or T4-006 implementation.

## E028 - 2026-11-04: T4-006 fresh final assessment audit

America/Los_Angeles; clock probes 2026-11-05 06:21:49 and 06:32:55 UTC are Nov 4
locally. Actual native Windows executions during THIS checkpoint, not reused E026
or independent review results. HEAD 6eaccafb52c4780892b311ea763aef6c62bc43c4;
initially clean index/tree, main ahead 4/behind 0 recorded origin/main (no fetch).
All three interpreters report Python 3.12.16 (Oct 26 2026 build, MSC v.1944 AMD64)
and SQLite 3.53.1. Supported Task 4 storage remains fixed-local-drive Windows.
Known sandbox restrictions require these native tests/install/socket probes outside
the sandbox; no platform gates, test skips or warning filters were changed.

### Full suites and Ruff: exact commands actually executed

| Cwd | Command | Actual result | Exit |
| --- | --- | --- | --- |
| repo root | `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4006-task1` | 149 passed in 36.06s | 0 |
| `task2/` | `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4006-task2` | 452 passed in 13.26s | 0 |
| `task4/` | `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t4006-task4` | 427 passed in 40.44s | 0 |
| repo root | `.\.venv\Scripts\python.exe -m ruff check task1 tests` | All checks passed | 0 |
| repo root | `.\.venv\Scripts\python.exe -m ruff format --check task1 tests` | 17 files already formatted | 0 |
| `task2/` | `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `task2/` | `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 16 files already formatted | 0 |
| `task4/` | `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `task4/` | `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 22 files already formatted | 0 |

Each pytest run: zero failures, errors, skips, warnings, xfails/xpasses. Three fresh
complete suites total 1,028 passes; targeted clean-env repeats below are separate.
Task 4 full run: 324 accepted + 74 ASGI/config/lifecycle + 29 real wire cases.
Sanitized receipts read after completion and copied into ignored root .cache BEFORE
targeted reruns overwrote the common receipt: t4006_native_http_wire_summary.json
and t4006_native_sqlite_process_summary.json. Native full suite wire: 28 children
reaped, 27 exit 0/one EXPECTED failed-startup exit 3, zero forced. Storage: 15 exit
0, zero live/forced. Total 43 reaped. All 21 local rejection receipts have provider
delta 0 AND new reservation delta 0. Per-mode charges/calls are in final audit.
Task 2 full-suite receipt: 12 children, alive/forced cleanup/reader threads all 0;
intentional upstream termination/startup-failure scenarios include nonzero child
exit codes while their enclosing tests pass. No false all-child-exit-0 claim.

### Runtime/package inspection (not extra test cases)

Each own interpreter executed `-c` imports of sys/sqlite3/importlib.metadata and
printed sys.version, sqlite3.sqlite_version and installed distribution versions;
exit 0. Full installed package inventories inspected with:

```powershell
.\.venv\Scripts\python.exe -c "import importlib.metadata as m,json; print(json.dumps(dict(sorted((d.metadata['Name'],d.version) for d in m.distributions())),indent=2))"
```

Task 1 inventory (38 installed distributions, including project):
ai-solutions-engineer-assessment 0.1.0; mcp/mcp-types 2.3.0; pydantic 2.12.5;
pydantic_core 2.41.5; pytest 9.2.0; pytest-asyncio 1.4.1.post1; ruff 0.17.3;
PyJWT 2.15.1; Pygments 2.21.0; annotated-types 0.8.0; anyio 4.16.0; attrs 26.1.0;
cffi 2.1.1; click 8.5.0; colorama 0.4.6; cryptography 50.0.2; h11 0.16.0;
httpcore2/httpx2 2.16.0; idna 3.20; iniconfig 2.3.1; jsonschema 4.26.0;
jsonschema-specifications 2025.9.1; opentelemetry-api 1.45.2; packaging 26.3;
pluggy 1.7.0; pycparser 3.12; python-multipart 0.0.33; pywin32 312;
referencing 0.37.0; rpds-py 2026.9.1; sse-starlette 3.6.0; starlette 1.10.0;
truststore 0.10.5; typing-inspection 0.4.4; typing_extensions 4.16.0; uvicorn 0.54.0.

Task 2 inventory / Task 4 locked installed inventory (27 distributions each):
respective assessment-task2-proxy / assessment-task4-accounting 0.1.0;
annotated-doc 0.0.5; annotated-types 0.8.0; anyio 4.16.0; asgi-lifespan 2.1.0;
certifi 2026.10.23; click 8.5.0; colorama 0.4.6; fastapi 0.162.0; h11 0.16.0;
httpcore 1.0.9; httpx 0.28.1; idna 3.20; iniconfig 2.3.1;
opentelemetry-api 1.45.2; packaging 26.3; pluggy 1.7.0; pydantic 2.14.2;
pydantic_core 2.50.2; Pygments 2.21.0; pytest 9.2.0; ruff 0.17.3; sniffio 1.3.1;
starlette 1.10.0; typing-inspection 0.4.5; typing_extensions 4.16.0; uvicorn 0.54.0.
Build requirement remains setuptools 82.0.1 (not an installed runtime distribution
claim). Direct pins and each full transitive lock remain unchanged.

### NEW environment: locked installation and deterministic reproduction

From task4/, absent path checked before first command. Temporary process variables:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.cache/t4006-clean-env'
$env:UV_CACHE_DIR = '..\.cache\uv'
..\.tools\bin\uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe --offline
```

Actual first result: exit 1, resolved 27 packages/created new environment but failed
to download Ruff 0.17.3 because the offline cache lacked its wheel. This is a setup
cache miss, not a product/test failure. Same environment variables, online retry:

```powershell
..\.tools\bin\uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe
```

Exit 0: resolved 27, prepared 7, installed 27 packages in 1.26s; downloaded Ruff
and Pygments. uv --version: 0.13.7 (316c827e0, 2026-11-03, Windows x86_64).
Clean interpreter imports task4_limiter.app/service/storage and inspects versions:
exit 0, Python 3.12.16/SQLite 3.53.1/project 0.1.0 and versions above. Editable
installation from current checkout, not a clean wheel packaging/other-OS proof.

Exact targeted commands in clean environment, task4/ cwd:

```powershell
.\.cache\t4006-clean-env\Scripts\python.exe -m pytest -q tests/test_http.py::test_routing_status_accounting_and_no_prompt_or_secret_leak --tb=short --basetemp=.cache/t4006-clean-asgi
.\.cache\t4006-clean-env\Scripts\python.exe -m pytest -q tests/test_http_wire.py::test_wire_content_length_chunked_and_success_privacy tests/test_http_wire.py::test_wire_routing_and_conservative_accounting --tb=short --basetemp=.cache/t4006-clean-wire
```

Actual results: **6 passed in 0.81s** and **7 passed in 16.61s**, each exit 0,
zero failures/skips/warnings/xfails. Fourteen real-wire children reaped, all exit 0,
zero forced. Primary success, HTTP 429/real 3 s fallback, backup failure/429,
transport error and unknown usage are reproducible without real credentials or
provider endpoint. Synthetic trusted adapters only. README adds these selectors.

Manual CLI/socket probe (NOT pytest): tool-inline Python helper launched clean
interpreter with `-m uvicorn task4_limiter.app:create_app --factory --host 127.0.0.1
--port 61736 --no-access-log --no-proxy-headers --log-level warning
--limit-max-requests 1`. Generated temporary key/identity, absolute ignored DB path,
backup 1000 ms/reservation 10000 ms supplied in child environment, never printed.
Bounded TCP readiness, one authenticated POST /generate with synthetic prompt:
HTTP 503/code service_unavailable as intended for stock unconfigured providers.
Child graceful exit 0; stdout/stderr 0 bytes, no forced cleanup. Helper exit 0.
Readiness chosen dynamic port; one-request limit is audit-only shutdown control,
not a new production policy. Real vendor/tokenizer and public deployment NOT tested.

### Source, accounting, recovery, security and Git inspections (not pytest)

Read original available attachment (Task 1-only), R1-R7/P1-P4/H1-H8, READMEs,
ADRs 016-020, implementation and accounting/storage/service/ASGI/wire test sources.
Requirements traceability and uncovered physical/OS-crash/remote-billing scenarios
are explicit in TASK4_FINAL_AUDIT.md; no invented crash/power-loss certification.
Native multiprocess races, graceful restart, transaction abort/COMMIT denial,
clock/identity mismatch, settlement and conservative recovery are exercised above.
No production defect identified; no extra feature/fault test created.

Git inspected with status/diff/log/rev-parse/rev-list/ls-files. Read all local
reachable objects using `git rev-list --objects --all` and `git cat-file --batch`,
tool-inline Python pattern scan with redacted contexts/fingerprints: 14 commits,
238 objects, 163 unique text blobs, no binaries; 81 initial tracked paths. No tracked
current/historical DB/WAL/SHM/env/cache/egg-info/ZIP/.env artifact. 141 candidate
occurrences: 139 Bearer documentation/grammar/RFC/invalid-fixture references, one
frozen-settings mutation sentinel, one deliberately rejected credentialed .test URL.
Manual classification found no actual secret. No private-key/common provider-key
candidate; origin URL has no embedded credential. No raw candidate value published.
Bounded heuristic/context review is not universal secret-format/unreachable-history,
dependency-CVE, CI/hosting-log or real-model semantic privacy certification.

Portable ignore rules cover actual .cache/.venv/.env/egg-info; local review ZIP
exclusions are .git/info/exclude only. Arbitrary DB/ZIP files outside ignored paths
still require explicit stage inspection. This is a documented publication risk,
not a tracked leak; no ignore/config changes made. No real credentials installed.
No Task 1/2 source/test/pin differences from recorded origin/main; no shared imports
or environment dependency changes. Root .cache/t4006_baseline.json holds 81 initial
tracked hashes for final docs-only comparison. Latest final integrity/whitespace/
status checks are appended after completion below. T4-006/TASK-4 IN_PROGRESS,
READY recommendation pending independent acceptance. No stage/commit/push/fetch.

Final inspection results (not additional tests): initial 81-path SHA256 comparison
finds exactly eight changed Markdown files and NO non-document change; 73 other
initial tracked files byte-identical. New TASK4_FINAL_AUDIT.md is the ninth docs-only
path. All matrix test references resolve to actual Python test definitions; all
relative links in changed/new docs exist. Current 82-file working-content scan
(81 tracked plus new audit) for private keys/common provider keys/credentialed URLs
finds only the previously classified deliberately rejected .test URL fixture,
no actual secret. git diff --check exits 0; index empty. git status shows eight
modified docs/one new audit only. HEAD remains 6eaccafb52c4780892b311ea763aef6c62bc43c4,
main ahead 4/behind 0 recorded origin/main. git diff --name-only origin/main --
task1 tests task2 pyproject.toml uv.lock manual_validation_lab.py manual_refund_lab.py
returns no paths. No accepted implementation/pins/test modification, staged files,
commit/push/fetch or DONE transition. Future publication needs independent approval
and separately authorized explicit docs-only staging/whitespace/secret review.

## E029 - 2026-11-05: T4-006 independent acceptance / final documentation Git checkpoint

America/Los_Angeles (client date). User reports independent ChatGPT engineering
review APPROVED: Task 4 assessment-ready within documented requirements, supported
Windows/SQLite environment and trusted-adapter policies. Reported review, NOT new
Codex test execution: seven traceability rows checked against previously submitted
source/test evidence; all named automated references verified; fresh E028 results,
documentation, limitations and submission findings consistent. No review command
lines, extra pass counts/timings or new runtimes supplied. T4-006/TASK-4 DONE.

E028 preserves actual 2026-11-04 149/452/427 native test passes, six Ruff checks,
clean installation and deterministic/stock CLI probes. No pytest/Ruff/install/
provider/SQLite execution in THIS acceptance checkpoint; no implementation/config
change warrants reruns. Historical independent Linux review substitutions, split
passes/combined teardown stall and supported native Windows/Python 3.12.16/SQLite
3.53.1 qualification remain unchanged. No new native Linux, real-vendor/tokenizer,
physical-crash or production-deployment verification claim.

Actual initial inspections (not tests): git status --short --branch, git diff --stat,
git diff --cached --name-status, git rev-parse HEAD and git rev-list --left-right
--count HEAD...origin/main exit 0. HEAD 6eaccafb52c4780892b311ea763aef6c62bc43c4,
main ahead 4/behind 0 recorded origin/main; empty index. Eight modified docs, new
TASK4_FINAL_AUDIT.md and local task4_final_audit_review.zip. SHA256 comparison with
E028 81-path baseline finds only eight Markdown changes, zero non-document changes.
Capture 83 hashes (tracked files/new audit/archive) in ignored acceptance baseline.

One authorized final nine-file documentation commit: AGENTS.md, root README,
task4/README.md, docs/TASK4_FINAL_AUDIT.md, docs/TASK4_REQUIREMENTS.md,
docs/TASK_LEDGER.md, docs/BUILD_LOG.md, docs/DECISIONS.md and this evidence file.
No accepted source/test/dependency/configuration/lock or Task 1/2 modification.
Retain review ZIP locally excluded, inspect complete diff and exact staged blobs,
exclude env/cache/DB/WAL/SHM/credential/generated/archive paths, run staged
whitespace check, commit once and verify final SHA/parent/inventory/clean status/
branch counts. These are Git/source inspections, not extra automated test passes.
No fetch/push or Task 3. Git history/final report record resulting commit identity.

Completed precommit inspections (not tests): entire tracked diff plus all 232 lines
of new audit reviewed; exact nine-file explicit index (eight modifications/one new
Markdown). git diff --cached --check exits 0; all staged blobs match reviewed
working files after Git EOL normalization. Targeted staged private-key/provider-key/
credentialed-URL/quoted-credential scan has zero candidates; only Markdown allowlist
paths, no env/cache/DB/WAL/SHM/credentials/generated/archive artifacts staged. All
74 captured non-allowlist files, including every accepted source/test/config/lock
and local review ZIP, unchanged. ZIP retained with .git/info/exclude rule, not
tracked ignore/config change. No unstaged or unignored leftovers. New audit's
LF/CRLF Git advisory is not an implementation change or test warning. No tests
rerun. Final checkpoint: one docs-only commit; verify parent/manifest/SHA, clean
tree and recorded-origin branch counts, report and stop without push.

## E030 - 2026-11-05: T3-001 materials/contract documentation inspection ONLY

America/Los_Angeles (client date). User reports independent architecture APPROVED
CONDITIONALLY; exact PII/profile/limits remain PROVISIONAL. This record has NO
new pytest/Ruff/install/provider/HTTP/SQLite execution or test pass claims.
Prior Task 1/2/4 actual E028 verification and acceptance evidence are unchanged.

Actual commands/inspections this checkpoint:

- Read AGENTS.md, task ledger, relevant ADRs/decision index and latest build/evidence.
- git status --short --branch / git rev-parse HEAD: exit 0, initially clean, HEAD
  7e3704588482b07ebf7cfbcfd65a8a58c0d2458e. No fetch/remote-publication verification.
- rg --files under supplied attachments for text/Markdown/PDF/Word inventory;
  rg -l -i with Task 3/T3-00/PII/redact/server-sent-events terms on text/Markdown,
  then rg -n -C 3 on four matching attachments: exit 0. Task 1 SSE/PII exclusions,
  Task 4 no-Task-3 exclusion, unrelated scene-schema Task 3 and unrelated security
  guidance only. No original Task 3 assessment contract recovered.
- Repository requirements/TASK3/PDF/Word/text filename inventory and git log --all
  --format= --name-only -- '*TASK3*' '*task3*': no original Task 3 brief/path found.
  Search bounded to available local materials, not external assessment systems.
- Tool-inline Python hashlib/subprocess capture of all 82 tracked paths in ignored
  .cache/t3001_design_baseline.json: exit 0. Used for docs-only preservation checks.

Created TASK3_REQUIREMENTS.md, updated AGENTS/ledger/ADR-022/M046 and this record.
T3-R1-R8 are user high-level requirements; T3-P1-P8/T3-L/T3-Q exact proposals need
independent approval. No application code/project/env/lock installed/created.
Pure-test and later async/wire matrices are NOT EXECUTED. T3-001/TASK-3 IN_PROGRESS;
T3-002 through T3-006 NOT_STARTED. Preserve Tasks 1/2/4, no commit/push/stage.
Final documentation link/ID/whitespace/hash/index inspections recorded below once
executed; those are inspections, not functional test evidence or mathematical proof
by test execution. Next: independent approval of T3-U1-U5 before implementation.

Completed actual documentation inspections (not tests): git diff --check exits 0;
new 340-line requirements file separately checked for trailing whitespace/final
newline. All proposed R/P/L/Q/U IDs present, exactly 21 Q matrix rows; relative
documentation links resolve. Targeted private-key/common-provider-key/credentialed-
URL scan of the six affected docs found zero candidates (bounded pattern scan,
not universal secret assurance). SHA256 comparison confirms exactly five existing
governance Markdown files changed; all 77 other original tracked paths byte-identical,
including completed-task sources/tests/READMEs/dependencies/config/locks. Existing
Task 1/2/4 ledger rows unchanged. Only new untracked path is TASK3_REQUIREMENTS.md;
no task3 directory/project/environment. HEAD remains 7e37045, index empty; no stage,
commit/push/fetch/install/test execution. Preserve docs-only handoff for review.

## E031 - 2026-11-05: accepted T3-001 / T3-002 pure implementation verification

America/Los_Angeles (client date). User independently APPROVES the explicitly
defined synthetic profile and authorizes T3-002 pure implementation/tests. Original
vendor brief unavailable; no universal PII or vendor interoperability inference.
T3-001 DONE/accepted. T3-002 implemented/locally verified, independent review PENDING;
T3-003 and later NOT_STARTED. No completed-task source/test/pin change authorized.

### Isolated setup / runtime (actual executions)

From task3/, using ignored repository uv 0.13.7 and installed parent Python solely
as interpreter selection (NOT installing into parent environment):

```powershell
$env:UV_CACHE_DIR = '..\.cache\uv'
..\.tools\bin\uv.exe sync --extra dev --python ..\.venv\Scripts\python.exe --offline
```

Exit 0: created task3/.venv and new uv.lock, built project, resolved/installed eight
packages. Python 3.12.16 (Oct 26 2026, MSC v.1944 64 bit AMD64). Installed runtime
inventory: assessment-task3-streaming 0.1.0; pytest 9.2.0; Ruff 0.17.3; colorama
0.4.6; iniconfig 2.3.1; packaging 26.3; pluggy 1.7.0; Pygments 2.21.0. No application
runtime dependencies. Build requirement setuptools 82.0.1, not a runtime-installed
distribution claim. Native SQLite 3.53.1 was probed as interpreter metadata only;
no Task 3 SQLite operations/imports or database verification claimed.

Locked recheck/import probe from task3/:

```powershell
$env:UV_CACHE_DIR = '..\.cache\uv'
..\.tools\bin\uv.exe sync --locked --extra dev --python ..\.venv\Scripts\python.exe --offline
.\.venv\Scripts\python.exe -c "import sys,importlib.metadata as m; import task3_streaming.sse,task3_streaming.payloads,task3_streaming.redaction; print(sys.version); print(dict(sorted((d.metadata['Name'], d.version) for d in m.distributions())))"
```

Combined probe exit 0, uv reports resolved eight/checked eight and package imports/
inventory succeed. No lock/pin changes during this recheck. Own Python/env/lock
separate from Tasks 1/2/4. No FastAPI/HTTPX/Uvicorn/vendor dependency installed here.

### Initial actual results / corrections (not hidden)

1. `.\.venv\Scripts\python.exe -m ruff format src tests`: exit 0, six reformatted/
   five unchanged. Subsequent format calls normalized only new Task 3 code/tests.
2. `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3002-first`:
   exit 0, **319 passed, one warning in 1.18s**. Warning is Windows sandbox
   PytestCacheWarning/WinError 5 creating .cache/pytest nodeids, not product behavior.
   Zero test failures/skips/xfails. No filters/skips/assertions weakened.
3. `.\.venv\Scripts\python.exe -m ruff check src tests`: standalone exit 1,
   six B008 default-call findings. Changed frozen Limits defaults to immutable
   DEFAULT_LIMITS singleton; no lint ignore/config weakening. An initial
   `ruff check --fix` reported four findings/three fixes/one B008 remaining; fixed
   remaining test helper default manually. Its unused import had been removed.
4. Expanded native suite, `.\.venv\Scripts\python.exe -m pytest -q --tb=short
   --basetemp=.cache/t3002-native`: exit 1, collection interrupted with **one error
   in 0.15s** (NameError DEFAULT_LIMITS in tests/test_sse.py). No passing-count claim
   for this run. Concurrent standalone Ruff exits 1/F821; format exits 0/11 formatted.
   Restored missing test-helper import; no production defect or assertion change.
5. `.\.venv\Scripts\python.exe -m pytest -q --tb=short
   --basetemp=.cache/t3002-native-final`: native exit 0, **334 passed in 1.20s**,
   zero failures/skips/warnings/xfails. Both standalone Ruff checks exit 0/11 files.
6. Final source review: abort after failed/abandoned terminal encoding must revoke
   a prepared success flag. Corrected Redactor.abort and added regression, then
   added explicit numeric grammar boundaries/decoder carry and 16 independent-
   reference adversarial-content seeds. Final full run below covers all changes.

### Final complete suite and Ruff (actual, final code)

All from task3/, native Windows outside the sandbox for pytest's cache permission;
no warning filters/marker changes or compatibility substitutions:

| Exact command | Actual result | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3002-complete` | **362 passed in 3.02s** | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 11 files already formatted | 0 |

Final suite: zero failures, errors, skips, warnings, xfails/xpasses. Eleven Python
files = five source/package files + six test/support/package files. Test references
are mapped to Q01-Q12 in requirements, not fabricated passing test names.

### What this execution verifies / does not verify

Four representative sensitive values: every raw SSE stream byte cut and every
model-delta cut, plus all 32 partitions of a short six-character candidate.
Unicode raw/JSON-escaped streams: every byte cut; explicit three-byte decoder carry,
CRLF/LF/lone CR/CR-only final terminal, multiline data/metadata and strict EOF.
32 seeded delta/chunk partitions and 16 seeded adversarial-content tests compare
against independent whole-input manual interval oracle, not production regexes.
Exact 255/256/257 candidates, 8192-byte lines/16384-byte events, scalar/UTF-8/
escaped-frame caps, duplicate decoded keys/strict JSON bounds and four-channel
transitions verified. Fixed error frames, private repr, captured logs/output,
no premature tail release, abort/terminal failure success revocation verified.

5000 bounded events consumed without retaining results internally; stats show no
event/hold/pending accumulation and bounded peaks. Four full 256-char holds remain
1024 chars total through 1000 empty deltas, then abort clears them. These are
logical retained-state counters and tests, NOT measured RSS/network buffers/real
async backpressure/cancellation/deadline/wire evidence. There is no upstream.py,
service.py, app.py or socket process, no real vendor/tokenizer/universal PII claim.
The standalone encoder validates shape/size; privacy requires redactor/Processor
composition, not encoding untrusted deltas directly. Synthetic fixtures only.

Requirements/ADR-022 record accepted engineering policies separately from original
brief absence; ADR-023 records implementation/ownership tradeoffs. Tasks 1/2/4
regressions not rerun: their shared code/config/env is unchanged. Git/hash/artifact/
source-boundary inspections recorded below after execution. No commit/push/stage,
T3-003 or completed-task modification. Next: independent T3-002 engineering review.

Final inspections (NOT additional tests): initial 83-file snapshot comparison finds
only the six authorized governance/requirements docs changed; all 77 other baseline
paths byte-identical, including completed Tasks 1/2/4 source/tests/READMEs/config/
dependency locks. Eleven final tested/formatted Python files snapshotted to ignored
.cache/t3002_verified_code.json and rechecked unchanged after documentation work.
AST source-boundary inspection finds no completed-task, HTTPX, FastAPI, socket,
SQLite or asyncio imports. Requirements test references resolve to actual functions
and relative documentation links exist. An internal reference-check regex initially
truncated module-name matches and was corrected; no application/test changes.

git diff --check exits 0; index empty, HEAD remains 7e3704588482b07ebf7cfbcfd65a8a58c0d2458e,
main aligned 0 ahead/0 behind recorded origin/main (no fetch). Exactly 15 new Task 3
project/source/test/README/config/lock files plus new requirements and five modified
governance docs; no env/cache/pycache/egg-info/database/archive artifact in unignored
inventory. Targeted private-key/provider-key/credentialed-URL scan of affected
docs/new project files found zero candidates, bounded scan not universal assurance.
No source changes after final 362-pass/Ruff run; no reason to rerun completed-task
suites. No stage/commit/push or T3-003 work. Independent acceptance still PENDING.

## E032 - 2026-11-05: T3-002 independent acceptance / Git checkpoint inspection

America/Los_Angeles (client date). User reports independent ChatGPT engineering
review APPROVED; T3-002 DONE/independently accepted. Supplied evidence, NOT new
Codex executions:

- Complete independent suite: 362 passed.
- Additional 1200 randomized interleaved SSE streams passed.
- 2961 channel-level reference comparisons passed.
- 256 candidate-prefix withholding probes/character-257 fail-closed behavior passed.
- 376 truncated-wire cuts checked without whole-value PII leakage.
- 24000-event retained-state test and Python compilation passed.
- No blocking production defect identified.

Independent Linux/Python 3.13.5/pytest 9.0.2 recorded ONE pytest configuration
warning; specific warning text/config key, commands, timings and Ruff results not
supplied. Do not invent them or present these as fresh native executions. Python
3.13 is outside project-pinned >=3.12,<3.13; no pin/config/filter/runtime-support
change shipped. E031 native Windows/Python 3.12.16/pytest 9.2.0 and Ruff 0.17.3
remain authoritative. Original brief unavailable, synthetic profile scope intact.

Actual initial inspections this checkpoint: git status --short --branch, diff
--stat, diff --cached --name-status, rev-parse HEAD, rev-list --left-right --count
HEAD...origin/main, ls-files --others --exclude-standard: exit 0. HEAD
7e3704588482b07ebf7cfbcfd65a8a58c0d2458e; main aligned 0 ahead/0 behind recorded
origin/main (no fetch), empty index. Five modified governance docs, new requirements,
15 new Task 3 files and local task3_t3002_review.zip. Tool-inline SHA256 comparison:
all 11 Python files match E031 verified snapshot; capture 99 current file hashes
including archive in ignored .cache/t3002_acceptance_baseline.json. Config/pins/
lock inspected, no unexpected changes; no pytest/Ruff/compile/install rerun needed.

Acceptance docs only updated now: AGENTS, Task 3 README, requirements, ledger,
ADR-023 provenance, M048 and this record. Preserve all code/tests/dependencies/
configuration/locks and completed Tasks 1/2/4. Retain/local-exclude archive; full
diff/new file content and exact 21-path stage inventory must exclude env/cache/
pycache/egg-info/temp/credentials/ZIP. Run git diff --cached --check, commit once,
verify parent/SHA/manifest/clean tree/branch counts. Git history/session report
record resulting identity. No push/T3-003; stop after accepted foundation checkpoint.

Precommit inspections completed (not tests): full tracked diff and all new approved
source/test/config/lock/README/requirements content reviewed. Exact 21-path index
(five tracked governance modifications, new requirements and 15 Task 3 files)
matches reviewed working bytes after Git EOL normalization. E031's 11 Python hashes
unchanged; all 92 captured files outside seven documentation-update paths unchanged,
including source/tests/pins/config/lock/review ZIP and completed Tasks 1/2/4.
No unstaged/unignored leftovers. Review ZIP retained via .git/info/exclude; no
tracked ignore/config mutation. Targeted staged private-key/provider-key/credentialed-
URL/quoted-credential scan zero candidates; no env/cache/pycache/egg-info/temp/archive
staged. git diff --cached --check exits 0. Git LF/CRLF advisories are normalization
not source functional changes or pytest warnings. No test/Ruff/compile/install
rerun. One descriptive commit, then parent/SHA/inventory/clean-tree/branch-count
verification and stop; commit identity recorded by Git history/session report.

## E033 - 2026-11-05: T3-003 async streaming, budgets and owned cleanup

America/Los_Angeles (client date). Latest supplied attachment authorizes async
adapter/service and deterministic tests over accepted 0a75587/362 pure tests.
Initial HEAD 0a75587e830618e69c4fcb827eb2d97ca37ec573, clean main ahead 1/behind 0
recorded origin/main; 98 tracked SHA256 hashes captured in ignored baseline.
Original vendor brief unavailable; only approved synthetic profile used. No
FastAPI endpoint, actual TCP/wire processes, vendor integration or later checkpoint.

### Runtime/setup/source inspection (not test pass claims)

Read AGENTS/ledger/approved contract/ADR-022/023; inspected installed HTTPX 0.28.1 /
httpcore 1.0.9 read-only using inspect.getsource on public Response.aiter_raw/aclose,
AsyncByteStream.aclose, AsyncClient sending implementation. Diagnostic read of native
HTTP/1.1 read constant yields 65536. No SDK monkeypatch/private API import in
application. Official async/timeout/transport docs consulted; links ADR-024.
Inspection explains avoiding coalescing small events and implicit EOF-close flag
ambiguity; it is NOT actual socket timing/allocation proof.

From task3/, actual isolated dependency command:

```powershell
$env:UV_CACHE_DIR = '..\.cache\uv'
..\.tools\bin\uv.exe sync --extra dev --python .venv/Scripts/python.exe --offline
```

Exit 0: lock resolves 15 packages; eight installed/replaced (project rebuilt),
only Task 3 env/config/lock affected. New runtime pin HTTPX 0.28.1; existing Python/
pytest/Ruff/build pins preserved. No external inference contacted; cache-only setup.
Final metadata probe prints native Python 3.12.16 (Oct 26 2026, MSC v.1944 AMD64)
and all 15 installed distributions: assessment-task3-streaming 0.1.0, anyio 4.16.0,
certifi 2026.10.23, colorama 0.4.6, h11 0.16.0, httpcore 1.0.9, httpx 0.28.1,
idna 3.20, iniconfig 2.3.1, packaging 26.3, pluggy 1.7.0, Pygments 2.21.0,
pytest 9.2.0, Ruff 0.17.3, typing_extensions 4.16.0. SQLite not used.

Final `.venv` metadata probe followed by
`..\.tools\bin\uv.exe sync --locked --extra dev --python .venv/Scripts/python.exe --offline`
with same UV_CACHE_DIR: exit 0, resolved/checked 15, no lock/pin changes. Parent
Task 1/2/4 environments/config/dependencies unchanged; no regression rerun needed.

### Initial actual failure and correction

From task3/, native outside sandbox (cache permissions), exact command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_upstream.py tests/test_service.py --tb=short --maxfail=3 --basetemp=.cache/t3003-initial
```

Exit 1: **86 passed, 1 failed in 1.17s**, no skips/warnings/xfails. Failure:
test_overall_deadline_closes_while_consumer_is_paused asserted response still open
at 119.999 s after a valid event, but it was closed. A delayed first-event watchdog
observed its timer after a large clock jump and falsely reclassified a valid
already-accepted event as late. Source correction respects synchronous accepted-
event state; original failing assertion/test preserved. No accepted pure change.

Standalone Ruff check exits 1 with six findings: UP047 generic syntax, I001 import
order and four F401 unused imports in NEW files. Corrected new source/test imports
and Python 3.12 generic syntax only. `ruff check --fix` reported six fixed/zero
remaining; new-file format command exits 0. No rule ignores/warning filters changed,
no accepted pure file reformatted. Added eight further cleanup/cancel/header/cap
regressions after the initial 87-case subset, for 95 new cases total.

### Intermediate full pass / process-capacity review

Before final capacity review, complete command
`.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3003-full`
exited 0, 457 passed in 3.86s; both Ruff checks exited 0 (16 Python files).
Further review found the optional per-instance test capacity parameter could opt
out of the default process-global counter. Removed that production override and
made all services use the same process capacity. New tests/conftest.py isolates
ONLY the new async test modules' process counter, not SDK/pure code; the cross-
service/parallel cap tests still share one counter within each test. No accepted
pure body/assertion changed. Full final rerun below verifies the correction.

### Final actual complete suite and both Ruff checks

All commands from task3/, supported native Windows/Python 3.12.16 environment;
pytest outside sandbox for ordinary cache permissions, no substitutions/filters:

| Exact command | Actual result | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3003-final` | **457 passed in 4.09s** | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 17 files already formatted | 0 |

Final 457 = 362 accepted pure tests unchanged +95 new async cases. Zero failures,
errors, skips, warnings, xfails/xpasses. Seventeen Python files = seven source/package
and ten test/support/package. No actual HTTP server or child processes started.

### Observed read-count/progressive/budget assertions from executed tests

- `test_progressive_delivery_and_exact_read_counts_under_blocked_demand`: safe prefix
  delivered while sensitive tail held and upstream gate unfinished; body/lease raw
  read/processing count all 1. Still 1 after 20 scheduler turns without demand. Next
  anext enters gated raw read 2 and cannot complete until released; final cross-
  network-chunk PII replaced, total reads 2, one confirmed response close/slot released.
- `test_pending_sanitized_frames_do_not_read_next_network_chunk`: output text lengths
  256/256/88 from one input use raw read 1, done/end use read 2. No producer queue.
- `test_raw_64k_segmentation_does_not_coalesce_small_events`: one 65536-byte raw block
  ->16 processing chunks, each4096; one raw chunk, next EOF read then owned close.
  65537-byte injected block rejects before any processing chunk, generic LIMIT.
- `test_long_stream_has_no_producer_queue_or_accumulated_pure_buffers`: 2000 deltas,
  exactly one read per delta demand and 2001 reads including terminal controls;
  held/pending pure buffers zero at each yielded ordinary-text frame. No RSS claim.
- First-event controlled boundary 14.999 passes, 15.0/15.001 time out. Comments,
  incomplete frames and small chunks do not renew budget; delayed headers do not
  reset admission anchor. Empty valid delta at14 qualifies, idle read expires29,
  not the old first deadline15. First watcher also closes at15 with no body demand.
- Overall watcher keeps response open at119.999 and closes at120 while consumer
  paused, with raw read count still1, no raw candidate flush. These are controlled
  monotonic assertions, not physical wall-clock/socket latency guarantees.
- HTTPX request extensions carry connect/pool/write5/read15. Typed phase timeout
  exceptions map TIMEOUT; MockTransport bypasses actual native phase timing. No
  invented DNS/TLS/socket connect benchmark from these settings/error tests.

### Cancellation, ownership, isolation and privacy results

Executed cancellation paths: connect, awaiting raw read, bounded redaction
checkpoint, paused consumer with pending output, request cleanup, repeated cancel,
shutdown/pool cleanup. Caller cancellation propagates; retained shielded work closes
and accounts for capacity, never flushes raw tails. No preemptive-bytecode claim.
Three uncertain-cleanup cases (resistant connect/read/response-close) retain one
owner/slot past1.001, quarantine adapter, reject new admission with zero extra
requests and do not close pool beneath live resource. Releasing the fake gate later
confirms response close/slot release then pool shutdown; quarantine not reopened.
Shared-grace test spends .75 s on cancel/discovery then close, expires at1.001
instead of renewing to1.75. Confirmed close at .999 is not quarantined. Failed fake
close returns controlled unavailable, retains owner/quarantine and emits no success
end; fixture-only manual disposal is not a production retry/recovery API.

Process-global cap verified across services and with parallel headers: 16 admitted,
17th CapacityExceeded, request count stays16, no waiting admission queue. Sixteen
concurrent independent streams redact correctly, one request/close each, no mixed
channel/candidate state. Strict status/type/encoding matrix reads zero rejected body
bytes; no redirects/retries/cookies/header/credential confusion. Original request
bytes preserved. Scoped HTTPX/httpcore logging filters suppress private body/token/
untrusted reason markers during owned I/O and preserve an unrelated logger record.
All emitted errors are accepted fixed Processor frames; other failures are generic
StreamError/CapacityExceeded for future HTTP presentation, no raw exception context.

No real sockets, downstream-send completion, actual network backpressure/RSS,
remote provider cancellation/billing or vendor interoperability validated. Future
T3-004 must bound actual ASGI send at min(10 s, remaining overall), own disconnect/
send cancellation and retain service when shutdown False. T3-005 owns wire proof.
Original brief remains unavailable. T3-003 locally verified/independent review
PENDING; no T3-004, stage/commit/push.

### Final integrity inspection (not additional test executions)

`git diff --check` exits 0. A native Python SHA256/inventory/document inspection
exits 0: nine authorized tracked changes, six new Python files, 89 baseline paths
unchanged, all 11 accepted pure Python files byte-identical, all 17 final verified
Python hashes unchanged. Checked 29 named test references and three relative local
Markdown links; no missing target or unexpected control character. Targeted
private-key/provider-key/credential-URL scan found one credential-URL candidate:
the deliberately invalid destination in test_upstream.py's rejection fixture,
not an actual credential. No actual secret identified by this targeted inspection;
this is not an exhaustive publication/history audit. Unignored changed inventory
contains no environment/cache/database/archive artifacts. Index empty; HEAD remains
0a75587e830618e69c4fcb827eb2d97ca37ec573; main ahead 1/behind 0 recorded origin/main.
No fetch, stage, commit or push. Subsequent changes are documentation-only.

## E034 - 2026-11-05: T3-003 reported independent acceptance and Git checkpoint

America/Los_Angeles. **Independent APPROVAL confirmed by user; T3-003 DONE.**
This section records reported review and actual documentation/Git inspection;
no pytest/Ruff/compile/install rerun during this checkpoint. E033 retains the
authoritative actual native Windows/Python 3.12.16 tests and Ruff results.

Reported independent evidence (not local commands executed here):

- Complete Task 3 suite: 457 passed.
- Additional 240 randomized HTTPX fragmentation cases passed.
- Resistant cancellation retained ownership, quarantined new admissions and
  released resources only after confirmed cleanup.
- Concurrent shutdown blocked admission and closed shared transport once.
- All 11 previously accepted pure source/test files byte-identical to review archive.
- Python compilation passed; no blocking production defect identified.

Review environment: Linux/Python 3.13.5, one nonfatal pytest configuration warning.
Exact warning/pytest version, commands and timings not supplied; do not invent
them or interpret as supported Python 3.13/native Windows verification. E033
native execution/Ruff remains authoritative. No real socket or ASGI claims are
authorized; original vendor brief unavailable, synthetic/narrow-PII scope retained.

Actual read-only commands: Get-Content AGENTS/ledger/current requirements/README/
ADR-024/evidence/build and new source/tests; git status --short --branch,
git diff --cached --name-status, git diff --stat and complete path-scoped git diff.
Initial HEAD 0a75587e830618e69c4fcb827eb2d97ca37ec573; main ahead 1/behind 0 recorded
origin/main; empty index. Nine tracked changes/six new Python files plus one local
review ZIP. Native Python SHA256 snapshot/inventory exits 0: captured 98 tracked/
seven untracked files, all 17 Python hashes match final verified E033 snapshot.
No unexpected functional change; no test rerun warranted. Completed Tasks 1/2/4
and all 11 accepted pure files preserved. Local review ZIP retained and excluded
from staging through exact local .git/info/exclude entry, no tracked ignore change.

Only acceptance documentation changed in this session. Authorized staging inventory:
two async source files/four test-support files, task3 pyproject/lock/README and
AGENTS/requirements/ledger/decisions/build/evidence (15 paths). Preserve accepted
source/tests/dependencies bytes, inspect staged manifest/contents for unexpected
paths/secrets/artifacts, run git diff --cached --check, commit once and verify
identity/parent/inventory/clean tree/ahead-behind. No fetch/push or T3-004.

Actual final staging inspection: explicit git add of those 15 authorized paths;
git diff --cached --name-status / --stat inspected. Native staged-content/hash/
artifact scan exits 0: exact 15-path manifest, index equals inspected working-file
content after Git newline normalization, no unstaged/unignored leftovers, 17
verified Python hashes and retained ZIP hash unchanged. No excluded environment/
cache/egg-info/database/archive/credential file staged. Targeted private-key/provider-
key patterns found none; one credential-URL match is the deliberate invalid-
destination negative fixture, not an actual secret. No actual secret identified;
not an exhaustive history/publication audit. git diff --cached --check exits 0.
No active default Git hooks. LF/CRLF advisories are normalization notices, not
functional changes or test warnings. Final changes after inspection are these
documentation records only; re-stage them and repeat staged whitespace check before
the one commit. SHA/parent/manifest/clean status/branch counts are verified afterward
and reported in the session/Git history. No test/Ruff/compile/install rerun.

## E035 - 2026-11-05: T3-004 FastAPI/ASGI integration and downstream ownership

America/Los_Angeles (client date). Actual local verification, not independent
acceptance. Baseline e4bd001039f8a752142adb84ff1ca51a57dad5ae, clean main ahead2/
behind0 recorded origin/main; 104 tracked SHA256 baseline captured. Read AGENTS,
ledger/approved synthetic contract/ADRs/accepted API source. User attachment
authorizes only HTTP settings/app and deterministic ASGI tests; no real sockets,
wire subprocesses, vendor APIs or completed-task modifications.

### Setup/runtime/API inspection (not implementation test claims)

Read installed public Starlette Response/StreamingResponse/init_headers and FastAPI
source read-only using Task 2's existing interpreter, no environment changes there.
Confirmed Response subclass callable can own public ASGI send/receive; ordinary
StreamingResponse does not expose our shared send deadline/retained-worker policy.
Official FastAPI custom-response and ASGI spec pages retrieved, ADR-025 links.
Starlette website fetch failed502; not used as successfully retrieved evidence.

From task3/, actual native offline setup:

```powershell
$env:UV_CACHE_DIR='..\.cache\uv'
..\.tools\bin\uv.exe sync --extra dev --extra serve --python .venv/Scripts/python.exe --offline
```

Exit0: resolved25 packages, rebuilt editable Task3 project, installed11 (including
replacement project). Only Task3 environment/pyproject/lock changed. New FastAPI
0.162.0/Starlette1.10.0/Pydantic2.14.2, optional Uvicorn0.54.0; Python/dev/HTTPX pins
preserved. Cache only, no external inference or TCP listener started.

Final sys.version/importlib.metadata probe: Python3.12.16 (Oct26 2026, MSC1944,
AMD64). Unique 25-package inventory: annotated-doc0.0.5, annotated-types0.8.0,
anyio4.16.0, assessment-task3-streaming0.1.0, certifi2026.10.23, click8.5.0,
colorama0.4.6, fastapi0.162.0, h110.16.0, httpcore1.0.9, httpx0.28.1, idna3.20,
iniconfig2.3.1, opentelemetry-api1.45.2, packaging26.3, pluggy1.7.0,
pydantic2.14.2, pydantic_core2.50.2, Pygments2.21.0, pytest9.2.0, Ruff0.17.3,
starlette1.10.0, typing-inspection0.4.5, typing_extensions4.16.0, uvicorn0.54.0.
The editable project appeared twice in metadata enumeration: inspected locations
are its .venv dist-info and ignored src egg-info, same0.1.0, not a second project
version. App import resolves task3/src/task3_streaming/app.py, exit0.
SQLite not used. No completed-task test/environment/pin changes needed.

Final actual locked check, same cwd/cache:

```powershell
..\.tools\bin\uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe --offline
.\.venv\Scripts\python.exe -m uvicorn --version
```

Both exit0: resolved/checked25, no lock changes; Running uvicorn0.54.0 with
CPython3.12.16 on Windows. Version probe is NOT a server startup/wire test.

### Initial failures / actual corrections, retained as evidence

From task3/, native outside sandbox due cache permissions:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_app.py tests/test_http_settings.py --tb=short --maxfail=3 --basetemp=.cache/t3004-initial
```

Exit1: **105 passed, 2 failed in2.97s**, no skips/warnings/xfails. Both new
test_exact_send_deadline_no_raw_tail_or_error_write_after_stall cases10/10.001
released ASGI send gate concurrently with clock expiry. An already-offered
SANITIZED frame completed before cancellation observation; no raw tail leaked.
Corrected new fixture synchronization to await cancellation signal before release;
retained original no-frame/end/attempt assertions. Timers cannot retract bytes
already offered to a server; this limitation remains documented, not hidden.

Initial ruff check exits1, 17 E501 findings; format --check exits1, four new files
would change/18 already formatted. Formatted only five named NEW files (four
changed/one unchanged), no rule ignores or accepted-file edits. Next Ruff check
passes. This was formatting, not an accepted source integration correction.

Expanded subset command (same as initial with --basetemp=.cache/t3004-expanded)
exits0: **119 passed in0.75s**, no skips/warnings. Further tests add cross-app
capacity/header-blocking and HTTPX ASGI smoke, plus explicit success bookkeeping.
First complete command
`.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3004-full`
exits1: **579 passed, 1 failed in4.54s**, no skips/warnings/xfails. New ASGITransport
smoke passed coalesced multi-event body to the accepted frame-at-a-time test helper.
Corrected only NEW test splitting on complete SSE blocks, preserving expected
redacted logical text. No production correction or accepted-test change.

First clean full command with --basetemp=.cache/t3004-final exits0:
580 passed in4.53s, Ruff lint/format22 pass. Final lifecycle review then made
unclean_shutdown true BEFORE awaiting teardown so a cancelled lifespan waiter
cannot leave that indicator unset. Added its assertion to existing NEW shutdown
test and reran complete suite/checks below. No accepted source correction.

### Final actual supported native verification

All commands from task3/, Windows/Python3.12.16, no compatibility substitutions,
warning filters or test selection. pytest outside sandbox for ordinary cache access:

| Exact command | Actual result | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3004-verified` | **580 passed in4.67s** | 0 |
| `.\.venv\Scripts\python.exe -m ruff check src tests` | All checks passed | 0 |
| `.\.venv\Scripts\python.exe -m ruff format --check src tests` | 22 files already formatted | 0 |

580 =457 accepted tests unchanged +123 new HTTP/settings cases. Zero failures,
errors, skips, warnings, xfails/xpasses. 22 Python files:9 source/package and13
test/support/package. No actual upstream/proxy listener or child services started.

### Actual ASGI assertions / bounded-state evidence

- test_asgi_send_backpressure_counts_and_progressive_safe_delivery: response200
  started, first safe prefix offered at raw read1; blocked send/20 scheduler turns
  stay read1/no delivered frame, next upstream gate not entered. Releasing send
  delivers safe prefix and enters read2; request still unfinished until upstream
  gate releases, final cross-chunk redaction/end and confirmed close, totalreads2.
- test_pending_sanitized_frames_await_individual_asgi_sends_without_more_reads:
  three independently gated 256/256/88-scalar sends all hold raw read1. Controls
  use read2. Existing service/pure high-water/long-stream tests also rerun.
- test_exact_send_deadline_no_raw_tail_or_error_write_after_stall:9.999 succeeds,
  10/10.001 cancel blocked send, zero further attempt/frame/error/end, close confirms.
  Header-block timeout/disconnect makes zero raw reads; attempted start not retried.
- test_send_uses_remaining_overall_budget_instead_of_another_ten_seconds: periodic
  event schedule reaches117s (14 raw reads), gated send remains pending/open119.999,
  completes if released then; 120/120.001 cancel, close, no end. No127s extension.
- test_postheader_failure_cannot_renew_an_expired_send_budget_for_error_or_close:
  after prior successful send, failure at11s yields zero new send attempts, no
  renewed error/empty-close allowance. No status change, no unclassified tail flush.
- Authentication/media/schema/framing/raw-byte/length/query/method rejects assert
  zero upstream requests; auth/metadata rejects also assert zero body receives.
  Two receive chunks exactly16384 accept;16385 rejects413 before upstream. Prompt
  exactly4096 ASCII/Unicode chars and valid Content-Length accept;4097 rejects400.
- Four upstream fragmentation step sizes1/2/7/4096 preserve independent channels,
  cross-delta PII and Unicode. Client Bearer/cookies/role/resume IDs absent upstream;
  separately configured Bearer and canonical prompt bytes confirmed. DEBUG caplog
  contains no synthetic private prompt/value/credential marker. Errors fixed only.
- Sixteen clients isolate prompts/results. Separate global HTTP capacity keeps16
  blocked terminal sends even when service.active=0;17th returns429, no17th upstream.
  Same invariant passes across two independent app instances, no waiting queue.

### Actual cancellation / lifespan / ownership assertions

Queued post-body disconnect can reject before upstream/header start. Disconnect
during upload/header acquisition/send/raw-tail read yields no new send or raw flush.
Request cancellation during blocked upstream propagates CancelledError and closes.
Repeated request cancellation does not discard shielded send/cleanup worker.
Transport send OSError never retries start or attempts an error write.

Shared-grace test: send stalls10s, resistant send cancellation plus response close
anchor same11s deadline; cancellation release10.75 does not extend it. At11.001
owner/session remain uncertain/quarantined; later close confirmation plus explicit
runtime.aclose releases only after public confirmation, no retry/new grace.
Uncertain ASGI send similarly retains owner/slot beyond11.001, blocks new request
503 with zero extra upstream calls and prevents pool close; releasing gate confirms
work, releases owner and allows exactly one pool close. Already-offered sanitized
frame may finish late; no new sends/end follow. No physical byte-retraction claim.

Actual ASGI lifespan messages startup.complete/shutdown.complete tested. Concurrent
shutdown blocks admission and closes shared transport once. Invalid startup config
opens zero transport/request; fixed configuration error only. Resistant upstream
read during shutdown produces shutdown.failed/Unclean streaming shutdown and true
unclean flag, retains app.state.runtime/owner, zero pool closes under uncertainty.
Late confirmed cleanup permits explicit close. Cancelled lifespan waiter propagates
cancellation, retains true unclean flag/shielded pool-close task, later confirmation
closes transport once. No dropped worker or automatic generation retry.

Scope qualification: native controlled ASGI/HTTPX doubles, not sockets, real server
buffering, HTTP client acknowledgement, RSS, TLS/deployment, subprocess cleanup,
real vendor/tokenizer integration or universal PII detection. Ordinary nonadmitted
JSON response lifetime/HTTP headers rely on ASGI server. Original brief unavailable.
T3-004 locally verified, independent acceptance PENDING; T3-005 NOT_STARTED.
No stage/commit/push. Final source/hash/link/artifact inspection follows.

### Final integrity inspection (not additional test executions)

Native Python baseline/inventory/AST/link/targeted credential inspection exits0:
94 baseline tracked paths unchanged, all17 accepted Task3 Python files byte-identical,
22 final verified Python SHA256 hashes captured. Exact unignored inventory is ten
tracked changes/five new Python files, no environment/cache/egg-info/database/review
archive or credential file. Completed Task1/2/4 directories/root source/tests/pins/
lock unchanged; root README only updates Task3 progress/stale-unimplemented text.
28 named test references and17 local Markdown links resolve; no unexpected control
characters. Targeted private-key/provider-key/credential-URL scan found zero
candidates in changed/new files, not an exhaustive publication/history audit.
git diff --check exits0 (LF/CRLF notice only, not a functional/test warning).
Index empty, HEAD still e4bd001039f8a752142adb84ff1ca51a57dad5ae, main ahead2/behind0
recorded origin/main. No fetch/stage/commit/push; no source/test/config changes
after final580/4.67s and Ruff22 verification. Further changes are documentation-only.

## E036 - 2026-11-05: T3-004 reported independent acceptance / Git checkpoint

America/Los_Angeles. User confirms **independent APPROVAL; T3-004 DONE**. This
record distinguishes reported review from actual documentation/Git inspection.
No pytest/Ruff/compile/install rerun during acceptance; E035 native Windows/
Python3.12.16 and Ruff remain the authoritative local execution record.

Reported independent evidence, not commands newly executed here:

- Complete Task3 suite:580 passed.
- Additional180 randomized interleaved two-channel ASGI scenarios passed.
- 4613 upstream read operations exercised across those randomized scenarios.
- Five additional fail-closed scenarios passed: candidate overflow, unexpected EOF,
  duplicate done, premature end and malformed payload.
- All17 previously accepted Task3 Python files byte-identical to T3-003 archive.
- Source-level inspection found no blocking defect.

Independent environment Linux/Python3.13.5 produced one nonfatal pytest
configuration warning. Specific warning, pytest version, commands and timings not
supplied; no invented details, local pass claim, pin widening or native verification
inference. Real sockets/RSS remain unverified; no vendor/deployment/universal PII
claim, original brief unavailable. Existing synthetic P/I/H policies retained.

Actual initial inspection commands: Get-Content AGENTS/ledger/current requirements/
README/build/ADR/evidence; git status --short --branch, git diff --cached
--name-status, git diff --stat and complete path-scoped git diff. Native SHA256/
inventory script exits0: snapshot104 tracked/six untracked paths, all22 verified
Python hashes unchanged, index empty, HEAD e4bd001039f8a752142adb84ff1ca51a57dad5ae.
Main ahead2/behind0 recorded origin/main, no fetch. Read-only AST/TOML inspection
enumerated all22 Python files and approved HTTPX/FastAPI/dev/serve pins/25-package
lock; this is not compilation or passing automated tests.

Only eight acceptance-documentation files changed this session: AGENTS, root/
Task3 READMEs, requirements/ledger/decisions/build/evidence. Approved application/
tests/config/dependencies/lock and Tasks1/2/4 preserved. Local review ZIP retained
and excluded via exact .git/info/exclude entry, no tracked ignore/config mutation.
Authorized15-path stage: two source/three test-support files, Task3 pyproject/lock/
README and root README/AGENTS/five governance documents. Inspect index/contents,
exclude env/cache/egg-info/credentials/databases/archives, run git diff --cached
--check, one descriptive commit and parent/SHA/manifest/clean-status/branch-count
verification. No T3-005 or push; TASK-3 remains IN_PROGRESS.

Actual final staging inspection: explicit git add of exactly15 authorized paths;
git diff --cached --name-status / --stat inspected. Native staged-content/hash/
artifact/link script exits0: exact manifest, staged bytes equal inspected working
files after Git newline normalization, no unstaged/unignored leftovers. All22
verified Python hashes/retained review ZIP hash unchanged. Targeted credential-URL/
private-key/provider-key scan zero candidates, no excluded artifact paths;18 local
Markdown links valid, no unexpected control characters. This is not an exhaustive
publication/history audit. git diff --cached --check exits0. No active default or
custom Git hooks; LF/CRLF notices are normalization, not functional/test warnings.
Final changes after inspection are these documentation records only; re-stage
and repeat staged whitespace check before one commit. Verify SHA/parent/manifest/
clean status/recorded-origin counts afterward; identity belongs to Git history and
the session report, avoiding a circular self-hash. No tests/Ruff/compile/install.

## E037 - 2026-11-05: T3-005 independent-process loopback HTTP verification

America/Los_Angeles. Actual native local verification, **independent acceptance
PENDING**. Baseline ecbd61c1a8e779b81e97652251085a9955366e09, clean main ahead3/
behind0 recorded origin/main;109 tracked SHA256 baseline captured. Read governance,
approved contract/ADR-022/024/025 and accepted factory/service. User attachment
authorizes harness/verification only; no accepted production/test correction.

### Runtime/configuration and inspection, not test pass claims

Native Windows/Python3.12.16 (Oct26 2026 MSC1944 AMD64), HTTPX0.28.1/httpcore1.0.9,
FastAPI0.162.0/Starlette1.10.0/Uvicorn0.54.0/h110.16.0/anyio4.16.0,
pytest9.2.0/Ruff0.17.3. Actual sys.version/importlib.metadata probe exits0.
Existing Task3 dev/serve environment used, no installation/dependency/lock change.
Task3 pyproject adds only http_wire marker/description; no rule/warning ignores.
Task1/2/4 environments not affected; their regression suites not rerun.

Read-only installed Uvicorn Server.serve(sockets=...)/Config/FlowControl.drain/
RequestResponseCycle.send source inspection exits0. Actual native send awaits
writable drain when flow.write_paused; used to interpret suspended-send receipts,
not a replacement implementation. Official Uvicorn documentation fetches timed out;
do not claim their retrieval. Earlier Task2 wire child filename lookup absent,
recorded M055, no effect on implementation/tests. No private SDK import/monkeypatch
in accepted application. New instrumentation delegates through public transport/
ASGI seams and observes public runtime/parser/redactor counters.

Each server child: own127.0.0.1:0 bound/exclusive Windows socket, listener backlog128/
SO_SNDBUF16384, Uvicorn asyncio/h11/HTTP1.1, lifespan on, proxy headers off, no
access log/server header, critical-only framework logs, keepalive2s/graceful2s.
Parent real HTTP readiness deadline10s. Client connections explicit close,22s
socket timeout for representative15s waits; slow-reader requests SO_RCVBUF4096.
Tokens are ephemeral/distinct and passed only in filtered child env, never args/
files/receipt journals. Child plan/release controls use stdin, no external services.
Provider journal counts generation calls independently; no raw body/prompt/key data.
Test-only outer stats route requires its own control token, not shipped in app.

### Actual commands/runs

All commands below from task3/, supported native Windows environment. pytest runs
outside sandbox for local socket/process/cache access; no compatibility shim,
warning filters or external generation. New-file Ruff format/check initially
exits0, three files formatted/no lint findings.

| Exact pytest command | Actual result | Exit |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py -k "not inactivity" --tb=short --maxfail=2 --basetemp=.cache/t3005-initial` |52 passed,2 deselected in18.22s |0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3005-full` |637 passed in53.09s |0 |
| `.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3005-final` |**637 passed in53.46s** |0 |

Initial subset omitted only real first/read inactivity cases. Before first complete
run added actual chunked byte boundaries, known upstream error and distinct16-client
safe/sensitive states (57 new cases total). Final measurement review then cross-
checked proxy native attempt counts against INDEPENDENT upstream stdin journal;
final complete rerun verifies that test-only change. No failing tests or accepted
source corrections occurred. Full final637 =580 accepted unchanged +57 new wire;
zero failures/errors/skips/warnings/xfails/xpasses/deselections in complete runs.

Final actual lint/format commands, after final suite, both exit0:

```powershell
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

All checks passed;25 files already formatted (9 source/package,16 test/support/
package). Source hash inspection confirms all22 accepted Python files byte-identical.
No code changes after final637/53.46s and Ruff25 results; later edits docs only.

### Final-run progression / protocol / rejection assertions

test_wire_progressive_delivery_before_gated_upstream_completion: client receives
safe SSE delta at~0.062s while provider held after first write; no provider_closed
receipt before explicit release. Native body chunks received1, native read attempts2
(includes pending attempt), not two delivered chunks or packets. Release permits
redacted continuation/done/end, valid headers and confirmed close. This is observed
ordering, not final-response equality or a universal latency SLA.

Four fragmentation/framing cases send1/2/3/7-byte fixture writes with LF/CRLF/CR/
multiline data. Actual UTF-8 split carry observed2 bytes, JSON escapes decoded,
email/phone/SSN span events/writes, two channels maintain independent text/control
order. Client reconstructs emitted frames against independent expected strings;
never assumes TCP preserves write/chunk boundaries. Whole-candidate masking,
candidate overflow257, unexpected EOF, duplicate done, premature end, duplicate-key
payload, unknown event, abrupt provider failure and known fixed error all fail
closed/no raw unresolved candidate/end. Metadata/comments/IDs stay dropped.

23 HTTP/auth/body rejection cases (7 auth,15 schema/media/query,1 chunked overflow)
each assert zero extra native request attempts AND independently journaled provider
calls;16/17 capacity test adds one further zero-forward rejection. Exactly16384-byte
chunked body accepts;16385 rejects413 without Content-Length reliance. Ordinary
Content-Length/chunked requests, fixed JSON status/header mapping, no forwarding
of client Bearer/cookies/role/resume claims and separate upstream auth verified.
Status302/429/500, non-SSE and encoded upstream responses return fixed502 JSON,
no private diagnostic echoed; bound-but-nonlistening endpoint yields fixed502.

Sixteen simultaneous held streams use distinct output markers and alternating
email-like versus safe candidate states.17th receives429, zero extra call in both
counters; release one slot, retry succeeds, remaining streams finish independently.
No shared redaction state, duplicate generation or admission queue observed.

### Final-run real backpressure / memory observations

Slow client pauses real reads after a valid frame; native Uvicorn send suspends.
Three separate control HTTP barriers observe the SAME pending send/read-attempt
counter117. Received raw body124004 bytes, offered SSE143545 bytes, suspended sends1.
No new upstream pull during this observed wait. Snapshot16 state probes, listener
send buffer16384, client requested receive buffer4096. These byte counters are
cumulative, differ due to framing/rechunking, and are NOT queue occupancy. No
claim about accepted-socket buffer inheritance/all OS tuning or summed memory.
Short flow-control suspension reproduced; exact10s kernel stall expiry explicitly
NOT verified. Accepted exact10/120s deterministic ASGI cases rerun in full suite.

Observed maxima across these wire probes (different scenarios, not a summed RSS
bound): line1055/event1069 bytes, UTF-8 carry2 bytes, candidate256/held256 chars,
pending256 chars/bytes, encoded frame300 bytes, raw body block1069 bytes. Approved
caps8192/16384/3/256/1024/1024+8192/8192/65536 respectively all hold. Configured
4096-byte processing slice unchanged; native partitions are not assumed to equal it.

Long-stream tests consume incrementally, independently compare SHA256/logical
length/control order and do not buffer complete output at the proxy. Actual
Windows instrumented process WorkingSetSize/PeakWorkingSetSize snapshots:

| Delta events / chars | Working set before / after (bytes) | Child peak (bytes) |
| --- | --- | --- |
|1000 /125000 |65052672 /65163264 |67788800 |
|5000 /625000 |65167360 /63582208 |67788800 |

Main-child long-run high-water counters remain line290/event304/decoder2/
candidate256/held256/pending125 chars+bytes/encoded169/raw304; prior scenarios can
contribute to cumulative peaks. Slow-reader child current63066112/peak68587520.
64MiB growth assertion is only an empirical regression guard. Interpreter/native/
framework/instrumentation overhead included; OS socket buffers/RSS ceiling/universal
deployment memory envelope NOT certified. Other platforms may report unavailable
RSS rather than invented observations; this execution is native Windows.

### Actual native timeout/disconnect/shutdown assertions

| Case | Final elapsed | Result |
| --- | --- | --- |
| First valid event inactivity |15.016s | Peer disconnect confirmed; no output/end, HTTP chunk completion false |
| Read idle after safe frame |15.047s | Peer disconnect confirmed; unresolved PII discarded, no end, HTTP chunk completion false |

Tests use broad representative13.5-22s wall tolerance, not exact phase-boundary
claims. Headers already200 per approved preflight contract, so failures close the
HTTP stream incomplete; no attempted status change/error leak. Two native client
disconnect cases (with/without prior safe output while provider gated/raw tail
held) confirm upstream receive disconnect and source response closure; owners/
slots drain, new send counter remains unchanged after completion, quarantine false.
Bytes already offered to ASGI/TCP cannot be retracted, no post-disconnect new sends
claimed possible. Resistant/uncertain ownership and quarantine remain deterministic
ASGI evidence, not falsely claimed native reproduction.

Active-request shutdown via ordered control invokes accepted runtime.aclose before
Uvicorn exits: clean true, active HTTP/upstream0, pool closes1, provider disconnect
observed, no false SSE end, lifespan.shutdown.complete. Stock signals/deployment
teardown not certified. Deliberate fixture exception still closes both child
processes; invalid configuration child exits expected2 without forced cleanup.

### Every service-child process receipt / cleanup outcome

Final complete run10 test children, all reaped; parent pipe-reader threads0 alive,
forced termination0/kill0/unexpected nonzero0/private diagnostic matches0:

| Role | PID | Exit | Classification |
| --- | --- | --- | --- |
| upstream |17128 |0 | normal |
| proxy |4916 |0 | normal |
| upstream |5540 |0 | normal |
| proxy |9132 |0 | normal |
| proxy |23540 |0 | normal (refused upstream) |
| upstream |19720 |0 | normal |
| proxy |19224 |0 | normal (active drain) |
| proxy |29944 |2 | expected invalid-configuration test |
| upstream |40128 |0 | normal (fixture-failure cleanup) |
| proxy |22480 |0 | normal (fixture-failure cleanup) |

Initial subset/first complete/final complete each spawned10 service children:
9 normal0 and1 expected2 each, zero forced/killed/live readers/private diagnostics.
Across all three actual runs30 service children:27 normal/3 expected2, no unexpected
nonzero. These counts exclude pytest/tool interpreter processes. Ignored separate
receipts retained in task3/.cache/t3005_initial_wire_summary.json,
t3005_first_full_wire_summary.json and t3005_wire_summary.json (final snapshot
also retained as t3005_verified_wire_summary.json); no credentials/raw bodies.

### Scope / current handoff

No real LLM vendor, external generation service, public listener, production TLS/
reverse proxy/deployment, formal RSS bound, exact socket10s/120s wall boundary,
native resistant-cleanup proof or final audit. Original vendor brief unavailable;
approved synthetic/narrow PII contract only. No implementation defect identified,
accepted source/tests/dependencies/lock and Tasks1/2/4 preserved. T3-005/TASK-3
IN_PROGRESS, NOT independently accepted; T3-006 NOT_STARTED. No stage/commit/push.
Final baseline/hash/link/artifact inspection follows; next independent review.

### Final integrity inspection (not additional pytest executions)

Native SHA256/inventory/TOML/AST/link/receipt scan exits0:100 original tracked paths
unchanged, all22 accepted Python files byte-identical,25 final verified Python
hashes captured. Exact unignored inventory nine tracked changes/three new test
files; pyproject diff is marker-only, dependency/lock/root pins/accepted source/
tests and Task1/2/4 directories unchanged.20 named test references/18 local links
resolve; no unexpected control character or targeted credential/private-key/
provider-key/credential-URL pattern finding. This is not an exhaustive history/
publication security audit. All three receipt sets confirm30 reaped service
children/27 normal0/3 expected2, zero forced/killed/live readers/private diagnostics.
git diff --check exits0. No environment/cache/database/archive/credential file in
unignored inventory, index empty. HEAD remains ecbd61c1a8e779b81e97652251085a9955366e09,
main ahead3/behind0 recorded origin/main; no fetch/stage/commit/push. No source/
test/config change after final637/53.46s and Ruff25; subsequent edits docs only.

## E038 - 2026-11-05: T3-005 qualified independent acceptance / Git checkpoint

America/Los_Angeles. User confirms **APPROVED, no blocking implementation defect;
T3-005 DONE**. This record distinguishes reported independent review from actual
documentation/Git inspection. No pytest/Ruff/compile/install rerun in acceptance;
E037 native Windows/Python3.12.16 full637/exit0/clean Ruff remains authoritative.

Reported independent evidence, not commands newly executed here:

- Existing Task3 tests:580 passed.
- All57 wire cases produced passing assertions across split executions.
- Additional40 randomized real-socket fragmentation tests passed.
- Progressive SSE, PII redaction, auth rejection, concurrency, disconnects, timeouts
  and cleanup reviewed.
- All22 previous Python files byte-identical to T3-004 review archive.
- No blocking implementation defect or production-code correction required.

**Linux qualification must remain attached to these results:** review used Linux/
Python3.13.5; an import-path change was applied ONLY to extracted review harness.
Combined Linux wire run STALLED after50 completed cases. A 19-case split run printed
passing summary but did NOT return promptly to enclosing command. Do not describe
Linux verification as a clean combined637-test run or infer clean process/exit
receipts from its assertion summaries. Exact commands/timings/pytest version and
independent Ruff results not supplied; do not invent them. No review shim/pin change
is shipped. Actual kernel10s stall expiry/production TLS/formal RSS ceilings/real-
provider interoperability remain unverified. Original vendor brief unavailable;
approved synthetic profile, historical evidence and limitations preserved.

Actual initial read-only commands: Get-Content AGENTS/ledger/current docs/local
exclude; git status --short --branch, git diff --cached --name-status, git diff
--stat and complete path-scoped git diff. Native SHA256/inventory script exits0:
109 tracked/four untracked hashes captured, all25 verified Python hashes match E037,
index empty, HEAD ecbd61c1a8e779b81e97652251085a9955366e09. Main ahead3/behind0
recorded origin/main, no fetch. Read-only AST inventory enumerated25 Python files;
not compilation or a test execution. No unexpected functional change introduced.

Only eight acceptance-doc files changed this session: AGENTS, root/Task3 READMEs,
requirements/ledger/decisions/build/evidence. Approved application/wire/previous
tests, dependencies/lock/marker and Tasks1/2/4 unchanged. Local review ZIP retained
and excluded via exact .git/info/exclude entry; no tracked ignore/config mutation.
Authorized12-path staging inventory: three wire test/support files, Task3 pyproject
marker, root/Task3 READMEs, AGENTS and five governance documents. Exclude env/caches/
egg-info/credentials/review ZIP/generated receipts; inspect staged inventory/content,
run git diff --cached --check, one descriptive commit then parent/full SHA/manifest/
clean tree/branch counts. TASK-3 IN_PROGRESS, no T3-006 or push; stop at Git checkpoint.

Actual final staging inspection: explicit git add of exactly12 approved paths;
git diff --cached --name-status / --stat inspected. Native staged-content/hash/
artifact/link script exits0: exact manifest, index equals inspected working bytes
after Git newline normalization, no unstaged/unignored leftovers. All25 verified
Python hashes and retained review ZIP unchanged; no shipped Linux import shim.
Zero targeted private-key/provider-key/credential-URL pattern findings or excluded
artifact paths;18 local links valid, no unexpected control characters. Not an
exhaustive history/publication audit. git diff --cached --check exits0; no active
default/custom hooks. LF/CRLF notices are normalization, not test/function changes.
Final inspection-record edits are documentation only; re-stage and repeat staged
whitespace check before the one commit. Verify full SHA/parent/manifest/clean tree/
recorded-origin counts afterward; identity remains in Git history/session report
to avoid circular self-hash. No tests/Ruff/compile/install/fetch/push or T3-006.


## E039 - 2026-11-05: T3-006 fresh four-project final audit

America/Los_Angeles. Audit-only baseline6b768780ace49c984d105b5ce558f69904f1076a.
These are NEW native Windows executions, distinct from E031-E038. Each suite ran
as an independent process in its own environment/cwd; no deselection/shim/skips.
Durations overlap and are not summed wall time. Final report:
[Task3 audit](TASK3_FINAL_AUDIT.md), ADR-027. T3-006/TASK-3 remain IN_PROGRESS pending
independent final review; no code/config/test/dependency/lock changes/commit/push.

### Fresh commands and results

Task1 cwd repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3006-task1
.\.venv\Scripts\python.exe -m ruff check task1 tests
.\.venv\Scripts\python.exe -m ruff format --check task1 tests
```

149 passed in39.44s, pytest exit0. Ruff all checks passed/exit0;
17 files already formatted/exit0.

Task2 cwd task2/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3006-task2
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

452 passed in12.39s, pytest exit0. Ruff all checks passed/exit0;
16 files already formatted/exit0.

Task4 cwd task4/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3006-task4
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

427 passed in50.33s, pytest exit0. Ruff all checks passed/exit0;
22 files already formatted/exit0.

Task3 cwd task3/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3006-task3
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

637 passed in56.31s, pytest exit0. Ruff all checks passed/exit0;
25 files already formatted/exit0. Includes all57 independent-process wire cases.

TOTAL1665 passed; ALL four suites zero failures/errors/skips/warnings/xfails/xpasses.
ALL8 Ruff commands exit0. Metadata probes used each environment's Python with
sys.version/sys.executable/sqlite3.sqlite_version/importlib.metadata.version:
Python3.12.16/MSC1944 AMD64, SQLite3.53.1, pytest9.2.0/Ruff0.17.3 in all four.
Task1 mcp2.3.0/Pydantic2.12.5/pytest-asyncio1.4.1.post1. Tasks2/3/4 HTTPX0.28.1,
FastAPI0.162.0/Starlette1.10.0/Pydantic2.14.2/Uvicorn0.54.0; Task2/3 httpcore1.0.9.
SQLite is metadata only outside Task4; Task4 retains supported fixed-local-drive
Windows/runtime gates. No Linux shim/pin widening/warning filter was applied.

### Actual fresh process/wire observations

Read fixture-generated ignored summaries after the completed suites. Task2:
12 children reaped,0 alive/forced/live readers; intentional upstream1/proxy3 exits
are negative scenarios. Task4:28 wire children27x0/1 expected3, all reaped/0 forced;
15 storage children all0/none alive or forced. Task3:10 children9x0/1 expected
startup-invalid2,0 forced/killed/live reader threads/private diagnostic violations.
Task3's fresh summary was task3/.cache/t3005_wire_summary.json (the filename is
historical; overwritten by THIS completed suite), not prior E037 receipts.

Fresh Task3 first client frame0.093s while source gate still closed,2 native read
attempts/1 delivered chunk;23 HTTP/auth/body zero-forwarding cases. Capacity16,
17th429/zero forwarding, confirmed release/reuse. Native first-event15.000s and
read-idle15.016s close with peer disconnect/no successful terminal. Slow client:
suspended send/read117 frozen across3 barriers,124004 native bytes/143545 ASGI bytes
offered; no kernel10s expiry claim. Long1000/5000-event runs125000/625000 chars:
line290/event304/decoder2/candidate256/held256/pending125 chars&bytes/encoded169/
raw304. Windows working set66027520->66043904 and66048000->63483904 bytes;
peak68521984, empirical not formalRSS. Native active shutdown clean/pool close1.
Exact first15/overall120/send10/cleanup1 boundaries and resistant ownership remain
fresh deterministic test assertions, distinct from measured sockets/OS buffers.

### Clean lockfile installation / imports

Cwd task3/, NEW target (did not exist before sync):

```powershell
$env:UV_CACHE_DIR='S:\2026 jobs\Projects\ai-solutions-engineer-assessment\.cache\uv'
$env:UV_PROJECT_ENVIRONMENT='S:\2026 jobs\Projects\ai-solutions-engineer-assessment\.cache\t3006-clean-env'
..\.tools\bin\uv.exe sync --locked --extra dev --extra serve --python .venv/Scripts/python.exe --offline
```

Exit0, CPython3.12.16, resolved25/installed25, editable
assessment-task3-streaming0.1.0 built/imported. Runtime pin/pyproject/uv.lock unchanged.
Locked installed selection: annotated-doc0.0.5,annotated-types0.8.0,anyio4.16.0,
assessment-task3-streaming0.1.0,certifi2026.10.23,click8.5.0,colorama0.4.6,
fastapi0.162.0,h110.16.0,httpcore1.0.9,httpx0.28.1,idna3.20,iniconfig2.3.1,
opentelemetry-api1.45.2,packaging26.3,pluggy1.7.0,pydantic2.14.2,
pydantic-core2.50.2,pygments2.21.0,pytest9.2.0,ruff0.17.3,starlette1.10.0,
typing-extensions4.16.0,typing-inspection0.4.5,uvicorn0.54.0.

### Real TCP assessor demonstrations (manual assertions, not added pytest counts)

1. From task3/, a PowerShell here-string containing the fixture recipe now in
   task3/README.md was piped to
   ..\.cache\t3006-clean-env\Scripts\python.exe. Exit0: missing/invalid credentials
   401/401 and zero upstream calls; authenticated200; safe hello prefix BEFORE
   releasing gated upstream, then whole-candidate redaction,done/end; active
   HTTP/upstream0 and not quarantined. UpstreamPID40180/proxyPID27056 both exit0,
   no forced cleanup. Ignored sanitized receipt .cache/t3006_clean_demo.json.
2. From root:

```powershell
.\.cache\t3006-clean-env\Scripts\python.exe .cache/t3006_factory_demo.py
```

   Final exit0. Public Uvicorn Config imported task3_streaming.app:create_app in
   factory mode, no HTTPSettings injection; actual T3_ACCESS_TOKEN/T3_UPSTREAM_URL/
   T3_UPSTREAM_BEARER env loading with ephemeral separate credentials. Real sockets,
   401/401/200, same gated redaction/done/end; upstream journal1. ProxyPID19952/
   upstreamPID28556 exit0, no forced cleanup, reader threads0. Sanitized ignored
   factory_demo/factory_cleanup JSON receipts. Graceful public Server.should_exit
   was used; literal shell-CLI signal/console behavior was NOT verified.

Initial factory utility invocation EXIT1 with AttributeError: its ignored
SimpleNamespace test adapter lacked .process, during Lab.ready before generation.
Only ignored utility corrected, then rerun exit0; not accepted application defect.
Bounded finally cleanup ran but complete initial-attempt exit/PID receipts were not
captured; do not count it as a successful demo. Subsequent Get-CimInstance matching
factory/provider processes returned no rows. One documentation editing command
also exited1 on nested PowerShell here-string parsing before writes; replaced
with structured patches. No pytest failure/production correction is inferred.

### Read-only security/publication/integrity inspection

Executed native Python .cache/t3006_security_scan.py, exit0; uses git rev-list
--all / --objects --all and git cat-file --batch-check/--batch to inspect all
unique reachable blobs plus current tracked files.19 commits/339 objects/234
unique text blobs/5475913 bytes/112 historical paths,0 binary. Current provider/
private-key matches0.11 deduplicated credential-looking candidates/12 occurrences:
6 synthetic fixtures/documentation,1 one-char invalid credential,1 malformed
credential fixture,2 invalid-destination URL fixtures,1 NONcredential token-count
invalid-type fixture. Context/AST review confirmed every classification;0 actual
disclosures/unresolved. No raw credential values printed or stored in report.
No tracked current/history env/cache/egg-info/DB/WAL/SHM/reviewZIP/receipt/credential-
history artifacts. Origin embeds no credential. No cross-task production imports.
Heuristic/contextual screen, not unknown-secret/PII/dependency-advisory certification
or inspection of unreachable/unfetched history. Original Task3 brief unavailable.

Actual git check-ignore probes: cache/newenv/generated egg-info/.env.production/
default .runtime DB excluded; specific existing ZIP locally excluded. Arbitrary
audit-review.zip/task4/usage.sqlite3 not ignored (intentional negative probe exit1).
No such artifacts tracked; portable ignore/config unchanged. Exact-path staging
required in any later authorized commit. This audit leaves index empty.

E038 Linux/Python3.13.5 import-path-only review-harness change/split assertion
passes/combined stall after50/19-case summary-not-returned qualifications preserved;
NOT a clean combined637 Linux run. Fresh Windows E039 authoritative. No real vendor,
universalPII/TLS/deployment/formalRSS/kernel10s or real120s wall-bound claim.
Final SHA/test-reference/link/whitespace/Git inventory verification follows below;
subsequent changes documentation only, no unnecessary test reruns.


### Final documentation/integrity checks (inspection, not additional tests)

Native SHA/AST/local-link/index inspection exit0:112 baseline tracked files,
104 unchanged/eight authorized Markdown changes plus new TASK3_FINAL_AUDIT.md.
All25 accepted Task3 Python files and all Task1/2/4 implementation/tests/config/
dependencies/locks remain byte-identical.73 distinct named test references and36
module/function references resolve;29 local links exist; README Python recipe
parses. Historical TEST_EVIDENCE/BUILD_LOG/DECISIONS content is an unchanged prefix,
with new audit entries appended. No unexpected control characters or targeted
provider-key/private-key/credential-URL patterns in the nine audit docs. Current
content/history artifact inventory additionally checks DB-wal/DB-shm suffixes:0.

The first reference-inspection command exited1 because its audit-only resolver
looked for the explicitly named TEST harness in the production package directory;
resolver corrected to use task3/tests, then all references validated exit0. No
missing application function/test and no accepted source correction. This is not
a failed pytest assertion or new passing test count.

Complete tracked documentation diff inspected; new audit content inspected with
R/Q/policy/source/test mappings. git diff --check explicitly returned0. Index empty;
working tree exactly eight modified docs and one new audit, no unignored environment,
cache,DB/WAL/SHM,archive,credential or generated receipt. HEAD remains
6b768780ace49c984d105b5ce558f69904f1076a; main ahead4/behind0 recorded origin/main,
no fetch/stage/commit/push. Local diagnostics/clean env/receipts remain ignored.
No functional changes after fresh suites/Ruff; final edits documentation only.
Local READY in documented scope; T3-006/TASK-3 IN_PROGRESS pending independent
acceptance. No blocking production defect found. Stop for review.


## E040 - 2026-11-05: T3-006 independent documentation acceptance / final Git checkpoint

America/Los_Angeles. User confirms independent ChatGPT engineering APPROVAL:
T3-006 and TASK-3 DONE, assessment-ready within accepted synthetic SSE/PII contract.
Reported independent DOCUMENTATION review (not commands executed here):

- Eight high-level requirements and21 detailed criteria covered.
- All73 unique named tests checked against previously submitted Task3 source archive.
- Implementation-symbol and local-link checks passed.
- E039 native Windows149/452/427/637 (1665) and eight Ruff checks consistent.
- Assessor demo recipe passed independent syntax inspection.
- No blocking documentation or traceability discrepancy.

Review did NOT rerun full native Windows regression, directly inspect unpublished
local Git history or validate unavailable vendor requirements. Preserve all
production/RSS/TLS/socket/PII/runtime qualifications. No new pytest/Ruff/compile/
install/demo/security-history rerun in this acceptance checkpoint. E039 remains
actual execution evidence; no reported review is presented as a fresh local run.

Actual initial inspections: Get-Content AGENTS/ledger/current docs/local exclude,
git status --short --branch, diff --cached --name-status, rev-parse HEAD,
rev-list --left-right --count origin/main...HEAD. HEAD6b768780ace49c984d105b5ce558f69904f1076a,
main ahead4/behind0 recorded origin/main, index empty; eight authorized modified
docs/new final audit plus a new local review ZIP. Native SHA/inventory check exit0:
all112 original tracked files compared to E039 baseline, only eight allowed docs
differ; all accepted source/tests/config/pins/locks and Tasks1/2/4 byte-identical.
Captured current tracked hashes/new audit/ZIP hash in ignored diagnostic inventory.
ZIP retained via exact .git/info/exclude entry, no tracked config edit.

Only nine authorized documentation paths may be staged: AGENTS.md, README.md,
task3/README.md, docs/TASK3_REQUIREMENTS.md, docs/TASK3_FINAL_AUDIT.md,
docs/TASK_LEDGER.md, docs/DECISIONS.md, docs/BUILD_LOG.md, docs/TEST_EVIDENCE.md.
Complete diff and staged content/inventory inspection, sensitive-artifact exclusion,
index/working-byte comparison, staged whitespace check, one descriptive commit,
then SHA/parent/inventory/clean-tree/ahead-behind verification. Retain local cache/
env/scripts/diagnostics/reviewZIP/DB/WAL/SHM outside commit. No fetch/push or new work.


Actual final inspection/staging: native SHA/AST/link/content check exit0;104 frozen
original tracked paths unchanged, prior E039/build/decision/AGENTS content preserved
as exact raw-byte prefixes before new acceptance entries.73 named tests/29 local
links valid, both current ledger statusesDONE, zero targeted secret patterns in
nine docs. No test/compile execution. One accidental historical dash re-encoding
was restored during diff inspection; no historical content change remains. An
initial inspection assumed LF append separators; adjusted only that inspection
for native CRLF, then exact-prefix SHA checks passed. No application defect.

Explicit git add staged EXACTLY the nine authorized paths; cached name-status/stat
inspected. Staged-content check exit0: index equals reviewed working bytes after
Git newline normalization, no unstaged/unignored leftovers or excluded artifact
path, all accepted implementation/config/tests/locks unchanged and retained ZIP
hash unchanged. git diff --cached --check exit0; no active default/custom hooks.
LF/CRLF notice for new audit is normalization only. Re-stage these final inspection
records, repeat staged check, create one descriptive commit, then verify full SHA,
parent/exact nine-file manifest/clean status/recorded-origin counts in Git/session
report. No fetch/push/test/Ruff rerun or further work authorized.


## E041 - 2026-11-06: T3-007 PAN remediation / Task4 evaluator-readiness verification

America/Los_Angeles. Baseline8d7a3c7f3bbd87deec1d83058315a8d732164ca5. T3-007
IN_PROGRESS / PENDING INDEPENDENT ACCEPTANCE. All results below actually executed
in native Windows environments, no Linux compatibility shim/new dependency.
Historical E039/E040/approvals are preserved, not relabeled as new evidence.

### Provenance and baseline reproduction

Read user attachment/current guidance/contracts/final audits/ADRs and relevant
redactor/models/test interfaces, Task4 accounting/SQLite admission/settlement/
service fallback/default provider source. Initial search did not find differently
named gap input because it was in ignored .cache; user supplied exact path:
.cache/evaluator_gap_audit_tasks_3_4.md. Entire text read, SHA256
 e7d5e1185501f08f3972eda37308956f31d97bdce4f02fa6dc23729d97ab157f.
Original full verbatim vendor brief/rubric still unavailable. Existing attachments
and requirements searched; original pasted assessment is Task1-specific. Recovered
email/SSN/card categories confirmed by user; separator/boundaries/tokenizer/vendor
format expectations are not invented. Input remains ignored, not copied into Git.

Before edits, from task3/, native .venv Python here-string imported Processor and
tests.support stream/text_output, fed each requested synthetic PAN byte-by-byte,
then finish. All3 contiguous/hyphen/spaced values emitted unmasked (counterexample,
not a passing security test). Initial governance inventory command used wrong
Task3 cwd and failed before documentation writes; corrected root113-file baseline
captured before implementation. After edits, corresponding pure/ASGI/TCP tests
require whole [REDACTED] replacements; no card prefixes/suffix digits/length output.

### Intermediate tests and actual failures

- Task3: python -m pytest -q -m 'not http_wire' --tb=short
  --basetemp=.cache/t3007-initial:5 failed/575 passed/57 deselected,4.76s, exit1,
  two cache-permission warnings in sandbox. Prototype applied256 cap to a combined
  bridge; five existing adversarial-reference seeds reproduced the regression.
- Same native command with --basetemp=.cache/t3007-core outside sandbox:
  5 failed/575 passed/57 deselected,4.30s/exit1,no warnings. Production K-token cap
  corrected, but old reference bridge rule still incorrectly joined prose.
- Corrected independent manual oracle, same selector
  --basetemp=.cache/t3007-core2:580 passed/57 deselected,5.17s/exit0,no warnings.
- python -m pytest -q tests/test_pan.py tests/test_app.py -k pan --tb=short
  --basetemp=.cache/t3007-pan:81 passed/94 deselected,2.18s/exit0. Ruff check exited1
  (UP031 new test format-string), format --check exited1 (5 files). Fixed f-string
  and formatted only authorized source/test files; no accepted transport/app rewrite.
- python -m pytest -q tests/test_pan.py tests/test_app.py tests/test_http_wire.py
  -k pan --tb=short --basetemp=.cache/t3007-adversarial:100 passed/151 deselected,
  5.73s/exit0,no warnings.96 new PAN cases plus4 old lifespan-name matches.

The three obsolete original negative PAN expectations are strengthened to require
masking (two negative-param rows/one phone-boundary row). No case removed, skipped,
xfail weakened or existing phone grammar enlarged. Independent reference uses
manual scans, no production PAN helpers. New tests cover every byte/delta cut in
21 length/format fixtures,24 random interleaved four-channel seeds, Unicode/escapes/
line endings, bounded state/3000 events, overflows/EOF/abandonment, ASGI cancel/
timeout/disconnect,17 native TCP cases and sensitive-output/diagnostic assertions.

### Fresh complete regression and both Ruff checks

Executed through ignored .cache/t3007_verify.py, using EACH project's own Python
executable/cwd; command arguments below are exact (absolute executable in JSON
receipt is represented by its cwd-relative path). Runs overlap; do not sum elapsed.

task1 cwd: repository root

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3007-final
.\.venv\Scripts\python.exe -m ruff check task1 tests
.\.venv\Scripts\python.exe -m ruff format --check task1 tests
```

- .....                                                                    [100%] / 149 passed in 40.49s; exit0; measured command wall 41.506s.
- All checks passed!; exit0; measured command wall 0.139s.
- 17 files already formatted; exit0; measured command wall 0.115s.

Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]; SQLite 3.53.1; versions pytest=9.2.0, ruff=0.17.3, mcp=2.3.0, pydantic=2.12.5, starlette=1.10.0, uvicorn=0.54.0.

task2 cwd: task2/

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3007-final
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

- ....................                                                     [100%] / 452 passed in 13.22s; exit0; measured command wall 13.944s.
- All checks passed!; exit0; measured command wall 1.354s.
- 16 files already formatted; exit0; measured command wall 0.11s.

Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]; SQLite 3.53.1; versions pytest=9.2.0, ruff=0.17.3, pydantic=2.14.2, httpx=0.28.1, httpcore=1.0.9, fastapi=0.162.0, starlette=1.10.0, uvicorn=0.54.0.

task3 cwd: task3/

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3007-final
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

- .............                                                            [100%] / 733 passed in 58.18s; exit0; measured command wall 58.756s.
- All checks passed!; exit0; measured command wall 0.159s.
- 26 files already formatted; exit0; measured command wall 0.102s.

Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]; SQLite 3.53.1; versions pytest=9.2.0, ruff=0.17.3, pydantic=2.14.2, httpx=0.28.1, httpcore=1.0.9, fastapi=0.162.0, starlette=1.10.0, uvicorn=0.54.0.

task4 cwd: task4/

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short --basetemp=.cache/t3007-final
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

- ...................................................................      [100%] / 427 passed in 40.08s; exit0; measured command wall 40.732s.
- All checks passed!; exit0; measured command wall 1.478s.
- 22 files already formatted; exit0; measured command wall 0.103s.

Python 3.12.16 (main, Oct 26 2026, 14:10:56) [MSC v.1944 64 bit (AMD64)]; SQLite 3.53.1; versions pytest=9.2.0, ruff=0.17.3, pydantic=2.14.2, httpx=0.28.1, httpcore=1.0.9, fastapi=0.162.0, starlette=1.10.0, uvicorn=0.54.0.

All1761 tests passed:Task1 149/40.49s,Task2 452/13.22s,Task3 733/58.18s,Task4
427/40.08s. All8 Ruff commands0;17/16/26/22 format files. All four suites0 failures/
errors/skips/warnings/xfails/xpasses. SQLite3.53.1 used for storage ONLY by Task4;
other interpreters metadata-only. No code/config/test changes after these final
commands, only documentation. Receipts are ignored .cache/t3007_task*_verification.json.

### Process cleanup, diagnostic capture and Task4 demo

Fresh Task3 full summary copied before further work:10 children9x0/one expected
invalid-startup2,0 forced/killed/live reader threads/privacy violations. PAN tests
extend existing private-marker capture before sending synthetic values; no harness
rewrite. Exact reconstructed outputs asserted, failure streams have no end/raw tail.
Gated progression observed0.078s, native first/read inactivity15.031/14.985s sampled
by fixture; not precise wall-clock boundary certification. Deterministic ASGI tests
verify exact10s sends/120s overall/1s cleanup. New four-channel numeric hold test
retains1168 chars/peak K-token256; documented conservative auxiliary bound1176 total.
Long native stream high-water line290/event304/decoder2/candidate256/held256/
pending125/encoded169/raw304, sampled peak working-set68837376 bytes. Empirical,
not formal RSS. Stable slow-send/read117 across3 barriers; no kernel10s guarantee.

Task4 fresh full receipt:28 wire children27 normal0/one expected3,0 forced;
15 storage children all0/no alive/forced.21 locally rejected requests show zero
provider/reservation deltas. Primary429/timeout modes exactly1 primary/1 backup,
charge25; unknown primary charge20, terminal backup failures charge40/no third call.
Task2 unchanged full receipt12 reaped/no alive/forced/live readers. Expected negative
child exits remain classified, not unexpected test failures. No new orphan claim
outside explicit fixture receipts and accepted retained/quarantined owner policies.

Task4 README one-command evaluator demo freshly executed from task4/:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_http_wire.py -k "content_length_chunked_and_success_privacy or routing_and_conservative_accounting or exact_quota_and_denial_never_dispatches" --tb=short
```

9 passed/20 deselected in18.89s,exit0,no warnings/skips/xfails.18 child processes
all exit0/reaped/0 forced; full-suite summary copied BEFORE selector overwrote local
summary. New demo summary ignored separately. Tests establish primary success,
429/real3000ms fallback/exact one backup,quota exhaustion/zero additional calls and
controlled failures using existing synthetic provider adapters. Stock default503
verified by fresh full-suite test_database_failure_is_sanitized_and_unconfigured_provider_fails_closed.
Real provider/model tokenization/billing NOT VERIFIED/rubric-dependent; no real
credentials installed, no Task4 source/tests/config/dependency/lockfile change.

### Documentation / source integrity handoff

ADR-028 and TASK3_TASK4_EVALUATOR_REMEDIATION.md record recovered category,
engineering choices, before/after evidence, safe-prefix proof and material limits.
Cross-space PAN starts inside NONnumeric K-tokens are out of profile; 20+-digit
continuous maximal runs not partially matched, bridged20th digit fails closed.
This limited grammar and new auxiliary budget need independent approval; do not
claim unavailable vendor/universal PII/TLS/formalRSS/real-provider compliance.
Historical approvals/evidence and Linux split/stall qualifications preserved.
No commit/push/staging; source/test/receipt/link/hash/diff inspection follows below.


Additional manual after-reproduction: from task3/, native Python here-string feeds
all three synthetic Card-prefix examples byte-by-byte to Processor; exact
`Card: [REDACTED] ` reconstruction for each,exit0. Initial attempt from root
resolved Task1's tests namespace and exited1 importing tests.support; rerun using
documented task3 cwd succeeded, no source change. Documentation-only patch with
incorrect Task4 heading also failed before writes, then corrected context used.
These are tooling outcomes, not pytest failures or extra passing cases.


### Final integrity inspection (not extra pytest executions)

Native SHA/AST/path/link/status script exit0:96 of113 baseline tracked paths
byte-identical; exactly17 allowed tracked modifications (12 docs/one production/
four tests-reference files) and two new paths (PAN tests/remediation report).
All Task1/2 implementation/tests/config/pins/locks and Task4 non-doc files unchanged.
Task3 parser/payload/models/upstream/service/app/harness/dependencies/locks/config
unchanged; one source patch, not wholesale replacement. All145 original Task3
test function names remain; AST/decorator comparison changes ONLY the two
explicitly documented obsolete-negative expectation functions. No removals/skips/
xfail modifications.29 named report tests/44 local links resolve. Original AGENTS/
BUILD_LOG/DECISIONS/TEST_EVIDENCE content preserved before appended records.

Git diff --check returned0; Git LF/CRLF normalization notices are not test failures.
Index empty; input gap MD ignored, receipts/temp verification scripts/cache/DBs/
archives not in unignored inventory. HEAD unchanged8d7a3c7, no history rewrite,
staging/commit/push. Final documentation-only edits follow verification; no further
source or test changes after final733/native Ruff26. T3-007 stays IN_PROGRESS /
PENDING INDEPENDENT ACCEPTANCE. No local blocking failure remains; material scoped
PAN boundary/budget and missing-rubric/provider limitations require review.


Final native inventory/key-pattern/Git check exit0:19 authorized paths only,
targeted private/provider-key/credential-URL screen0 in changed content; generated
artifacts/gap MD ignored. Both git diff --check and empty-index cached check0.
HEAD8d7a3c7f3bbd87deec1d83058315a8d732164ca5, main0 ahead/0 behind recorded
origin/main, no fetch/stage/commit/push. Documentation-only final record; T3-007
remains IN_PROGRESS / PENDING INDEPENDENT ACCEPTANCE. No further work authorized.


## E042 - 2026-11-06: T3-007 independent acceptance / Git checkpoint

America/Los_Angeles. User APPROVES within documented13-19-digit synthetic PAN
grammar; T3-007 DONE. These are REPORTED independent results, not executions here:

- 659 non-wire tests passed.
- All17 new PAN real-HTTP wire tests passed with a review-only Linux subprocess
 import-path adjustment.
- 1200 additional randomized PAN streams/8812 model-delta fragments passed.
- Prefix withholding/fail-closed overflow/four-channel bounded-state probes passed.
- No blocking production defect; accepted SSE parser/HTTPX service/FastAPI/transport
 architecture unchanged.

Qualification: E041 actual native Windows149/452/733/427 (1761) and eight Ruff
successes were NOT independently rerun in full. Do not infer full733 Linux suite
or native rerun from selections. Independent Python/pytest versions/commands/
durations/full child receipts not supplied. No review shim or widened supported
pin shipped. No new pytest/Ruff/compile/demo/install/history scan in acceptance.
Preserve spaced-start scope,294/channel auxiliary policy, all historical approvals
and production/RSS/TLS/socket/PII limits. Task4 real-provider interoperability stays
NOT VERIFIED/rubric-dependent; no source/test/config/dependency/lock change.

Actual initial Git/docs checks: Get-Content AGENTS/ledger/current docs/exclude,
git status --short --branch, diff --cached --name-status, rev-parse HEAD,
rev-list --left-right --count origin/main...HEAD. HEAD8d7a3c7f3bbd87deec1d83058315a8d732164ca5,
main0 ahead/0 behind recorded origin, index empty. Exact approved17 tracked changes/
two new remediation paths plus new reviewZIP, no unexpected functional change.
Native SHA/inventory probe exit0 compared113 baseline hashes with E041 inventory:
only intended17 differ, all Task1/2/Task4 non-doc intact. Captured current115-file
tracked/new approved hash snapshot and retained ZIP hash; exclude ZIP via exact
.git/info/exclude entry, no tracked ignore/config mutation. Accepted PAN source/
tests/dependencies will remain identical; no need for test rerun.

Authorized manifest: one Task3 source,five Task3 test/reference files,thirteen
related documentation paths, as listed in remediation report (19 total). Review
complete diff/294-character policy/index contents, explicitly stage only manifest,
exclude cache/temp verification scripts/receipts/env/DB/WAL/SHM/credentials/ZIPs,
run git diff --cached --check, commit once, verify SHA/parent/manifest/clean tree/
recorded-origin counts. No fetch/push/new provider or additional feature.


Actual final inspection/staging: complete tracked diff and both new files read,
including safe-prefix/294-character auxiliary retention policy and scope exclusions.
Native SHA/AST/link checks exit0:102 captured paths outside authorized acceptance
MD edits unchanged; accepted PAN source/tests and Task1/2/Task4 non-doc intact.
Historical Git text in AGENTS/build/decisions/evidence preserved after newline
normalization.29 named report test references/44 local links resolve, targeted
private/provider-key/credential-URL patterns0. An inspection-only scanner first
mistook inventory filename test_redaction.py for a function; filename exclusion
corrected, references validated. No test execution or production correction.

Explicit git add staged exactly19 approved paths. Cached name-status/stat reviewed;
index/working-byte check exit0 after Git newline normalization, no unstaged or
unignored leftovers/excluded artifact path. Verify script/gap input/ZIP ignored;
review ZIP hash unchanged. git diff --cached --check exit0, no active default or
custom hooks. LF/CRLF notices are normalization, not implementation/test changes.
Re-stage final inspection records, repeat staged check, commit once, then report
fullSHA/parent/exact manifest/clean tree/recorded-origin counts from Git. No tests,
install/features/fetch/push. E041 actual native evidence remains authoritative,
not independently rerun in full; no shipped Linux import-path adjustment.
