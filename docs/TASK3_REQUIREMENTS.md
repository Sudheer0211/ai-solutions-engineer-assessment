# TASK-3 / T3-001: approved synthetic streaming contract and implementation gates

Date: 2026-11-05 (America/Los_Angeles). Baseline: `7e37045`.
Status: **T3-001 independently APPROVED / accepted**, user confirmation 2026-11-05.
Approval is ONLY for the explicitly defined synthetic assessment profile, not an
unavailable original vendor brief, universal PII detection or vendor interoperability.
P1-P8 and L1-L10 are approved ENGINEERING POLICIES, not original assessment numbers.
T3-002 independently APPROVED, user confirmation 2026-11-05; DONE. E032 records
qualified review provenance. One accepted T3-001/T3-002 foundation commit authorized;
preserve pure code/tests/pins/lock. No networking/HTTP/T3-003 or push authorized.
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
T3-003 through T3-006
NOT_STARTED. Completed Tasks 1/2/4 remain DONE and must not change. One accepted
foundation commit authorized; no push.

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
