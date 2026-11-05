import json
import logging
from contextlib import contextmanager

import httpx
import pytest

from rq_generator.telemetry import JsonFormatter, LokiHandler, Telemetry


def test_log_fields_and_no_document_content():
    record = logging.LogRecord(
        "rq-generator", logging.INFO, "", 1, "document_completed", (), None
    )
    record.fields = {"doc_id": "doc_test"}
    data = json.loads(JsonFormatter().format(record))
    assert data["service"] == "rq-generator"
    assert data["severity"] == "INFO"
    assert data["doc_id"] == "doc_test"
    assert "text" not in data


def test_unavailable_telemetry_does_not_fail_jobs(monkeypatch):
    monkeypatch.setenv("PUSHGATEWAY_URL", "http://unavailable.invalid")
    monkeypatch.setenv("LOKI_URL", "http://unavailable.invalid")

    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("controlled failure")

    monkeypatch.setattr(httpx, "put", unavailable)
    monkeypatch.setattr(httpx, "post", unavailable)
    telemetry = Telemetry()
    telemetry.job(True, 1.5)
    assert telemetry.completed == 1
    LokiHandler().emit(
        logging.LogRecord("rq-generator", logging.INFO, "", 1, "test", (), None)
    )


def test_trace_errors_are_recorded_without_swallowing_document_failure():
    updates = []

    class Observation:
        def update(self, **fields):
            updates.append(fields)

    class Client:
        @contextmanager
        def start_as_current_observation(self, **kwargs):
            yield Observation()

    telemetry = Telemetry()
    telemetry.langfuse = Client()
    with pytest.raises(ValueError), telemetry.span("document", doc_id="doc_test"):
        raise ValueError("private content excluded")
    assert updates == [{"level": "ERROR", "status_message": "ValueError"}]
