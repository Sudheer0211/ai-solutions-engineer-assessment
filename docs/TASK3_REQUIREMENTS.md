# TASK-3 / T3-001: approved synthetic streaming contract and implementation gates

## Current T3-007 corrective contract - 2026-11-06

**DONE / independently APPROVED within the documented synthetic PAN grammar.**
User confirmation2026-11-06/E042; original approvals preserved. User confirms the recovered
original PII list includes email, SSN and credit cards; phone is additional
coverage. The ignored supplied gap audit was read at the user's clarified path;
full verbatim vendor brief/rubric remains unavailable. Historical T3-001..006
approvals/evidence below remain historical and do not cover the omitted PAN category.

T3-PII-PAN: implemented synthetic13-19 ASCII digit maximal numeric runs, optional
single ASCII space/hyphen between nonempty groups, no Luhn/issuer check. Standalone
contiguous/hyphen/spaced examples supported across every transport/delta boundary.
Whole classified compound becomes `[REDACTED]` once. Exact engineering grammar,
overlaps/false positives and exclusions are in the
[corrective report](TASK3_TASK4_EVALUATOR_REMEDIATION.md). Cross-space bridging
starts only after a wholly numeric K-token/span; a spaced value beginning inside
`word4111` or initial K punctuation is outside the profile. Single spaces are
held conditionally, never added unconditionally to K.20th bridged digit fails
closed; continuous20+-digit maximal runs are outside PAN syntax, never suffix-matched.

This supersedes historical P1 card exclusions/P3's all-PII-within-K proof/L5's
1024 aggregate for the PAN path ONLY. K-token cap256 is unchanged; auxiliary
numeric prefix<=37 + joining space + current K-token<=256 gives conservative
294 raw held characters/channel,1176/four channels and4 known-space flags. Pending,
encoded/input/parser/channel/deadline caps unchanged. New grammar/auxiliary budget
are independently accepted engineering choices for this profile, not original rubric text.
New proof withholds complete numeric possibilities until a nonextending boundary
or valid done. Unsafe EOF/errors/cancellation never flush holds or space flags.

E041 fresh native Task3 **733** (637 retained+96 new), Task1 149/Task2 452/Task4 427:
**1761 passes**, all8 Ruff checks0. E042 records independent659 non-wire/17 new
PAN wire passes with review-only Linux import-path adjustment,1200 random streams/
8812 delta fragments and bounded-state/privacy probes. No blocking production
defect. Full native results NOT independently rerun; no new tests/deps/features
in acceptance. One Git checkpoint authorized, no push. Task4 remains implementation-
identical, real-provider interoperability NOT VERIFIED/rubric-dependent.

## Historical T3-006 independent acceptance - 2026-11-05

America/Los_Angeles. Independently APPROVED within accepted synthetic SSE/PII
contract; T3-006/TASK-3 DONE. E040 records reported review of eight requirements,
21 criteria,73 named tests against prior source archive, implementation symbols/
local links/demo syntax and consistent E039 evidence, with no blocking discrepancy.
Final documentation review did not rerun native Windows tests, inspect unpublished
local Git history directly or validate unavailable vendor requirements. E039
actual1665 passes/eight Ruff checks remain unchanged. Preserve original-brief,
production/RSS/TLS/socket/PII/environment limitations and all accepted source/
tests/config/dependencies/locks. One final documentation-only commit authorized;
no push or new work. The records below preserve historical local-review gates.

## Historical T3-006 local audit / review handoff - 2026-11-05

America/Los_Angeles. Audit over6b76878: R1-R8/Q01-Q21 plus all approved P/L/I/H/W
policies mapped in [final audit](TASK3_FINAL_AUDIT.md). No contract changes.
E039 fresh native Windows/Python3.12.16:149/452/427/637 passes (1665), all8 Ruff
checks0, no failures/skips/warnings/xfails. Clean locked Task3 environment25 packages,
fixture and default-factory/env real-TCP demos passed with sanitized progressive
output,401 rejection,done/end and confirmed cleanup. Initial ignored audit utility
adapter failure/correction are tool evidence, not an application defect or extra
passing test. Accepted implementation/tests/pins/config/locks and Tasks1/2/4
preserved. History screen found no actual disclosure; scan/ignore/OS/deployment
limitations retained. Original vendor brief still unavailable; synthetic choices
remain approved engineering policies, not recovered original requirements. Exact
ASGI timing is not a kernel/TLS/remote guarantee; E038 Linux split/stall qualifications
remain. Local READY, independent acceptance pending. T3-006/TASK-3 IN_PROGRESS.
No staging/commit/push or new feature authorized; stop for review.

## Historical checkpoint records and approved contract

Date: 2026-11-05 (America/Los_Angeles). Baseline: `7e37045`.
Status: **T3-001 independently APPROVED / accepted**, user confirmation 2026-11-05.
Approval is ONLY for the explicitly defined synthetic assessment profile, not an
unavailable original vendor brief, universal PII detection or vendor interoperability.
P1-P8 and L1-L10 are approved ENGINEERING POLICIES, not original assessment numbers.
T3-002 independently APPROVED, user confirmation 2026-11-05; DONE, committed 0a75587.
E032 records qualified review provenance. T3-003 independently APPROVED, confirmed
2026-11-05; DONE. E033 preserves actual native execution; E034 records qualified
independent review and this acceptance Git checkpoint, without new test executions.
T3-003 accepted baseline e4bd001. T3-004 independently APPROVED, user confirmation
2026-11-05; DONE. E035 preserves actual native verification; E036 records qualified
review and acceptance Git inspection without new test executions. One descriptive
acceptance commit authorized; preserve all source/tests/config/dependencies/lock.
T3-005 independently APPROVED, user confirmation 2026-11-05; DONE. E037 preserves
actual authoritative Windows verification; E038 records qualified Linux split review
and this Git checkpoint, not new test execution or a clean combined Linux637 run.
One descriptive acceptance commit authorized, preserving wire/source/tests/pins/lock.
T3-006 final audit independently APPROVED; T3-006/TASK-3 DONE. See E039 actual
verification, E040 qualified independent documentation acceptance and
TASK3_FINAL_AUDIT.md. Historical pending/no-audit gates below are superseded only
for the authorized final documentation acceptance checkpoint. Loopback/working-set observations remain qualified,
not kernel10s/TLS/vendor/deployment/formal RSS certification. No push. T3-H policies below define
the implemented HTTP choices; they are not recovered original assessment wording.
The T3-003 section below supersedes historical no-network gates for the accepted
async checkpoint only; pure contract remains unchanged.
The additional mandatory rules preserve valid-done-only finalization, no raw EOF/
overflow flush, separate byte/scalar/encoded limits, strict channel sequencing,
duplicate-key rejection and equality of detector/candidate alphabets.

## Provenance and available assessment requirements

Second inspection found NO original Task 3 assessment brief. Searched tracked/
available repository requirements/text/PDF/Word filenames, reachable Git Task 3
filenames and supplied text attachments. Matches were Task 1 SSE/PII exclusions,
Task 4's no-Task-3 instruction, unrelated scene-schema Task 3 and unrelated secret
redaction guidance. None supplies this assessment's exact PII/event contract.
No separate PDF/Word brief was found in the searched attachment inventory. This
is a bounded search, not a claim about unavailable external assessment materials.

The following are HIGH-LEVEL USER-SUPPLIED REQUIREMENTS, not recovered verbatim
original brief text. Do not promote approved engineering policies T3-P/T3-L into original brief wording.

| ID | Available high-level requirement |
| --- | --- |
| T3-R1 | Independent asynchronous LLM streaming proxy consuming and forwarding SSE |
| T3-R2 | Detect and redact PII before emitting sensitive output |
| T3-R3 | Handle arbitrary transport/UTF-8/SSE/model-delta splits under a confirmed logical-text contract |
| T3-R4 | Bounded buffering and memory, including malicious or unusually long input |
| T3-R5 | Deliver safe output before complete upstream consumption; correct backpressure |
| T3-R6 | Correct cancellation/disconnect/error cleanup without raw-buffer leakage |
| T3-R7 | Preserve the confirmed semantics of framing, metadata and terminal signals |
| T3-R8 | No sensitive prompts, responses, credentials or redaction buffers in logs |

## T3-P1: approved PII grammar and replacement

**ALL rules here are approved engineering policies for the synthetic profile.** Detection is deliberately
narrow and syntactic; not universal PII discovery, vendor tokenization, entity
recognition or legal/compliance certification. Use synthetic fixtures only.

Define ASCII candidate alphabet K as letters A-Z/a-z, digits 0-9 and exactly
`._%+@-`. A candidate is a MAXIMAL consecutive run of K characters in one logical
channel. Every other Unicode scalar is a delimiter. Hold a candidate until its
delimiter or a validated channel-done event; never emit any part while unfinished.

| Pattern ID | Approved recognized syntax / bounds |
| --- | --- |
| T3-PII-EMAIL | ASCII local part: one or more atoms separated by single dots, atom characters letters/digits/underscore/percent/plus/hyphen; local length 1-64, no leading/trailing/consecutive dot. Then one @. Domain: at least two dot-separated labels, each 1-63 ASCII alnum/hyphen with alnum first/last; final label 2-63 ASCII letters; domain <=253, total address <=254 characters. Not full RFC mailbox syntax. |
| T3-PII-PHONE | Either `+` followed by 8-15 ASCII digits, first digit 1-9, or exactly `DDD-DDD-DDDD` with D an ASCII digit. No adjacent ASCII digit immediately before/after the matched interval within the candidate. These are syntactic forms, not country/assignment validation. |
| T3-PII-SSN | Exactly `DDD-DD-DDDD`, no adjacent ASCII digit before/after the interval. All numeric combinations masked; no issued-number validation. |

The email grammar classifies canonical examples. Additional CONSERVATIVE rule:
**any candidate containing @ is masked in its entirety**, even if invalid/ambiguous
as an email. This prevents malformed/overlong-in-grammar email-like values from
falling through as safe text. Candidate-size overflow still aborts, never truncates.
Phone/SSN recognition examines intervals inside the complete bounded candidate.
If ANY rule matches, replace the ENTIRE candidate once with literal `[REDACTED]`;
do not reveal category, original length, last digits or hash. Thus overlapping
matches cannot double-redact, and surrounding K punctuation/text can be removed.
Completed unmatched candidates and delimiters are preserved exactly.

Accepted consequences: even harmless @ tokens are masked; punctuation
within a masked candidate may disappear. A harmless uninterrupted identifier/URL
longer than 256 characters aborts. Phone numbers with spaces/parentheses, bare digit
phones, Unicode/internationalized addresses, names, postal addresses, cards, other
national IDs, obfuscations and encoded forms are NOT covered by these patterns.
Those categories cannot be silently claimed compliant without the original brief.

## T3-P2: normalization, logical text and Unicode

Decode transport UTF-8 incrementally and strictly; remove at most one leading BOM.
Malformed/incomplete UTF-8 fails closed. After SSE assembly, parse complete JSON
and decode its normal string escapes BEFORE redaction. Reject duplicate decoded
keys, unpaired surrogate values, nonfinite numbers and invalid payload types.
No string/numeric coercion, case folding, NFC/NFKC, percent/HTML/base64 decoding,
zero-width removal or transliteration. Preserve unmatched Unicode scalars exactly;
non-ASCII lookalikes are outside P1's grammar. Strict rejection is an application
profile choice, not an assertion that browser UTF-8 error recovery behaves alike.

Text for each channel is the exact concatenation of that channel's decoded `text`
values, WITHOUT separators inserted at event/delta boundaries. States survive
adjacent events, arbitrary HTTP partitions and interleaving with other channels.
No cross-channel concatenation/detection; clients must reconstruct each channel
independently. Channels are integer 0-3, at most four DISTINCT channels per response,
never reused after done. State never crosses requests or reconnects.

## T3-P3: safe-prefix proof and over-limit behavior

All recognized sensitive patterns consist exclusively of K. Therefore a recognized
match cannot cross a delimiter. At a real delimiter, the preceding maximal K-run
is complete and no future channel continuation can change it. Classify the entire
run, emit its unchanged text or one replacement, then emit the delimiter. Retain
only the unfinished final K-run. Keep scalar order within each channel.

Inductive invariant: every emitted candidate is complete and classified; every
candidate that might extend is wholly withheld. Transport/event splits insert no
delimiter, so partitions cannot invalidate this invariant. A validated channel-done
is the ONLY synthetic logical EOF permitting final candidate classification.
Abrupt transport EOF/error/cancellation is NOT such a boundary: discard pending
raw candidates/output, never flush them. This is a proof under P1/P2's grammar,
not a proof against unmodeled semantic/obfuscated PII or cross-channel rendering.

Candidate up to 256 ASCII characters is allowed. Before retaining character 257,
raise generic stream_limit_exceeded and stop; no prefix of that run was emitted.
Event/line/delta/output limits are likewise checked before growing their retained
buffers past the cap. Never cut an over-limit value into apparently safe pieces,
drop a suffix and continue, or release raw text because a timer expired.
The pure detector exposes deterministic high-water counters for verification.

This trades one-candidate latency and conservative masking/rejection for an easily
reviewable proof. Ordinary text with delimiters can flow before upstream completion.
An ambiguous unfinished word may produce NO content until delimiter/done/limit;
there is no universal content-latency promise for arbitrary malicious input.
Do not replace this with a guessed regex overlap window. Regexes alone neither
provide safe partial-match semantics nor establish complete semantic PII coverage.

## T3-P4: approved synthetic upstream and downstream SSE profile

This is a SYNTHETIC ASSESSMENT INTERCHANGE PROFILE, not an inferred real LLM API.
Real providers require a separately approved adapter. Upstream must be successful
HTTP 200 with text/event-stream, UTF-8 and no Content-Encoding. Redirects/retries/
automatic reconnect/resume are disabled. Destination and separate credentials are
trusted configuration, never client-supplied; no inbound credentials/cookies forwarded.

Parser follows SSE line/event semantics: CRLF, LF and lone CR, split terminators,
blank-line event dispatch, multiline data joined with LF, and one optional leading
BOM. Each application event requires exactly one `event` field and at least one
`data` field. Reject duplicate event fields as profile ambiguity (stricter than
SSE's last-value behavior). Empty blocks and blocks containing only comments or
ignored metadata have no application dispatch. A block containing event or data
requires BOTH; missing counterparts, unknown event types and invalid JSON are
profile errors. Whitespace-only lines are fields, not blank separators.

| Upstream event | Exact decoded JSON object | State / downstream behavior |
| --- | --- | --- |
| `delta` | `{"channel":0,"text":"synthetic text"}`; exact keys; channel exact integer 0-3, text 0-4096 Unicode scalars | Open channel if first seen; append to its redactor. Empty text valid, no empty output event required. Delta on closed channel is invalid. |
| `done` | `{"channel":0}`; exact key | Require previously opened, not-yet-done channel. Classify final candidate, emit remaining safe text then exactly one done for that channel. No further channel text permitted. |
| `end` | `{}` | Require all opened channels done; zero-channel empty response allowed. Emit one end after all pending safe output; stop reading and close upstream. Trailing upstream bytes are not read/validated or forwarded. |
| `error` | `{"code":"upstream_error"}`; exact key/value | Terminal failure: discard all pending raw state; emit proxy-owned generic error if possible; no done/end success signals. |

No extra JSON keys/metadata, arrays, fragmented JSON across separate events, other
delta shapes, usage/tool-call/reasoning fields or vendor sentinels are supported.
Multiline data may contain one complete JSON value. SSE events need not align
with HTTP chunks; JSON must be complete only at event dispatch, not at each chunk.

Downstream uses the SAME delta/done/end payload shapes, generated from validated
state, and additionally a proxy-owned error event defined in P7. UTF-8 JSON is
serialized safely and framed with `event: <fixed type>`, one `data: <JSON>` line and
a blank LF line. Text scalars/newlines are JSON-escaped as necessary, never inserted
as raw SSE field syntax. Emit text in fragments of at most 256 Unicode scalars.
Rechunking and suppression of empty events are allowed; preserve per-channel text
and control order, not original bytes, event count, inter-channel delivery timing
or serialization. Clients must not concatenate text across distinct channels.
No downstream Content-Length; text/event-stream, no-store, nosniff; do not propagate
upstream cookies, redirects, raw headers or compression. No default heartbeat.

## T3-P5: metadata and terminal/truncation policy

Comments, `id`, `retry` and unknown SSE field names are parsed/bounded then DROPPED,
never forwarded/logged/retained as a replay journal. Do not forward Last-Event-ID
or enable reconnection. Apply standard NUL-id/nondigit-retry interpretation if
needed by parser tests, but these fields cannot affect application authority/output.
An unknown event TYPE is different from an ignored field and is a profile error.
Only fixed validated event names and generated integer channel IDs can reach output.
This deliberate metadata loss is approved; arbitrary transparent metadata and
the guarantee against metadata PII leakage cannot both be assumed.

Only fully framed end is success. EOF before end, an unterminated event/JSON/string,
unfinished UTF-8, done for unknown/closed channel or end while a channel remains
open is truncated/invalid stream, not successful implicit flush. If done previously
validated a channel, already emitted classified output stays valid, but a missing
global end is still failure. Do not invent a vendor done marker or success on EOF.

## T3-P6 / T3-L: separately measurable approved engineering budgets

| ID | Limit (approved policy, not an original assessment number) | Enforcement |
| --- | --- | --- |
| T3-L1 | Raw processing chunk <=4096 bytes; incremental UTF-8 carry <=3 bytes | Single pull path; transport allocation bounds additionally verified in T3-003 |
| T3-L2 | Physical partial/complete line <=8192 raw UTF-8 octets including any terminator | Check before append; blank/CRLF split counts exact; initial BOM counts against first line |
| T3-L3 | Event <=16384 raw bytes, including all comments/fields/terminators up to separating blank line | Counter resets at each block; no infinite comment/metadata block bypass |
| T3-L4 | One decoded delta <=4096 Unicode scalars; exact tiny object schemas | Bounded event before JSON parse, then schema validation; JSON allocation overhead audited separately |
| T3-L5 | Unresolved K-run <=256 ASCII chars per channel; <=4 distinct channels | Check before character 257; reject IDs outside 0-3 before allocating state; <=1024 unresolved raw candidate bytes total |
| T3-L6 | Pending safe output <=1024 scalars AND <=8192 encoded bytes; one encoded event <=8192 bytes | Output fragment <=256 scalars, await consumer, no unbounded event/metadata queue |
| T3-L7 | <=16 admitted active streams per process, zero waiting-stream queue | Future HTTP admission rejects excess before upstream work; multiworker total is workers x16 |
| T3-L8 | Pool/connect/write <=5000 ms each; first application event <=15000 ms; upstream read idle <=15000 ms | Explicit upstream deadlines; comments/metadata do not renew first-application-event budget |
| T3-L9 | Overall stream <=120000 ms; downstream send stall <=10000 ms | Monotonic; overall includes setup, safe-text withholding and backpressure |
| T3-L10 | Cleanup <=1000 ms total per request | One shared budget, not renewed per close/cancel step; quarantine unresolved ownership |

Limits are inclusive; the next unit over the limit fails. Pending output accounts
for staged sanitized text/encoded frames, not the separately capped currently
parsed event/delta. Process current bounded delta incrementally as the consumer
pulls; do not materialize an expanded list of output events. Retain no collection
of old event envelopes while waiting for a candidate boundary. Known control frames
are bounded constants and yielded after text, not accumulated in a queue.

Bound is O(active_streams x (chunk + decoder + line + event + parsed delta + channel
holds + pending output)), independent of total stream length. Count Python object,
JSON/encoding scratch copies and framework/transport buffers when measuring actual
memory; do NOT claim the table sums to a certified RSS ceiling. Source event bytes
bound JSON input even if malformed or deeply nested. Reject nesting >8, numeric
lexemes >16 ASCII bytes and object member count >8 before constructing an unbounded
parse tree (bounded lexical precheck over the already capped event). JSON decoding
limits are profile policies, not arbitrary JSON compatibility. No recursive or
catastrophic-backtracking detector; audit bounded CPU work on adversarial candidates.

## T3-P7: backpressure, cancellation and public failures

One request owner holds the response/parser/channel states. Pull -> process bounded
input -> yield sanitized fragment -> await downstream send before next upstream
pull. No producer queue/unbounded task spawning. Cleanup/disconnect monitoring may
run alongside this chain without reading a second copy of the upstream body.
Read-idle applies while awaiting an upstream read; slow downstream sending has its
own budget, plus overall deadline. Await ASGI send; framework/OS buffering must be
tested over sockets, not inferred from successful mock calls.

Overall deadline ends reads/content delivery; the separate cleanup grace may add
up to 1000 ms to owner teardown, not renew the content/send budget. On unconfirmed
cleanup quarantine the shared upstream adapter against NEW admissions, retain its
handle/stream-slot ownership and report unclean shutdown. This prevents repeated
failed cleanup from creating unbounded orphan resources; asyncio cannot certify
physical termination of arbitrary resistant code.

Disconnect, public coroutine cancellation, send failure, timeout, limit breach or
parser failure stops further reads/output, cancels owned work and closes upstream
in finally. Drop pending raw/sanitized tails on failure; never include them in an
exception, log, traceback response or diagnostic. No retry/replay. App shutdown
stops admission, drains/cancels active owners, then closes pooled client. Retain
unconfirmed cleanup handles/ownership, quarantine the affected resource and signal
generic unclean shutdown; never claim asyncio can kill arbitrary resistant I/O.
Local cancellation cannot prove remote provider execution/billing stopped.

Before response headers: use JSON `{"error":{"code":"...","message":"..."}}`.
Approved streaming-error mapping: 400 invalid_request; 413 request_too_large; 415 unsupported_media;
429 stream_capacity_exceeded (local concurrent-stream limit); 502 upstream_error /
invalid_stream; 503 service_unavailable; 504 stream_timeout. Inbound route/method/
authentication schema is a separate approval item before T3-004, not presumed from
Task 2 or Task 4. No upstream diagnostic body/header/message is echoed.

After headers, HTTP status cannot change. If peer writable and the EXISTING send
and overall budgets remain (no fresh error-send allowance),
emit at most ONE `event: error` with exact JSON keys code/message, both selected
from this fixed map, then close WITHOUT done/end:

| Code | Fixed message |
| --- | --- |
| invalid_stream | Invalid upstream stream |
| upstream_error | Upstream service failed |
| stream_limit_exceeded | Stream limit exceeded |
| stream_timeout | Stream timed out |
| service_unavailable | Service unavailable |

No attempt to write an error to a disconnected/stalled peer. Cancellation propagates
after owned cleanup is initiated/discovered. Prior successfully sent output is
irreversible but was classified under P3. Avoid access/body/debug logging, raw
exception formatting and telemetry payload capture; log only generated correlation
IDs, fixed outcome codes and non-sensitive resource counters. Do not persist prompts,
completions, keys or buffers. Discarding Python strings is not secure zeroization.

## T3-P8: isolated modules and T3-002 implementation boundary

task3/ now owns pyproject/environment/lock: Python 3.12.16, pytest 9.2.0,
Ruff 0.17.3 and setuptools 82.0.1 build requirement; locked installed inventory in E031.
No imports or dependency changes in completed Tasks 1/2/4. FastAPI/Starlette for
future factory/lifespan and streaming; HTTPX for future pooled async I/O. These
libraries do not supply cross-delta redaction automatically. Standard codecs and
typed records plus a small bounded parser/detector are sufficient for pure work.

Contract approval and explicit implementation authorization now received; T3-002 ONLY:

- Create isolated project/environment/lock with dev/build tools and no unnecessary
  HTTP dependencies until the integration milestone needs them.
- `models.py`: immutable events/validated channels/approved limit/error records.
- `sse.py`: pure incremental bytes-to-event parser and safe event encoder; no sockets.
- `payloads.py`: bounded JSON lexical/schema validation, P4 control transitions,
  text extraction; strict bool-vs-int channel rules and duplicate-key rejection.
- `redaction.py`: pure per-channel candidate detector/safe-prefix/finalization,
  bounded counters, no global state, independent whole-input reference in tests.
- Deterministic pure tests T3-Q01 through Q12 and Ruff checks, actual evidence.

EXCLUDED from T3-002: settings/credentials implementation, upstream.py/service.py,
HTTPX calls, async networking/backpressure execution, FastAPI/app.py/routes,
Uvicorn/wire processes, real vendor/tokenizer, persistence, completed-task edits.
Pure proof/tests cannot certify actual HTTP streaming, memory RSS or cancellation.

## Approved acceptance-test matrix (execution evidence recorded separately)

| ID | Checkpoint / required evidence |
| --- | --- |
| T3-Q01 | T3-002: Exact PII grammar, accepted/unsupported forms, digit boundaries, conservative @ masking, one whole-candidate replacement and unchanged ordinary text |
| T3-Q02 | T3-002: Every single byte split, short-fixture two-cut/exhaustive partitions, one-byte chunks and seeded many-chunk partitions give reference-equivalent output |
| T3-Q03 | T3-002: No unfinished candidate prefix emitted; sensitive values across 2/3/many SSE deltas/events, interleaved independent channels; no separator injection |
| T3-Q04 | T3-002: UTF-8 all multibyte split positions/BOM/incomplete/malformed sequences, JSON escapes/surrogate pairs/unpaired values; explicit non-normalization |
| T3-Q05 | T3-002: CRLF/LF/lone CR and split delimiters, multiline data, comments/id/retry/unknown field dropping; duplicate/missing/unknown event type rejection |
| T3-Q06 | T3-002: Strict JSON exact schema, duplicate decoded keys, nesting/numeric/member limits, scalar/type/unknown-field errors and complete-JSON-per-event rule |
| T3-Q07 | T3-002: Exactly-at/one-over chunk/line/event/delta/candidate/output/channel caps, including comments and no-delimiter adversarial input; no raw overflow flush |
| T3-Q08 | T3-002: done/end/error state transitions, duplicate closed channel, early end, empty response, transport EOF/truncation; error drops tails, only validated done finalizes |
| T3-Q09 | T3-002: Encoder cannot inject fields/events; CR/LF/control/Unicode text remains correctly escaped JSON, frame sizes respected, no opaque metadata forwarded |
| T3-Q10 | T3-002: High-water counters independent of arbitrarily many bounded events; no queue/event-envelope accumulation; fixed bounded pending state across four channels |
| T3-Q11 | T3-002: Independent reference transformation plus adversarial prefix withholding; privacy checked on decoded/reassembled output, not raw substring search alone |
| T3-Q12 | T3-002: Bounded deterministic detector work on hostile candidates, stable error types/messages and no candidate values in repr/errors/captured logs |
| T3-Q13 | T3-003: One upstream reader; gated slow consumer proves bounded read-ahead/backpressure; safe prefix delivered while upstream completion withheld |
| T3-Q14 | T3-003: Controlled monotonic deadlines, cancellation at each await, response closure and one bounded cleanup budget; no replay or unowned live tasks |
| T3-Q15 | T3-003: Concurrent request/channel isolation, fixed destination/credential isolation, transport errors/compression/header checks, real transport allocation inspection |
| T3-Q16 | T3-004: Approved inbound/auth/request contract and streaming response/status/header behavior; early rejection does zero upstream work |
| T3-Q17 | T3-004: Preheader JSON versus postheader fixed SSE error; no success terminal after failure, raw buffer or diagnostics leak; disconnect during blocked send |
| T3-Q18 | T3-004: 16/17 active-stream admission, lifespan startup/shutdown/cancellation and counter/resource cleanup, no mutation of completed tasks |
| T3-Q19 | T3-005: Independent loopback Uvicorn/upstream/client processes, dynamic child-bound ports, readiness gates, real progressive delivery and no proxy buffering |
| T3-Q20 | T3-005: Real slow clients, Unicode/framing splits, upstream termination/disconnect, deadlines, concurrent isolation and privacy/log capture |
| T3-Q21 | T3-005: Long-stream measured memory envelope, server/OS-buffer caveats, no leaked connections/tasks/processes, failed-fixture cleanup and exact child receipts |

All PASS claims require actual commands/exits/results later. Proposed assertions,
mathematical argument and current inspection are not passing implementation tests.

## Independent acceptance / remaining limitations

User independently APPROVES T3-001 on 2026-11-05 for this synthetic profile.
T3-U2/U3/U4 and streaming portions of U5 are resolved by approval of the documented
PII, normalization, replacement, safe-prefix, event, metadata, limit and deadline
policies. Original brief (U1) remains unavailable and this limitation persists.
Inbound route/method/request/authentication/browser-client decisions still require
explicit approval before T3-004. Real vendor adapters/tokenizers are not inferred.

T3-001/T3-002 DONE / independently accepted within the synthetic profile.
T3-003 through T3-005 DONE/independently accepted; T3-006 NOT_STARTED. Completed
Tasks1/2/4 remain DONE and must not change. One T3-005 acceptance commit authorized;
no T3-006 or push. Full TASK-3 remains IN_PROGRESS.

## Standards references consulted for the design

- [WHATWG SSE](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- [Python incremental codecs](https://docs.python.org/3.12/library/codecs.html#incrementaldecoder-objects)
- [HTTPX async streaming and closure](https://www.python-httpx.org/async/)
- [Starlette StreamingResponse](https://starlette.dev/responses/)

P1-P8, resource caps and strict failure policies are approved engineering choices. A standards
reference establishes framing/API behavior, not the missing assessment requirements.

## T3-002 actual implementation / verification mapping

Independently ACCEPTED, user confirmation 2026-11-05. E031 records actual native commands/results,
including initial failures/warnings; final **362 passed in 3.02s**, both Ruff checks
pass (11 files). No HTTPX/FastAPI/network or later deadline/concurrency execution.
Functions are in task3/src/task3_streaming; tests below relative to task3/tests.

| Criteria | Implementation | Representative executed tests |
| --- | --- | --- |
| Q01 | redaction.classify_candidate/is_canonical_email | test_redaction.py::test_all_categories_and_conservative_whole_candidate_masking; test_canonical_email_grammar_and_exact_lengths; test_phone_ssn_numeric_boundaries_exactly_match_approved_syntax |
| Q02/Q03 | SSEParser.feed; Redactor.process; Processor.feed | test_every_transport_byte_split_and_every_model_delta_split; test_all_short_candidate_partitions_and_no_prefix_before_done; test_four_channels_independent_shared_delta_state_and_no_cross_channel_join |
| Q04/Q05 | SSEParser._decode/_end_line/finish; inspect_event | test_sse.py::test_line_endings_bom_metadata_and_multiline_data; test_decoder_holds_at_most_three_bytes_of_incomplete_four_byte_scalar; test_redaction.py::test_multibyte_unicode_and_decoded_ascii_escapes_across_every_byte_boundary |
| Q06 | payloads._bounded_lexical_check/_pairs/inspect_event; models.Event | test_payloads.py::test_ambiguous_invalid_and_unknown_shapes_reject_without_raw_context; test_json_resource_prechecks_fail_before_decoding_large_structures |
| Q07 | Limits; SSEParser._count; Redactor.process/_safe; encode_event | test_candidate_255_256_257_never_release_at_retention_threshold; test_sse.py::test_default_8192_line_and_16384_event_exact_boundaries; test_serialized_byte_limit_separate_from_scalar_limit |
| Q08 | Redactor.process/abort; Processor.finish | test_invalid_channel_transitions; test_unexpected_eof_never_flushes_unresolved_text; test_only_valid_done_finalizes_tail_error_clears_every_channel; test_terminal_encoder_failure_and_abandoned_terminal_cannot_claim_success |
| Q09 | sse.encode_event | test_sse.py::test_encoder_escapes_text_without_sse_injection; test_error_encoder_uses_fixed_code_and_message |
| Q10 | ParserStats/RedactionStats; lazy Processor | test_long_stream_retained_state_independent_of_event_count; test_four_maximum_holds_do_not_accumulate_event_envelopes |
| Q11/Q12 | bounded classifier plus independent manual test oracle | test_random_chunk_and_delta_partitions_match_independent_reference; test_bounded_adversarial_candidates_differential_reference; test_no_sensitive_output_or_error_details_logs_or_abandoned_state |

No full stream/event list is retained by the production library. Raw input chunk,
line, event/current JSON object and current delta are separately bounded; holds
<=4x256 ASCII chars, pending sanitized buffer <=1024 scalars/8192 UTF-8 bytes,
serialized frame <=8192 bytes and text fragment <=256 scalars. JSON encoder scratch
is bounded by the small input event fragment; no claimed total RSS ceiling. Valid
done alone can finalize; error/abandon/overflow clears tails and revokes success.
The shape encoder alone is NOT a privacy boundary; use Processor/redactor composition.

## T3-002 independent acceptance / environment qualification

User APPROVES T3-002 on 2026-11-05 (America/Los_Angeles). Reported independent
362-test suite plus 1200 randomized interleaved streams, 2961 channel-reference
comparisons, 256 prefix withholding/character-257 rejection probes, 376 truncated
wire cuts without whole-value PII leakage, 24000-event retained-state test and
Python compilation passed. No blocking production defect identified.

Review used Linux/Python 3.13.5/pytest 9.0.2, one pytest configuration warning
(specific text/commands/timings not supplied). This is outside the pinned Python
3.12 project runtime; do not alter pins or infer full supported installation there.
E031 native Windows/Python 3.12.16/pytest 9.2.0/Ruff 0.17.3 remains authoritative.
E032 records supplied review and actual Git inspection, not new local executions.
Original vendor brief still unavailable; no universal PII/vendor interoperability.

T3-002 DONE/independently accepted. One descriptive T3-001/T3-002 foundation commit
authorized for approved source/tests/pins/config/lock/README and relevant governance
only, preserving implementation unchanged. TASK-3 IN_PROGRESS; no T3-003 or push.

## T3-003 actual async implementation / policies and verification

Latest user attachment authorizes async upstream/service only over 0a75587, not
HTTP endpoints/wire/final audit. T3-003 DONE/independently accepted, user confirmation
2026-11-05; qualified review E034. E033 final native Python 3.12.16: **457 passed in 4.09s**, zero
failures/errors/skips/warnings/xfails; both Ruff checks pass, 17 Python files.
All 11 accepted T3-002 source/test files and 362 pure tests remain byte-identical.
Original brief/synthetic-only/narrow-PII scope remains unchanged.

Implementation choices I1-I8 below refine the authorized transport seam; they are
engineering policies, not recovered vendor requirements or new PII rules:

- T3-I1: immutable trusted UpstreamSettings requires HTTPS or literal-loopback HTTP
  destination, no userinfo/query/fragment, separately configured optional Bearer.
  UpstreamRequest contains 1-65536 opaque already formed bytes, fixed POST and JSON
  media type. No provider/prompt schema inferred; no caller URL/header API or
  inbound credentials/cookies forwarded. Future T3-004 must approve/validate input.
- T3-I2: owned HTTPX 0.28.1/httpcore 1.0.9 pool, 16 HTTP/1.1 connections, TLS,
  trust_env=False, no redirects/retries, reject cookie persistence. Validate 200,
  one text/event-stream Content-Type/optional UTF-8 charset, NO Content-Encoding.
  Reject before reading diagnostic bodies; no upstream headers reach output.
- T3-I3: public response AsyncByteStream yields raw bytes without decoding or
  implicit EOF close; own response.aclose explicitly under a shielded task. Native
  pinned HTTP/1.1 network read size inspected as 65536. Enforce one retained raw
  block <=65536 and lazily slice <=4096 for Processor, without coalescing small
  events to 4 KiB. Reject oversized injected blocks. External transport/header/OS
  buffers are not a certified RSS bound; T3-005 must verify real wire behavior.
- T3-I4: StreamService/StreamSession async context and iterator retain one accepted
  Processor, one operation and one bounded pending iterator per admitted request.
  No producer queue/background reader. Direct encoder/parser bypass is prohibited.
  Process-global Capacity is unconditionally atomic across services/loops, <=16 active,
  no waiting queue; excess has fixed CapacityExceeded/zero requests.
  No per-instance capacity override; only test fixtures isolate the counter in
  new async test modules, not in production or the accepted pure components.
- T3-I5: pool/connect/write 5 s/read 15 s configured in HTTPX (native transport owns
  these phases). First VALID event absolute 15 s from admission including headers;
  empty valid delta qualifies via accepted channel state, comments/incomplete data
  do not. Read-idle 15 s from each body await, not time paused downstream. Monotonic
  overall 120 s includes setup/processing/paused consumer. Owned timer-only watchdogs
  enforce first/overall even with no demand. Read/event observation at deadline loses;
  a delayed watchdog cannot reject an event already accepted before its deadline.
- T3-I6: close drops raw tails/pending frames, cancels/discovers owned open/read work
  then closes iterator/response under ONE additional 1 s grace anchored at close
  initiation. Caller cancellation cannot cancel/drop the shielded close worker.
  Unconfirmed/failed cleanup retains owner/slot and quarantines shared adapter/new
  admissions; never close pool under live uncertain response. Late confirmed close
  releases slot, quarantine stays. Permanent failed close needs supervisor, no retry
  API. Pool shutdown has a separate one-time 1 s resource-close budget AFTER response
  owners drain; no repeated request-grace renewal or silent discarded close tasks.
- T3-I7: only Processor frames yielded. Known upstream error yields its fixed error
  frame; other failures raise fixed StreamError codes, no raw diagnostic/context or
  automatic after-header response. Public HTTP mapping remains T3-004. A terminal
  success frame waits for confirmed cleanup, no false end after close failure.
  HTTPX/httpcore HTTP/1.1 logs are filtered inside owned I/O ContextVar scope only,
  including untrusted reason phrases; unrelated request logging unaffected.
- T3-I8: bounded synchronous processing checkpoints provide cooperative cancellation,
  not preemptive Python interruption. T3-004 owns actual ASGI send under minimum of
  10 s and remaining session.deadline, disconnect monitoring and send-task cleanup.
  Overall watchdog closes upstream but cannot prove socket-send completion. No
  actual HTTP endpoint, process harness, remote cancellation/billing or RSS claim.

| Q13-Q15 evidence | Executed tests (task3/tests/) / observed assertions |
| --- | --- |
| Progressive delivery/backpressure | test_service.py::test_progressive_delivery_and_exact_read_counts_under_blocked_demand: first safe prefix after read 1, no-demand count still 1 after 20 scheduler turns, explicit next pull enters read 2, final cross-chunk replacement/count 2 |
| Pending frames / bounded reads | test_pending_sanitized_frames_do_not_read_next_network_chunk: 256/256/88 scalar frames use read 1, controls read 2; test_long_stream_has_no_producer_queue_or_accumulated_pure_buffers: 2000 deltas, 2001 reads including controls, bounded pure holds/output |
| Fixed transport/privacy | test_upstream.py status/type/encoding matrix, request preservation/credentials/cookies/timeouts, no-retry failures, raw 64 KiB ->16x4 KiB, oversized-block rejection and scoped log filtering |
| First/read/overall timing | test_first_valid_event_monotonic_boundary_and_no_partial_flush (14.999/15/15.001); frequent partial/comment chunks do not renew first deadline; empty valid delta switches to read idle; headers do not reset first budget; overall/first watchdogs close even without demand |
| Cancellation/ownership | tests cover connect/read/processing checkpoint/pending output, caller and shutdown cleanup cancellation, repeated cancel, shared 750 ms cancel +close grace, .999 s confirmed close, uncertain connect/read/close >1 s retention and zero new sends, late cleanup/pool closure, failed close preventing success end |
| Isolation/capacity | process-global 16 across services; parallel 16/17 zero-forward admission; 16 simultaneous streams separate candidates and finish/close once |

Only controlled async/HTTPX transports were executed, no real sockets or external
inference. HTTPX phase timeout settings/exceptions verified; mocks do not establish
actual DNS/TLS/socket phase timing. First/idle/overall/cleanup tests use monotonic
controlled clocks and gates. Native HTTP/1.1 source inspection is not wire evidence.
Initial delayed-first-watchdog failure and Ruff findings/fix retained in E033.
No pure integration defect/correction needed. Independent T3-003 review approved;
next: the authorized acceptance commit, then stop. No T3-004 or push.
Full TASK-3 stays IN_PROGRESS.

### T3-003 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User confirms independent APPROVAL: complete suite 457 passed,
240 additional randomized HTTPX fragmentation cases passed; resistant cancellation
retained ownership/quarantined admissions until confirmed cleanup, concurrent
shutdown blocked admission/closed shared transport once, all 11 accepted pure
files byte-identical and compilation passed. No blocking production defect found.
Reported Linux/Python 3.13.5 review had one nonfatal pytest configuration warning;
exact warning, commands/timings and pytest version were not supplied. This is not
a supported Python-pin change or a new local execution. E033 native Windows/
Python 3.12.16 and Ruff remain authoritative. No real socket or ASGI claims,
vendor interoperability or universal PII guarantees follow from this acceptance.
Preserve all engineering policies/limitations and Tasks 1/2/4. E034 records this
documentation/Git checkpoint only; no test rerun absent unexpected functional change.

## T3-004 HTTP implementation choices / review checkpoint - 2026-11-05

America/Los_Angeles. Latest attachment authorizes FastAPI integration and direct
ASGI verification over e4bd001/457 tests. These H1-H9 are implementation policies,
not original vendor requirements. Original brief unavailable; approved narrow
PII/synthetic SSE/metadata/terminal rules are unchanged. Native E035: 580 passes
(457 preserved +123 new), both Ruff checks/22 Python files. T3-004 DONE,
independently APPROVED 2026-11-05; qualified review E036. No FastAPI shortcuts bypass accepted Processor,
SSE/payload/redaction/upstream/service components; none of their bytes changed.

- T3-H1: exact POST /stream, no slash redirects, query strings, documentation/schema
  routes, CORS, SSE resume/retry or extra routes. Other methods 405/Allow: POST;
  unknown paths 404. One lifespan per factory-created app. Plain HTTP examples bind
  loopback only, not deployment/TLS certification.
- T3-H2: one operator-configured opaque Bearer token, 32-4096 ASCII token-syntax
  characters, separate from optional upstream Bearer (equal values rejected).
  Scheme is case-insensitive, token exact; one header/one ASCII space, no commas,
  tabs, outer whitespace or duplicate authorization. Constant-time comparison.
  No production credential defaults, role/tenant/OAuth/JWT system or caller URL/
  credential/routing options. Missing/invalid auth fails before body consumption.
- T3-H3: operator environment T3_ACCESS_TOKEN and T3_UPSTREAM_URL required;
  T3_UPSTREAM_BEARER optional. Typed HTTPSettings/UpstreamSettings injection is
  trusted composition. Load/validate before resource creation; no connection opens
  until an admitted upstream call. No await between client creation and retaining
  it in app.state.runtime. Test transport/clock injection never comes from HTTP.
- T3-H4: strict UTF-8 application/json, optional UTF-8 charset; reject ANY
  Content-Encoding including identity. Reject duplicate Content-Type/Encoding/
  Length/Transfer-Encoding, malformed/nondecimal/over-10-digit Content-Length,
  Length+Transfer-Encoding and transfer coding other than sole chunked. ASGI server
  already de-chunks; limit every received body increment before extending storage.
  Raw body <=16384 bytes and absolute body-read deadline 10s. Declared lengths must
  match. Receive/disconnect during upload has one reader; confirmed upload disconnect
  writes nothing. ASGI receive is the trusted cancellation-cooperative server API.
- T3-H5: one exact JSON object with ONLY prompt, a strict string of 1-4096 Unicode
  scalars. Reject malformed JSON/UTF-8/BOM, decoded duplicate keys, extra fields,
  numeric/nonfinite values, nested/type-mismatched prompt and unpaired surrogates.
  All invalid prompt/schema cases 400, including character overflow; raw-byte
  overflow 413. Both bounds apply independently. Form canonical UTF-8 compact
  {"prompt":...} bytes; accepted adapter preserves THOSE bytes unchanged, not original
  inbound whitespace/escapes. This is a synthetic prompt API, not a vendor format.
- T3-H6: order: framework path/method -> runtime availability -> Bearer -> HTTP
  metadata -> bounded body -> strict JSON -> HTTP capacity -> accepted service
  admission/header preflight -> one response.start. Preflight validates upstream
  HTTP headers WITHOUT reading any response body. Payload errors after 200 close
  as failed SSE, not retroactive JSON status. Early rejection does zero upstream work.
- T3-H7: custom Response owns one post-body receive monitor and one sequential
  open/read/send operation; no producer queue/background body reader. Await each
  ASGI send before another anext/upstream read. Admitted response.start, frames
  and final empty body each use min(now+10s, session.deadline); observation at the
  deadline loses. Overall 120s includes setup/processing/backpressure and is never
  reset. Only Processor-approved frames reach SSE; all upstream metadata stays
  dropped. No Content-Length/compression; text/event-stream; charset=utf-8, no-store,
  nosniff. ASGI completion is not a socket acknowledgement or wire backpressure proof.
- T3-H8: after headers, local processing/upstream/timeout errors CLOSE without a
  locally generated SSE event or end. A best-effort empty HTTP close may use only
  the EXISTING last-send/overall budgets, never a fresh error-send allowance.
  Known synthetic upstream error remains the existing Processor-owned fixed error
  frame. Disconnect/send failure/shutdown writes no further frames or errors.
  Attempted response.start is never retried even if delivery is uncertain. Bytes
  already offered to a server send cannot be retracted; resistant test sends may
  finish that already-offered sanitized frame later. No new sends follow failure.
- T3-H9: separate atomic process-global HTTP cap16 holds through final ASGI send
  and confirmed cleanup, in addition to unchanged upstream service cap16. This
  prevents blocked terminal sends bypassing the cap after upstream slot release.
  No waiting admission queue. HTTP owner shares one anchored additional 1s for
  send/operation cancellation, receive-monitor close and accepted session cleanup;
  never renew an existing service grace. Work stays owned/shielded on repeated
  caller cancellation. Unconfirmed close retains owner/slot, quarantines admissions
  and prevents pool close underneath it. Late confirmed work releases its slot;
  if service confirmation arrives after its guard returns false, explicit runtime
  aclose rechecks public session.cleaned state without retrying resource close.
  Quarantine is sticky. Shutdown sets stop barrier, cancels/drains HTTP owners then
  invokes unchanged service.aclose/pool budget. app.state.runtime retains handles;
  app.state.unclean_shutdown stays true until confirmation, including cancelled
  lifespan waiters. Failed shutdown raises fixed Unclean streaming shutdown. No
  automatic restart/replay/recovery or remote termination guarantee.

Before headers, every error uses {"error":{"code":"...","message":"..."}},
no-store/nosniff; fixed values only:

| HTTP status | Code / meaning |
| --- | --- |
| 400 | invalid_request: framing/schema/query/JSON invalid |
| 401 | invalid_credentials; WWW-Authenticate: Bearer realm="task3" |
| 404 / 405 | not_found / method_not_allowed (Allow: POST) |
| 408 | request_timeout: body-read deadline |
| 413 | request_too_large: raw-byte limit |
| 415 | unsupported_media: unsupported media/encoding |
| 429 | stream_capacity_exceeded: HTTP or accepted service cap, no queued work |
| 502 | upstream_error, invalid_stream or stream_limit_exceeded per fixed MESSAGES |
| 503 | service_unavailable: unavailable/stopping/quarantined runtime |
| 504 | stream_timeout during preflight |

Admission failures are ordinary bounded-size JSON responses without an upstream
owner; ASGI server owns nonadmitted connection/receive lifecycle and request-header
allocation. Streaming/send deadlines are verified at the admitted ASGI boundary,
not as transport-level guarantees for every rejected HTTP connection. Limits do
not certify total RSS or arbitrary server/OS buffers. No input/output secrets are
logged; operator must keep access/body/debug/telemetry capture disabled.

| Actual Q16-Q18 evidence | Named tests (task3/tests/test_app.py unless stated) |
| --- | --- |
| Strict HTTP/auth/zero forwarding | test_http_authentication_rejects_before_body_or_upstream; test_metadata_failures_do_not_read_body_or_contact_upstream; test_strict_prompt_validation_zero_upstream; test_body_limit_enforced_across_chunked_receive_messages; tests/test_http_settings.py |
| ASGI backpressure/progression | test_asgi_send_backpressure_counts_and_progressive_safe_delivery: read1 while send blocked/20 scheduler turns, read2 only after release; test_pending_sanitized_frames_await_individual_asgi_sends_without_more_reads: 256/256/88 scalars, all from read1 |
| Deadlines | test_exact_send_deadline_no_raw_tail_or_error_write_after_stall: 9.999/10/10.001; test_send_uses_remaining_overall_budget_instead_of_another_ten_seconds: send starts117, 119.999/120/120.001; test_postheader_failure_cannot_renew_an_expired_send_budget_for_error_or_close |
| Disconnect/error privacy | test_disconnect_never_writes_error_or_flushes_pending_pii; test_queued_disconnect_is_seen_before_admission_or_headers; test_blocked_response_start_does_not_pull_upstream_body; test_send_failure_no_second_status_or_error_send; test_postheader_failure_closes_without_end_or_new_status |
| Capacity/isolation | test_http_cap_includes_blocked_terminal_sends_after_upstream_releases; test_http_capacity_is_process_global_across_application_instances; test_concurrent_clients_isolate_prompts_channels_and_responses |
| Lifecycle/ownership | test_real_asgi_lifespan_startup_shutdown_messages_and_shared_close_once; test_unclean_lifespan_retains_resource_owner_and_reports_fixed_shutdown_failure; test_send_cancellation_and_response_close_share_one_cleanup_grace; test_repeated_request_cancellation_cannot_discard_owned_send_cleanup; test_cancelled_lifespan_waiter_retains_and_finishes_shared_pool_close |

No accepted-component integration correction was required. Initial/new-fixture
failures and intermediate results remain in E035/M052. HTTP/TLS socket behavior,
proxy/server buffering, process/RSS/leak audit, deployment, real LLM providers and
universal PII detection are unverified/excluded. Independent T3-004 review approved;
next the authorized acceptance commit, then stop. No T3-005 or push.
T3-001 through T3-004 accepted, TASK-3 IN_PROGRESS.

### T3-004 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User confirms independent APPROVAL: complete suite580 passed,
180 additional randomized interleaved two-channel ASGI streaming scenarios passed,
4613 upstream reads exercised. Five additional fail-closed scenarios passed:
candidate overflow, unexpected EOF, duplicate done, premature end, malformed payload.
All17 previously accepted Python source/test files byte-identical to T3-003 review
archive; source inspection found no blocking defect. These are reported review
results, not new commands executed during acceptance. Linux/Python3.13.5 produced
one nonfatal pytest configuration warning; warning text/pytest version/exact
commands/timings not supplied. E035 native Windows/Python3.12.16 verification and
Ruff remain authoritative. No widened Python support, real socket/RSS evidence,
vendor compatibility or universal PII claim. All H/P/I policies, historical
failures/evidence and limitations retained; original vendor brief unavailable.
E036 records this acceptance/docs/Git checkpoint, with accepted source/tests/
dependencies/lock unchanged. No T3-005 or push; stop after one commit verification.

## T3-005 real-wire verification / engineering observations - 2026-11-05

America/Los_Angeles. Latest attachment authorizes verification only over ecbd61c /
580 accepted tests. E037 actual native Windows/Python3.12.16: **637 passed in53.46s**,
including57 new wire cases, zero failures/errors/skips/warnings/xfails/xpasses;
Ruff lint/format25 pass. T3-005 DONE/independently APPROVED 2026-11-05; qualified
review E038, no new execution in acceptance. Original
vendor brief remains unavailable; P/I/H synthetic profile/policies unchanged.
No accepted production/test/dependency/lock correction was needed.

W1-W8 below document harness choices/observed evidence, NOT new original brief
requirements or production deployment settings:

- T3-W1: independent child provider and accepted app/Uvicorn processes; pytest
  client uses actual http.client TCP, never ASGITransport/MockTransport. Child-bound
  127.0.0.1:0 sockets, exclusive address use on Windows, explicit startup receipts
  and real HTTP readiness checks. No reserve-close-rebind race, public interfaces,
  LLM vendors or external generation traffic. Child cwd/interpreter is Task3's pin.
- T3-W2: stdin plans/gates/counter-journal control, bounded sanitized stdout receipts,
  ephemeral distinct client/upstream/control tokens only in child environment.
  Environment allowlist excludes ambient credentials; no token command-line args,
  prompt/body/key journals or generated DBs. Control stats route exists ONLY in
  outer test wrapper, never changes accepted /stream. Provider call journal counts
  independently cross-check proxy native request attempts for zero-forward assertions.
- T3-W3: public HTTPX AsyncBaseTransport/AsyncByteStream wrappers delegate to actual
  AsyncHTTPTransport with same pooling/timeouts via request extensions, no retries/
  redirects/env proxies. Original byte partitions passed unchanged. ASGI wrapper
  awaits the actual Uvicorn send in the existing pull chain, records counters/high
  water only, no producer task/queue or parser/redactor replacement. Independent
  client framing/known expected text checks avoid a production-redactor oracle.
- T3-W4: gated first provider write contains completed safe text and unresolved
  candidate. Real client receives safe frame while provider cannot finish; gate
  release permits remaining replacement/done/end. Native reads-before-release2
  include a pending read attempt, with only1 body chunk received; not two delivered
  chunks or upstream-write/TCP-read equivalence. Upstream writes may coalesce/split.
- T3-W5: slow reader with requested4096-byte receive buffer and child listener
  SO_SNDBUF16384 observed same suspended ASGI send/read counter117 across3 control
  round trips. Received124004 raw body bytes/offered143545 SSE bytes are cumulative
  counters, NOT buffer occupancy; framing/rechunking changes lengths. HTTPX/native/
  Uvicorn/asyncio/OS buffers add overhead. Accepted-socket buffer inheritance and
  all kernel autotuning are not measured. No exact10s socket-stall expiry claim;
  exact10/120s boundaries remain in accepted deterministic ASGI suite rerun here.
- T3-W6: real first-event inactivity15.016s/read-idle15.047s each closed native
  resources and was observed as provider disconnect, without flushing unresolved
  text or SSE end. Headers already200, HTTP chunk termination incomplete as allowed
  by fail-closed contract. Connection refusal returns fixed502. Native wire cleanup
  confirmed/no quarantine in tested cases; resistant/uncertain cleanup and sticky
  quarantine remain deterministic ASGI evidence, not falsely reproduced native cases.
- T3-W7: Windows GetProcessMemoryInfo WorkingSetSize/PeakWorkingSetSize captures
  instrumented proxy observations, not formal total RSS/allocator bounds.1000/
  5000-event streams produce125000/625000 characters and independent SHA256 output
  checks; fixed application high-water counters stay within P6 limits. Empirical
  64MiB RSS-growth guard is a regression guard, not a guaranteed memory ceiling.
  Memory includes interpreter/native/framework/probe overhead, not OS socket totals.
- T3-W8: bounded startup10s, native client22s for representative waits, child stop7s
  then terminate2s/kill2s only if needed; all sockets/stdin/stdout/stderr/reader
  threads explicitly closed/joined. Ordered test stop drains accepted runtime before
  Uvicorn exit; stock signal/deployment shutdown is not certified. Final run10 child
  processes:9 exit0,1 expected invalid-config exit2, no unexpected nonzero/forced/
  killed/alive readers. Across subset/two full runs30 children:27 normal/3 expected
  exit2, zero forced. Failed-fixture cleanup and active-request shutdown included.

| Q19-Q21 evidence | Named tests in task3/tests/test_http_wire.py |
| --- | --- |
| Gated progressive TCP | test_wire_progressive_delivery_before_gated_upstream_completion |
| Protocol/PII/UTF-8/framing | test_wire_fragmentation_unicode_json_escapes_and_three_pii_categories; test_wire_whole_candidate_masking_includes_surrounding_candidate_text |
| Fail-closed / fixed error | test_wire_fail_closed_without_unresolved_text_or_false_end; test_wire_known_upstream_error_stays_fixed_and_drops_unresolved_candidate |
| HTTP/auth/body/no forwarding | test_wire_auth_rejections_zero_upstream; test_wire_http_schema_rejections_zero_upstream; test_wire_chunked_upload_enforces_actual_byte_limit_without_content_length; test_wire_content_length_and_chunked_requests_credentials_isolated |
| Header/connection failure | test_wire_upstream_preflight_failure_is_sanitized_json; test_wire_connection_refusal_is_controlled_json |
| Disconnect/timeouts | test_wire_client_disconnect_closes_blocked_upstream_and_withheld_pii; test_wire_real_inactivity_deadlines_close_native_resources |
| Capacity / channel-state isolation | test_wire_sixteen_active_streams_seventeenth_denied_then_capacity_released |
| Buffer/RSS observations | test_wire_slow_reader_native_buffering_probe_and_disconnect; test_wire_long_stream_high_water_and_empirical_process_rss |
| Process hygiene | test_wire_shutdown_with_active_request_cancels_native_upstream; test_wire_invalid_configuration_child_exit_is_expected_and_reaped; test_wire_fixture_exception_still_reaps_both_children |

23 HTTP/auth/body rejection cases plus the17th-stream capacity case assert zero
extra proxy attempts/independent upstream journal calls. Sixteen simultaneous
streams use distinct markers and alternating sensitive/safe candidates; released
capacity is successfully reused. Captured diagnostic private-marker count0.
No end after failed/truncated/disconnected stream; prior safe delivery irreversible.
Final raw receipt/high-water/RSS values and PID/exit evidence are durable in E037;
ignored harness summaries contain counters only and are not submission artifacts.

Limits: instrumented loopback native HTTP/1.1 on supported Windows only, empirical
RSS/short flow-control observation, not exhaustive RSS/OS buffering/10s-kernel-stall
proof, production TLS/reverse-proxy settings/real vendor/provider billing or universal
PII detection. No native uncertain-close/physical cancellation guarantee or automatic
resume/retry. T3-006/final audit not begun. Independent T3-005 review now approved;
next one authorized acceptance commit, then stop. No T3-006 or push. Tasks1/2/4
and all22 previously accepted files preserved; wire harness unchanged in acceptance.

### T3-005 independent acceptance provenance - 2026-11-05

America/Los_Angeles. User independently APPROVES, no blocking implementation defect
or production correction required. Reported580 existing passes; all57 wire cases
produced passing assertions across split executions;40 additional randomized
real-socket fragmentation tests passed. Progressive SSE/PII/auth rejection/
concurrency/disconnects/timeouts/cleanup reviewed. All22 previously accepted Python
files byte-identical to T3-004 archive. No new local tests in this checkpoint.

Linux/Python3.13.5 review used an import-path change ONLY in the extracted harness,
not repository source. Combined Linux wire run STALLED after50 completed cases;
19-case split printed passing summary but did NOT return promptly to enclosing
command. Do not describe this as a clean combined637-test Linux run or invent
clean process/exit/Ruff receipts. Exact review commands/timings/pytest version not
supplied. E037 native Windows/Python3.12.16 full637/exit0 and Ruff remain authoritative.
Kernel-level10s send-stall expiry, production TLS, formal RSS ceilings, real-provider
interoperability and original vendor brief remain unverified/unavailable. Synthetic
profile and all historical evidence/limitations retained. E038 records reported
acceptance and Git inspection only. Preserve all25 verified Python files, marker/
dependencies/lock and Tasks1/2/4; one acceptance commit, no push or T3-006.
