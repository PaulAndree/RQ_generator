"""Verify real service request contracts and bounded retries."""

import json

import httpx
import pytest

from rq_generator.config import Settings


def test_service_contracts_and_metadata(tmp_path):
    from rq_generator.services import Services

    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/services/ocr":
            assert b'name="type_name"' in request.content
            assert b"pdf" in request.content
            return httpx.Response(
                200, json={"ocr_language": "en", "content_parsed": "# Title\nStudy"}
            )
        assert request.url.path == "/services/chunking/doc_by_titles"
        assert b"content_parsed=" in request.content
        return httpx.Response(
            200,
            json={
                "chunk_list": ["Study"],
                "chunk_title": ["Title"],
                "token_count": [2],
                "chunk_size": 1,
                "chunk_language": "en",
                "output_path": "",
            },
        )

    p = tmp_path / "test.pdf"
    p.write_bytes(b"test")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = Services(Settings(), client=client)
        chunks = service.extract(p, "doc_test")
    assert len(requests) == 2
    assert chunks[0].section == "Title"
    assert chunks[0].source_metadata["token_count"] == 2
    assert chunks[0].source_metadata["ocr_language"] == "en"


@pytest.mark.parametrize("status,expected", [(429, 3), (500, 3), (400, 1)])
def test_bounded_retries(status, expected):
    from rq_generator.services import Services

    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(status)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        service = Services(Settings(), client=client, sleep=lambda _: None)
        with pytest.raises(httpx.HTTPStatusError):
            service.request("POST", "http://test/route")
    assert len(calls) == expected


def test_ollama_model_and_json_contract():
    from rq_generator.services import Services

    def handler(request):
        payload = json.loads(request.content)
        assert payload["model"] == "qwen3:14b"
        assert payload["stream"] is False
        assert payload["think"] is False
        return httpx.Response(
            200,
            json={
                "message": {"content": '{"ok":true}'},
                "prompt_eval_count": 10,
                "eval_count": 3,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert Services(Settings(), client=client).generate("test", {"type": "object"}) == {
            "ok": True
        }


def test_malformed_success_is_not_retried():
    from rq_generator.services import Services

    count = []
    with (
        httpx.Client(
            transport=httpx.MockTransport(
                lambda r: count.append(r) or httpx.Response(200, text="invalid")
            )
        ) as client,
        pytest.raises(ValueError),
    ):
        Services(Settings(), client=client).generate("test", {})
    assert len(count) == 1


def test_timeout_retries_are_bounded_and_malformed_chunks_rejected(tmp_path):
    from rq_generator.services import Services

    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("controlled timeout", request=request)

    with (
        httpx.Client(transport=httpx.MockTransport(timeout)) as client,
        pytest.raises(httpx.ReadTimeout),
    ):
        Services(Settings(retries=1), client=client, sleep=lambda _: None).request(
            "POST", "http://test/route")
    assert len(calls) == 2

    def malformed(request):
        if request.url.path == "/services/ocr":
            return httpx.Response(200, json={"content_parsed": "A source"})
        return httpx.Response(200, json={"chunk_list": ["A"], "chunk_title": [],
                                       "token_count": [1], "chunk_size": 1})

    path = tmp_path / "paper.pdf"
    path.write_bytes(b"test")
    with (
        httpx.Client(transport=httpx.MockTransport(malformed)) as client,
        pytest.raises(ValueError, match="malformed aligned lists"),
    ):
        Services(Settings(), client=client).extract(path, "doc_test")


def test_truncated_model_response_records_available_usage_before_failure():
    from contextlib import nullcontext

    from rq_generator.services import Services

    class Telemetry:
        results = []

        def observation(self, **fields):
            return nullcontext()

        def model_result(self, response, duration, content):
            self.results.append((response["prompt_eval_count"], response["eval_count"], duration))

    telemetry = Telemetry()
    with (
        httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(200, json={
            "done_reason": "length", "message": {"content": '{"main_claims":['},
            "prompt_eval_count": 12, "eval_count": 128,
        }))) as client,
        pytest.raises(ValueError, match="exhausted"),
    ):
        Services(Settings(), client=client, telemetry=telemetry).generate("test", {})
    assert len(telemetry.results) == 1
    assert telemetry.results[0][:2] == (12, 128)
    assert telemetry.results[0][2] >= 0
