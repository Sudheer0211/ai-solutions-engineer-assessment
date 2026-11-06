# T3-007: Task 3/4 evaluator-compliance remediation

2026-11-06, America/Los_Angeles. Baseline:
`8d7a3c7f3bbd87deec1d83058315a8d732164ca5`.
**DONE / independently APPROVED within the documented13-19-digit synthetic PAN
grammar**, confirmed by user2026-11-06. Local mandatory checks PASS within that
profile; E042 records qualified independent review, E041 actual native evidence.
One acceptance commit authorized; no push, dependency or Task1/2 implementation change.

## Independent acceptance and evidence qualification

2026-11-06, America/Los_Angeles. User reports APPROVED:659 non-wire tests passed;
all17 new PAN real-HTTP wire cases passed with a review-only Linux subprocess
import-path adjustment;1200 additional randomized PAN streams passed across8812
model-delta fragments. Prefix withholding, fail-closed overflow and four-channel
bounded-state probes passed. No blocking production defect identified. Accepted
SSE parser/HTTPX service/FastAPI/transport architecture remains unchanged.

The reported native Windows149/452/733/427 (1761) and eight Ruff successes were
NOT independently rerun in full. Do not describe these selections as a complete
733-case Linux run or a new native regression. Exact independent commands,
Python/pytest versions, durations and complete child receipts were not supplied;
do not infer them. No Linux review adjustment ships. No tests were rerun in this
acceptance checkpoint. The approved scope includes the explicit spaced-start
boundary and294-character/channel auxiliary policy; it does not widen PII, vendor,
RSS/TLS/socket guarantees or Task4 real-provider interoperability. All previous
approvals/evidence/limits remain preserved. After one authorized Git checkpoint,
stop without pushing or implementing further features.

## Provenance and findings verified against source

Input: user-supplied ignored `.cache/evaluator_gap_audit_tasks_3_4.md`, SHA256
`e7d5e1185501f08f3972eda37308956f31d97bdce4f02fa6dc23729d97ab157f`.
Initially the differently named attachment could not be located; the user supplied
this path during work and the entire audit was then read. It remains out of Git.
The attachment directories, repository requirements and available assessment
text were searched again. The original full verbatim Task3 vendor/rubric remains
unavailable; the original pasted assessment attachment concerns Task1. No provider
API, evaluator event schema, PAN checksum rule or production rubric was recovered.

The gap audit reports recovered original categories **email, SSN, credit cards**;
the user explicitly confirms PAN as this corrective requirement. Telephone support
is additional coverage, not a replacement for credit cards. The gap audit's static
finding is confirmed: baseline `PII` and `classify_candidate` have no PAN category,
and baseline `Redactor.process` treats every space as a finalizing delimiter.
Fresh baseline one-byte Processor feeds reproduce unmasked contiguous, hyphenated
and spaced PANs. Historical synthetic-contract approvals/E039/E040 are preserved,
but do not establish compliance with the newly recovered card requirement.

Task4 findings also match source: atomic SQLite reservations, seven documented
requirements, bounded one-backup routing and default unconfigured503 exist.
No independently reproduced Task4 defect or requirement for live vendor access
was found. Its implementation/tests/config/dependencies/lockfile remain unchanged.
This checkpoint did not independently browse/revalidate published GitHub links;
inspection is against the local accepted baseline and supplied audit text.

| Provenance | Classification |
| --- | --- |
| Email + SSN + card category | Recovered high-level description, confirmed by current user |
| 13-19 ASCII digits, three formats, marker, bounded fragmentation safety | Explicit current corrective requirements |
| Exact boundaries, mixed separators, whole-compound replacement, auxiliary bound | Independently accepted engineering choices within this profile |
| Synthetic SSE schema, four channels, deadlines and trusted adapters | Historical accepted engineering policies, retained |
| Vendor format/tokenizer, live providers, universal PII, production rubric | NOT VERIFIED / unresolved; do not invent |

## Before/after reproduction

All values here are synthetic examples explicitly supplied for this assessment.
Before: native Python3.12.16 baseline Processor, one-byte transport feeds, validated
done/end. Each of the following was emitted unchanged. After: the new pure tests,
ASGI tests and real TCP cases reconstruct client text and require these replacements.

| Logical input | Baseline result | Corrected result |
| --- | --- | --- |
| `Card: 4111111111111111 ` | Original PAN emitted | `Card: [REDACTED] ` |
| `Card: 4111-1111-1111-1111 ` | Original PAN emitted | `Card: [REDACTED] ` |
| `Card: 4111 1111 1111 1111 ` | Groups emitted unredacted | `Card: [REDACTED] ` |

Implementation is a patch to `task3/src/task3_streaming/redaction.py` only:
`PII.PAN`, `_contains_pan`, `_bridgeable`, `Redactor._classify`/`process`/`abort`.
The accepted SSE parser, payloads, models, HTTPX/service/app and wire harness are
byte-identical to baseline. New tests reuse their existing injection/control APIs.

## Implemented PAN grammar and false-positive policy

These exact grammar choices are not claimed to be verbatim evaluator wording.

- ASCII digits only; **13 through19 inclusive**, counting digits, not separators.
  No Luhn, issuer, country, expiry or real-card assignment validation. All-zero
  and invalid-checksum in-range numbers are masked: intentional false positives.
- A numeric run is maximal `[0-9]+(?:[ -][0-9]+)*`: optional SINGLE ASCII space or
  single hyphen between nonempty digit groups. Arbitrary group sizes and mixed
  single separators are supported. Contiguous digits are one group. Never match
  a13-19-digit suffix/subrange inside a maximal20+-digit run.
- Original K alphabet `A-Za-z0-9._%+@-` is unchanged. Within a K-token, maximal
  numeric runs are searched; if any PAN/email-like/phone/SSN match exists, mask
  the entire token. Thus `x4111111111111111y` masks fully.
- **Cross-space boundary rule:** a bridge starts only after a completed wholly
  numeric/hyphen K-token (or already bridged wholly numeric span) of <=19 digits.
  One pending space joins only if the next scalar is an ASCII digit. Channels and
  events are not boundaries. No ordinary prose is accumulated across its spaces.
  A final digit-starting K-token can include a suffix; the whole compound is then
  classified/masked, including suffix K punctuation such as a directly attached dot.
- This means `Card: 4111 1111 1111 1111` and `(4111 1111 1111 1111)` are covered;
  a spaced PAN beginning inside a NONnumeric K-token such as
  `word4111 1111 1111 1111` is **outside this profile**. So are initial K punctuation
  prefixes before the first group, doubled separators, tabs/newlines, Unicode
  digits, invisible-character insertions and normalization/encoded obfuscations.
  JSON escapes are decoded before detection; they are covered, not obfuscation.
- Combining adjacent numbers with single spaces can overmask unrelated values;
  3 unrelated digits plus a16-digit PAN form19 digits and mask as one compound.
  Compound overlap with email/SSN/phone also produces ONE marker. Multiple adjacent
  PANs without a hard delimiter can instead exceed the bridge bound and fail closed.
  This conservative behavior is an explicit tradeoff, not semantic number recognition.
- Output is exactly `[REDACTED]` for the entire classified compound, without raw
  digits, prefix/suffix digits, number length, hash, category or separator count.
  A pending trailing space is a delimiter and is preserved after classification.
- A continuous20-256-digit K-token is outside PAN grammar and is not partially
  masked (other PII rules can still match). K-token character257 aborts. A bridged
  numeric span reaching digit20 aborts immediately without releasing any prefix.
  Ambiguous overlong spans are never released merely to meet a retention limit.

The spaced-start boundary and20+-digit behavior are material coverage limitations;
they are preserved by the independent approval and may require expansion if the
missing rubric requires a broader grammar. No claim of protection for out-of-profile forms.

## Safe-prefix reasoning and resource bounds

For each channel, hold an unfinished K-token as before. At a space after a wholly
numeric completed span, retain a one-space flag instead of emitting digits or the
space. A next digit commits that bridge; another scalar terminates the numeric
possibility, so the previous span can be classified before processing that scalar.
Only wholly numeric spans can bridge AGAIN. This avoids joining ordinary sentences.

Under the grammar above, future input cannot turn a released span into a supported
cross-space PAN: a span is released only when numeric bridging is impossible,
after a nonnumeric K-token, after a hard delimiter, or valid done. A >19-digit
continuous run cannot shrink into a supported maximal run. A bridged20th digit
fails closed. Every byte/delta split follows the SAME character transitions;
therefore output is fragmentation-independent. No split inserts a delimiter.
Only valid done classifies the last candidate; errors, EOF, abandonment, timeout,
disconnect and cancellation clear both raw holds and pending-space state.

Generic K-token cap remains256; stats `peak_candidate_chars` measures that token,
not a concatenation of unrelated words. A bridged prefix of <=19 digits/single
separators is <=37 characters, plus one joining space and a current K-token <=256:
conservative raw-held bound **294/channel,1176/four channels**, plus <=4 known-space
flags. No new queue or unbounded buffer. This explicitly replaces the old aggregate
1024-held-byte statement for PAN paths; the new auxiliary budget is independently
accepted within this profile.
An adversarial four-channel test retains1168 characters while each K-token stays256.
Trusted tightened candidate limits still apply to each K-token; numeric auxiliary
budget is fixed and separately bounded. No model/config/dependency change was needed.
4096 processing bytes,8192 line bytes,16384 event bytes,4096 delta scalars,
1024 pending scalars/8192 pending bytes,8192 encoded-frame bytes,256-scalar output,
four channels, pool/transport sizes and all deadlines are unchanged/enforced.
No formal whole-process RSS or timing-side-channel claim follows from these bounds.

## Executed verification and test mapping

E041 records exact commands/versions/exit codes, preliminary failures and receipts.

| Coverage | Automated references | Result |
| --- | --- | --- |
| Every13-19 length/three formats, every representative byte/delta split | `task3/tests/test_pan.py::test_pan_all_lengths_formats_every_byte_and_delta_cut` | PASS,21 cases with exhaustive single cuts |
| Bounds, overlap, punctuation, adjacent numbers, unsupported forms/no Luhn | `test_pan_boundaries_overlaps_false_positives_and_out_of_scope` | PASS,16 explicit expected outputs |
| Random interleaved four-channel streams/reference | `test_pan_random_fragmentation_interleaved_channels_and_reference` | PASS,24 deterministic seeds |
| UTF-8/JSON digit escapes/CR/LF/CRLF/one-byte feeds | `test_pan_json_escapes_multibyte_unicode_and_one_byte_sse` | PASS,3 cases |
| EOF/invalid termination, overflow, abandoned iterator, bounded state | `test_pan_unsafe_eof_malformed_termination_never_flushes`; `test_pan_overflow_fails_closed_without_retention_threshold_release`; `test_pan_additive_bridge_state_bounded_without_expanding_generic_candidate_cap`; `test_pan_abandoned_iterator_clears_bridge_and_channel_state` | PASS |
| Long numeric/prose stream, no accumulated state | `test_pan_long_stream_retains_no_unbounded_numeric_or_prose_history` | PASS,3000 events |
| ASGI safe prefix, blocked upstream, concurrent clients, disconnect/cancel/timeout | `task3/tests/test_app.py::test_pan_asgi_gated_cross_delta_backpressure_and_safe_output`; `test_pan_asgi_concurrent_channel_context_and_disconnect_withheld_numbers`; `test_pan_asgi_cancellation_and_timeout_discard_numeric_bridge` | PASS,6 new cases |
| Actual TCP13/15/16/19 lengths,3 formats, gated source writes/one-char deltas | `task3/tests/test_http_wire.py::test_wire_pan_gated_cross_write_and_delta_redaction` | PASS,12 new cases |
| TCP overflow/disconnect/truncation/malformed input,3 simultaneous clients x4 channels | `test_wire_pan_ambiguous_overflow_and_disconnect_never_flush`; `test_wire_pan_truncation_and_malformed_termination_drop_tail`; `test_wire_pan_concurrent_clients_and_interleaved_channels` | PASS,5 new cases |

New whole-input reference in `tests/support.py` uses manual scans, no production
PAN regex/helpers. It independently encodes numeric run boundaries and the
cross-space profile; known expected outputs prevent relying on oracle agreement
alone. The legacy637 cases remain: three obsolete negative expectations in two
functions were changed to expect masking for the now-supported synthetic16-digit
values. No test was removed/skipped/xfail-weakened; phone grammar itself is unchanged.
73 pure +6 ASGI +17 wire =**96 added cases**, total Task3 **733**.

### Fresh full native Windows regression

Each project ran in its own pinned environment/cwd. Python3.12.16,
SQLite3.53.1 (storage in Task4 only), pytest9.2.0/Ruff0.17.3. No Linux substitutions.

| Project | Pytest | Duration | Lint / format | Exit codes | Fail/skip/warning/xfail |
| --- | --- | --- | --- | --- | --- |
| Task1 |149 passed|40.49s|PASS /17 files|0/0/0|0/0/0/0|
| Task2 |452 passed|13.22s|PASS /16 files|0/0/0|0/0/0/0|
| Task3 |733 passed|58.18s|PASS /26 files|0/0/0|0/0/0/0|
| Task4 |427 passed|40.08s|PASS /22 files|0/0/0|0/0/0/0|

**1761 passing tests, eight Ruff checks PASS, no errors/xpasses.** Durations overlap;
these are four complete processes, not one combined pytest run. Focused adversarial
run also passed100 cases (96 new PAN cases plus4 existing lifespan-name matches),
151 deselected,5.73s/exit0. These are additional executions, not extra unique cases.
No functional edits followed the final full regression/Ruff; remaining work docs only.

Task3 full-run receipts:10 children reaped,9 exit0/one expected startup-invalid2;
zero forced/killed/live reader threads/diagnostic privacy violations. New wire cases
register synthetic PAN markers with existing capture before I/O. All successful
client reconstructions require exact safe output and done/end; failures require
no raw tail and no end. Actual gating proves progression before source completion.
Native sampled first-safe delivery0.078s; first/read inactivity observations15.031/
14.985s are fixture measurements, not exact native deadline proofs. Deterministic
deadline assertions remain authoritative for exact edges. Long-stream sampled peak
working set68837376 bytes, high-water raw304/candidate256/pending125 in tested
baseline workloads; no formal RSS/TLS/kernel10s/provider certification.

## Task4 evaluator readiness: verification only

| Requirement/finding | Source and fresh automated evidence | Decision |
| --- | --- | --- |
| Exactly50000,50001 denied; sliding interval `(t-60000,t]` | `accounting.calculate_usage`, `assess_admission`; `test_accounting.py::test_exact_lower_boundary_excluded_upper_boundary_included`; `test_storage.py::test_atomic_49999_50000_50001_boundary`; `test_http_wire.py::test_wire_exact_quota_and_denial_never_dispatches` | PASS |
| Tenant isolation, SQLite durable reopen/restart | `SQLiteStore._tenant`, `admit`, `settle`; `test_storage_processes.py::test_committed_settlement_and_hold_survive_independent_process_restart`; `test_http.py::test_http_concurrency_tenant_isolation_and_restart_persistence` | PASS, supported Windows fixed-local storage |
| Concurrent atomic admission | `SQLiteStore._transaction`, `BEGIN IMMEDIATE` read/decision/two inserts/COMMIT; `test_storage_processes.py::test_barrier_processes_compete_for_final_capacity` | PASS;6 competitors/one winner,15 storage children0 |
| Primary429/monotonic3000ms -> one eligible backup | `LLMService._exchange`, `_run`; `test_service.py::test_primary_429_exactly_one_backup_after_cleanup`; `test_primary_monotonic_timeout_boundaries`; wire routing test | PASS; controlled2999/3000/3001 edges and native synthetic fallback |
| Local quota never triggers backup; unconfirmed cleanup prevents unsafe fallback | `test_service.py::test_local_quota_denial_zero_provider_calls`; `test_cleanup_shared_grace_and_no_concurrent_backup`; exact-quota wire test | PASS; accepted500ms safety policy preserved |
| Conservative reservation/settlement/recovery | `SQLiteStore.settle`, `_recover`; `test_storage.py::test_holds_survive_window_and_recovery_is_full_bound_once_at_deadline`; `test_service.py::test_timeout_unknown_usage_is_full_primary_charge` | PASS; holds not zeroed/replayed after uncertainty |
| Standard sanitized errors; stock authenticated503 without adapters | `app._UnconfiguredProvider.prepare` raises BoundsUnavailable; `test_http.py::test_database_failure_is_sanitized_and_unconfigured_provider_fails_closed` | PASS, intentional default; no guessed tokens |
| Real providers/tokenizer/billing integration | No supplied vendor contract, endpoint or live API requirement; trusted Provider/PreparedAttempt injection only | NOT VERIFIED / rubric-dependent |

Full Task4 receipt:28 wire children (27 normal0,one expected startup3),15 storage
children all0, zero forced/live.21 local rejection journal entries show zero
provider/reservation deltas. Synthetic429 and timeout each show exactly1 primary,
1 backup,25 charged tokens; unknown-primary mode conservatively charges20; terminal
backup failure charges40 and has no third attempt. Quota over50000 never dispatches.

Task4 README now prominently documents stock503 and a one-command existing-fixture
demo. Exact command in E041/README freshly passed **9 cases,20 deselected,18.89s,
exit0**, including success,429,real timeout,quota and controlled failure cases.
All18 demo children exited0 with no forced cleanup. Full-suite receipts were copied
before this separate selector overwrote its local summary. No source/test/config/
dependency/lockfile change. Real-provider semantics remain unresolved, not a fail.

## Decisions, integrity and next action

| Decision | Status |
| --- | --- |
| Historical submitted Task3 without PAN detector | CHANGES REQUIRED; counterexamples reproduced, superseded by this correction |
| Three confirmed PAN counterexamples, within documented synthetic profile | PASS after correction; baseline FAIL reproduced |
| Existing/new redaction, async, ASGI and TCP regression | PASS;733 Task3 cases |
| Task4 explicit recovered requirements and executable synthetic demo | PASS in documented environment/accounting policies |
| Missing verbatim rubric/vendor formats, broader PII, real-model integration | NOT VERIFIED; request original rubric if required |
| Independent acceptance of new grammar, additive memory bound and implementation | APPROVED within documented synthetic profile; T3-007 DONE/E042 |

ADR-028 records alternatives/tradeoffs. All historical approvals/ADRs/test evidence
are preserved, with current-status correction notices. Task1/2 code/tests/config/
locks and ALL Task4 non-documentation files are byte-identical to captured baseline;
Task3 changes are one production file, existing test/oracle additions and one new
pure-test module. No new runtime dependency or wholesale parser/transport/app rewrite.
Ignored input/security/demo/verification scripts, receipts, DBs and archives stay
out of Git. At local verification handoff index was empty/no commit/push; E041
preserves that inspection. E042 and Git/session results record the subsequent
authorized acceptance checkpoint.

Changed-file inventory (19 paths):

- Production: `task3/src/task3_streaming/redaction.py`.
- Tests/reference: `task3/tests/support.py`, `task3/tests/test_redaction.py`,
  `task3/tests/test_app.py`, `task3/tests/test_http_wire.py`, new `task3/tests/test_pan.py`.
- Documentation: `AGENTS.md`, `README.md`, `task3/README.md`, `task4/README.md`,
  `docs/TASK3_REQUIREMENTS.md`, `docs/TASK4_REQUIREMENTS.md`,
  `docs/TASK3_FINAL_AUDIT.md`, `docs/TASK4_FINAL_AUDIT.md`,
  `docs/TASK_LEDGER.md`, `docs/DECISIONS.md`, `docs/BUILD_LOG.md`,
  `docs/TEST_EVIDENCE.md`, new `docs/TASK3_TASK4_EVALUATOR_REMEDIATION.md`.

Final SHA/AST/path inspection:96/113 original tracked paths unchanged, exactly17
authorized tracked modifications/two new paths. All145 original Task3 test
functions remain; only the two documented functions' obsolete PAN expectations
change, all other original function ASTs/decorators are identical.29 named report
test references and44 local links validate. No Task1/2 or Task4 non-documentation
change, parser/transport/app/harness change or dependency/config/lock mutation.

No outstanding local test failure or reproduced Task4 defect. Remaining material
risks are the explicit PAN scope/false positives, unavailable full rubric and
unchanged production/RSS/TLS/socket/provider limitations. Independent review
approved this documented grammar and auxiliary policy; full unavailable vendor
rubric remains NOT VERIFIED. One descriptive remediation acceptance commit is
authorized; preserve accepted implementation/tests, verify Git status and stop.
No additional feature, dependency, provider integration or push is authorized.
