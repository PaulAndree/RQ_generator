import json
from pathlib import Path

import httpx
import pytest

from rq_generator.models import Chunk, Draft, validate_references
from rq_generator.pipeline import run
from rq_generator.services import Config, Services


def draft(refs):
    return {
        "main_claims": [
            {
                "claim": "The treatment may help under laboratory conditions.",
                "chunk_id": refs,
            }
        ],
        "summary": {
            "findings": "A conditional effect.",
            "methods": "A controlled experiment.",
            "conditions": "Laboratory conditions.",
            "limitations": None,
        },
        "candidate_research_questions": [
            {
                "question": "Does the effect persist in field conditions?",
                "rationale": "Only laboratory conditions were studied.",
                "chunk_id": refs,
            }
        ],
    }


def fixture_services(tmp_path, fail=False):
    calls = []

    def handler(request):
        calls.append(request)
        if request.url.path == "/services/ocr":
            if fail and b"broken" in request.content:
                return httpx.Response(500, json={"error": "controlled failure"})
            return httpx.Response(
                200,
                json={
                    "content_parsed": "# Results\nA conditional effect.",
                    "ocr_language": "en",
                },
            )
        if request.url.path == "/services/chunking/doc_by_titles":
            return httpx.Response(
                200,
                json={
                    "chunk_list": ["A conditional effect."],
                    "chunk_title": ["Results"],
                    "token_count": [5],
                    "chunk_language": "en",
                },
            )
        if request.url.path == "/api/chat":
            body = json.loads(request.content)
            data = json.loads(body["messages"][1]["content"])
            refs = sorted(
                {
                    ref
                    for item in data
                    for ref in (
                        [item["chunk_id"]]
                        if "text" in item
                        else [r for c in item["main_claims"] for r in c["chunk_id"]]
                    )
                }
            )
            return httpx.Response(
                200,
                json={
                    "message": {"content": json.dumps(draft(refs))},
                    "done": True,
                    "done_reason": "stop",
                    "prompt_eval_count": 30,
                    "eval_count": 40,
                },
            )
        raise AssertionError(request.url)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    return Services(Config(), client=client), calls


def test_folder_pipeline_and_stable_ids(tmp_path):
    inputs = tmp_path / "pdfs"
    inputs.mkdir()
    (inputs / "b.PDF").write_bytes(b"second")
    (inputs / "a.pdf").write_bytes(b"first")
    (inputs / "ignore.txt").write_text("skip")
    services, calls = fixture_services(tmp_path)
    output = tmp_path / "output"
    assert run(inputs, output, services) == 0
    chunks = json.loads((output / "chunks.json").read_text())["chunks"]
    cards = json.loads((output / "document_cards.json").read_text())["cards"]
    assert [Path(c["source_path"]).name for c in chunks] == ["a.pdf", "b.PDF"]
    assert len(cards) == 2
    assert chunks[0]["section"] == "Results"
    assert cards[0]["main_claims"][0]["chunk_id"] == [chunks[0]["chunk_id"]]
    assert run(inputs, output, services) == 0
    assert json.loads((output / "document_cards.json").read_text())["cards"] == cards
    assert services.telemetry.completed == 2
    assert any(
        b"type_name" in r.content for r in calls if r.url.path == "/services/ocr"
    )


def test_failure_continues_and_saves_progress(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"broken")
    (tmp_path / "b.pdf").write_bytes(b"good")
    services, _ = fixture_services(tmp_path, fail=True)
    output = tmp_path / "out"
    assert run(tmp_path, output, services) == 1
    assert len(json.loads((output / "document_cards.json").read_text())["cards"]) == 1
    assert [
        p["status"]
        for p in json.loads((output / "progress.json").read_text())["documents"]
    ] == ["failed", "completed"]


def test_unknown_evidence_rejected():
    value = Draft.model_validate(draft(["invented"]))
    with pytest.raises(ValueError, match="evidence"):
        validate_references(value, {"real"})


def test_strict_schema_and_question_limit():
    data = draft(["c1"])
    data["candidate_research_questions"] *= 6
    with pytest.raises(ValueError):
        Draft.model_validate(data)
    data = draft(["c1"])
    del data["summary"]["limitations"]
    with pytest.raises(ValueError):
        Draft.model_validate(data)


def test_long_chunk_is_bounded_and_evidence_retained(tmp_path):
    services, calls = fixture_services(tmp_path)
    services.config = Config(context_tokens=8192, output_tokens=1024)
    chunk = Chunk(
        doc_id="d",
        chunk_id="c",
        text="conditional effect " * 2000,
        source_path="a.pdf",
        section="Results",
        index=0,
        token_count=6000,
        language="en",
    )
    result = services.card("d", [chunk])
    assert result.main_claims[0].chunk_id == ["c"]
    model_calls = [json.loads(r.content) for r in calls if r.url.path == "/api/chat"]
    assert len(model_calls) > 2
    for call in model_calls:
        assert services.request_size(call["messages"]) <= services.input_budget


def test_output_failure_is_fatal(tmp_path):
    services, _ = fixture_services(tmp_path)
    (tmp_path / "a.pdf").write_bytes(b"good")
    output = tmp_path / "file"
    output.write_text("not a directory")
    with pytest.raises(OSError):
        run(tmp_path, output, services)


def test_checkpoint_exists_before_next_pdf(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"first")
    (tmp_path / "b.pdf").write_bytes(b"second")
    services, _ = fixture_services(tmp_path)
    original = services.chunks
    output = tmp_path / "out"

    def inspect(path, doc_id):
        if path.name == "b.pdf":
            assert (
                len(json.loads((output / "document_cards.json").read_text())["cards"])
                == 1
            )
            assert (
                json.loads((output / "progress.json").read_text())["documents"][0][
                    "status"
                ]
                == "completed"
            )
        return original(path, doc_id)

    services.chunks = inspect
    assert run(tmp_path, output, services) == 0


def test_generation_failure_retains_chunks(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"good")
    services, _ = fixture_services(tmp_path)

    def fail(*args):
        raise ValueError("invalid model output")

    services.card = fail
    assert run(tmp_path, tmp_path / "out", services) == 1
    assert len(json.loads((tmp_path / "out/chunks.json").read_text())["chunks"]) == 1
    assert json.loads((tmp_path / "out/document_cards.json").read_text()) == {
        "cards": []
    }


def test_duplicate_document_is_processed_once(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"same")
    (tmp_path / "b.pdf").write_bytes(b"same")
    services, calls = fixture_services(tmp_path)
    assert run(tmp_path, tmp_path / "out", services) == 0
    assert len([r for r in calls if r.url.path == "/services/ocr"]) == 1
    assert (
        json.loads((tmp_path / "out/progress.json").read_text())["documents"][1][
            "status"
        ]
        == "duplicate"
    )


def test_empty_input_and_output_lock(tmp_path):
    services, _ = fixture_services(tmp_path)
    output = tmp_path / "out"
    assert run(tmp_path, output, services) == 0
    assert json.loads((output / "document_cards.json").read_text()) == {"cards": []}
    (output / ".rq-generator.lock").touch()
    with pytest.raises(FileExistsError):
        run(tmp_path, output, services)


@pytest.mark.parametrize(
    "response",
    [
        {"done": False, "message": {"content": "{}"}},
        {"done": True, "done_reason": "length", "message": {"content": "{}"}},
        {"done": True, "message": {"content": "not json"}},
        {"done": True, "message": {"content": json.dumps(draft(["invented"]))}},
    ],
)
def test_invalid_model_outputs_fail(response):
    services = Services(
        Config(),
        client=httpx.Client(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(200, json=response)
            )
        ),
    )
    with pytest.raises(ValueError):
        services.generate([{"chunk_id": "real", "text": "Study."}], {"real"})


def test_consolidation_retains_evidence_when_chunks_have_no_claims(tmp_path):
    services, _ = fixture_services(tmp_path)
    services.config = Config(context_tokens=8192, output_tokens=1024)
    consolidations = []

    def generate(items, allowed, *, consolidate=False):
        if consolidate:
            consolidations.append(allowed)
            assert allowed == {"c1", "c2"}
        return Draft.model_validate(
            {
                "main_claims": [],
                "summary": {
                    "findings": None,
                    "methods": "A controlled study.",
                    "conditions": None,
                    "limitations": None,
                },
                "candidate_research_questions": [],
            }
        )

    services.generate = generate
    chunks = [
        Chunk(
            doc_id="d",
            chunk_id=ref,
            text="Methods " * 800,
            source_path="a.pdf",
            section="Methods",
            index=i,
            token_count=800,
            language="en",
        )
        for i, ref in enumerate(["c1", "c2"])
    ]
    services.card("d", chunks)
    assert consolidations
