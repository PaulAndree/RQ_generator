# RQ Generator

Generate extracted chunks and one evidence-linked card for each successfully
processed scientific PDF. The pipeline uses the existing OCR and section-aware
chunking services, then Ollama qwen3:14b. Cross-document ranking is deferred.

## Run the application

Use Python 3.12 or later. Install the locked environment with tracing support:

```bash
uv sync --extra dev --extra telemetry
cp .env.example .env
# Edit .env with your service endpoints and local credentials.
uv run rq-generator /path/to/pdfs --output-dir output
```

The directory is the only required data input. Discovery processes direct-child
regular PDF files in Unicode filename order, ignoring extension case and excluding
symlinks and subdirectories. `python -m rq_generator` is also supported.
The default output directory is `./output`.

The application reads `.env` in the working directory. Process environment
variables override this file; optional CLI flags override both. Use `--env-file`
for another configuration file, and `--help` for supported service/model flags.
An empty directory succeeds without contacting processing services or downloading
vocabularies. Exit codes are 0 for all successes, 1 for isolated PDF failures,
and 2 for input, configuration, or persistence failure.

The configured Ollama model must already be installed. Context/output budgets
default to 32768/8192 tokens; set OLLAMA_CONTEXT_TOKENS/OLLAMA_OUTPUT_TOKENS for
the installed model. Each complete serialized request uses a conservative UTF-8
byte budget after output reserve and a 1024-token margin. Oversized chunks are
segmented at sentence boundaries, and intermediate results use bounded consolidation.
If a single complete source sentence cannot fit, that document fails rather than
using a clipped statement that could lose a scientific qualifier. A document fails
visibly if consolidation cannot make progress within its finite call budget.
Processing requests default to a 600-second read timeout, 10-second connection
timeout, and two retries with one/two-second backoff for connection errors,
timeouts, HTTP 429, and HTTP 5xx. Other HTTP 4xx and malformed success responses
are not retried. Set SERVICE_TIMEOUT_SECONDS and SERVICE_RETRIES to override.

## Outputs and checkpoints

`chunks.json` stores `documents` and ordered `chunks`. Document records contain
doc_id, relative source_path, and PDF sha256. Chunks contain doc_id, chunk_id,
ordinal, text, section, page_start/page_end, and source_metadata. Unavailable
page/section metadata is null.

`document_cards.json` has a single `cards` array. Each card contains doc_id,
main_claims with claim_id/text/chunk_id references, summary, normalized entities,
and zero to five candidate_research_questions with question/rationale/chunk_id.
Evidence fields named chunk_id are arrays. Summary fields are findings, methods,
conditions, limitations, and entities, each concise prose or null. Structured
entities are also retained top-level with group, normalized_name, and evidence.
The model selects source sentence IDs for claims and summary fields. Python
renders those complete sentences exactly, preserving qualifiers and conditions.
Unsupported summary fields remain null. Research questions require a source
sentence that explicitly identifies an unresolved issue. Their rationales quote
that sentence exactly; documents without such a statement may have zero questions.
This prevents paraphrase from adding certainty. Source selection and question
quality still require semantic review.
JSON schemas and same-document evidence references are validated before saving.

SHA-256 IDs use relative filename and file bytes for documents, and document ID,
ordinal, text, section/page metadata for chunks. Identical inputs and service
results retain IDs across relocated input roots. Renames or changed OCR results
change IDs. Python assigns claim IDs from document/text/sorted evidence; model
generation changes can change claim IDs.

Each invocation starts a fresh run. Existing card/chunk outputs in the selected
output directory are replaced. There is no automatic resume. An OS advisory
lock rejects concurrent writers and releases automatically after process death.
The lock file may remain and must not be deleted while another writer is active.
Individual PDF failures are logged and processing continues. Valid extracted
chunks may remain for a failed generation, but a failed PDF has no partial card.

After every attempt, the application atomically replaces cumulative chunks,
then cards, then `run_state.json`. On a fresh run, old cards are cleared before
old chunks. An interrupted write may leave extra unused chunks, but published
cards retain all their evidence. run_state.json can lag the last output pair
after a crash. A persistence failure stops the run. Unrelated files are preserved.

## Biomedical reference resources

Official resources download automatically into
`~/.cache/rq-generator/vocabularies` on the first nonempty run. Set VOCABULARY_DIR
or `--vocabulary-dir` to a writable application cache or a prepared offline mirror.
The directory holds go.obo, cl.obo, mesh.xml, and hgnc.tsv. Existing snapshots
are reused; remove or replace them deliberately when updating reference releases.
The loader writes provenance.json with source URLs and exact SHA-256 snapshot
identifiers. Each run logs those identifiers without document text.

- [GO](https://www.geneontology.org/docs/download-ontology/) uses go-basic OBO,
  restricted to nonobsolete biological_process terms and exact synonyms.
  [GO data license](https://www.geneontology.org/docs/go-citation-policy/) is CC BY 4.0.
- [Cell Ontology](https://obofoundry.org/ontology/cl.html) uses CL OBO cell types
  and exact synonyms, with its CC BY 4.0 attribution.
- [NLM MeSH 2026](https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/)
  uses descriptor XML and entry terms. NLM is the source of MeSH data;
  this application does not imply NLM endorsement. The snapshot is explicitly
  versioned 2026 under [NLM terms](https://www.nlm.nih.gov/databases/download/terms_and_conditions_mesh.html).
- [HGNC](https://www.genenames.org/download/) uses its complete approved TSV
  set, official symbols, and unambiguous aliases under
  [CC0](https://www.genenames.org/about/license/).

The cache is roughly 400 MB before Python indexes. Downloads need network access;
offline runs require all four cached resources. Reference failures are reported.
Model-suggested names alone are never accepted as official normalization.

## Shared monitoring

JSON logs go to stderr and shared Loki. Batch snapshots go to Pushgateway;
the existing Prometheus must scrape that gateway. Langfuse records the logical
run and every model attempt, usage when available, timings, and error categories.
Install the telemetry extra and set LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY, and
LANGFUSE_SECRET_KEY. LANGFUSE_HOST remains a supported fallback. Tracing flushes
before exit. Missing/failed telemetry is reported locally and does not stop
document processing. Local inference cost is omitted when unavailable.

TRACE_CAPTURE_CONTENT defaults to false. Metadata includes IDs, counts, status,
timings, and model information. Explicitly setting it true permits prompts,
responses, and separate full-card log events to enter telemetry. Credentials
never belong in Git or logs. Keep `.env` ignored.

The shared Grafana deployment currently publishes port 3005. Project documents
list 3013, so confirm actual mappings and set GRAFANA_URL rather than changing
shared infrastructure. Set a scoped GRAFANA_TOKEN, then install the dashboard:

```bash
uv run python scripts/install_dashboard.py
```

The dashboard definition is `monitoring/grafana/document-cards.json`. Select the
existing Loki and Prometheus sources and APP_ENV value. Panels show card IDs,
counts/status, logs, batch duration and model metrics. The full-content panel
has data only for explicitly opted-in runs. Files remain the source of truth.
Stable Pushgateway groups use job=rq-generator and environment=APP_ENV; each run
replaces its snapshot. Remove obsolete environment groups through the shared
gateway's documented DELETE /metrics/job/rq-generator/environment/ENV route
when that environment is retired. Do not label metrics with document/run IDs.

## Verify the application

```bash
uv run python -m pytest -q
uv run ruff check src tests scripts
uv run rq-generator --help
```

Unit tests use isolated fixtures. Live verification requires real scientific
PDFs, OCR/chunking, the configured qwen3:14b model, official resources, and the
shared monitoring/trace services. Exercise success, a failed middle document,
and a document requiring several generation batches. Inspect saved references
and compare claims, summary, entities, and questions against source evidence.
Query Loki/Prometheus, inspect Grafana panels and Langfuse observations. A
configuration file or mocked test does not prove telemetry delivery.

## Workflow

For SDD features:

pending → specification → spec_ready → human approval →
in_progress → implementation → review → authorized delivery → done

The main conversation coordinates the work through four roles:

- leader: selects or resumes a feature and coordinates handoffs.
- spec_author: writes requirements, design, and tasks.
- implementer: implements and verifies approved work.
- reviewer: independently checks the implementation and evidence.

These roles follow repository instructions. Workflow rules are not enforced
by a standalone orchestration program.

## Before starting

1. Read AGENTS.md.
2. Define a real feature in feature_list.json with a unique ID and name,
   acceptance criteria, pending status, and "sdd": true.
3. Remove or complete invalid placeholder entries.
4. Ensure required workflow files are available in the task's Git base.
   A new worktree does not inherit another checkout's uncommitted files.
5. Configure the repository remote and task isolation required by /new-feature.

Do not enter credentials in specifications or progress reports.

## Start an SDD feature

Ask the agent:

"Prepare the specification for feature <id>. Stop for my approval before
implementation."

The leader assigns a task worktree and delegates specification drafting.

Review these files:

- specs/<name>/requirements.md
- specs/<name>/design.md
- specs/<name>/tasks.md

Approve the specific feature and specification, or request revisions.
Implementation begins only after approval is recorded.

Specify whether delivery should remain local or include a pull request.
Pull requests are not merged without an explicit instruction.

## Resume work

Ask the agent to resume the feature recorded in progress/current.md.

The progress record identifies the worktree, branch, execution phase,
approval evidence, reports, blockers, and next action.

Preserve this record when work is interrupted or awaiting approval.
After completion, append a summary to progress/history.md and reset the
active template.

## Project documents

| Document | Purpose |
|---|---|
| AGENTS.md | Repository workflow and role boundaries |
| Instructions.md | Application brief |
| docs/architecture.md | Application requirements and open decisions |
| docs/specs.md | Specification format and approval rules |
| docs/conventions.md | Python, service, and observability conventions |
| docs/verification.md | Required checks and delivery verification |
| .codex/config.toml | Main conversation instructions and agent settings |
| .codex/agents/ | Agent configurations and protocols |

The project targets Python 3.12 or later.
Follow docs/verification.md for test setup requirements and commands.
