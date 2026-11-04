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
