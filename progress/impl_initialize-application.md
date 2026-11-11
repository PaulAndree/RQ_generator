# Implementation report

Feature 1, initialize-application. Approved for authorized delivery.
Worktree /tmp/rq-initialize-application-1110a, branch agent/initialize-application-1110a.
Base 6b9de636dfb838a9d1543dcbf8baa20c2761428b. Changes are uncommitted.
The user authorized delivery and PR publication on 2026-11-11. No merge is authorized.
Feature stays in_progress pending delivery and leader-authorized finalization.

## Outcome and revision

87 tests pass and Ruff passes after F1/F2 review corrections. The original
real-service A/B/C run establishes failure isolation, multibatch C behavior and
backend delivery. Its A card failed contextual fidelity review and is superseded
by the corrected real A run documented below. The final A card omits the refuted
introductory claim while retaining the qualified conclusion and conditions.
Reference integrity and direct metadata-only Loki/Prometheus/Langfuse checks pass.
Prior Grafana, explicit content opt-in and controlled model-failure evidence apply
to unchanged telemetry paths. Independent review approved the final implementation; authorized delivery is next.

Final implementation SHA-256 is
678c5c1a9fc128a887df65c03e304090a02b21b861e8188938dd7b48864ac072.
.artifacts/initialize-application/final-implementation-manifest.json contains sorted
path/SHA-256 entries for src, tests, scripts, monitoring, README.md, pyproject.toml,
uv.lock and .env.example, excluding Python caches. The digest hashes that manifest's
canonical JSON. Progress/checklist edits and ignored credentials/artifacts are excluded.

The successful full run used snapshot
1f253378605f06e09bd3fd9a635c0a5395e92db39c03ba2a02daeebe18929026.
Subsequent runtime deltas record available usage before rejecting length-exhausted
output and add complete-source claim review for single-segment documents. The
multibatch extraction/consolidation/compression path, model settings and telemetry
are unchanged. The final A run exercises the changed single-segment path. A repeated
real model failure exercises usage recording. The final full suite passes.

Specification revision 1 approval is in progress/current.md. Requirements SHA-256
8307e3049c00bd8d08d52c18ecb763f2844140a7bc8cbb8debb7d72869ac0068;
design f6e6da7fb0008170597853127e4af0165d102360a9e5e7b552c2777ca76f5e9b;
tasks before completion checkbox updates
64321b785f81151bdbfa1c3757e39cd0ccc7dfa6e46f199188fbbdee159664b0.
No substantive specification text changed. T1 through T17 are complete for review.

## Changes

Added installed console/module entry points, configuration, ordered PDF discovery,
stable IDs, strict schemas, verified OCR/chunking/Ollama clients, official vocabulary
normalization, sequential failure isolation and reference-safe atomic checkpoints.

Generation selects source sentence IDs. Python renders exact claims/summary and
derives claim/question evidence. Questions require explicit unresolved-source
rationales. Citations/abbreviations stay attached to their sentences. All extraction
entity mentions are normalized/deduplicated in Python with their full evidence,
independently of semantic reduction. Bounded reduction deduplicates units and omits
redundant hashes. When grouping stalls, bounded claim-only compression halves the
selection limit, preserves summary/questions/evidence, and must strictly reduce
complete packet bytes. Existing finite call limits remain; no fixed card claim cap.

Added JSON Loki logs, stable Pushgateway batch metrics, Langfuse observations/flush,
a shared Grafana dashboard, privacy/outage controls, usage/reference documentation,
.env.example and dashboard installer. No shared monitoring stack was deployed.

## Verification

Python 3.12.3 and task-local editable environment from
`uv sync --extra dev --extra telemetry`, exit 0.

| Command/check | Exit | Result |
| --- | --- | --- |
| .venv/bin/python -m pytest -q | 0 | 87 passed in 10.00 seconds |
| .venv/bin/ruff check src tests scripts | 0 | All checks passed |
| .venv/bin/rq-generator --help | 0 | Installed entry point |
| .venv/bin/python -m rq_generator --help | 0 | Module entry point |
| git diff --check | 0 | No whitespace errors |
| Full normal CLI below | 1 expected | A success, invalid B failure, C success |
| .venv/bin/python tests/integration/check_live_outputs.py .artifacts/initialize-application/complete-output --environment integration-complete | 0 | Saved schemas/refs, Loki, Prometheus, Langfuse and privacy assertions |
| .venv/bin/python .artifacts/initialize-application/check_complete_grafana.py | 0 | All six actual dashboard queries |
| Controlled model-failure CLI below | 1 expected | Real Qwen length exhaustion, no card |
| Direct HTTP backend assertions recorded in model-failure-fixed-evidence.json | 0 | ERROR trace, exact usage/latency, one call, metadata-only, gateway values |

Initial failures preceded fixes. Core import absence at baseline exited 2 and is
interface-absence evidence, not runtime success. Adapter tests initially failed 6,
generation 3, vocabulary 2 with 1 passing, pipeline stub 2 with 2 passing, and
telemetry stub 3, each exit 1. Later scientific/source-ID/schema/reference/entity/
compression regressions failed before their corrections, exit 1. The final suite
passes those cases. Setup-only missing test imports and Ruff findings were corrected
and are not counted as feature successes. Regression details are mapped below.

## Real-service run

```bash
TRACE_CAPTURE_CONTENT=false APP_ENV=integration-complete \
VOCABULARY_DIR=/tmp/rq-initialize-application-1110a/.artifacts/vocabularies \
.venv/bin/python .artifacts/initialize-application/run_complete.py \
.artifacts/initialize-application/verified-input \
--output-dir .artifacts/initialize-application/complete-output
```

This invokes normal installed rq_generator.cli.main, real Services/Generator, and
only captures ignored local diagnostics. It changes no application settings or
processing decisions. Original PDF paths/hashes are recorded in
.artifacts/initialize-application/verified-input-provenance.json. C is the complete
Fidelity and infidelity, Nature 2001 PDF, not truncated content. Real OCR/chunking
returned 6320 source bytes in four chunks; four bounded extraction batches were used.

Run ef55cba1a7f0457f8e5475716d98086e started 2026-11-10T22:54:54Z and completed
2026-11-10T23:07:08Z in 734.227 seconds. A had 5 claims/2 entities; C had
13 claims/17 entities. B failed OCR as deliberately supplied invalid input. State
assertions confirm success/failed/success order, two cards, five saved chunks,
valid same-document references and no partial B card.

All 18 actual requests, including their exact dynamic schemas, fit the 11264-byte
allowance. Maximum was 11104 bytes. Requests comprised 5 extraction, 10 consolidation
and 3 compression calls. C used 17 calls within its finite limit of 32. Live fallback
reduced packets 13→6 claims, 8556→6425 bytes; 11→5, 8694→6718; and 16→8,
9742→7103. Summaries/questions were unchanged. Evidence is final-request-budgets.json
and complete-diagnostics/compression-*.json under .artifacts/initialize-application.

Configured qwen3:14b, context 16384/output 4096 and 600-second timeout were retained.
Ollama advertises maximum context 40960. OCR/chunking OpenAPI info versions are
0.1.0. Verified routes are multipart /services/ocr with type_name=pdf and form
/services/chunking/doc_by_titles. No local PDF parser substitutes for these services.

## Scientific source comparison

The original A card preserved exact quotations but incorrectly presented an
introductory exception as a central claim beside the conclusion that resolves it.
Review F1 correctly rejected that result. Exact quotation did not establish
contextual fidelity. The corrected final A source comparison appears below and
supersedes the earlier A acceptance result.

C's thirteen claims are exact saved-source sentences. They preserve "may", "probably",
"up to half", the normal-human-cell context, and the final innovation/robustness
conclusion. Findings/conditions/entities quote supported source statements. Methods
and limitations are null, appropriate for this commentary without a reported
experimental protocol or explicit study limitation. Rhetorical questions in the
source are answered there; no candidate question is invented. Official examples
include GO and MeSH DNA replication, each with both supporting chunks, GO protein
biosynthetic process, and MeSH streptomycin/neurons/myocardium. OCR line-break artifacts
are preserved rather than silently changing source wording.

## Telemetry and privacy

complete-delivery.json verifies two Loki card events, controlled document failure,
run completion, Prometheus successes=2, 18 real qwen3:14b generations and three OCR
error observations. All generation usage is positive; totals 33255 input/6206 output
tokens match Pushgateway values, with maximum generation output 1874 below reserve
4096. Prompts/responses are absent from all observed final-run tracing IO.

Pushgateway reports executions=1, successes=2, failures=1, model_calls=18 and positive
model/job durations. Grouping is stable job/environment, without run/document labels.
Actual shared targets are Loki3101, gateway9095, Prometheus9094, Grafana3005 and the
configured Langfuse. Documented Grafana3013 does not answer; no infrastructure changed.

Dashboard http://127.0.0.1:3005/d/rq-generator-document-cards/scientific-document-cards
is imported/read back, using shared-loki/shared-prometheus sources. Authenticated
/api/ds/query verifies all six panels. Final table has two card rows with ID/status/
counts, logs include success/failure, metric panels have data, and metadata-only
full-content panel has zero rows. Evidence is complete-grafana-panel-evidence.json.
No browser screenshot is claimed.

Prior explicit content-enabled run a724d52246084f75a2ac6736cda3feea verified actual
Langfuse prompt/response capture and Loki full-card events. Authenticated Grafana
queries showed one content row for feature1-test and zero for feature1-metadata.
That evidence remains in grafana-panel-evidence.json and earlier delivery artifacts;
content-capture behavior is unchanged. Independent backend outage tests preserve
valid pipeline outputs and suppress secret exception text.

## Controlled real generation failure

The normal CLI error check used the same model/context, explicit
OLLAMA_OUTPUT_TOKENS=128, TRACE_CAPTURE_CONTENT=false,
APP_ENV=integration-model-failure, the task vocabulary cache, metadata-input and
model-failure-fixed-output, through run_model_failure.py. This captures provider
usage metadata only. It exited 1 as expected, persisted no partial card and flushed
one GENERATION ERROR observation for actual done_reason=length.

The initial error check exposed available provider usage not recorded before
length rejection. test_truncated_model_response_records_available_usage_before_failure
failed with zero observations before the isolated fix. Model usage now records
before that rejection; the test asserts exactly one update. Repeated real error
run 0001c54f5ec54f12913a7faf539d187b records exactly 1564 input/128 output tokens,
one model call, positive duration and ERROR status. Trace usage and gateway usage
match the actual provider counters, with no content capture or double count.
Evidence is model-failure-fixed-evidence.json. Normal successful response handling
and the successful full-run model prompts are unchanged by this final delta.

## Resources and traceability

Official reference snapshots/provenance are in .artifacts/vocabularies/manifest.json
and provenance.json. GO release2026-07-26 SHA256
b08d45b268b8c24ccb2513dbbbc7d4df9f6521c099b413f79eb31e06e0fa3bcc;
CL2026-06-08 7e19b4aef8e7fe7720b0c4474c6a5b8713c904ea9ab7b7d5d96f2cb28b8fc51f;
MeSH2026 449792ed59ba4d60035e44724352f7361ec0dc945b67dcd821a50ff32f81bcdb;
HGNC Last-Modified2026-11-05
3944cdad7affce5bc2c7d63d7079d7e68762ed28ef414fc287cc0f57c4b0d78f.

[GO policy](https://www.geneontology.org/docs/go-citation-policy/) and
[CL metadata](https://obofoundry.org/ontology/cl.html) confirm CC BY4.0;
[HGNC](https://www.genenames.org/about/license/) confirms CC0.
[NLM terms](https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html)
require attribution, no implied endorsement and current data or an identified release.
README records the sources/terms and MeSH release. No reference cache is published.

| Acceptance | Requirements | Tasks | Concrete assertions/evidence |
| --- | --- | --- | --- |
| Ordered PDF discovery | R1, R2, R19 | T2, T3, T9, T10, T13 | test_discovery_filters_and_orders excludes symlinks/directories, orders Unicode filenames; test_cli_order_failure_and_outputs asserts OCR-call order and output override; test_cli_rejects_invalid_input_and_handles_empty asserts invalid status and empty JSON output. |
| Stable source outputs | R4, R5, R6 | T2, T3, T4, T5, T13 | test_document_and_chunk_id_stability changes bytes/filename/ordinal; test_ids_relocate_and_change_with_source_metadata compares relocated roots and metadata changes; test_service_contracts_and_metadata asserts required multipart/form fields, section and OCR metadata. |
| Existing OCR/chunking and Qwen | R3, R7, R17 | T1, T4, T5, T6, T7 | test_service_contracts_and_metadata asserts exact normal routes; test_ollama_model_and_json_contract asserts qwen3:14b and request settings; test_timeout_retries_are_bounded_and_malformed_chunks_rejected and test_bounded_retries assert bounded attempts and bad response rejection. Live source/model checks are documented above and in the corrected A evidence below. |
| Evidence-linked compact cards | R8, R9, R10, R12, R13, R14, R16 | T2, T3, T6, T7 | test_selected_source_sentences_preserve_qualifiers_and_reject_inventions asserts exact final claim/summary and invented ID rejection; test_generation_bounds_every_request_and_assigns_claim_ids checks every serialized request, all chunks, Python claim IDs; test_multilevel_reduction_bounds_all_requests checks several reductions; test_zero_claims_and_invalid_evidence permits zero claims and rejects invalid refs; test_oversized_intermediate_never_reaches_unbounded_request and test_oversized_complete_sentence_fails_without_clipping_source reject unsafe budgets; test_consolidation_cannot_select_sentence_from_another_group rejects unprovided sentences; test_fidelity_prompt_keeps_qualifiers_and_explicit_summary_support checks prompt instructions. Manual source comparison exposed F1; the corrected final A run below now passes implementer comparison and awaits independent review. |
| Official biomedical entities | R11, R13, R16 | T8 | test_normalization_supported_aliases_and_vocabulary_overlap asserts GO/MeSH overlap, HGNC alias mapping, explicit evidence; test_ambiguous_aliases_case_and_explicit_evidence rejects ambiguity, unsupported case, substring matches; test_reference_load_filters_go_namespace excludes GO non-process/obsolete terms; test_reference_provenance_and_offline_failure checks exact source hashes and unavailable references. Official live samples are recorded in the C comparison and corrected A evidence. |
| Single consolidated cards JSON | R9, R15, R16, R18 | T2, T3, T9, T10 | test_cli_order_failure_and_outputs asserts one card per success in input order and failed middle attempt; test_cli_continues_after_generation_or_validation_failure excludes failed cards; test_checkpoint_fault_matrix_keeps_published_evidence injects 10 write boundaries and independently resolves saved refs; test_writer_lock_released_on_process_death proves lock recovery; test_all_evidence_types_reject_invalid_references covers empty/unknown/cross-document/duplicate refs for claims/entities/questions; test_referential_integrity rejects malformed claims and extra card fields. |
| Grafana cards/logs and metrics | R20, R21, R22, R24, R25 | T11, T12, T13 | test_structured_metadata_and_content_opt_in checks JSON lifecycle fields and low-cardinality Loki labels; test_metric_groups_and_units checks stable metric group and units; test_metadata_only_logs_and_explicit_opt_in checks content privacy and secret exclusion; authenticated Grafana datasource evidence proves 6 panels query data and content opt-in boundary. Final-run delivery is verified in the backend evidence above. |
| Langfuse | R23, R24, R25 | T11, T12, T13 | test_observation_privacy_usage_and_flush asserts metadata-only arguments, token usage, and flush; test_error_observations_are_recorded_without_exception_content asserts sanitized ERROR updates; test_telemetry_outages_and_secret_free_failure suppresses backend secrets; test_independent_backend_outages_preserve_pipeline_outputs verifies valid cards independently during Loki/Pushgateway/Langfuse outages. Real success/error model observations and final-run delivery are recorded above; the corrected A run adds two verified metadata-only generations. |

Final assertion additions complete the mapping:

- R11/T8/T11/T12: test_reduction_retains_all_extracted_entities_without_model_repetition
  verifies all source evidence survives model reduction and official deduplication;
  test_entity_extraction_instruction_is_separate_from_empty_reducer_output verifies
  extraction is requested and empty mentions is restricted to reduction.
- R8/R10/R12/R13/T6/T7: request schema enum tests scope source selections; citation
  tests preserve scientific abbreviations; explicit unresolved rationale tests reject
  invention/answered questions; trusted sentence tests derive evidence in Python.
- R14/T6/T7/T14: sanitized captured packet shapes, byte-decreasing adaptive compression,
  a 20-chunk forced-stall pipeline, noncompacting-model rejection after one call,
  and source-substitution rejection establish bounded progress and safe failure.
- R21/R23/T11/T12/T16: truncated-response regression asserts exactly one usage update
  before error; actual generation-error trace/counters above verify live delivery.

## Historical failures and limits

Earlier runs are failed acceptance/diagnostic history, not waived requirements:
source overstatement/inferred limitations led to exact sentence rendering;
fe46d843fb2a43e19e8a05ec6a769353 exposed invented sentence IDs;
b3ed1846baa141c7aa0efb031cdb18f2 exposed citation/question fidelity issues, with
unrecoverable historical C ValueError not assigned a speculative cause;
d0fcdb5502304eadb0f8487dd6722630 captured redundant hash mismatch;
72ac2f2b54b04bafaf592797cf0a9530 and e4924fd25c52451db133be8611d138ba captured
exact no-progress states. Each drove a failing regression and bounded correction.

One complete source sentence too large for the request budget fails explicitly.
If immutable summary/question support or a noncompacting model prevents progress,
the document fails within finite limits. Scientific source selection remains a
semantic-review concern; exact quotes and references do not guarantee perfect ranking.
No required behavior is waived. Detailed ignored artifacts remain for reviewer access;
no unrelated files or user changes were removed. Next action is independent review.


## Review corrections F1 and F2

F1 reproduced before correction with
`.venv/bin/python -m pytest -q tests/test_generation.py -k single_packet_final_selection`,
exit 1, one failed test. Extraction returned both the introductory exception and
qualified conclusion; the card incorrectly retained both. The regression now
asserts resulting claim omission, exact qualified conclusion, corrected findings,
removal of superseded conditions, unchanged supported entity summary, and all
normalized entity evidence. Five additional cases reject missing or extra
assessments and unknown, self, or earlier resolving references.

Single-segment documents now receive a separate complete-source claim review after
extraction. Its structured schema requires one assessment for each extracted
candidate and constrains resolving references to later source sentences, or null.
Python validates the response, omits superseded candidates, updates affected
findings to the resolving sentence, and clears other superseded summary selections.
Unchanged summary selections and every extracted entity remain intact. Review
requests use the same complete-payload byte budget and finite call counter.
No document-specific phrase or identifier is hardcoded in application logic.
Multisegment document behavior is unchanged.

A generic second selection did not resolve F1 and is not the final implementation.
A first explicit review omitted the contradiction but over-pruned compatible
background. A subsequent response named itself as its resolving sentence and was
correctly rejected by validation. The final schema excludes such references before
inference. These failed attempts are historical diagnostics, not acceptance passes.
Full-suite service doubles were updated for the new review response contract;
original pipeline/failure/outage assertions remain in place.

Final actual invocation, exit 0:

```bash
TRACE_CAPTURE_CONTENT=false APP_ENV=integration-review-delivery \
VOCABULARY_DIR=/tmp/rq-initialize-application-1110a/.artifacts/vocabularies \
.venv/bin/python .artifacts/initialize-application/run_review_delivery.py \
.artifacts/initialize-application/review-fix-input \
--output-dir .artifacts/initialize-application/review-delivery-output
```

Run 6d16245fb71940ed946492b51173d342 used the original complete A.pdf, SHA-256
62d45364215e787a4617c23aa3467ebee1ecd5429d9f79c85d15a663d5a3aa47,
real OCR/chunking and qwen3:14b with unchanged context 16384/output 4096.
One saved chunk produced four claims and three official MeSH entities. The
introductory exception, sentence_2, is identified as superseded by sentence_10
and omitted. General rule with "appears", interpretation with "likely", the
life-cycle condition, and final qualified conformity conclusion remain. Findings,
conditions and entity summary select the supported general-rule sentence, which
names DNA genomes/organisms and replication conditions. Methods and limitations
are null; no unsupported question is generated. MeSH Bacteria, Escherichia coli
and Yeasts have explicit mentions and same-document evidence. All four claims
and all non-null summary values exactly match complete saved source sentences.

Complete serialized requests, including their schemas, are 7702 bytes for
extraction and 5300 for review, both below 11264. Two calls remain below the
single-segment limit of eight. Final source/schema/reference/budget assertions
passed, exit 0; evidence is
.artifacts/initialize-application/review-delivery-source-evidence.json and
review-delivery-diagnostics/call-*.json. The diagnostic CLI wrapper only captures
local evidence and does not change application decisions.

`.venv/bin/python tests/integration/check_live_outputs.py .artifacts/initialize-application/review-delivery-output --environment integration-review-delivery`
passed, exit 0: one card/one chunk, direct Loki card/run completion, Prometheus
successes=1 and two actual qwen3:14b generations with usage and no content.
Final full suite passes 87 tests; Ruff and git diff --check pass, each exit 0.
The additional six tests cover R7/R8/R10/R13/R14/R16, T6/T7/T14/T15/T17.

F2 is corrected by updating current publication authorization, verification counts,
A acceptance evidence, and all stale T15/T16 statements. Historical failures are
identified explicitly. No runtime or test changes followed final live inference;
only progress/evidence updates followed the successful run. Current content digest
above identifies the final reviewed source/test candidate. Independent review is
still required before commit and PR publication.


## Authorized delivery

Renewed independent review approved content
678c5c1a9fc128a887df65c03e304090a02b21b861e8188938dd7b48864ac072.
Leader authorized commit, push and PR creation on 2026-11-11. Required verification
and review are complete. No code changed after approval. Delivery is in progress;
feature finalization will follow leader confirmation of the published PR.
