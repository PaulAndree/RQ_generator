"""Check privacy defaults, observation details, delivery, and backend isolation."""

import io
import json

import httpx

from rq_generator.config import Settings
from rq_generator.telemetry import Telemetry


def test_structured_metadata_and_content_opt_in():
    stream = io.StringIO()
    requests = []
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: requests.append(r) or httpx.Response(204))
    ) as client:
        telemetry = Telemetry(Settings(), client=client, stream=stream)
        telemetry.event("card_completed", doc_id="doc_test", claim_count=2)
        event = json.loads(stream.getvalue().splitlines()[-1])
        assert event["service"] == "rq-generator"
        assert event["severity"] == "INFO"
        assert event["run_id"] and event["timestamp"]
        assert event["claim_count"] == 2
        payload = json.loads(requests[0].content)
        assert payload["streams"][0]["stream"] == {
            "service": "rq-generator",
            "environment": "local",
        }


def test_observation_privacy_usage_and_flush():
    class Span:
        updates = []

        def update(self, **kw):
            self.updates.append(kw)

    class Context:
        def __enter__(self):
            return Span()

        def __exit__(self, *args):
            assert args == (None, None, None)

    class Langfuse:
        observations = []
        flushed = False

        def start_as_current_observation(self, **kw):
            self.observations.append(kw)
            return Context()

        def flush(self):
            self.flushed = True

    lf = Langfuse()
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(204))) as client:
        telemetry = Telemetry(Settings(), client=client, langfuse=lf, stream=io.StringIO())
        with telemetry.observation(name="ollama-generation", model="qwen3:14b", input="private"):
            telemetry.model_result(
                {"prompt_eval_count": 12, "eval_count": 3}, 0.5, "private output"
            )
        telemetry.close(successes=1, failures=0, duration=0.5)
    assert all("input" not in o and "output" not in o for o in lf.observations)
    assert any(u.get("usage_details") == {"input": 12, "output": 3} for u in Span.updates)
    assert lf.flushed


def test_telemetry_outages_and_secret_free_failure():
    class Broken:
        def start_as_current_observation(self, **kw):
            raise RuntimeError("private secret")

        def flush(self):
            raise RuntimeError("private secret")

    stream = io.StringIO()

    def failure(request):
        raise httpx.ConnectError("private secret", request=request)

    with httpx.Client(transport=httpx.MockTransport(failure)) as client:
        telemetry = Telemetry(Settings(), client=client, langfuse=Broken(), stream=stream)
        telemetry.event("run_started")
        with telemetry.observation(name="generation", model="qwen3:14b"):
            pass
        telemetry.close(successes=1, failures=0, duration=1)
    assert "private secret" not in stream.getvalue()


def test_metadata_only_logs_and_explicit_opt_in():
    for enabled in [False, True]:
        stream = io.StringIO()
        with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(204))) as client:
            telemetry = Telemetry(Settings(capture_content=enabled), client=client, stream=stream)
            telemetry.event(
                "card_content",
                card={"summary": "SOURCE TEXT"},
                prompt="SOURCE TEXT",
                secret_key="NEVER SEND",
            )
        text = stream.getvalue()
        assert ("SOURCE TEXT" in text) is enabled
        assert "NEVER SEND" not in text


def test_metric_groups_and_units():
    requests = []
    with httpx.Client(
        transport=httpx.MockTransport(lambda r: requests.append(r) or httpx.Response(204))
    ) as client:
        telemetry = Telemetry(Settings(environment="test"), client=client, stream=io.StringIO())
        telemetry.close(successes=2, failures=1, duration=3.5)
    request = [r for r in requests if r.method == "PUT"][0]
    assert request.url.path == "/metrics/job/rq-generator/environment/test"
    assert b"rq_generator_duration_seconds 3.5\n" in request.content
    assert b"rq_generator_document_failures 1\n" in request.content
    assert telemetry.run_id.encode() not in request.content


def test_independent_backend_outages_preserve_pipeline_outputs(tmp_path):
    import re

    from rq_generator.cli import main
    from rq_generator.models import Card, ChunkStore, validate_outputs
    from rq_generator.storage import make_chunk

    class BrokenLangfuse:
        def start_as_current_observation(self, **kwargs):
            raise RuntimeError("private secret")

        def flush(self):
            raise RuntimeError("private secret")

    class Services:
        def extract(self, path, doc_id):
            return [make_chunk(doc_id, 0, "A qualified finding appears supported.")]

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return {"assessments": dict.fromkeys(
                    schema["properties"]["assessments"]["required"])}
            return {
                "main_claims": [{"text": re.findall(r"sentence_[0-9a-f]+", prompt)[0]}],
                "summary": dict.fromkeys(
                    ["findings", "methods", "conditions", "limitations", "entities"]),
                "entity_mentions": [], "candidate_research_questions": [],
            }

    source = tmp_path / "input"
    source.mkdir()
    (source / "paper.pdf").write_bytes(b"test")
    for backend in ["loki", "pushgateway", "langfuse"]:
        stream = io.StringIO()

        def handler(request):
            failing = ((backend == "loki" and request.method == "POST")
                       or (backend == "pushgateway" and request.method == "PUT"))
            if failing:
                raise httpx.ConnectError("private secret", request=request)
            return httpx.Response(204)

        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            telemetry = Telemetry(Settings(), client=client, stream=stream,
                                  langfuse=BrokenLangfuse() if backend == "langfuse" else None)
            output = tmp_path / backend
            assert main([str(source), "--output-dir", str(output)], services=Services(),
                        normalizer=lambda *_: [], telemetry=telemetry) == 0
        store = ChunkStore.model_validate_json((output / "chunks.json").read_text())
        cards = [Card.model_validate(c) for c in json.loads(
            (output / "document_cards.json").read_text())["cards"]]
        assert len(cards) == 1 and len(cards[0].main_claims) == 1
        validate_outputs(store, cards)
        assert '"backend": "' + backend + '"' in stream.getvalue()
        assert "private secret" not in stream.getvalue()


def test_error_observations_are_recorded_without_exception_content():
    class Span:
        updates = []

        def update(self, **fields):
            self.updates.append(fields)

    class Context:
        def __enter__(self):
            return Span()

        def __exit__(self, *args):
            assert args == (None, None, None)

    class Langfuse:
        def start_as_current_observation(self, **fields):
            return Context()

    import pytest

    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(204))) as client:
        telemetry = Telemetry(Settings(), client=client, langfuse=Langfuse(), stream=io.StringIO())
        with (
            pytest.raises(ValueError, match="private source"),
            telemetry.observation("ollama-generation", model="qwen3:14b"),
        ):
            raise ValueError("private source")
    assert Span.updates == [{"level": "ERROR", "status_message": "ValueError"}]
