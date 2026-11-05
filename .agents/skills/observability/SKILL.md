---
name: observability-shared-monitoring
description: Add or troubleshoot structured logs, metrics, Grafana dashboards, alerts, and LLM tracing using the shared monitoring stack. Use when instrumenting an application or investigating missing telemetry.
---

# Shared observability

Add or update observability (structured logs, metrics, dashboards, and LLM tracing) for a service using the shared Grafana, Prometheus, Loki, Pushgateway and Langfuse stack. Use when the user asks to add monitoring, logging, metrics, tracing, dashboards, or alerts to an application, or to debug why telemetry is missing.

## Shared services

These are expected published host ports. Confirm actual endpoints,
internal container ports, and networking from project configuration.

| Service | Purpose | Host port | Configuration |
| --- | --- | --- | --- |
| Grafana | Dashboards | 3005 | GRAFANA_URL |
| Prometheus | Scrape and query metrics | 9094 | PROMETHEUS_URL |
| Loki | Logs | 3101 | LOKI_URL |
| Pushgateway | Suitable short-lived batch jobs | 9095 | PUSHGATEWAY_URL |
| Langfuse UI/API | LLM tracing | 3006 | LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY |
| Langfuse Media storage | LLM tracing | 9190 | |

Preserve existing configuration names. Check the installed Langfuse SDK
before changing an existing LANGFUSE_HOST setting.

## Workflow

1. **Inspect first.**
   Read applicable AGENTS.md instructions. Inspect existing logging,
   metrics, tracing, dashboards, and deployment configuration.
   Extend existing libraries and conventions; avoid duplicate instrumentation.

2. **Reuse the shared stack.**
   Resolve endpoints from environment variables or project configuration.
   From containers, use reachable service names and internal ports.
   Add monitoring infrastructure only when required and confirmed absent.
   Document non-secret settings in the existing environment example.

3. **Emit structured logs.**
   Use JSON with timestamp, level, message, service, and environment.
   Include request_id for request-scoped logs and trace_id when available.
   Validate and propagate X-Request-ID or generate one; return it in the
   response. Ship logs through the existing collector or delivery mechanism.
   Use low-cardinality Loki labels such as service and environment.
   Keep request IDs and other unique values in log fields.

4. **Expose appropriate metrics.**
   For HTTP services, expose /metrics with request count, status, and
   request-duration histograms in seconds. Derive error rates from status.
   Use templated routes such as /users/{id}; never label metrics with raw
   URLs, request IDs, user IDs, or document content.
   Ensure Prometheus discovers and scrapes the application.
   For workers, measure job count, failures, and duration.
   Reserve Pushgateway for suitable service-level batch jobs that cannot
   be scraped; use stable grouping keys and manage stale series.

5. **Trace LLM applications.**
   Reuse compatible Langfuse/framework instrumentation.
   Create one logical trace per request or job, with observations for
   retrieval, prompt construction, and model calls.
   Record model, token usage when available, latency, and errors.
   Preserve async context and flush telemetry before short-lived processes
   exit. Keep telemetry delivery failures from breaking application work.

6. **Update dashboards and alerts when requested.**
   Store dashboards as provisioned JSON or existing infrastructure as code.
   Include request rate, error rate, p50/p95/p99 latency, and service logs.
   Use service/environment variables.
   For LLM panels, expose aggregate token and model-latency metrics through
   Prometheus or an existing supported integration.
   Use project SLOs or documented thresholds for alerts and reuse existing
   notification routing.

7. **Protect recorded data.**
   Exclude secrets and follow project rules for personal data and user
   content. Default to metadata-only LLM tracing unless content capture
   is allowed.

8. **Verify end to end.**
   Send a successful and controlled failing request or job.
   Confirm logs in Loki, metrics in Prometheus, applicable dashboard data,
   and LLM traces in Langfuse. Allow for scrape and ingestion delays.
   Validate changed configuration with available tools.

## Completion report

Summarize changes, required configuration, and verification results.
State what could not be verified and the remaining check.
Never claim delivery from configuration validation alone.