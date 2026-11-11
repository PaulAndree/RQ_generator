"""Structured metadata, batch metrics, and optional Langfuse tracing."""

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime

import httpx


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(record.event, ensure_ascii=False)


class Telemetry:
    def __init__(self, settings, client=None, langfuse=None, stream=None):
        self.settings = settings
        self.run_id = uuid.uuid4().hex
        self.client = client or httpx.Client(timeout=3)
        self.owns_client = client is None
        self.langfuse = langfuse
        self.spans = []
        self.model_calls = 0
        self.model_seconds = 0.0
        self.input_tokens = 0
        self.output_tokens = 0
        self.logger = logging.getLogger("rq-generator." + self.run_id)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(stream or sys.stderr)
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        if self.langfuse is None and settings.langfuse_public_key.get_secret_value():
            try:
                from langfuse import Langfuse

                self.langfuse = Langfuse(
                    public_key=settings.langfuse_public_key.get_secret_value(),
                    secret_key=settings.langfuse_secret_key.get_secret_value(),
                    base_url=settings.langfuse_base_url or None,
                    environment=settings.environment,
                    timeout=3,
                    flush_at=1,
                    flush_interval=1,
                )
            except Exception as exc:
                self._local(
                    "telemetry_failure",
                    backend="langfuse",
                    error_type=type(exc).__name__,
                )
        if self.langfuse is None:
            self._local("telemetry_disabled", backend="langfuse")

    def _fields(self, name, fields):
        forbidden = {"prompt", "response", "input", "output", "text", "card"}
        filtered = {
            k: v
            for k, v in fields.items()
            if not any(s in k.lower() for s in ["secret", "password", "authorization", "api_key"])
            and (self.settings.capture_content or k not in forbidden)
        }
        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": "ERROR"
            if name in {"document_failed", "run_failed", "telemetry_failure"}
            else "INFO",
            "service": "rq-generator",
            "environment": self.settings.environment,
            "run_id": self.run_id,
            "trace_id": self.run_id,
            "operation": name,
            **filtered,
        }

    def _local(self, name, **fields):
        self.logger.info("", extra={"event": self._fields(name, fields)})

    def event(self, name, **fields):
        event = self._fields(name, fields)
        self.logger.info("", extra={"event": event})
        if not self.settings.loki_url:
            return
        try:
            response = self.client.post(
                self.settings.loki_url.rstrip("/") + "/loki/api/v1/push",
                json={
                    "streams": [
                        {
                            "stream": {
                                "service": "rq-generator",
                                "environment": self.settings.environment,
                            },
                            "values": [[str(time.time_ns()), json.dumps(event)]],
                        }
                    ]
                },
            )
            response.raise_for_status()
        except Exception as exc:
            self._local("telemetry_failure", backend="loki", error_type=type(exc).__name__)

    @contextmanager
    def observation(self, name, model=None, input=None, **metadata):
        context, span = None, None
        if model:
            self.model_calls += 1
        if self.langfuse:
            try:
                kwargs = {
                    "name": name,
                    "as_type": "generation" if model else "span",
                    "metadata": metadata,
                }
                if model:
                    kwargs["model"] = model
                if self.settings.capture_content and input is not None:
                    kwargs["input"] = input
                if not self.spans:
                    kwargs["trace_context"] = {"trace_id": self.run_id}
                context = self.langfuse.start_as_current_observation(**kwargs)
                span = context.__enter__()
            except Exception as exc:
                context = None
                self._local(
                    "telemetry_failure",
                    backend="langfuse",
                    error_type=type(exc).__name__,
                )
        self.spans.append(span)
        try:
            yield span
        except BaseException as exc:
            if span:
                self._update(span, level="ERROR", status_message=type(exc).__name__)
            raise
        finally:
            self.spans.pop()
            if context:
                try:
                    # Exception messages can contain document text or credentials.
                    context.__exit__(None, None, None)
                except Exception as exc:
                    self._local(
                        "telemetry_failure",
                        backend="langfuse",
                        error_type=type(exc).__name__,
                    )

    def _update(self, span, **fields):
        try:
            span.update(**fields)
        except Exception as exc:
            self._local("telemetry_failure", backend="langfuse", error_type=type(exc).__name__)

    def model_result(self, response, duration, content):
        self.model_seconds += duration
        usage = {}
        for source, destination in [
            ("prompt_eval_count", "input"),
            ("eval_count", "output"),
        ]:
            if isinstance(response.get(source), int):
                usage[destination] = response[source]
        self.input_tokens += usage.get("input", 0)
        self.output_tokens += usage.get("output", 0)
        if self.spans and self.spans[-1]:
            details = {
                "usage_details": usage,
                "metadata": {"duration_seconds": duration},
            }
            if self.settings.capture_content:
                details["output"] = content
            self._update(self.spans[-1], **details)

    def close(self, *, successes, failures, duration):
        self.event("run_completed", successes=successes, failures=failures, duration=duration)
        values = {
            "executions": 1,
            "document_successes": successes,
            "document_failures": failures,
            "duration_seconds": duration,
            "model_calls": self.model_calls,
            "model_duration_seconds": self.model_seconds,
            "model_input_tokens": self.input_tokens,
            "model_output_tokens": self.output_tokens,
        }
        if self.settings.pushgateway_url:
            try:
                # Stable group labels avoid a new persistent series for each run.
                from urllib.parse import quote

                url = (
                    self.settings.pushgateway_url.rstrip("/")
                    + "/metrics/job/rq-generator/environment/"
                )
                body = "".join(f"rq_generator_{key} {value}\n" for key, value in values.items())
                response = self.client.put(
                    url + quote(self.settings.environment, safe=""),
                    content=body,
                    headers={"Content-Type": "text/plain; version=0.0.4"},
                )
                response.raise_for_status()
            except Exception as exc:
                self._local(
                    "telemetry_failure",
                    backend="pushgateway",
                    error_type=type(exc).__name__,
                )
        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception as exc:
                self._local(
                    "telemetry_failure",
                    backend="langfuse",
                    error_type=type(exc).__name__,
                )
        if self.owns_client:
            self.client.close()
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)
