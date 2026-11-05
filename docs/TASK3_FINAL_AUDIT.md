# T3-006: final Task 3 engineering and submission audit

2026-11-05, America/Los_Angeles. Audited baseline:
`6b768780ace49c984d105b5ce558f69904f1076a`.

**Final verdict: independently APPROVED; TASK-3 is assessment-ready within the
accepted synthetic SSE/PII contract and documented Windows environment.**
T3-006 and TASK-3 are **DONE**, user confirmation 2026-11-05. No blocking
implementation or documentation discrepancy was found. Tasks 1, 2 and 4 remain
DONE. One final documentation-only acceptance commit is authorized; no push.
Accepted implementation, tests, dependencies, configuration and lockfiles remain
unchanged. E039 is actual audit execution; E040 records qualified independent
documentation acceptance and Git inspection, not new test execution.

## Independent acceptance and review scope

2026-11-05, America/Los_Angeles. User reports independent ChatGPT engineering
APPROVAL: all eight high-level requirements/21 detailed criteria covered;73 unique
named tests checked against the previously submitted Task3 source archive;
implementation-symbol/local-link checks passed; E039 regression/eight Ruff results
consistent; assessor recipe passed syntax inspection. No blocking documentation
or traceability discrepancy. This final DOCUMENTATION review did not rerun the
full native Windows regression, directly audit unpublished local Git history or
validate unavailable vendor requirements. It does not independently re-execute
or broaden E039 findings. All historical environment, production, RSS, TLS,
socket and PII-coverage qualifications below are preserved. No new tests ran for
acceptance; no production changes or wider certification are implied.

## Requirement provenance and result interpretation

The original Task 3 vendor brief remains unavailable. The bounded materials search
and approval history are preserved in [the contract](TASK3_REQUIREMENTS.md) and
ADR-022. R1-R8 are the available user-supplied high-level requirements; P/L/I/H/W
are explicitly approved engineering policies. PASS below means verified for that
contract, not universal PII protection or compatibility with an unspecified vendor.
E039 in [test evidence](TEST_EVIDENCE.md) records executions during THIS audit.
Prior E031-E038 are historical evidence and independent-review provenance.

Paths in the matrices are relative to `task3/src/task3_streaming/` for implementation
and `task3/tests/` for tests. Every named test ran in the fresh 637-case suite.
The Q matrix and policy crosswalk expand the eight high-level rows, rather than
silently treating implementation choices as additional original requirements.

## High-level requirements traceability

| Requirement | Exact implementation | Automated test references | New evidence / status | Qualification |
| --- | --- | --- | --- | --- |
| T3-R1: independent async SSE proxy | `app.py:create_app`, `_Exchange.run`; `service.py:StreamSession.__anext__`; `upstream.py:UpstreamLease.read` | `test_app.py::test_asgi_send_backpressure_counts_and_progressive_safe_delivery`; `test_http_wire.py::test_wire_progressive_delivery_before_gated_upstream_completion` | E039 full suite and clean-environment TCP demos; PASS | Synthetic POST /stream, not a vendor API |
| T3-R2: redact before sensitive output | `redaction.py:classify_candidate`, `Redactor._classify`, `Redactor.process`, `Processor._events` | `test_redaction.py::test_all_categories_and_conservative_whole_candidate_masking`; `test_http_wire.py::test_wire_fragmentation_unicode_json_escapes_and_three_pii_categories` | E039 pure/ASGI/wire assertions; PASS | Narrow ASCII grammars and conservative whole-candidate masking |
| T3-R3: arbitrary chunk boundaries | `sse.py:SSEParser._decode`, `SSEParser.feed`; `payloads.py:inspect_event`; `redaction.py:Redactor.process` | `test_redaction.py::test_every_transport_byte_split_and_every_model_delta_split`; `test_redaction.py::test_random_chunk_and_delta_partitions_match_independent_reference` | E039 every representative split and randomized partitions; PASS | Adjacent deltas share state only within the same channel |
| T3-R4: bounded buffering | `models.py:Limits`; `sse.py:SSEParser._count`; `redaction.py:Redactor._safe`; `upstream.py:UpstreamLease.read` | `test_redaction.py::test_candidate_255_256_257_never_release_at_retention_threshold`; `test_redaction.py::test_long_stream_retained_state_independent_of_event_count`; `test_http_wire.py::test_wire_long_stream_high_water_and_empirical_process_rss` | E039 counters/limits and measured working set; PASS | Application-state bounds; no formal whole-process RSS ceiling |
| T3-R5: progressive delivery/backpressure | `service.py:StreamSession.__anext__`; `app.py:_Exchange._send`, `_Exchange.run` | `test_service.py::test_progressive_delivery_and_exact_read_counts_under_blocked_demand`; `test_http_wire.py::test_wire_slow_reader_native_buffering_probe_and_disconnect` | E039 gate/counter observations and clean demos; PASS | Awaited ASGI send is not physical socket acknowledgement |
| T3-R6: cancellation/error ownership/privacy | `service.py:StreamSession._start_close`, `_close_owned`; `app.py:_Exchange.aclose`, `_Runtime.aclose`; `redaction.py:Processor.abort` | `test_service.py::test_uncertain_cleanup_one_grace_retained_quarantine_and_late_release`; `test_app.py::test_disconnect_never_writes_error_or_flushes_pending_pii`; `test_http_wire.py::test_wire_shutdown_with_active_request_cancels_native_upstream` | E039 deterministic resistant cleanup plus native cooperative cleanup; PASS | Unconfirmed work remains owned and quarantined, not declared terminated |
| T3-R7: framing/metadata/terminals | `sse.py:SSEParser._end_line`, `encode_event`; `payloads.py:inspect_event`; `redaction.py:Redactor.process` | `test_sse.py::test_line_endings_bom_metadata_and_multiline_data`; `test_redaction.py::test_invalid_channel_transitions`; `test_http_wire.py::test_wire_fail_closed_without_unresolved_text_or_false_end` | E039 parser/profile and wire tests; PASS | Rechunking and metadata loss are approved profile semantics |
| T3-R8: private logs/errors | `models.py:StreamError`; `upstream.py:_private_io`, `_PrivateFilter.filter`; `app.py:_Exchange._report` | `test_redaction.py::test_no_sensitive_output_or_error_details_logs_or_abandoned_state`; `test_upstream.py::test_httpx_private_io_logging_suppressed_without_suppressing_other_requests`; `test_http_wire.py::test_wire_known_upstream_error_stays_fixed_and_drops_unresolved_candidate` | E039 captured diagnostics and publication screen; PASS | Operators must disable body/debug/access/telemetry capture; synthetic data only |

## Approved acceptance criteria: detailed implementation/test mapping

All Q rows are PASS under E039, with the explicit limits below. Test selections
are representative exact references, not a claim that one test alone covers every
assertion. The complete accepted suite was executed without deselection.

| ID / criterion | Implementing functions | Exact automated tests | Status / evidence |
| --- | --- | --- | --- |
| Q01: supported grammar, whole-candidate mask, unsupported forms | `redaction.py:is_canonical_email`, `classify_candidate`, `Redactor._classify` | `test_redaction.py::test_canonical_email_grammar_and_exact_lengths`; `test_redaction.py::test_phone_ssn_numeric_boundaries_exactly_match_approved_syntax`; `test_redaction.py::test_out_of_scope_forms_and_unmatched_unicode_are_not_normalized` | PASS / E039 |
| Q02: byte/delta partition equivalence | `sse.py:SSEParser.feed`; `redaction.py:Processor.feed` | `test_redaction.py::test_every_transport_byte_split_and_every_model_delta_split`; `test_redaction.py::test_all_short_candidate_partitions_and_no_prefix_before_done` | PASS / E039 |
| Q03: withheld candidates and independent channels | `redaction.py:Redactor.process` | `test_redaction.py::test_four_channels_independent_shared_delta_state_and_no_cross_channel_join`; `test_redaction.py::test_four_closed_channel_ids_still_cannot_be_reused` | PASS / E039 |
| Q04: Unicode, UTF-8 and JSON escapes | `sse.py:SSEParser._decode`; `payloads.py:inspect_event`; `models.py:scalar_text` | `test_redaction.py::test_multibyte_unicode_and_decoded_ascii_escapes_across_every_byte_boundary`; `test_sse.py::test_malformed_or_incomplete_input_latches_failure_without_raw_details` | PASS / E039 |
| Q05: SSE line endings, multiline data and dropped metadata | `sse.py:SSEParser._end_line`, `SSEParser.finish` | `test_sse.py::test_line_endings_bom_metadata_and_multiline_data`; `test_sse.py::test_empty_and_metadata_only_blocks_not_dispatched`; `test_redaction.py::test_composed_multiline_sse_and_cr_at_eof_terminal` | PASS / E039 |
| Q06: strict unambiguous bounded JSON | `payloads.py:_bounded_lexical_check`, `_pairs`, `inspect_event` | `test_payloads.py::test_ambiguous_invalid_and_unknown_shapes_reject_without_raw_context`; `test_payloads.py::test_json_resource_prechecks_fail_before_decoding_large_structures`; `test_payloads.py::test_lexical_resource_scan_respects_quotes_escapes_and_delimiter_characters` | PASS / E039 |
| Q07: separate exact/overflow resource caps | `models.py:Limits`; `sse.py:SSEParser._count`; `redaction.py:Redactor._safe`; `sse.py:encode_event` | `test_redaction.py::test_candidate_255_256_257_never_release_at_retention_threshold`; `test_sse.py::test_default_8192_line_and_16384_event_exact_boundaries`; `test_redaction.py::test_tightened_pending_scalar_byte_and_channel_caps_independent`; `test_payloads.py::test_payload_scalar_and_byte_limits_are_independent` | PASS / E039 |
| Q08: done/end/error state, EOF and truncation | `redaction.py:Redactor.process`, `Processor.finish`, `Processor.abort` | `test_redaction.py::test_only_valid_done_finalizes_tail_error_clears_every_channel`; `test_redaction.py::test_unexpected_eof_never_flushes_unresolved_text`; `test_redaction.py::test_missing_global_end_is_failure_even_after_valid_channel_done`; `test_redaction.py::test_terminal_encoder_failure_and_abandoned_terminal_cannot_claim_success` | PASS / E039 |
| Q09: safe framing and serialized size | `sse.py:encode_event` | `test_sse.py::test_encoder_escapes_text_without_sse_injection`; `test_sse.py::test_serialized_byte_limit_separate_from_scalar_limit`; `test_redaction.py::test_composition_rejects_encoded_output_overflow_without_success_or_raw_tail` | PASS / E039 |
| Q10: retained state independent of stream length | `sse.py:SSEParser.stats`; `redaction.py:Redactor.stats`, `Redactor._drain`; `service.py:StreamSession.__anext__` | `test_redaction.py::test_long_stream_retained_state_independent_of_event_count`; `test_redaction.py::test_four_maximum_holds_do_not_accumulate_event_envelopes` | PASS / E039; not formal RSS |
| Q11: independent reference and no prefix leak | `redaction.py:classify_candidate`, `Redactor.process` | `test_redaction.py::test_random_chunk_and_delta_partitions_match_independent_reference`; `test_redaction.py::test_bounded_adversarial_candidates_differential_reference`; `test_redaction.py::test_safe_prefix_is_delivered_without_consuming_complete_stream` | PASS / E039 |
| Q12: bounded detector and fixed private diagnostics | `redaction.py:classify_candidate`; `models.py:StreamError`; `upstream.py:_private_io` | `test_redaction.py::test_candidate_alphabet_is_exact_and_detector_has_no_extra_pattern_characters`; `test_redaction.py::test_no_sensitive_output_or_error_details_logs_or_abandoned_state` | PASS / E039 |
| Q13: single reader/progression/backpressure | `upstream.py:UpstreamLease.read`; `service.py:StreamSession.__anext__` | `test_service.py::test_progressive_delivery_and_exact_read_counts_under_blocked_demand`; `test_service.py::test_pending_sanitized_frames_do_not_read_next_network_chunk` | PASS / E039 |
| Q14: deadline and cancellation ownership | `service.py:StreamSession._watch`, `_guard_cleanup`, `_close_owned`; `app.py:_Exchange._send`, `aclose` | `test_service.py::test_first_valid_event_monotonic_boundary_and_no_partial_flush`; `test_service.py::test_overall_deadline_closes_while_consumer_is_paused`; `test_service.py::test_repeated_cancel_cannot_discard_request_cleanup_worker`; `test_app.py::test_send_cancellation_and_response_close_share_one_cleanup_grace` | PASS / E039; deterministic exact boundaries |
| Q15: isolation, fixed transport and credentials | `upstream.py:UpstreamSettings.__post_init__`, `UpstreamAdapter.__init__`, `UpstreamLease.open`; `service.py:Capacity.acquire` | `test_upstream.py::test_authorized_content_types_request_bytes_and_separate_credentials`; `test_upstream.py::test_open_failures_no_retry_and_no_diagnostic_context`; `test_upstream.py::test_raw_64k_segmentation_does_not_coalesce_small_events`; `test_service.py::test_process_global_16_stream_cap_across_services_zero_requests_for_excess` | PASS / E039 |
| Q16: HTTP/auth/schema/status and zero forwarding | `settings.py:authenticated`, `load_settings`; `app.py:_metadata`, `_body`, `_inspect`, `create_app` | `test_app.py::test_http_authentication_rejects_before_body_or_upstream`; `test_app.py::test_metadata_failures_do_not_read_body_or_contact_upstream`; `test_app.py::test_strict_prompt_validation_zero_upstream`; `test_app.py::test_body_limit_enforced_across_chunked_receive_messages` | PASS / E039 |
| Q17: ASGI send deadlines, disconnects, fail closed | `app.py:_Exchange._send`, `_listen`, `_report`, `run` | `test_app.py::test_exact_send_deadline_no_raw_tail_or_error_write_after_stall`; `test_app.py::test_send_uses_remaining_overall_budget_instead_of_another_ten_seconds`; `test_app.py::test_postheader_failure_closes_without_end_or_new_status`; `test_app.py::test_disconnect_never_writes_error_or_flushes_pending_pii` | PASS / E039; physical kernel expiry NOT VERIFIED |
| Q18: global capacity, lifespan and quarantine | `app.py:_StreamResponse.__call__`, `_Runtime.aclose`, `_Exchange._release`; `service.py:StreamService.aclose` | `test_app.py::test_http_capacity_is_process_global_across_application_instances`; `test_app.py::test_http_cap_includes_blocked_terminal_sends_after_upstream_releases`; `test_app.py::test_uncertain_send_cleanup_retains_owner_quarantine_and_late_confirmed_release`; `test_app.py::test_cancelled_lifespan_waiter_retains_and_finishes_shared_pool_close` | PASS / E039 |
| Q19: actual independent-process HTTP progression | `app.py:create_app`, `_Exchange.run`; `upstream.py:UpstreamLease.read` | `test_http_wire.py::test_wire_progressive_delivery_before_gated_upstream_completion`; `test_http_wire.py::test_wire_content_length_and_chunked_requests_credentials_isolated` | PASS / E039 native sockets and two clean-env demos |
| Q20: real failures/concurrency/privacy | `app.py:_Exchange.run`, `_Exchange.aclose`; `service.py:StreamSession._watch` | `test_http_wire.py::test_wire_real_inactivity_deadlines_close_native_resources`; `test_http_wire.py::test_wire_sixteen_active_streams_seventeenth_denied_then_capacity_released`; `test_http_wire.py::test_wire_client_disconnect_closes_blocked_upstream_and_withheld_pii` | PASS / E039; native cooperative cancellation |
| Q21: measured memory/flow control and subprocess cleanup | `redaction.py:Redactor.stats`; `app.py:_Runtime.aclose`; accepted test harness `http_wire_support.py:Lab` | `test_http_wire.py::test_wire_long_stream_high_water_and_empirical_process_rss`; `test_http_wire.py::test_wire_slow_reader_native_buffering_probe_and_disconnect`; `test_http_wire.py::test_wire_fixture_exception_still_reaps_both_children`; `test_http_wire.py::test_wire_invalid_configuration_child_exit_is_expected_and_reaped` | PASS / E039 with OS/RSS qualifications |

## Complete approved-policy crosswalk

The contract remains authoritative for exact syntax and all numeric caps. Each
policy below maps to the exact functions/tests above; all have PASS evidence in
E039 within the stated scope. No new contract is introduced by this audit.

| Approved policy IDs | Concrete policy audited | Detailed traceability |
| --- | --- | --- |
| T3-P1; T3-PII-EMAIL/PHONE/SSN | Narrow ASCII grammar; whole maximal candidate replacement `[REDACTED]`; conservative any-@ masking | Q01, Q03, Q11, Q12 |
| T3-P2 | Decode UTF-8/JSON only; no normalization; independent per-channel logical text across events | Q02-Q04 |
| T3-P3 | Maximal candidate withholding until true delimiter or valid done; overflow never releases prefix | Q03, Q07, Q08, Q11 |
| T3-P4 | Exact synthetic delta/done/end/error JSON-over-SSE profile; four channel IDs; rechunked sanitized output | Q05, Q06, Q08, Q09 |
| T3-P5 | Drop comments/IDs/retry/unknown fields; no duplicate done/data-after-done/premature end; no truncated success | Q05, Q08, Q09 |
| T3-P6; T3-L1-L6 | Independent chunk/UTF-8/line/event/decoded-scalar/candidate/pending/encoded-byte limits | Q04, Q06, Q07, Q09, Q10, Q15 |
| T3-L7 | Process-global cap16, no admission queue, cap includes HTTP terminal sends | Q15, Q18, Q20 |
| T3-L8 | Pool/connect/write5s, first-valid15s, read-idle15s | Q14, Q15, Q20 |
| T3-L9 | Overall120s, send10s, monotonic absolute budgets | Q14, Q17; native inactivity/progression observations supplement, not replace controlled boundary proof |
| T3-L10; T3-P7 | One anchored request cleanup1s, backpressure, fixed errors, retained uncertain owners/quarantine | Q13, Q14, Q17, Q18, Q20, Q21 |
| T3-P8 | Isolated modules/environment/lock; pure Processor is only privacy composition path | Q01-Q12; locked-install and baseline/import inspections below |
| T3-I1-I3 | Fixed trusted URL, separate credentials, no redirects/retries/env proxy/cookies, strict response headers, <=64KiB raw block/4KiB slices | Q15, Q16, Q19 |
| T3-I4-I5 | Pull-driven single owner/reader, capacity and first/read/overall deadlines | Q13, Q14, Q18, Q20 |
| T3-I6-I8 | Shielded close worker, retained uncertain ownership, sanitized Processor frames/logs, cooperative cancellation | Q12, Q14, Q17, Q18, Q21 |
| T3-H1-H3 | POST /stream only, operator Bearer, fixed environment loading/lifespan | Q16, Q18; default-factory clean demo below |
| T3-H4-H6 | Bounded framing/body/schema, canonical prompt bytes, auth before body, upstream preflight before headers | Q15-Q17, Q19 |
| T3-H7-H9 | Await actual ASGI sends, no postheader local error/end, disconnect ownership, HTTP cap/shutdown/quarantine | Q13, Q14, Q17, Q18, Q20 |
| T3-W1-W3 | Separate loopback processes, ephemeral child-bound ports, gated secret-free journals, actual native HTTPX/Uvicorn wrappers | Q19-Q21; fresh child receipts below |
| T3-W4-W6 | Gated progression, slow-client/native buffers and representative native inactivity timeouts | Q19-Q21; numeric observations below |
| T3-W7 | Bounded high-water counters and empirical Windows working set | Q21; numeric observations below, not formal RSS |
| T3-W8 | Bounded fixture cleanup, classified process exits, explicit wire/deployment limits | Q20-Q21; receipts/limitations below |

Additional mandatory T3-001 rules are covered explicitly: valid-done-only tail
classification (Q08); no malformed termination/EOF flush (Q08); separate byte,
scalar and serialized caps (Q07/Q09); no retention-threshold prefix release
(Q03/Q07); strict channel state (Q03/Q08); unambiguous JSON (Q06); detector alphabet
equal to candidate alphabet (Q12). All PASS. No unresolved interpretation of the
approved synthetic contract was found; unavailable vendor requirements are
**NOT VERIFIED**.

## Fresh four-project regression and runtime evidence

Each suite used its own existing pinned native Windows environment and separate
working directory. Runs were independent concurrent processes, not one combined
pytest invocation. Commands and per-command exit codes are recorded in E039.

| Project / cwd | Python | SQLite runtime | Fresh pytest outcome | Duration | Ruff lint / format | Format files |
| --- | --- | --- | --- | --- | --- | --- |
| Task 1 / repository root | 3.12.16 | 3.53.1 metadata | 149 passed, exit0 | 39.44s | PASS0 / PASS0 | 17 |
| Task 2 / task2 | 3.12.16 | 3.53.1 metadata | 452 passed, exit0 | 12.39s | PASS0 / PASS0 | 16 |
| Task 4 / task4 | 3.12.16 | 3.53.1 supported storage | 427 passed, exit0 | 50.33s | PASS0 / PASS0 | 22 |
| Task 3 / task3 | 3.12.16 | 3.53.1 metadata only | 637 passed, exit0 | 56.31s | PASS0 / PASS0 | 25 |

**1665 passed total; zero failures, errors, skips, warnings, xfails or xpasses.**
All eight Ruff commands exit0. Durations overlap and are not total elapsed time.
All environments: pytest9.2.0/Ruff0.17.3. Task1: mcp2.3.0/Pydantic2.12.5/
pytest-asyncio1.4.1.post1. Tasks2/3/4: HTTPX0.28.1, FastAPI0.162.0,
Starlette1.10.0, Pydantic2.14.2, Uvicorn0.54.0; Task2/3 httpcore1.0.9.
Task3 has no SQLite dependency/operation. Task4 retains Windows fixed-local-drive
and supported-runtime gates; no Linux compatibility shim was used here.

Fresh process receipts: Task2 12 reaped, zero alive/forced/live reader threads
(intentional failure exits1 and3 remain negative scenarios); Task4 28 wire children
all expected exits (27x0/1x3), zero forced, plus15 storage children all0, none alive
or forced. Task3 10 children:9x0 and1 expected startup-invalid2; zero forced,
killed, live reader threads or private diagnostic violations. These are fixture
receipts, not a blanket OS-wide process or remote-provider termination guarantee.

## Privacy, bounded-state and stream-integrity findings

The candidate alphabet is exactly ASCII letters/digits plus `._%+@-`. Every
supported sensitive form uses only that alphabet. A maximal run is withheld until
a true nonalphabet delimiter or validated done; therefore a supported sensitive
value cannot straddle a released run boundary within one channel. Classification
replaces the ENTIRE candidate once; conservative any-@ masking intentionally
overmasks. Candidate257 fails closed before release, including benign long tokens.
No fixed suffix-retention threshold can justify releasing a prefix. Only valid
done finalizes a tail; errors, abandonment, malformed events and EOF discard it.

Four channel states are request-local. UTF-8 and JSON escapes decode before
classification. Streams cannot join text across channel IDs or reuse a done
channel; end requires all opened channels completed. Framing metadata is dropped,
not echoed. Strict duplicate-key and size/depth/member/numeric checks reject
ambiguous payloads. Output encoding cannot inject SSE fields or error diagnostics.
Known synthetic upstream errors use fixed messages. Other postheader failures
close without a local error event or successful end; clients must require end.
A validated end/error stops consumption; trailing bytes in that raw chunk are not
claimed validated. Encoder alone is not a privacy boundary; use Processor.

Independent caps remain:4KiB processing chunk,3-byte decoder carry,8192-byte line,
16384-byte event,4096 decoded scalars/delta,256 candidate ASCII chars/channel,
four channels/1024 unresolved bytes total,1024 pending scalars AND8192 pending
UTF-8 bytes,8192 serialized event bytes,256-scalar emitted fragments,64KiB retained
native transport block. All count their own representation, including escaped
serialization overhead. Event envelopes do not accumulate. No producer queue.

Fresh native wire observations (not mathematical OS bounds):

- First safe client frame in0.093s while source completion was gated;2 read
  attempts included1 delivered raw chunk. The proxy did not consume all input.
- 23 HTTP/auth/body rejection cases caused zero upstream journal calls. Capacity
  rejection also forwarded0;16 streams occupied slots and17th returned429, then
  confirmed cleanup allowed reuse.
- First-valid timeout15.000s/read-idle15.016s closed with peer disconnect and no
  successful HTTP-stream completion. Exact10s send/120s overall/1s cleanup edges
  were verified by deterministic clocks/ASGI tests, not long native wall-clock runs.
- Slow client reproduced one suspended ASGI send;117 native read attempts stayed
  frozen through3 control barriers,124004 native bytes received/143545 ASGI bytes
  offered. Cumulative counts are not buffer occupancy. Requested client receive
  buffer4096/listener send buffer16384 are test settings, not production guarantees.
- 1000/5000-event streams produced125000/625000 logical characters. Both had
  high-water line290/event304/decoder2/candidate256/held256/pending125 chars and
  bytes/encoded169/raw304. Windows working set was66027520->66043904 and
  66048000->63483904 bytes, sampled peak68521984. Empirical only, not formal RSS.
- Active native shutdown was clean and closed pool once. Resistant-close tests
  retain owners/slots, quarantine new admissions, release only after confirmed
  completion and never close pool under uncertain work. Quarantine remains sticky.

Unsupported PII includes names, addresses, cards, semantic identifiers, non-ASCII
mailboxes/digits, obfuscated/encoded/normalized representations and phone formats
outside the approved syntax. Splitting a value across channels or changing logical
text with inserted delimiters is outside the profile. No universal privacy claim.

## Reproducibility and assessor demonstration

A NEW ignored environment `.cache/t3006-clean-env` was created with the unchanged
Task3 lockfile and `uv sync --locked --extra dev --extra serve --offline`, using
native3.12.16. Exit0;25 locked packages installed, editable package/imports worked.
Exact command and versions are in E039. No existing environment was repurposed.

Two real-TCP, separate-process demonstrations ran from that clean environment:

1. The self-contained fixture-backed recipe now in [Task3 README](../task3/README.md)
   uses deterministic source gates. Missing/invalid credentials each401 and zero
   forwarding; authenticated200 emits `hello ` before releasing source completion,
   then `[REDACTED] `, done and end. Active HTTP/upstream owners return0,
   no quarantine. Upstream40180/proxy27056 both exit0, no forced cleanup.
2. Public Uvicorn Config loaded `task3_streaming.app:create_app` in factory mode
   without injected HTTPSettings, using T3_ACCESS_TOKEN/T3_UPSTREAM_URL/
   T3_UPSTREAM_BEARER with separate ephemeral credentials. Same401/401/200,
   gated progression/sanitized terminal; independent upstream journal exactly1.
   Proxy19952/upstream28556 exit0, no forced cleanup, zero live reader threads.
   This verifies factory import/config/lifespan using public Uvicorn APIs;
   literal shell-CLI signal/console shutdown behavior was not exercised.

An initial invocation of the IGNORED audit utility failed with AttributeError
because its test adapter lacked a process handle, before any generation request.
Only that utility was corrected; no accepted source/test changed. Bounded finally
cleanup ran, but that failed attempt has no complete PID/exit receipt and is not
counted as a successful demo. A later native process inventory found no matching
remaining audit/provider child. The second factory-demo invocation exited0.

README explains setup, required env variables, separate client/upstream credentials,
loopback Uvicorn command, a real HTTP client, canonical prompt API, completion
semantics and limits. The new fixture recipe needs dev/serve extras but no vendor,
external service, configured real secret or reading of harness internals. Its
`__wire_stats` instrumentation is fixture-only, not a production endpoint.

## Security and Git publication findings

Read-only current-file and reachable-history scan covered19 commits,339 objects,
234 unique text blobs/5475913 bytes and112 historical paths. No binary blobs.
Private-key/common provider-key screens found0. Eleven deduplicated
(pattern-kind,fingerprint) credential-looking candidates/12 occurrences were
context-reviewed:6 synthetic fixture/documentation,1 invalid one-character test
credential,1 malformed credential test,2 invalid-destination URL fixtures and1
token-count type-error false positive. **No actual disclosure or unresolved
candidate was identified.** No real prompt/completion/customer data was found in
the reviewed synthetic fixtures. Reports contain counts/paths/fingerprints, not
raw credentials. Origin has no embedded credential.

No tracked current/history environment, cache, egg-info, SQLite/DB/WAL/SHM, review
archive, receipt or credential-history artifact was found. This is a heuristic
screen plus contextual review, not a certification of arbitrary PII, unknown key
formats, unreachable objects, remote/unfetched history or dependency advisories.

Ignore probes confirm `.cache`, environments/generated egg-info, `.env.production`
and default `.runtime/usage.sqlite3` are excluded. A specific existing review ZIP is
locally excluded. Arbitrary root `audit-review.zip` and `task4/usage.sqlite3` outside
ignored runtime directories are NOT covered by portable ignore rules. No such
artifact is tracked. Preserve explicit-path staging; portable ignore expansion
requires separately authorized configuration work. It was not silently changed.

Baseline SHA256 inventory covers112 tracked files. Accepted Task3 Python files,
all Task1/2/4 implementation/tests/dependencies/lockfiles/configuration and root
pins are unchanged. AST import inspection found no cross-task production imports.
Four separate environments/import namespaces remain independently executable.
104 of112 original tracked files are byte-identical; eight authorized documentation
files differ, plus this new audit. All25 Task3 Python files are byte-identical.
AST inspection validates73 named test references and36 module/function references;
29 local links resolve and the copyable Python recipe parses. Historical build,
decision and test-evidence content is preserved as an unchanged prefix, with new
entries appended. Only authorized audit documentation changed; index empty, no
unexpected untracked artifacts. Final whitespace/status checks are in E039.
At the original audit handoff, HEAD was6b768780ace49c984d105b5ce558f69904f1076a,
main ahead4/behind0 recorded origin/main; no fetch/publication/staging/commit/push
was performed during that audit. The subsequent documentation-only acceptance
checkpoint is recorded in E040 and Git/session results, preserving these findings.

## Qualifications, remaining risks and submission checklist

E038 independent Linux/Python3.13.5 review used an import-path change ONLY in its
extracted harness. 580 prior tests and57 wire cases had passing assertions across
split executions, with40 extra fragmentation cases. A combined wire run stalled
after50 cases; a19-case split printed a passing summary but did not return promptly.
It is NOT a clean combined637 Linux pass. E039 is a fresh native Windows637 pass,
exit0. Prior review qualifications/history remain intact.

**NOT VERIFIED / excluded:** unavailable vendor requirements; real-provider APIs,
tokenization/billing/remote cancellation; universal PII; production TLS, reverse
proxy buffering, deployment, multiworker/global distributed limits; literal
console/signal shutdown; formal whole-process RSS ceilings; actual kernel-level
10s send-stall expiry and120s native wall boundary. Cooperative cancellation cannot
force arbitrary resistant code to stop; retained/quarantined ownership is the
fail-closed policy and may require supervisor intervention. HTTP server owns
unadmitted connections/header allocations. No retries, redirects, hedging, resume,
provider credential passthrough or cross-channel semantic reconstruction is added.

| Submission check | Result |
| --- | --- |
| Available requirements and all approved policies mapped to source/tests | PASS; R/Q/policy matrices above |
| Fresh complete independent project suites and eight Ruff checks | PASS;1665 tests, all command exits0 |
| Clean locked setup/imports/startup and deterministic successful demo | PASS with synthetic/CLI qualifications above |
| Streaming privacy, terminal integrity and supported-category fragmentation | PASS within approved narrow profile |
| Backpressure/deadlines/cleanup/capacity and process receipts | PASS within deterministic/native distinctions |
| Current/reachable-history secret/artifact contextual screen | PASS; no actual finding, heuristic scope documented |
| Accepted code/tests/config/locks and project isolation | PASS; SHA/import inspection, no functional changes |
| README contract, assessor demo and governance status | PASS; documentation corrected; T3-006/TASK-3 DONE after independent approval |
| Independent T3-006 acceptance and final documentation Git checkpoint | PASS independent documentation review; one final documentation commit authorized, no push |

No blocking production correction is recommended. Independent review is complete;
READY is restricted to the documented scope, not the unavailable original vendor
brief. Preserve all accepted implementation and evidence. After the authorized
documentation commit, stop; publication or further work needs separate authorization.
