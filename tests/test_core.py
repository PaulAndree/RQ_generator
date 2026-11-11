"""Exercise discovery, schemas, identifiers, and configuration contracts."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rq_generator.config import Settings
from rq_generator.models import Card, Chunk, ChunkStore, Document, validate_outputs
from rq_generator.storage import discover, document_record, make_chunk


def sample(doc_id="doc_test", chunk_id="chunk_test"):
    return {
        "doc_id": doc_id,
        "main_claims": [
            {
                "claim_id": "claim_test",
                "text": "A supported claim",
                "chunk_id": [chunk_id],
            }
        ],
        "summary": dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"]),
        "entities": [],
        "candidate_research_questions": [],
    }


def test_discovery_filters_and_orders(tmp_path):
    for name in ["z.pdf", "A.PDF", "b.txt"]:
        (tmp_path / name).write_bytes(b"pdf")
    (tmp_path / "directory.pdf").mkdir()
    (tmp_path / "link.pdf").symlink_to(tmp_path / "z.pdf")
    assert [p.name for p in discover(tmp_path)] == ["A.PDF", "z.pdf"]
    with pytest.raises(ValueError):
        discover(tmp_path / "missing")


def test_document_and_chunk_id_stability(tmp_path):
    p = tmp_path / "paper.pdf"
    p.write_bytes(b"first")
    d = document_record(p)
    assert document_record(p) == d
    q = tmp_path / "other.pdf"
    q.write_bytes(p.read_bytes())
    assert document_record(q).doc_id != d.doc_id
    p.write_bytes(b"changed")
    assert document_record(p).doc_id != d.doc_id
    c = make_chunk(d.doc_id, 0, "text", "Methods", {"token_count": 2})
    assert make_chunk(d.doc_id, 0, "text", "Methods", {"token_count": 2}) == c
    assert make_chunk(d.doc_id, 1, "text", "Methods", {}).chunk_id != c.chunk_id
    assert c.page_start is None and c.page_end is None
    assert c.section == "Methods"


def test_configuration_precedence_and_validation():
    settings = Settings.from_sources(
        {"OLLAMA_MODEL": "qwen3:14b", "APP_ENV": "test"},
        {"output_dir": Path("custom"), "ollama_model": "local"},
    )
    assert settings.ollama_model == "local"
    assert settings.environment == "test"
    assert settings.output_dir == Path("custom")
    assert not settings.capture_content
    with pytest.raises(ValueError):
        Settings.from_sources({"OLLAMA_CONTEXT_TOKENS": "-1"})


@pytest.mark.parametrize("mutation", ["blank", "unknown", "cross", "duplicate", "extra"])
def test_referential_integrity(mutation):
    store = ChunkStore(
        documents=[
            Document(doc_id="doc_test", source_path="a.pdf", sha256="a"),
            Document(doc_id="other", source_path="b.pdf", sha256="b"),
        ],
        chunks=[
            Chunk(doc_id="doc_test", chunk_id="chunk_test", ordinal=0, text="A"),
            Chunk(doc_id="other", chunk_id="other_chunk", ordinal=0, text="B"),
        ],
    )
    data = sample()
    if mutation == "blank":
        data["main_claims"][0]["text"] = " "
    elif mutation == "unknown":
        data["main_claims"][0]["chunk_id"] = ["unknown"]
    elif mutation == "cross":
        data["main_claims"][0]["chunk_id"] = ["other_chunk"]
    elif mutation == "duplicate":
        data["main_claims"] *= 2
    else:
        data["extra"] = True
    with pytest.raises((ValueError, ValidationError)):
        validate_outputs(store, [Card.model_validate(data)])


def test_summary_and_question_schema():
    data = sample()
    assert json.loads(Card.model_validate(data).model_dump_json())["summary"]["entities"] is None
    data["candidate_research_questions"] = [
        {"question": "Unanswered?", "rationale": "Reason", "chunk_id": ["chunk_test"]}
    ] * 6
    with pytest.raises(ValidationError):
        Card.model_validate(data)


def test_ids_relocate_and_change_with_source_metadata(tmp_path):
    roots = [tmp_path / "first", tmp_path / "second"]
    for root in roots:
        root.mkdir()
        (root / "paper.pdf").write_bytes(b"identical")
    assert document_record(roots[0] / "paper.pdf") == document_record(roots[1] / "paper.pdf")
    chunk = make_chunk("doc_test", 0, "source", "Methods", {"page_start": 1, "page_end": 2})
    assert chunk.page_start == 1 and chunk.page_end == 2
    assert make_chunk("doc_test", 0, "source", "Results").chunk_id != chunk.chunk_id
    assert make_chunk("doc_test", 0, "changed", "Methods").chunk_id != chunk.chunk_id


@pytest.mark.parametrize("kind", ["main_claims", "entities", "candidate_research_questions"])
@pytest.mark.parametrize("refs", [[], ["unknown"], ["other_chunk"], ["chunk_test", "chunk_test"]])
def test_all_evidence_types_reject_invalid_references(kind, refs):
    store = ChunkStore(
        documents=[Document(doc_id="doc_test", source_path="a.pdf", sha256="a"),
                   Document(doc_id="other", source_path="b.pdf", sha256="b")],
        chunks=[Chunk(doc_id="doc_test", chunk_id="chunk_test", ordinal=0, text="A"),
                Chunk(doc_id="other", chunk_id="other_chunk", ordinal=0, text="B")])
    data = sample()
    items = {
        "main_claims": {"claim_id": "claim_test", "text": "Finding", "chunk_id": refs},
        "entities": {"group": "GO", "normalized_name": "DNA repair", "chunk_id": refs},
        "candidate_research_questions": {"question": "Why?", "rationale": "Unknown", "chunk_id": refs},
    }
    data[kind] = [items[kind]]
    with pytest.raises((ValueError, ValidationError)):
        validate_outputs(store, [Card.model_validate(data)])
