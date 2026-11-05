# Task 3: pure synthetic SSE parsing and PII redaction

## Current T3-003 acceptance checkpoint

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
uv sync --locked --extra dev --python 3.12.16
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
