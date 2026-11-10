# Project conventions

Follow existing project patterns and keep changes consistent with nearby code.
AGENTS.md defines the workflow; docs/verification.md defines verification.

## 1. Python and code style

- Use the Python version specified by pyproject.toml.
  The current minimum is Python 3.12; .python-version selects 3.12.
- Follow PEP 8 with a maximum line length of 100 characters.
- Group imports as standard library, third-party packages, then project modules.
- Prefer one imported module per import statement.
- Use double-quoted strings. Use single quotes when they avoid unnecessary escaping.
- Prefer f-strings for interpolation. Preserve deferred formatting in logging calls.
- Follow the lint rules configured in pyproject.toml.

## 2. Naming

| Element | Convention | Example |
|---|---|---|
| Modules | snake_case | document_cards.py |
| Classes | PascalCase | DocumentCard |
| Functions and variables | snake_case | load_cards |
| Constants | UPPER_SNAKE_CASE | DEFAULT_OUTPUT_PATH |
| Internal names | Leading underscore | _atomic_write |

Use names that describe the domain and behavior.

## 3. Module structure

Start modules with a short docstring describing their purpose.
Place future imports, when used, before other imports.

Import application modules through the rq_generator package.
Do not use src as an application package prefix.

Example:

```python
"""Validate and persist scientific document cards."""

from __future__ import annotations

import json
from pathlib import Path
```

Include imports only when the module uses them.

## 4. Tests

- Use pytest as defined in docs/verification.md.
- Name test modules tests/test_<module>.py where that organization fits.
- Use descriptive names such as test_load_returns_empty_when_file_missing.
- Prefer plain test functions and fixtures unless a class improves organization.
- Use tmp_path or another isolated temporary directory for filesystem tests.
- Restore mutable state and clean up resources created by tests.
- Keep unit tests independent of live services.
- Run required service integration checks separately and report their results.

Do not require temporary directories for tests that do not use the filesystem.

## 5. AI and document-processing services

Use the existing Ollama, OCR, chunking, and embedding services when required.
Reuse existing clients and integration patterns where available.

Read endpoints and model names from configuration.
Preserve existing configuration names:

| Setting | Documented value |
|---|---|
| OLLAMA_BASE_URL | http://localhost:11436 |
| OLLAMA_MODEL | qwen3:14b |
| CHUNKING_URL | http://localhost:8085 |
| OCR_BASE_URL | http://127.0.0.1:8084 |
| EMBEDDING_MODEL | http://127.0.0.1:8089/embed |

EMBEDDING_MODEL currently identifies an endpoint despite its name.
Do not silently rename it or reinterpret it as a model identifier.

Verify actual configuration and connectivity before integration checks.
Report unavailable services rather than substituting another provider.

Preserve compatibility between embedding models and existing indexes.
Model changes must account for any required reindexing.

## 6. Logging and observability

For applications and runtime changes, use the repository skill at
.agents/skills/observability/SKILL.md, named observability-shared-monitoring.

Include observability appropriate to the application and approved specification.

### Shared infrastructure

Reuse the shared monitoring services.

| Service | Documented endpoint |
|---|---|
| Grafana | http://127.0.0.1:3013 |
| Prometheus | http://127.0.0.1:9094 |
| Loki | http://127.0.0.1:3101 |
| Pushgateway | http://127.0.0.1:9095 |

Keep endpoints and port mappings in deployment configuration.
Confirm actual endpoints before use. Project configuration takes precedence
over example ports in a reusable skill.

From containers, use addresses reachable from that container.
Do not deploy a separate monitoring stack for each application.

Read credentials from environment variables or the existing secret manager.

### Application instrumentation

- Emit structured logs through the project's logging framework.
- Include service, environment, severity, and relevant request or trace IDs.
- For APIs, measure request counts, failures, and latency.
- For background jobs, measure executions, failures, and duration.
- Use Pushgateway for suitable short-lived batch jobs.
- Never log credentials or tokens.
- Follow project privacy rules for document and user content.

### Dashboards

- Create or update applicable dashboards in the shared Grafana instance.
- Identify telemetry by application and environment.
- Keep dashboard definitions and provisioning configuration in version
  control where supported.

### LLM tracing

Include Langfuse tracing when using Ollama for local inference.

- Read the endpoint and credentials from environment variables.
- Trace model calls and relevant retrieval or tool steps.
- Record model name, latency, token usage, and cost when available.
- Make prompt and response capture configurable.
- Default to metadata-only tracing unless content capture is authorized.
- Flush telemetry before short-lived processes exit.

Telemetry failures must not break application work unless the approved
specification explicitly requires that behavior.

Verify actual telemetry delivery as described in docs/verification.md.

## 7. Authorized delivery

Follow AGENTS.md and the assigned agent protocol for review and completion.

When shipping is authorized:

1. Keep changes limited to the assigned task.
2. Complete the applicable checks and implementation review.
3. Commit with a clear message and follow the task branch's update procedure.
4. Rerun relevant checks after rebasing or making further changes.
5. Push the task branch. If rewriting its published history is necessary
   and authorized, use --force-with-lease.
6. Open a pull request explaining the problem, resulting behavior,
   verification results, and material risks or limitations.
7. Apply /unslop to the title and description before posting.
8. Report the pull request URL and delivered revision.

Use screenshots or before-and-after evidence when they help demonstrate
the change.

Do not merge unless explicitly instructed.
Keep the task worktree until the pull request is merged or closed.
