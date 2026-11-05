# Task 3: pure synthetic SSE parsing and PII redaction

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
