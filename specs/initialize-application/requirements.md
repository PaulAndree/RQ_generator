# Requirements

Feature 1, initialize-application. Revision 1, awaiting human approval.
Implementation must not begin before approval is recorded.

## Scope and decisions

Build the folder-to-document-cards stage described in Instructions.md and
docs/architecture.md. Cross-document discovery and ranking are deferred.
There is no application source or test suite in the baseline checkout.

The user requested entities in the summary as well. Summary fields are
findings, methods, conditions, limitations, and entities. Each is concise
evidence-grounded prose or null. Structured normalized entities remain a
separate top-level card field.

The user selected card IDs, counts, and processing status in Grafana, with
optional full text. Content capture remains disabled by default.

The remaining operational choices below are proposals for specification
approval, not records of prior approval.

## R1: Folder input

WHEN invoked with a readable directory, the system SHALL discover its
direct-child regular files, excluding symlinks, with a case-insensitive .pdf
suffix and process
them sequentially in Unicode filename order.

Verification: test_discovery_filters_and_orders and an entry-point test that
records the order of OCR requests, including mixed-case extensions and an
ignored subdirectory. Recursion is excluded by this proposed scope.

## R2: Input validation

IF the input is missing, unreadable, or not a directory, THEN the system
SHALL exit nonzero with a clear error before invoking processing services.

Verification: test_cli_rejects_invalid_input asserts exit status, error,
and absence of service requests.

## R3: Existing processing services

WHEN processing a PDF, the system SHALL use the configured existing OCR
service followed by the section-aware chunking service.

Verification: adapter tests assert multipart and form contracts against
verified response fixtures; live integration checks verify both services
with a representative scientific PDF. No local parser replaces them.

## R4: Stable document identifiers

The system SHALL derive document IDs deterministically from the PDF bytes
and its path relative to the input directory.

Verification: test_document_id_stability checks identical input across
reruns and relocated input roots, changed bytes, and distinct relative paths.
Renaming a PDF changes its ID; identical bytes under different filenames
represent separate input documents.

## R5: Stable chunk identifiers

The system SHALL derive chunk IDs deterministically from the document ID,
chunk ordinal, text, and available section/page metadata.

Verification: test_chunk_id_stability checks repeated identical service
outputs, repeated text at different ordinals, and changed content/metadata.
Stability requires identical OCR and chunking results and settings.

## R6: Saved chunks

WHEN chunk extraction succeeds, the system SHALL save the document record
and ordered chunks with their source metadata in chunks.json.

Verification: test_chunks_schema_and_source_metadata and a CLI test inspect
doc_id, relative source path, content hash, chunk_id, ordinal, text, section,
and page metadata. Missing source metadata is null, never fabricated.

## R7: Claim extraction

WHEN processing extracted chunks, the system SHALL use configured Ollama
Qwen3:14b inference to return zero or more supported central claims for
each chunk.

Verification: test_generation_uses_configured_model_and_all_chunks asserts
the configured model and coverage, including zero-claim chunks; a live
Qwen3:14b check inspects supported and unsupported claim examples.

## R8: Claim identifiers and evidence

The system SHALL assign each retained claim a Python-generated unique
claim_id, nonempty text, and a nonempty chunk_id array of supporting chunks
belonging to the same document.

Verification: test_claim_ids_and_evidence rejects model-assigned IDs,
blank claims, missing references, unknown chunks, and cross-document evidence.

## R9: One card per successful document

WHEN a PDF completes successfully, the system SHALL contribute exactly one
card with doc_id, main_claims, summary, entities, and candidate_research_questions.

Verification: test_one_card_per_successful_pdf includes a failed middle PDF,
and rejects duplicate card IDs and partial cards.

## R10: Summary

The system SHALL produce summary fields findings, methods, conditions,
limitations, and entities as concise source-supported prose or null when
unsupported.

Verification: test_summary_schema accepts exactly the five keys and
string-or-null values; a representative live review compares each field
with source chunks, including a document with unsupported fields.

## R11: Biomedical entities

The system SHALL retain only explicitly mentioned biomedical entities that
can be unambiguously normalized against official GO biological-process,
MeSH, Cell Ontology, or HGNC terms.

Verification: test_entity_normalization covers official names, unambiguous
HGNC aliases, ambiguous aliases, unsupported mentions, non-biological-process
GO terms, and one mention matching multiple vocabularies. Integration
evidence records the official reference release used and verifies a sample.

Each retained entity has group, normalized_name, and a nonempty chunk_id
array. Separate objects represent separate vocabulary groups. Reference
data are configuration resources, not an additional required user data input.

## R12: Research questions

The system SHALL produce zero to five candidate research questions per card,
each with nonempty question, rationale, and a nonempty chunk_id array
referencing the same document.

Verification: test_question_limits_and_evidence covers bounds and invalid
references. Representative live review verifies that questions are specific,
investigable, motivated by evidence, and not already answered by the document.

## R13: Scientific fidelity

The system SHALL preserve uncertainty and study conditions without inventing
findings, biomedical mentions, or supporting evidence.

Verification: prompt contract tests assert these instructions at extraction
and consolidation stages; live source comparison records claim, summary,
entity, and question examples. Structural validation alone cannot establish
scientific fidelity, so this manual integration review is required.

## R14: Bounded generation

WHEN a document exceeds the configured inference input budget, the system
SHALL process bounded batches and consolidate bounded intermediate results
while retaining valid supporting chunk references.

Verification: test_generation_bounds_every_request covers oversized chunks,
many chunks, oversized intermediate responses, and multi-level reduction.
It checks every request, not only the first extraction stage. A live check
uses a document large enough to require multiple batches.

## R15: Consolidated card output

The system SHALL save all completed cards in document_cards.json with the
root object {"cards": [...]} in input processing order.

Verification: test_output_root_and_order inspects persisted JSON after
multiple PDFs, an empty folder, and a failure between successful documents.

## R16: Referential validation

Before publishing cards, the system SHALL validate schema, ID uniqueness,
document membership, and all claim/question/entity evidence references
against persisted chunks.

Verification: test_referential_integrity independently mutates each type of
reference and uniqueness constraint, and asserts that invalid cards are
rejected before publication.

## R17: Per-document failure isolation

IF OCR, chunking, generation, or document validation fails for one PDF, THEN
the system SHALL log the failure, omit its card, and continue to later PDFs.

Verification: test_pipeline_continues_after_document_failure injects each
failure class into the middle PDF and checks final cards and failure logs.

## R18: Checkpoint persistence

After each attempted PDF, the system SHALL persist completed work without
publishing a card whose evidence chunks are absent from chunks.json.

Verification: test_checkpoint_after_each_pdf and fault-injection tests
interrupt between output replacements, verify readable JSON and valid saved
card references, and check that the last committed cards retain all their
evidence, allowing additional orphan chunks after an interrupted write.
Exact restart and file replacement semantics are defined in design.md.

## R19: Configuration and executable usage

The system SHALL accept the PDF directory as its only required data input,
provide a default output directory and optional output-directory override,
and read service URLs/model configuration from environment variables or
optional command-line flags.

Verification: test_cli_configuration_precedence and an installed
rq-generator smoke check cover defaults, environment, flags, help, and the
documented usage. Preserve existing setting names from docs/conventions.md.

## R20: Structured logs

The system SHALL emit structured lifecycle and failure logs with timestamp,
severity, service, environment, run ID, applicable document ID, and trace ID
when available, and deliver them to the configured shared Loki backend.

Verification: log schema/redaction tests plus successful and controlled
failing live runs queried in Loki. Secrets and document text are excluded
by default. Unique IDs remain log fields rather than Loki labels.

## R21: Batch metrics

The system SHALL publish executions, document successes/failures, job duration,
and available model latency/token measurements to the shared monitoring stack.

Verification: metric unit tests check units and low-cardinality labels;
live Pushgateway and Prometheus queries establish delivery. Stable grouping
keys prevent a new persistent series for every run.

## R22: Grafana cards and logs

The system SHALL provide a version-controlled dashboard in the shared Grafana
instance that displays card IDs, claim/entity/question counts, processing
status, and application logs filtered by service and environment, with an
optional full-card-text view when content capture is explicitly enabled.

Verification: dashboard structure/query checks and a live successful/failing
run inspected in Grafana. Verify that full text is absent by default and
visible only after explicit content-capture opt-in.

## R23: Langfuse tracing

The system SHALL capture logical run traces and Ollama generation observations
in configured Langfuse, including model, latency, errors, and usage/cost when
available, and flush pending telemetry before exit.

Verification: tracing test doubles assert model observations, error recording,
and flush; real Qwen3:14b success/failure traces are inspected in Langfuse.
Unavailable token/cost fields are omitted rather than fabricated.

## R24: Telemetry privacy

Unless content capture is explicitly enabled, the system SHALL exclude
prompts, responses, and document text from telemetry.

Verification: test_telemetry_metadata_only_defaults inspects complete emitted
logs and tracing arguments; opt-in tests verify content capture boundaries
and credential redaction.

## R25: Telemetry failure isolation

IF a telemetry backend is unavailable, THEN the system SHALL preserve PDF
processing and output persistence and report the telemetry failure locally.

Verification: test_telemetry_outages_do_not_break_pipeline injects independent
Loki, Pushgateway, and Langfuse failures and asserts valid final cards.

## Acceptance mapping

| Acceptance criterion from feature_list.json | Requirements |
| --- | --- |
| "Discover all PDFs in the supplied directory and process them in order." | R1, R2, R3, R4, R5, R6, R17, R18, R19 |
| "Use an llm service, Ollama Qwen3:14b model to extract the central claims for each chunk if exists and generate one compact card per document." | R7, R8, R9, R10, R11, R12, R13, R14, R16 |
| "Generate a single JSON file containing all the cards." | R9, R15, R16, R18, R19 |
| "Grafana dashboard to visualize the cards and logs." | R20, R21, R22, R24, R25 |
| "langfuse integration to capture traces and logs from ollama qwen3:14b" | R23, R24, R25 |

The single card file does not remove the separate chunks.json required by
Instructions.md and docs/architecture.md.
