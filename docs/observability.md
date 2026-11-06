# Observability and monitoring

The RQ application already emits telemetry. The development workflow needs its
own events to explain agent work. Keep the two service names and dashboards
separate so a PDF failure is distinguishable from a failed review.

## Existing application telemetry

`src/rq_generator/telemetry.py` owns JSON stderr logs, optional Loki delivery,
Pushgateway metrics, and optional Langfuse traces. `.env.example` documents its
configuration. `monitoring/rq-generator.json` is the application dashboard.
See the README for content capture and dependency settings.

| Shared service | Local host endpoint | Configuration |
| --- | --- | --- |
| Grafana | `http://127.0.0.1:3013/` | `GRAFANA_URL` for operational tooling |
| Prometheus | `http://127.0.0.1:9094` | `PROMETHEUS_URL` for verification |
| Loki | `http://127.0.0.1:3101` | `LOKI_URL` |
| Pushgateway | `http://127.0.0.1:9095` | `PUSHGATEWAY_URL` |
| Langfuse | `http://127.0.0.1:3006` | `LANGFUSE_BASE_URL` and secret keys |

These are this workspace's documented endpoints, not health claims. Environment
and deployment configuration take precedence. The vendored monitoring skill
mentions a different Grafana port; use 3013 here unless configuration changes.
Container loopback may point to the container itself. Verify network reachability
from the process that sends telemetry. Do not deploy a duplicate stack.

For runtime changes verify a successful job and a controlled failure. Query
Loki for service/environment and a correlation field; inspect Pushgateway and
then Prometheus to prove scraping; check the Grafana data source; inspect a
Langfuse trace when enabled. Store sanitized query results and distinguish
unconfigured, unavailable, and verified integrations. Optional exporter failures
must not fail the PDF job.

## Readiness observed during this cleanup

On 2026-11-06, read-only probes returned HTTP 200 from Prometheus, Loki,
Pushgateway, and Langfuse at the endpoints above. Grafana on port 3013 refused
the connection. This check did not send an application job or verify ingestion,
traces, dashboard data sources, or alert routing. Confirm the configured Grafana
endpoint before using the dashboard; do not substitute another instance silently.

## Workflow telemetry contract for a future feature

No workflow exporter is installed by this documentation change. Implement it
through an approved SDD feature, with instrumentation owned by a runner or
command wrapper that observes outcomes rather than relying on agent narration.

Persist a local event stream and forward best-effort copies to shared backends.
Suggested events are `run_started`, `spec_ready`, `spec_approved`,
`agent_started`, `agent_finished`, `check_finished`, `review_finished`,
`pr_opened`, `run_blocked`, and `run_finished`. Each event should contain UTC
time, service `rq-harness`, environment, run ID, feature ID, role, phase, status,
branch, commit, and duration when known. Capture exit status for actual checks.
Keep unique IDs in log fields, not metric labels. Approval events reference a
human statement and spec revision; they do not create approval themselves.

Metrics should cover run outcomes, stage duration, check failures, review cycles,
and PR creation outcomes with bounded labels such as environment, phase, and
result. Define counter behavior across short-lived runs and stale Pushgateway
group cleanup before choosing an exporter. Track time waiting for a human
separately from agent execution time.

Use Langfuse for model calls that the runner can actually observe. Record model,
latency, usage, and cost only when available. Do not invent Codex token counts
or infer a complete trace from a CLI exit status. Native Codex telemetry is a
separate user-level setup; repository settings alone do not configure its
telemetry routing. Keep prompts and responses off by default.

A workflow dashboard should show outcomes, time per phase, review rework, and
linked logs/traces. Alert routing and thresholds need explicit operational
ownership. End-to-end acceptance must prove both success and failure arrive in
backends and that unavailable telemetry does not corrupt local task state.
