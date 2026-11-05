# Task 3: asynchronous synthetic SSE proxy with PII redaction

## Reproduce a successful synthetic assessor demo

From `task3/`, install `uv sync --locked --extra dev --extra serve --python 3.12.16`.
This self-contained recipe uses accepted deterministic test adapters: `Lab` starts
independent loopback upstream/Uvicorn processes on child-selected ports, configures
ephemeral separate credentials, and owns bounded readiness/cleanup. `wire` encodes
the synthetic event profile. No real secret, external provider or reading of the
harness internals is needed. The gate proves delivery before upstream completion;
auth failures must not forward. Fixture stats/control routes are not production
endpoints. This is an assessor fixture API, not a real LLM vendor integration.

```powershell
@'
import json
from tests.http_wire_support import Lab
from tests.support import wire

with Lab() as demo:
    case = demo.plan([
        wire('delta', {'channel': 0, 'text': 'hello private@'}),
        wire('delta', {'channel': 0, 'text': 'example.test '})
        + wire('done', {'channel': 0}) + wire('end', {}),
    ], gate_at=1)
    before = demo.calls()
    for auth in ([], ['Bearer invalid']):
        denied, trace = demo.open(raw=b'{"prompt":"synthetic input"}', auth=auth)
        assert denied.status == 401
        assert json.loads(denied.response.read())['error']['code'] == 'invalid_credentials'
        demo.settled(trace)
    assert demo.calls() == before
    stream, _ = demo.open(case)
    assert stream.status == 200
    demo.peer.event('held', case)
    assert stream.frame() == ('delta', {'channel': 0, 'text': 'hello '})
    assert not any(e['event'] == 'provider_closed' and e.get('case') == case
                   for e in demo.peer.events)
    demo.release(case)
    rest = stream.all()
    assert ''.join(v['text'] for k, v in rest if k == 'delta') == '[REDACTED] '
    assert rest[-1] == ('end', {})
    state = demo.settled(case)
    assert state['active_http'] == state['active_upstream'] == 0
    assert not state['quarantined']
assert all(c.process.returncode == 0 and not c.forced for c in demo.children)
print('PASS: auth rejection, progressive redaction, done/end, clean child exits')
'@ | .\.venv\Scripts\python.exe
```

E039 executed these assertions using a fresh locked25-package environment:
401/401 rejection,200 authenticated SSE, safe `hello ` before release, then
`[REDACTED] ` and done/end, both children exit0/no forced cleanup. A separate
clean-environment demo verified public Uvicorn factory import
`task3_streaming.app:create_app`, actual T3_* environment loading and the same
outcomes. Factory startup/graceful public-API shutdown was tested; literal shell
console/signal behavior was not. See [final audit](../docs/TASK3_FINAL_AUDIT.md).

## Current T3-006 final independent acceptance

T3-001 through T3-006 are independently accepted. T3-006 and TASK-3 are **DONE**,
independent APPROVAL confirmed 2026-11-05 within the accepted synthetic SSE/PII
contract. E040 records documentation review: eight high-level requirements,
21 detailed criteria,73 named tests, implementation symbols/local links and demo
syntax inspected; no blocking discrepancy. Review did not rerun native Windows
tests, inspect unpublished local Git history directly or validate unavailable
vendor requirements. No new executions are claimed. One documentation-only final
acceptance commit is authorized; no push or further implementation.
[Final traceability and findings](../docs/TASK3_FINAL_AUDIT.md)
and E039 in [test evidence](../docs/TEST_EVIDENCE.md) preserve actual native Windows
2026-11-05 results: Task1 **149**, Task2 **452**, Task4 **427**, Task3 **637**
passes, **1665 total**, zero failures/skips/warnings/xfails; all eight Ruff checks
pass. Task3 took56.31s. Accepted source/tests/configuration/dependencies/lockfiles
are unchanged. Original vendor brief unavailable; synthetic-profile, kernel/send,
RSS, deployment and provider limitations remain. The T3-005 acceptance record
below is historical; final acceptance supersedes earlier pending/no-commit gates
only for the authorized documentation checkpoint. All limitations remain.

## Historical T3-005 real-wire acceptance checkpoint

T3-005 is **DONE and independently APPROVED**, confirmed 2026-11-05. E037
final native Windows/Python3.12.16: **637 passed in53.46s**, including57 new wire
cases plus all580 accepted tests; zero failures/errors/skips/warnings/xfails/xpasses.
Ruff lint/format25 pass. All22 accepted Python source/test files, dependencies/lock
and Tasks1/2/4 remain unchanged. Only isolated pytest marker configuration added.
T3-001 through T3-005 independently accepted; TASK-3 IN_PROGRESS. One descriptive
acceptance commit authorized, then stop. No T3-006 or push.
Original vendor brief unavailable; approved synthetic/narrow PII profile unchanged.

E038 records reported independent580 existing passes, all57 wire cases with passing
assertions across split executions,40 additional real-socket fragmentation passes
and no blocking implementation defect. All22 prior files byte-identical; no source
correction required. Linux/Python3.13.5 used import-path change ONLY in extracted
review harness. Combined Linux wire run stalled after50 completed cases;19-case
split printed passing summary but did not return promptly to enclosing command.
This is NOT a clean combined637-test Linux run. Native Windows/Python3.12.16 E037
full637/exit0/Ruff remains authoritative. No new tests during acceptance, shipped
import-path change or widened runtime/kernel/TLS/RSS/vendor certification.

From task3/, with the documented dev/serve extras already installed:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m http_wire
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Three new files under tests: http_wire_child.py (provider/proxy process roles),
http_wire_support.py (readiness/gates/TCP/process cleanup), test_http_wire.py
(independent client acceptance assertions). No mock transport/ASGITransport in
wire cases. A public HTTPX transport wrapper delegates to actual pooled native
HTTP/1.1 I/O and preserves byte partitions; a public ASGI wrapper awaits real
Uvicorn send. Accepted app/service/parser/redactor/encoder are unchanged.

Each child binds 127.0.0.1:0 before reporting its port; real HTTP probes verify
readiness. Secret-free stdin plans/releases and counter-only provider journal
control the fixture; ephemeral separate tokens are injected through an allowlisted
environment, never args/files/logs. The __wire_stats route is TEST WRAPPER ONLY,
not a production route. Logs contain generated case IDs/counters/lifecycle receipts,
not prompts/PII/bodies/keys. Captured private-marker violations:0.

Final-run observations (not production performance/memory guarantees):

| Evidence | Actual observation |
| --- | --- |
| Progressive delivery | Client safe frame ~0.062s while upstream held; one native body chunk received, second read attempt pending, no provider completion until explicit release |
| Redaction/framing | Email/phone/SSN across events/writes, UTF-8 and JSON escapes, two interleaved channels, LF/CRLF/CR/multiline, whole-candidate masking; no TCP-write-boundary assumption |
| Zero forwarding |23 HTTP/auth/body rejection cases plus capacity rejection have zero extra native attempts/independent provider-journal calls |
| Concurrency |16 active streams with distinct sensitive/safe states;17th429/no forwarding; released slot reused successfully |
| Slow reader | Same suspended Uvicorn send/native read count117 across3 control barriers;124004 received native bytes/143545 offered SSE bytes; no next pull during that observation |
| Timeouts | First-event15.016s/read-idle15.047s, observed provider disconnect, no raw tail or end; already200 HTTP stream intentionally closes incomplete |
| Shutdown/disconnect | Gated provider observes disconnect before/after safe output; active runtime drain clean, pool closes once, no false end |
| Memory |1000/5000 events =125000/625000 chars, independent output digests; observed working set65052672->65163264 and65167360->63582208 bytes; peak67788800 bytes in that child |
| Child cleanup | Final run10 children:9 normal0,1 expected invalid-config2,0 forced/killed/live reader threads; failed-fixture cleanup included |

Across the initial subset and two complete runs:30 test children,27 normal0 and3
expected startup2 exits, no forced cleanup/unexpected nonzero/private log matches.
E037 retains each run's counts separately; initial subset deselected only the two
real15s waits. Final run includes both. Counter/journal measurement was tightened
after first complete run and final637/53.46s run verifies it; no production defect.

High-water observations remain within approved caps: candidate256 chars, UTF-8
carry2 bytes, line1055/event1069 bytes, pending256 chars/bytes, encoded frame300
bytes, observed raw block1069 bytes across these probes. Different probes have
different maxima; these are observed counters, not the sum of a process RSS bound.
Working-set probes include interpreter/framework/native/instrumentation overhead.

Slow-reader test requests client receive buffer4096 and child listener send buffer
16384. HTTPX/Uvicorn/asyncio/OS buffers may retain additional bounded bytes;
accepted-socket inheritance/autotuning and total kernel allocation are unmeasured.
Received/offered byte totals differ due to framing/rechunking and are NOT buffer
occupancy. A short real flow-control stall was reproduced; exact10s kernel stall
expiry and120s wall-clock stream cutoff were NOT claimed. Exact10/120 boundaries
remain in accepted deterministic ASGI tests, rerun in this full suite.

Wire cleanup in tested cases confirmed/no quarantine. Resistant/uncertain close
and quarantine remain deterministic ASGI evidence, not invented native cases.
Ordered test shutdown invokes the accepted runtime drain before Uvicorn exits;
stock signal/deployment behavior is not certified. No production TLS/proxy/vendor/
remote billing/physical cancellation or universal PII claim. T3-006 not begun.
Independent T3-005 review approved with qualifications above; complete the one
authorized acceptance commit, then stop. No T3-006 or push.

## Accepted T3-004 checkpoint (history)

FastAPI HTTP integration is **DONE and independently APPROVED**, confirmed
2026-11-05 (America/Los_Angeles). E035 final native Windows/Python 3.12.16: **580 passed in 4.67s**, zero
failures/errors/skips/warnings/xfails/xpasses; both Ruff checks pass, 22 Python
files. Existing 457 tests and all 17 accepted Python files remain unchanged.
FastAPI 0.162.0/Starlette 1.10.0, HTTPX 0.28.1/httpcore 1.0.9, optional Uvicorn
0.54.0; isolated 25-package lock. T3-001 through T3-004 accepted; TASK-3 IN_PROGRESS.
This gate supersedes historical no-HTTP/T3-004 instructions below for current work.
No actual socket/process wire tests, deployment/vendor/universal PII certification,
T3-005 or push. One descriptive T3-004 acceptance commit authorized, then stop.
Original vendor brief remains unavailable.

E036 records reported independent580 suite passes,180 additional randomized
interleaved two-channel ASGI scenarios/4613 upstream reads, five extra fail-closed
scenarios (candidate overflow, unexpected EOF, duplicate done, premature end and
malformed payload), all17 prior Python files byte-identical and no blocking source
defect. Linux/Python3.13.5 review had one nonfatal pytest configuration warning;
native Windows/Python3.12.16 and Ruff E035 remain authoritative. No tests rerun
during acceptance; real sockets/RSS still unverified, no widened-runtime claim.

## HTTP setup and synthetic request contract

From task3/, use its own environment, never a completed task's environment:

```powershell
uv sync --locked --extra dev --extra serve --python 3.12.16
```

The app factory is task3_streaming.app:create_app. It reads T3_ACCESS_TOKEN and
T3_UPSTREAM_URL at lifespan startup; optional T3_UPSTREAM_BEARER is separate.
There are no secret defaults. Access token must be 32-4096 ASCII Bearer-token
characters, and must differ from upstream token. Use a randomly generated value
outside the repository, not a fixture value. Config/body/error values are not logged.

Example operator setup/launch. E039 verified this factory import/environment over
real TCP through public Uvicorn APIs; the literal CLI/console-signal path below
was not exercised:

```powershell
$env:T3_ACCESS_TOKEN = (& .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))")
$env:T3_UPSTREAM_URL = 'http://127.0.0.1:9103/stream'
.\.venv\Scripts\python.exe -m uvicorn task3_streaming.app:create_app --factory --host 127.0.0.1 --port 8003 --no-access-log --log-level warning
```

The URL must identify an already available trusted upstream implementing the
[synthetic SSE profile](../docs/TASK3_REQUIREMENTS.md). Port 9103 is an example,
not a server bundled/launched by this checkpoint. HTTPS or literal-loopback HTTP
only; no query/userinfo/fragment. Set optional upstream credential separately from
the inbound access token. No real LLM vendor API/endpoint/tokenizer is inferred.

POST /stream with one Authorization: Bearer header and application/json (optional
UTF-8 charset). Exact JSON shape: {"prompt":"synthetic input"}. Prompt is 1-4096
Unicode scalars, no unpaired surrogates; entire raw UTF-8 body <=16384 bytes,
absolute upload timeout 10s. Reject duplicate keys/extra fields/non-string prompt,
malformed JSON/UTF-8/BOM, ANY content encoding, duplicate framing/media headers,
Length+Transfer-Encoding, invalid lengths or mismatched actual bytes. De-chunked
bodies are checked incrementally. Queries/credentials/routing/model options are
not accepted. Valid input becomes compact UTF-8 prompt JSON; inbound whitespace/
escape serialization is not preserved. Never forward inbound tokens/cookies/IDs.
No CORS, docs/schema, OAuth, SSE retry/resume, slash redirect or extra route.

Example real client for a separately available synthetic upstream. E039 separately
verified the default factory with environment loading over loopback; this command
does not provide a vendor adapter or certify production deployment:

```powershell
@'
import os
import httpx
with httpx.stream(
    "POST", "http://127.0.0.1:8003/stream",
    headers={"Authorization": "Bearer " + os.environ["T3_ACCESS_TOKEN"]},
    json={"prompt": "synthetic input"}, timeout=130,
) as response:
    response.raise_for_status()
    for part in response.iter_text():
        print(part, end="", flush=True)
'@ | .\.venv\Scripts\python.exe
```

HTTP 200 has text/event-stream; charset=utf-8, no-store/nosniff and no Content-Length.
Clients reconstruct text separately by channel, require valid done/end for success
and treat abrupt closure/missing end as failure even after HTTP 200. Only existing
Processor-approved delta/done/end/error frames are forwarded/rechunked.

Before streaming headers, fixed JSON errors have {"error":{"code":"...","message":"..."}}:

| Status | Code |
| --- | --- |
| 400 | invalid_request (schema/JSON/framing/query, including >4096 chars) |
| 401 | invalid_credentials; WWW-Authenticate: Bearer realm="task3" |
| 404 / 405 | not_found / method_not_allowed (Allow: POST) |
| 408 / 413 / 415 | request_timeout / request_too_large / unsupported_media |
| 429 | stream_capacity_exceeded (no queue, zero upstream on rejection) |
| 502 | upstream_error / invalid_stream / stream_limit_exceeded |
| 503 / 504 | service_unavailable / stream_timeout |

Runtime availability -> authentication -> metadata -> bounded upload/strict JSON ->
HTTP cap -> service admission/header preflight -> response.start. Preflight reads
zero upstream body bytes; payload/stream errors after 200 cannot change status.
Local postheader failures close without locally constructed SSE error/end. The
existing upstream synthetic error is still Processor-owned and sanitized. A
best-effort empty HTTP close uses the existing last-send/overall deadline only.
No further writes after known disconnect/send failure/stall/shutdown. Ordinary
nonadmitted JSON errors have no upstream owner; their connection lifecycle and
request-header allocation are server responsibilities, not certified by ASGI tests.

## ASGI send deadlines, ownership and verification

The custom Response awaits every admitted response.start/body/final-empty send
under min(now+10s, the accepted session's original 120s deadline). Send observation
at the deadline fails; no timer restarts overall or grants a new error-send budget.
One post-upload receive monitor handles disconnect without stealing body chunks.
No producer queue or detached reader. A separate atomic global HTTP cap16 remains
held through terminal ASGI send/cleanup, even after accepted upstream slot release.
The 17th is rejected immediately across app instances, before another upstream call.

One anchored additional 1s joins HTTP operation/send cancellation, monitor shutdown
and accepted session.aclose; existing service grace is not renewed. Shielded worker
stays retained if the request/lifespan waiter is cancelled repeatedly. Unconfirmed
cleanup keeps ownership/slot, quarantines admission and prevents shared-pool close.
Late confirmed HTTP work releases its slot. If service confirmation arrives after
its guard returned false, explicit runtime.aclose rechecks public confirmation,
without retrying resource close; quarantine stays sticky. Request success requires
source completion, final ASGI send and confirmed teardown.

Lifespan initializes one pooled service only after valid config, blocks admission
on shutdown, cancels/drains HTTP owners then calls the accepted service shutdown.
app.state.runtime retains ownership even on failure; unclean_shutdown stays true
until confirmed (including cancelled lifespan waiters). Failed shutdown raises a
fixed Unclean streaming shutdown. Pool's existing one-time 1s close budget follows
drained request ownership; no repeated request-grace renewal. Retain the app and
supervise uncertain resources; GC, asyncio and local cancellation do not certify
physical remote-provider termination/billing cancellation.

Executed direct-ASGI evidence: first sanitized safe prefix at raw read1; while its
send is blocked, 20 scheduler turns leave reads1; release permits read2, whose
separate upstream gate still blocks completion. Three 256/256/88-scalar sends use
the SAME read1. Send tests cover 9.999/10/10.001s, and an overall-budget send started
at117s remains pending119.999 but aborts120/120.001, not127. Disconnect/body/header/
raw-tail/cancellation/shutdown/quarantine/late-confirmation tests are included.
Read/send/cancel gates, not wall-clock sleeps, control assertions.

Bytes already offered to ASGI cannot be retracted; resistant sends may complete
that one already-offered SANITIZED frame after local cancellation. No new sends
follow failure, and no success flag follows unconfirmed teardown. This is not
actual socket acknowledgement, OS/proxy-buffer/RSS/process-cleanup evidence.
Those concerns remain T3-005; no real wire services/processes started here.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

E035 records exact basetemp commands, setup/versions, actual final 580/4.67s pass,
zero failures/skips/warnings/xfails and Ruff22, plus initial fixture failures/fixes.
No accepted source/test correction; Tasks 1/2/4 unchanged. Independent review now
approved; next one acceptance commit, then stop. No T3-005 or push.

## Accepted T3-003 checkpoint (history)

Async HTTPX adapter and owned StreamService are **DONE and independently APPROVED**,
confirmed 2026-11-05 (America/Los_Angeles). E033 native Windows/Python 3.12.16: **457 passed
in 4.09s** (362 accepted pure tests unchanged +95 new async cases), zero failures/
errors/skips/warnings/xfails; Ruff lint/format pass (17 Python files). HTTPX 0.28.1 /
httpcore 1.0.9, isolated 15-package lock, locked offline sync/import inventory checked.
All accepted pure code/tests and completed Tasks 1/2/4 remain byte-identical.
T3-001 through T3-003 are DONE; TASK-3 IN_PROGRESS. This gate supersedes historical
T3-002 no-network/no-T3-003 instructions below only for implemented async work.
One descriptive T3-003 acceptance commit authorized, then stop. No public HTTP
endpoint, wire processes, vendor API, push or T3-004 work.

E034 records reported independent 457 passes, 240 additional randomized HTTPX
fragmentation cases, resistant-cancellation/concurrent-shutdown checks, 11 pure
file comparisons and compilation. Linux/Python 3.13.5 review produced one nonfatal
pytest configuration warning; native Windows/Python 3.12.16 and Ruff E033 remain
authoritative. No tests rerun during acceptance, no real socket or ASGI validation
claimed. Original brief unavailable; synthetic profile limitations remain intact.

## Accepted T3-001/T3-002 foundation history

T3-001 is independently ACCEPTED (2026-11-05 America/Los_Angeles) for the explicitly
defined [synthetic profile](../docs/TASK3_REQUIREMENTS.md), ADR-022. The original
vendor brief remains unavailable. This is not universal PII detection or a real
vendor integration. Completed Tasks 1/2/4 are separate and unchanged.

**T3-002 is DONE and independently APPROVED**, confirmed 2026-11-05.
E032 records reported independent review; no new local tests in acceptance.
E031: **362 passed in 3.02s**, zero failures/errors/skips/warnings/xfails/xpasses;
Ruff lint and formatting pass (11 Python files). Native Windows/Python 3.12.16,
pytest 9.2.0/Ruff 0.17.3. Isolated eight-package lock; standard-library-only runtime.
No HTTPX, FastAPI, upstream transport, service, HTTP route or socket harness yet.
One descriptive accepted T3-001/T3-002 foundation commit is authorized.
Preserve source/tests/configuration/pins/lock; no T3-003 or push.

Reported independent review: 362 passes; 1200 randomized interleaved streams; 2961
channel-reference comparisons; 256 candidate-prefix probes/character-257 rejection;
376 truncated-wire cuts without whole-value PII leakage; 24000-event retained-state
test and compilation passed. No blocking production defect found. Linux/Python
3.13.5/pytest 9.0.2 had one pytest configuration warning (details not supplied).
This is outside the project-pinned Python 3.12 runtime, not a new supported-runtime
claim or replacement for authoritative native Windows/Python 3.12.16/pytest 9.2.0
and Ruff 0.17.3 evidence. No config/pin changes or warning suppression are shipped.

## Install and verify

From task3/, with uv installed and Python 3.12.16 available:

```powershell
uv sync --locked --extra dev --extra serve --python 3.12.16
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m ruff format --check src tests
```

Local ignored uv tool is ../.tools/bin/uv.exe; local verification used
`UV_CACHE_DIR=..\.cache\uv` and `--python ..\.venv\Scripts\python.exe` to select
the already installed 3.12.16 base without changing Task 1's environment. A locked
offline sync/import check passed. uv 0.13.7; build requirement setuptools 82.0.1.
Native pinned-environment execution is verified on Windows; the qualified Linux
review above does not widen supported pins. SQLite 3.53.1 is interpreter metadata only;
Task 3 neither imports SQLite nor accesses a database.

## Pure interfaces and ownership

- `models`: frozen `Limits`, `RawEvent` and `Event`; exact integer channel 0-3,
  fixed error codes/messages, private payload repr. Limits may be tightened but
  not enlarged above approved caps. RawEvent is untrusted input, not safe output.
- `SSEParser.feed(bytes)` / `finish()`: lazy event iterators. Raw chunk <=4096,
  line <=8192 bytes including terminator/BOM, event <=16384 bytes including all
  metadata/comments. Strict incremental UTF-8, CR/LF/CRLF, multiline data; ignore
  comment/id/retry/unknown fields. Duplicate/missing event fields fail closed.
- `payloads.inspect_event`: bounded JSON lexical precheck then stdlib JSON syntax/
  escape decoding; exact profile schemas, duplicate decoded-key rejection, no
  coercion. JSON depth <=8, object members <=8, numeric lexemes <=16 bytes;
  decoded delta <=4096 Unicode scalars. No arbitrary extension/provider fields.
- `Redactor.process(Event)`: four independent, lifetime channel identities; holds
  candidates across deltas/events, emits only classified complete candidates.
  Only valid done finalizes a tail; malformed EOF/error never flushes it.
- `Processor.feed(bytes)` / `finish()`: pure parser -> payload -> redactor -> safe
  encoder composition, yielding one bounded frame at a time. No producer queue.
  A validated end/error terminates consumption, including trailing bytes within
  its current chunk; no claim that those trailing bytes were validated.
- `encode_event`: shape/size encoder only, NOT an independent privacy filter.
  Encode redactor output via Processor; do not bypass it with raw model deltas.
  Error frames contain only fixed code/message; no raw provider diagnostics.

Fully consume or explicitly close each iterator before another call on that owner.
Abandoned iteration or malformed input latches failure and clears retained buffers;
do not resume a failed owner. `abort()` clears raw tails and revokes success.
After successful end, `redactor.success` describes pure protocol completion, not
proof that a future HTTP client received it. A transport must own send cancellation.
Processor raises generic StreamError for malformed input without automatically
inventing a postheader error response. A future transport must select the approved
pre/postheader policy; known upstream error already yields one fixed error frame.

## Redaction and bounds

Candidate alphabet is EXACTLY ASCII letters/digits plus `._%+@-`. Retain every
unfinished maximal candidate, <=256 characters per channel. A real delimiter or
validated done makes it safe to classify. Mask the whole candidate once with
`[REDACTED]` if it contains @, an approved phone interval or an SSN interval.
Canonical email classification follows the documented ASCII local/domain limits;
the stronger @ rule masks malformed email-like candidates too.

Phone forms are + followed by 8-15 ASCII digits (first 1-9) or DDD-DDD-DDDD;
SSN is DDD-DD-DDDD. Phone/SSN intervals have ASCII-digit boundaries. All pattern
characters belong to the candidate alphabet: no supported match can cross a real
delimiter. Character 257 aborts before retention, never releases a prefix. A long
harmless token can therefore fail; @ tokens and surrounding K punctuation can be
overmasked. No Unicode normalization, percent decoding, formatted-phone/name/card/
internationalized/obfuscated PII guarantee; unsupported forms are not silently
claimed covered. JSON escapes ARE decoded before inspection.

Separate maxima: four holds total <=1024 ASCII bytes; pending safe output <=1024
scalars AND 8192 bytes; output delta fragments <=256 scalars; serialized event
<=8192 bytes, checked before extending the retained encoding buffer. Line/event
limits count raw bytes, delta/fragment limits count Unicode scalars, and serialization
checks escaped UTF-8 separately. Stats expose current/peak parser, decoder, candidate,
hold and pending counts; Processor records peak encoded frame length. Current event,
decoded payload and encoding scratch are separately bounded, not a claimed RSS sum.

No retained collection grows with stream length. Code yields safe text before
global end when a real delimiter exists; an unfinished candidate can delay content.
Actual async backpressure, 16-stream concurrency admission, network deadlines and
1000 ms cleanup execution remain T3-003/004 work. Pure generator tests are not real
HTTP latency/memory/cancellation or uncooperative-provider termination evidence.

## Verification coverage and limitations

Tests exercise all four representative PII values across every raw-stream byte cut
and every model-delta cut, every partition of a short candidate, two Unicode wire
representations across every cut, 32 seeded chunk/delta partitions, and 16 seeded
adversarial-content comparisons against an independent manual whole-input oracle.
They also cover exact 255/256/257 candidates, 8192-byte lines/16384-byte events,
decoded/escaped-output limits, strict payloads, duplicate keys, channel transitions,
metadata dropping, truncation, fixed errors and abandonment. A 5000-event stream
and 1000 empty deltas with four full holds verify bounded retained counters.
No raw synthetic PII appears in decoded emitted text or error/log assertions.

E031 preserves initial 319-pass sandbox run with one cache warning, initial six
Ruff B008 findings, a corrected test-helper import collection failure, intermediate
334-pass verification and final 362-pass execution. No tests/warning filters were
weakened. Failures are not presented as passing runs. No real credentials/prompts/
customer data; fixtures use synthetic values only. No networking/wire/RSS/vendor
or universal privacy claim. T3-002 is accepted; next action is the one authorized
foundation Git checkpoint, then stop. Original brief/synthetic profile limitations
remain unchanged.

## Async upstream and ownership API (T3-003)

`UpstreamSettings(url, bearer_token=None)` is trusted immutable configuration;
HTTPS or literal-loopback HTTP only, no userinfo/query/fragment, no secret defaults.
`UpstreamRequest(body: bytes)` holds already formed request bytes (1-65536), private
repr; the adapter uses fixed POST/application-json, preserves bytes and invents no
provider/prompt schema. Future inbound route/auth/body validation is T3-004 approval
work. There is no caller URL/header/cookie interface. Operator URLs/credentials
are separate from inbound credentials. No environment/secret is printed or logged.

`UpstreamAdapter` owns one pooled AsyncClient with 5 s pool/connect/write, 15 s read,
16 HTTP/1.1 connections, TLS verification, trust_env=False, retries=0, redirects
disabled and cookie rejection. Response must have status 200, one text/event-stream
Content-Type (optional UTF-8 charset), and NO Content-Encoding, even identity.
It never reads a diagnostic body for a rejected response. Private HTTPX/httpcore
HTTP/1.1 log records are suppressed only inside owned I/O context; other callers'
logging remains enabled. Arbitrary external telemetry/untrusted transports are
outside that logging guarantee; application body/debug logging must remain disabled.

`StreamService(adapter)` owns request sessions and final pool shutdown. Use:

```python
service = StreamService(adapter)
try:
    async with service.stream(UpstreamRequest(validated_request_bytes)) as session:
        async for sanitized_frame in session:
            await downstream_consumer(sanitized_frame)
finally:
    clean = await service.aclose()
    # If False, retain service/resource ownership and handle unclean shutdown.
```

This snippet describes the library seam, not an implemented HTTP endpoint.
Async context entry admits before any await/send; Capacity is unconditionally process-global
across services/event loops, at most 16, with immediate CapacityExceeded/zero request
for the 17th. Clock/transports are trusted test dependencies; there is no per-instance capacity override.
Every session has its own accepted Processor and one reader; no producer queue.
Fully consume or exit/close the context. Retain the service if cleanup is unconfirmed;
Python GC/remote-provider cancellation are not physical termination guarantees.

Service yields only Processor frames. Errors raise fixed StreamError codes before/
after output; it does not invent an HTTP response or automatically send after failure.
Known synthetic upstream error already becomes the accepted fixed error frame.
Terminal end/error exhausts the pure iterator normally, closes resources, then yields
the terminal frame. Unconfirmed terminal cleanup prevents a false success end.

Small raw transport blocks flow immediately; do not use a coalescing 4096-byte
iterator that waits for more data before delivering a small event. Public response
AsyncByteStream is read directly without content decoding; response close is owned
separately, avoiding hidden EOF-close cancellation/is_closed ambiguity. One raw block
is capped at 65536 bytes (pinned native HTTP/1.1 read size), then lazily split into
<=4096 processing slices. A larger injected block is rejected before retained growth.
HTTPX/httpcore/OS buffers and encoding scratch add overhead; no total RSS or real
wire allocation claim. Parser's independent 8 KiB line/16 KiB event caps still apply.

First-valid deadline is 15 s from admission INCLUDING header acquisition. Valid
empty delta counts; comments/incomplete frames do not. Read-idle gets 15 s only
while awaiting the next body read. Overall is monotonic 120 s from admission and
has an owned timer that closes even when downstream stops pulling. First-valid
timer likewise closes if consumer never pulls. Checks occur at bounded processing
checkpoints; late observation cannot reject a first event already accepted timely.
Events/read results observed at a deadline lose; no budget refresh from small chunks.

One 1 s cleanup grace is anchored when close starts, shared by pending open/read
cancellation and response close. Shielded close work is retained past caller
cancellation/grace expiry. Unconfirmed/failed cleanup quarantines new admissions,
keeps the owner/slot and never closes the shared pool beneath it. Late confirmed
cleanup releases the slot but does not reopen quarantined admissions. A failed close
needs supervisor intervention; there is no automatic retry/recovery API. Pool shutdown
has its own one-time 1 s resource-close budget only after response owners drain,
and keeps an uncertain close task. Repeated aclose does not renew response grace.

The service has fairness/cancellation checkpoints around bounded synchronous
Processor steps, not preemptive interruption of Python bytecode. T3-004 must await
actual ASGI send under min(10 s, remaining session.deadline), monitor disconnect and
close the session on failure. Service's watchdog closes upstream, not a caller's
blocked socket send; an async generator alone does not certify socket backpressure.

New test evidence: first safe output after one read; still ONE read across 20
scheduler turns with no demand; second pull starts read TWO and blocks at its gate;
after release, final output has redacted cross-chunk PII and total reads TWO.
Three pending 256/256/88-scalar frames consume ONE read, then controls use read TWO.
A 2000-event test asserts one read per demand and 2001 total raw reads including
terminal controls. Sixteen parallel requests accepted/17th zero upstream; uncertain
connect/read/close work stays owned and blocks admissions. E033 includes exact tests,
timing/cancel/quarantine coverage and the initial delayed-watchdog failure/fix.
