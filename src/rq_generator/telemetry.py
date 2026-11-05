"""Best-effort metadata telemetry to the existing shared services."""

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from datetime import UTC, datetime

import httpx


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "severity": record.levelname,
                "service": "rq-generator",
                "environment": os.getenv("APP_ENV", "local"),
                "message": record.getMessage(),
                **getattr(record, "fields", {}),
            }
        )


logger = logging.getLogger("rq-generator")


class LokiHandler(logging.Handler):
    def emit(self, record):
        try:
            endpoint = os.getenv("LOKI_URL")
            payload = {
                "streams": [
                    {
                        "stream": {
                            "service": "rq-generator",
                            "environment": os.getenv("APP_ENV", "local"),
                        },
                        "values": [[str(time.time_ns()), self.format(record)]],
                    }
                ]
            }
            httpx.post(
                endpoint.rstrip("/") + "/loki/api/v1/push", json=payload, timeout=2
            ).raise_for_status()
        except Exception:
            # Avoid recursion if the remote log sink fails.
            sys.stderr.write("rq-generator: Loki delivery failed\n")


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.handlers[:] = [handler]
    if os.getenv("LOKI_URL"):
        remote = LokiHandler()
        remote.setFormatter(JsonFormatter())
        logger.addHandler(remote)
    logger.setLevel(logging.INFO)
    logger.propagate = False


class Telemetry:
    def __init__(self):
        self.langfuse = None
        self.completed = self.failed = 0
        self.duration = 0.0
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            try:
                from langfuse import Langfuse

                self.langfuse = Langfuse()
            except Exception:
                logger.warning("Langfuse initialization failed")

    @contextmanager
    def span(self, name, *, generation=False, **metadata):
        observation = None
        manager = None
        if self.langfuse:
            try:
                manager = self.langfuse.start_as_current_observation(
                    name=name,
                    as_type="generation" if generation else "span",
                    metadata=metadata,
                    **({"model": metadata["model"]} if generation else {}),
                )
                observation = manager.__enter__()
            except Exception:
                logger.warning("Langfuse observation failed")
                manager = None
        try:
            yield observation
        except Exception as exc:
            if observation:
                try:
                    observation.update(level="ERROR", status_message=type(exc).__name__)
                except Exception:
                    logger.warning("Langfuse error update failed")
            raise
        finally:
            if manager:
                try:
                    manager.__exit__(None, None, None)
                except Exception:
                    logger.warning("Langfuse delivery failed")

    def reset(self):
        self.completed = self.failed = 0
        self.duration = 0.0
        self.publish()

    def job(self, success, duration):
        self.completed += int(success)
        self.failed += int(not success)
        self.duration += duration
        self.publish()

    def publish(self):
        endpoint = os.getenv("PUSHGATEWAY_URL")
        if endpoint:
            metrics = (
                f'rq_documents_total{{status="completed"}} {self.completed}\n'
                f'rq_documents_total{{status="failed"}} {self.failed}\n'
                f"rq_job_duration_seconds_sum {self.duration}\n"
                f"rq_job_duration_seconds_count {self.completed + self.failed}\n"
            )
            try:
                env = os.getenv("APP_ENV", "local")
                from urllib.parse import quote

                httpx.put(
                    endpoint.rstrip("/")
                    + "/metrics/job/rq-generator/environment/"
                    + quote(env, safe=""),
                    content=metrics,
                    timeout=2,
                ).raise_for_status()
            except Exception:
                logger.warning("Pushgateway delivery failed")

    def close(self):
        if self.langfuse:
            try:
                self.langfuse.flush()
            except Exception:
                logger.warning("Langfuse flush failed")
