# Application architecture

RQ generator processes scientific PDFs into evidence-linked document cards.
The workflow that develops it is described in `docs/workflow.md`. Keep workflow
state out of the application package.

## Existing boundaries

| Module | Responsibility |
| --- | --- |
| `src/rq_generator/cli.py` | Parse flags and environment defaults; select exit status |
| `src/rq_generator/services.py` | Configuration and OCR, chunking, Ollama clients; bounded generation and correction |
| `src/rq_generator/models.py` | Strict output schemas and evidence reference validation |
| `src/rq_generator/pipeline.py` | Discovery, IDs, per-document execution, atomic output files, output locking |
| `src/rq_generator/telemetry.py` | Structured logs and optional shared telemetry delivery |
| `src/rq_generator/__init__.py` | Export CLI entrypoint |
| `src/rq_generator/__main__.py` | Module execution entrypoint |

Use existing clients and service contracts. Service URLs, model name, context
limits, timeouts, and telemetry settings come from flags or environment.
`.env.example` documents defaults; the application does not load `.env` itself.

The pipeline discovers direct-child PDFs, processes them in filename order,
and writes `chunks.json`, `document_cards.json`, and `progress.json`.
Python assigns document, chunk, and claim identifiers. Models validate schemas
and ensure citations refer to saved chunks from the same document. Evidence
integrity does not prove scientific truth.

Failures in one document allow later documents to proceed. Storage and invalid
configuration errors stop the run. Writes replace individual files atomically;
the output set is not one transaction. Runs start fresh and refuse a concurrently
used output directory. CLI exit statuses are documented in `README.md`.

## Change boundaries

Keep CLI parsing separate from processing. Share operations at the module that
owns them rather than duplicating service calls in CLI branches. Add modules
when an approved design needs them; this document is not a fixed file allowlist.
Retain strict evidence validation and service compatibility. Document protocol
or output changes in the spec and include migration implications.

The deployed OCR, chunking, Ollama, and monitoring services are external.
Offline tests use local fixtures. Live verification checks configured services
without substituting another provider or deploying a separate monitoring stack.
