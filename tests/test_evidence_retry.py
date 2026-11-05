import json
import logging

import httpx
import pytest

from rq_generator.models import validate_references
from rq_generator.services import Config, Services


def draft(refs):
    return {
        "main_claims": [{"claim": "A conditional effect.", "chunk_id": refs}],
        "summary": dict.fromkeys(["findings", "methods", "conditions", "limitations"]),
        "candidate_research_questions": [],
    }


def services_with_responses(responses):
    calls = []

    def handler(request):
        calls.append(json.loads(request.content))
        result = responses[min(len(calls) - 1, len(responses) - 1)]
        return httpx.Response(200, json=result)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Services(Config(), client=client), calls


def response(refs):
    return {
        "done": True,
        "done_reason": "stop",
        "message": {"content": json.dumps(draft(refs))},
        "prompt_eval_count": 30,
        "eval_count": 40,
    }


@pytest.mark.parametrize("consolidate", [False, True])
@pytest.mark.parametrize("invalid_refs", [["invented"], ["real", "real"]])
def test_invalid_evidence_gets_one_correction(invalid_refs, consolidate, caplog):
    services, calls = services_with_responses([response(invalid_refs), response(["real"])])
    items = [{"chunk_id": "real", "text": "Private source text."}]
    if consolidate:
        items = [{**draft(["real"]), "source_chunk_ids": ["real"]}]
    with caplog.at_level(logging.WARNING, logger="rq-generator"):
        result = services.generate(items, {"real"}, consolidate=consolidate)
    validate_references(result, {"real"})
    assert len(calls) == 2
    assert calls[1]["messages"][:2] == calls[0]["messages"]
    assert calls[1]["messages"][2] == {
        "role": "assistant", "content": json.dumps(draft(invalid_refs), ensure_ascii=False, separators=(",", ":"))
    }
    instruction = calls[1]["messages"][-1]["content"]
    assert '"real"' in instruction
    assert "unsupported" in instruction
    for name in ("Claim", "Question"):
        assert calls[1]["format"]["$defs"][name]["properties"]["chunk_id"]["items"]["enum"] == ["real"]
        assert "enum" not in calls[0]["format"]["$defs"][name]["properties"]["chunk_id"]["items"]
    assert "evidence_correction_retry" in caplog.text
    assert "Private source text" not in caplog.text
    assert all(services.request_size(c["messages"], c["format"]) <= services.input_budget for c in calls)


def test_second_invalid_response_fails_without_third_call(caplog):
    services, calls = services_with_responses([response(["invented"])])
    with pytest.raises(ValueError, match="after one correction retry"):
        services.generate([{"chunk_id": "real", "text": "Evidence."}], {"real"})
    assert len(calls) == 2
    assert "evidence_correction_failed" in caplog.text


@pytest.mark.parametrize("failure", ["schema", "truncated", "json"])
def test_other_model_failures_do_not_trigger_evidence_retry(failure):
    result = response(["real"])
    if failure == "schema":
        result["message"]["content"] = '{}'
    elif failure == "truncated":
        result["done_reason"] = "length"
    else:
        result["message"]["content"] = 'invalid json'
    services, calls = services_with_responses([result])
    with pytest.raises(ValueError):
        services.generate([{"chunk_id": "real", "text": "Evidence."}], {"real"})
    assert len(calls) == 1


def test_valid_evidence_does_not_retry():
    services, calls = services_with_responses([response(["real"])])
    services.generate([{"chunk_id": "real", "text": "Evidence."}], {"real"})
    assert len(calls) == 1


def test_correction_that_exceeds_context_is_not_sent():
    services, calls = services_with_responses([response(["invented"])])
    item = {"chunk_id": "real", "text": ""}
    item["text"] = "x" * (services.input_budget - services.request_size(services.messages([item])))
    with pytest.raises(ValueError, match="Evidence correction exceeds configured context budget"):
        services.generate([item], {"real"})
    assert len(calls) == 1


def test_invalid_question_evidence_is_corrected():
    invalid = response(["real"])
    data = draft(["real"])
    data["candidate_research_questions"] = [{
        "question": "Does it hold in the field?",
        "rationale": "Only laboratory conditions were studied.",
        "chunk_id": ["invented"],
    }]
    invalid["message"]["content"] = json.dumps(data)
    services, calls = services_with_responses([invalid, response(["real"])])
    result = services.generate([{"chunk_id": "real", "text": "Evidence."}], {"real"})
    validate_references(result, {"real"})
    assert len(calls) == 2


def test_model_may_remove_unsupported_claims():
    corrected = response(["real"])
    data = draft(["real"])
    data["main_claims"] = []
    corrected["message"]["content"] = json.dumps(data)
    services, calls = services_with_responses([response(["invented"]), corrected])
    result = services.generate([{"chunk_id": "real", "text": "Evidence."}], {"real"})
    assert result.main_claims == []
    assert len(calls) == 2


def test_correction_budget_includes_allowed_id_schema():
    services, calls = services_with_responses([response(["invented"]), response(["real"])])
    item = {"chunk_id": "real", "text": "Evidence."}
    services.generate([item], {"real"})
    padding = services.input_budget - services.request_size(calls[1]["messages"])
    item["text"] += "x" * padding
    services, calls = services_with_responses([response(["invented"]), response(["real"])])
    with pytest.raises(ValueError, match="Evidence correction exceeds configured context budget"):
        services.generate([item], {"real"})
    assert len(calls) == 1
