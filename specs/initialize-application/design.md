# Design

Feature 1, initialize-application. Revision 1, awaiting human approval.

## Baseline and user decisions

Baseline commit is 6b9de636dfb838a9d1543dcbf8baa20c2761428b.
pyproject.toml already declares Python >=3.12, httpx, Pydantic, optional
Langfuse, pytest, and the rq-generator entry point. There are no src/ or
tests/ directories and no existing application clients to reuse.
Reuse those package settings and the running services rather than importing
unavailable code from historical worktrees.

The user resolved both product questions during drafting:

- Summary includes findings, methods, conditions, limitations, and entities.
  Summary.entities is concise prose or null. Normalized structured entities
  remain top-level.
- Grafana shows card IDs, counts, and processing status by default, with
  optional full text. Document content must not enter telemetry by default.

All operational choices below are proposed for approval with this revision.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| src/rq_generator/__init__.py | Export main for existing console entry point |
| src/rq_generator/__main__.py | Support python -m rq_generator |
| src/rq_generator/cli.py | Arguments, configuration, exit reporting |
| src/rq_generator/config.py | Validated environment/flag settings |
| src/rq_generator/models.py | Strict chunk/card schemas and cross-reference validation |
| src/rq_generator/services.py | HTTP adapters for OCR, chunking, and Ollama |
| src/rq_generator/entities.py | Official vocabulary loading, lookup, and alias validation |
| src/rq_generator/generation.py | Extraction prompts, bounded requests, consolidation |
| src/rq_generator/pipeline.py | Ordered document processing and failure isolation |
| src/rq_generator/storage.py | IDs, validated checkpoint writes |
| src/rq_generator/telemetry.py | Structured logging, metrics, optional Langfuse |
| tests/test_*.py | Requirement-focused tests and contract fixtures |
| tests/integration/ | Explicitly selected live checks, separate from unit tests |
| monitoring/grafana/document-cards.json | Shared dashboard definition |
| .env.example | Non-secret service/model/telemetry settings |
| README.md | Installation, usage, outputs, monitoring, verification |
| pyproject.toml and generated lockfile | Any needed dependencies and reproducible environment |

Keep implementations small. A module may combine closely related helpers;
do not add an orchestration framework or a database.

## Entry point and configuration

Normal usage is rq-generator PDF_DIRECTORY, with optional --output-dir
defaulting to ./output relative to the working directory. The directory is
the only positional data input. Direct-child .pdf matching ignores extension
case; sort by the original filename's Unicode code-point order. Do not
recurse or follow file symlinks. Process files sequentially.

Optional flags override environment settings, which override documented
defaults. Preserve OLLAMA_BASE_URL, OLLAMA_MODEL, OCR_BASE_URL, CHUNKING_URL,
and EMBEDDING_MODEL. The embedding endpoint is not used in this stage and
must not be renamed or contacted unnecessarily. Defaults for processing
services are those in docs/conventions.md; OLLAMA_MODEL is qwen3:14b.

Expose bounded HTTP timeout, retry, context, and output-budget settings.
Proposed defaults are 10-second connection timeout, 600-second OCR/chunking
and model read timeout, and two retries after the first attempt for
connection failures, timeouts, HTTP 429, and HTTP 5xx, with delays of one
and two seconds. Do not retry other HTTP 4xx or malformed successful
responses. Each retry is traced. Retries for these processing requests can
repeat compute but must never duplicate a committed card.

Use Ollama context size 32768 and maximum output 8192 tokens by default,
subject to the actual installed model supporting those settings. Verify
model availability and context metadata before live checks. Require enough
space for the complete serialized prompt, output reserve, and safety margin.
Use a conservative UTF-8 byte budget for prompt text, limited to the
remaining input allowance, rather than a characters-per-token estimate.
Never silently increase context size or change the model to make a check pass.

Use exit status 0 when every discovered PDF succeeds, including an empty
folder, 1 when at least one PDF fails, and 2 for invalid invocation or global
configuration/output errors. An output write failure is fatal because
continuing would falsely imply persisted progress.

## Verified local service discovery

On 2026-11-10, read-only GET requests to the live OpenAPI documents established:

| Contract source | Processing route and request |
| --- | --- |
| http://127.0.0.1:8084/openapi.json | POST /services/ocr, multipart file and required type_name, optional doc_id |
| http://127.0.0.1:8085/openapi.json | POST /services/chunking/doc_by_titles, form content_parsed, optional doc_id, max_split_tokens default 800 |

Both GET requests succeeded. Their HTTP 200 processing responses have no
declared schema. The meaning/value of OCR type_name and successful response
shapes therefore remain integration discovery work, not verified facts.
Before implementing adapters, inspect the running services' documentation
or source and exercise a small representative PDF through their normal
processing routes. Record the non-secret contract and sanitized fixtures.
If those services are unavailable, report the integration blocker; do not
invent a response shape or substitute a local PDF parser.

The chunking adapter must preserve section and page metadata returned by
the service, normalize missing values to null, and retain service-specific
source metadata in a JSON object. Use the section-aware route, not the
generic short-text route. Reject empty/unusable extracted text as a
document failure. Empty but valid claim/entity/question arrays are allowed.

## Data formats and identifiers

Use strict Pydantic models for external generation output and persisted
schemas. Reject extra fields in cards and malformed references. Python
assigns IDs after validating model text and evidence; never trust model IDs.

chunks.json has this root structure:

```json
{
  "documents": [
    {"doc_id": "doc_...", "source_path": "paper.pdf", "sha256": "..."}
  ],
  "chunks": [
    {
      "doc_id": "doc_...",
      "chunk_id": "chunk_...",
      "ordinal": 0,
      "text": "Source text",
      "section": null,
      "page_start": null,
      "page_end": null,
      "source_metadata": {}
    }
  ]
}
```

Use full SHA-256 hex digests with type prefixes. Document ID input is a
canonical serialization of relative POSIX path and PDF SHA-256. Chunk ID
input is document ID, ordinal, exact normalized service text, and preserved
section/page metadata. Specify canonical JSON encoding with sorted keys and
UTF-8 bytes. Do not include absolute roots or timestamps. The guarantee is
determinism for identical file paths/content and identical service output,
not persistence after renames or OCR/model-version changes.

document_cards.json has only a cards array at the root. Each card contains:

- doc_id.
- main_claims, each with claim_id, text, and chunk_id as an array of IDs.
- summary, with findings, methods, conditions, limitations, entities.
  Each value is a nonblank string or null.
- entities, each with group, normalized_name, and chunk_id as an array.
  Group values are GO, MeSH, Cell Ontology, and HGNC.
- candidate_research_questions, zero to five objects with question,
  rationale, and chunk_id as an array.

Claim IDs hash document ID, trimmed claim text, and sorted unique evidence
IDs. Deduplicate exact equal claims/evidence deterministically. IDs are
stable for identical retained claims, not guaranteed across stochastic
generation changes. Validate uniqueness and require every cited chunk to
exist and belong to the card's document. Duplicate entity/group/name pairs
merge evidence. Never repair an invented reference by guessing a chunk.

## Generation and biomedical normalization

Each extraction request names the supplied chunk IDs and asks for zero or
more central claims, candidate biomedical mentions, summary evidence, and
possible unresolved questions. Include instructions about uncertainty,
conditions, unsupported fields, and already-answered questions in both
extraction and consolidation prompts. Request constrained JSON using the
verified Ollama structured-output interface.

Split oversized chunk text into bounded inference segments while retaining
the saved parent chunk ID for evidence. Avoid dropping text. Budget the
complete prompt, including schema and formatting overhead. Validate every
response before passing it into a bounded reduction tree. Reduction groups
must fit the same limit; a reduction must reduce size or finish, with a
finite call budget proportional to input segments. If reduction cannot
make progress, fail that document visibly instead of truncating evidence
or making an unbounded request. Never ask a final call to consume the
entire original document when it exceeds the budget.

Normalize model-suggested biomedical mentions through official vocabulary
reference indexes. Use GO biological-process terms, Cell Ontology terms,
MeSH descriptors, and HGNC approved symbols with unambiguous aliases.
Load versioned official releases into an application cache, downloading
documented official release artifacts when the cache is absent. Permit
configured local mirrors/cache paths for offline use, and record release
identifiers/checksums. Vocabulary data are application resources rather
than additional required data supplied for each folder run. Match mentions
case-aware where the vocabulary requires it. A model's assertion alone
does not establish an official term match. Skip ambiguous/unsupported
matches; reference-data load failures must be reported rather than silently
accepting model guesses. The implementation must document actual release
sources and license/format details discovered before adding the loader.

Manual source comparison on representative PDFs remains necessary for
scientific fidelity. Structural validation cannot establish that a claim is
scientifically supported or a question remains unanswered.

## Checkpoints and failures

A run starts fresh, without implicit resume from a prior run. Use a single
writer for each output directory and reject a concurrent writer using an
OS-managed advisory file lock on .rq-generator.lock. The initial target is
the Linux/POSIX server environment. The OS releases the lock on a crash;
the persistent lock file's existence alone does not mean another writer is
active. Do not unlink the lock file while another process could hold its
inode. Record the policy in usage documentation and test process-death
recovery without manual file removal.

For an existing output directory, publish empty cards before clearing old
chunks so no old card points to removed evidence. Write JSON to a temporary
file in the same directory, flush, and atomically replace each destination.
After each attempted PDF, save the cumulative chunks first and cumulative
cards second. Append-only chunks within a run mean a failure between those
replacements leaves old cards with all their evidence still present.
Orphan chunks are permitted; dangling card evidence is not. Keep failed
PDFs' valid extracted chunks when generation fails, but never a partial card.

Write run_state.json after the pair with run ID, attempted relative source
paths, success/failure statuses, document IDs where known, and error
categories without document content or credentials. It is an internal
progress record, not a replacement card output. A crash may leave this
record behind the valid output pair; on the next run, start fresh and log
that policy. Automatic restart/resume is outside this initial stage.

If persistence fails, abort and preserve the last committed cards with all
their referenced chunks; additional orphan chunks are permitted. Do not delete
unrelated existing files. Clear only task-created temporary write files and
release the advisory lock on orderly exit. Tests must cover failures before and after
each replacement and ensure malformed JSON is never observable.

## Monitoring and privacy

Use Python logging with a JSON formatter. Include timestamp, severity,
service=rq-generator, environment, run_id, document ID when known, operation,
duration, status, and trace ID when available. Exclude secrets and document
text by default. Ship structured events through a bounded-time Loki client
or an existing verified collector. Loki labels are service and environment;
document and run IDs are fields.

Publish batch counts/duration and available LLM aggregate usage/latency to
the shared Pushgateway. Use stable service/environment grouping, replace
the prior batch snapshot, and document stale-series cleanup. Do not use
document/run IDs as Prometheus labels. Verify that the shared Prometheus
actually scrapes the selected gateway before claiming metric delivery.

Dashboard panels include a Loki-backed card table with doc_id, processing
status, and counts of claims/entities/questions, processing failures, batch
duration/throughput, available aggregate model metrics, and logs. Emit one
card-completed metadata event per saved card and a document-failed event
per failed PDF. The optional full-text panel reads a separate content event
emitted only when explicit content capture is enabled; keep default queries
and logs metadata-only. The file output remains the source of truth.

Create a logical Langfuse trace for a folder run and model observations for
all extraction/consolidation attempts. Include operation, model, timing,
usage when returned, and error category. Do not fabricate cost for local
inference. Read LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY
from configuration; preserve a supported legacy LANGFUSE_HOST if present
after checking the installed SDK. Default content capture to false. Flush
on successful exit and errors. Missing/disabled telemetry must be reported
locally; it does not waive required live telemetry checks for completion.

All telemetry operations have bounded timeouts and isolated errors. Optional
Langfuse dependencies must not prevent local document processing when
tracing is disabled. Never deploy another monitoring stack or alter shared
infrastructure to bypass missing access.

Use configurable GRAFANA_URL, LOKI_URL, PUSHGATEWAY_URL, PROMETHEUS_URL,
environment, and explicit capture settings. Project endpoint defaults take
precedence over generic skill examples. Confirm actual targets before live
dashboard creation or telemetry checks. Credentials never enter Git.

## Alternatives

- Local PDF extraction would reduce service dependencies, but violates the
  requirement to reuse existing OCR and section-aware chunking.
- One model request per whole document is simpler, but cannot handle long
  documents within the context limit.
- A database with transactionally joined cards/chunks would offer atomic
  snapshots, but adds unnecessary storage infrastructure for two JSON outputs.
  Ordered atomic file replacement maintains the required reference invariant.
- Logging complete cards by default would simplify Grafana text panels,
  but conflicts with the selected metadata defaults and telemetry privacy.
- Treating model-produced entity names as official normalization avoids
  reference resources but does not establish authoritative vocabulary matches.

## Verification and completion limits

Unit tests use HTTP and telemetry test doubles with sanitized fixtures.
Run meaningful failing tests before implementation. Entry-point tests must
exercise sequential processing and inspect saved files, not just helper calls.
Run the full pytest suite and configured lint checks on Python 3.12, recording
commands, exit codes, collection/pass counts, and requirement mappings.

Live checks require a representative scientific PDF, working OCR/chunking,
the actual qwen3:14b model, vocabulary references, shared Loki/Pushgateway/
Prometheus/Grafana, and configured Langfuse credentials. Verify one success
and one controlled processing failure. Inspect saved evidence and source
fidelity, logs in Loki, metrics in Prometheus, dashboard data in Grafana,
and model traces in Langfuse. Include a multi-batch document. Record any
unavailable service as unverified behavior and a blocker to full completion.
Do not substitute mocks for these live acceptance checks.

Opening a PR or publishing the branch is outside current authorization.
Implementation and review require their assigned agents after specification
approval. Final workflow bookkeeping follows independent review and any
subsequently authorized delivery.
