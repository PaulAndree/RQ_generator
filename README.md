# RQ generator

Turn a folder of scientific PDFs into document cards with evidence references.
This stage processes documents independently. Cross-document discovery and
ranking are outside its scope.

## Install and run

Requires Python 3.12+ and access to the existing OCR, section-aware chunking,
and Ollama services. The Ollama server must have `qwen3:14b` installed.

```bash
uv sync --extra dev
uv run rq-generator /path/to/pdfs
uv run rq-generator /path/to/pdfs --output /path/to/results
```

Alternatively, install with `python3 -m pip install .` and run
`rq-generator /path/to/pdfs`. `python3 -m rq_generator /path/to/pdfs` also works
in the installed environment. Run `rq-generator --help` for optional flags.

The PDF folder is the only required input. Files with a `.pdf` suffix,
regardless of case, are processed in filename order directly inside that
folder. Subdirectories are not scanned. Identical PDF bytes produce one
card, with duplicate paths recorded in progress.

## Configuration

URLs, model name, context and output limits, and HTTP timeout have environment
variable defaults in [.env.example](.env.example). Flags override those values.
The program does not load `.env` files itself. To export the example in Bash:

```bash
cp .env.example .env
# Edit .env for your existing services and optional telemetry credentials.
set -a
source .env
set +a
uv run rq-generator /path/to/pdfs
```

The defaults use OCR on port 8084, section chunking on 8085, and Ollama on
11436. The clients use the deployed `/services/ocr`,
`/services/chunking/doc_by_titles`, and `/api/chat` contracts. PDFs are uploaded
to OCR; extracted Markdown is passed to the title-aware chunking service.
No local parser or alternate inference provider replaces these services.

## Outputs

The default destination is `output/`. Each run rebuilds these files for its
input folder. Use a separate `--output` directory to retain an earlier run.

- `chunks.json` has root `{"chunks": [...]}`. Each chunk stores `doc_id`,
  `chunk_id`, extracted `text`, absolute `source_path`, `section`, zero-based
  `index`, service `token_count`, and `language`. Page numbers are omitted
  because the deployed service does not supply them.
- `document_cards.json` has root `{"cards": [...]}`. Each card has the shape
  below. `chunk_id` is always an array, including when there is one source.
- `progress.json` records each PDF path, document ID, status, and error class
  for failures. Full document text and service exception bodies are excluded
  from logs.

```json
{
  "cards": [
    {
      "doc_id": "doc_<sha256-of-pdf-bytes>",
      "main_claims": [
        {
          "claim_id": "claim_<python-assigned-hash>",
          "claim": "The reported effect may hold under the tested conditions.",
          "chunk_id": ["chunk_<hash>"]
        }
      ],
      "summary": {
        "findings": "Reported findings with scientific uncertainty preserved.",
        "methods": "Methods supported by the source.",
        "conditions": "Conditions supported by the source.",
        "limitations": null
      },
      "candidate_research_questions": [
        {
          "question": "Does the reported effect persist under field conditions?",
          "rationale": "The source reports only controlled laboratory conditions.",
          "chunk_id": ["chunk_<hash>"]
        }
      ]
    }
  ]
}
```

Document IDs hash PDF bytes, so renaming a file does not change its ID.
Chunk IDs hash the document ID, chunk index, section, and text. Chunk IDs
remain stable when extraction and chunking results remain the same. Claim
IDs are assigned in Python from the document, claim position, text, and sorted
evidence IDs. Changed model wording can change a claim ID.

The model extracts partial cards from bounded chunk batches, then consolidates
them in bounded rounds. Intermediate cards retain source chunk IDs even when
those chunks contain no central claims. An oversized chunk is split internally without changing
its saved evidence ID. UTF-8 byte counts conservatively bound Qwen input tokens;
the budget also includes the JSON schema and reserves space for chat overhead
and output tokens. Set `--context-tokens` within the server/model's supported
context window. Truncated responses, oversized intermediate cards, and
consolidation that cannot shrink within the budget fail that PDF explicitly.
Increasing the context or output limit may help those documents.

All outputs pass strict structure and reference checks. Claims and questions
must reference chunks from the same document, and each card has at most five
questions. These checks cannot prove that model prose is scientifically true
or that every question is unanswered. Review cards against their cited chunks
before using them for research decisions.

Progress is saved after each PDF, including failed PDFs. Successfully extracted
chunks survive a card-generation failure. Each file is replaced atomically;
the three files are not a single filesystem transaction. A rerun starts fresh
and does not resume from saved progress. Concurrent runs sharing an output
directory are refused. After a killed process, remove `.rq-generator.lock`
only after checking that no process is still using that output directory.
Storage failures stop the run. Other document failures are logged and the next
PDF continues. Exit codes are `0` for success, including an empty folder, `1`
for document failures, and `2` for invalid configuration or storage errors.

## Telemetry

Logs are JSON on stderr with service, environment, severity, document ID when
available, and model latency and token counts. Set `LOKI_URL` for best-effort
delivery to the existing shared Loki. Set `PUSHGATEWAY_URL` to publish completed
and failed document counts plus cumulative processing duration. Metrics use
stable job/environment groups and represent the latest run, not all-time totals.
Shared Prometheus must already scrape the Pushgateway. Remove stale groups
through the shared Pushgateway when retiring an environment.

Install `uv sync --extra dev --extra telemetry` and set the Langfuse endpoint
and keys to trace each document, OCR/chunking steps, and model calls. Traces
record model, latency, usage, and errors. Content capture defaults to off;
`TRACE_CAPTURE_CONTENT=true` opts into recording prompts and generated cards.
Cost is omitted because no local model price is configured. Telemetry delivery
failures do not stop document processing. Import
[the dashboard](monitoring/rq-generator.json) into the shared Grafana and select
its existing Prometheus and Loki sources. No monitoring stack is deployed.

## Checks

```bash
uv sync --extra dev
uv run python3 -m pytest tests/ -q
git diff --check
```

Tests use local HTTP fixtures for service contracts, evidence validation,
long-input batching, checkpointing, and controlled failures. They do not prove
scientific accuracy or availability of deployed services. Keep generated test
and integration evidence in the ignored `.artifacts/` directory.
