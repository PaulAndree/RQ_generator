"""Exercise CLI outputs, failure isolation, and durable reference invariants."""

import json
import multiprocessing
import os
import signal

import pytest

from rq_generator.cli import main
from rq_generator.models import Card, ChunkStore, Claim, Document, validate_outputs
from rq_generator.storage import Checkpoints, make_chunk


class QuietTelemetry:
    run_id = "test-run"
    events = []

    def event(self, name, **fields):
        self.events.append((name, fields))

    def close(self, **fields):
        pass


def test_cli_order_failure_and_outputs(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    for name in ["C.pdf", "B.pdf", "A.PDF"]:
        (source / name).write_bytes(name.encode())
    calls = []

    class Services:
        def extract(self, path, doc_id):
            calls.append(path.name)
            if path.name == "B.pdf":
                raise ValueError("controlled failure")
            return [make_chunk(doc_id, 0, "A supported finding")]

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return {"assessments": dict.fromkeys(
                    schema["properties"]["assessments"]["required"])}
            import re

            return {
                "main_claims": [{"text": re.findall(r"sentence_[0-9a-f]+", prompt)[0]}],
                "summary": dict.fromkeys(
                    ["findings", "methods", "conditions", "limitations", "entities"]
                ),
                "entity_mentions": [],
                "candidate_research_questions": [],
            }

    out = tmp_path / "out"
    assert (
        main(
            [str(source), "--output-dir", str(out)],
            services=Services(),
            normalizer=lambda *_: [],
            telemetry=QuietTelemetry(),
        )
        == 1
    )
    assert calls == ["A.PDF", "B.pdf", "C.pdf"]
    store = ChunkStore.model_validate_json((out / "chunks.json").read_text())
    cards = [
        Card.model_validate(c)
        for c in json.loads((out / "document_cards.json").read_text())["cards"]
    ]
    assert len(cards) == 2
    assert [d.source_path for d in store.documents] == ["A.PDF", "B.pdf", "C.pdf"]
    assert [c.doc_id for c in cards] == [
        store.documents[0].doc_id,
        store.documents[2].doc_id,
    ]
    states = json.loads((out / "run_state.json").read_text())["attempts"]
    assert [s["status"] for s in states] == ["success", "failed", "success"]


def test_cli_rejects_invalid_input_and_handles_empty(tmp_path):
    assert main([str(tmp_path / "missing")]) == 2
    source = tmp_path / "empty"
    source.mkdir()
    out = tmp_path / "out"
    assert main([str(source), "--output-dir", str(out)], telemetry=QuietTelemetry()) == 0
    assert json.loads((out / "document_cards.json").read_text()) == {"cards": []}


def test_checkpoint_preserves_old_card_references_on_interrupted_write(tmp_path, monkeypatch):
    import rq_generator.storage as storage

    doc = Document(doc_id="doc", source_path="a.pdf", sha256="hash")
    chunk = make_chunk("doc", 0, "evidence")
    summary = dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"])
    card = Card(
        doc_id="doc",
        main_claims=[Claim(claim_id="claim", text="evidence", chunk_id=[chunk.chunk_id])],
        summary=summary,
        entities=[],
        candidate_research_questions=[],
    )
    with Checkpoints(tmp_path) as checkpoints:
        checkpoints.save(ChunkStore(documents=[doc], chunks=[chunk]), [card], {})
        original = storage.os.replace

        def interrupt(src, dst):
            if dst.name == "document_cards.json":
                raise OSError("controlled interruption")
            original(src, dst)

        monkeypatch.setattr(storage.os, "replace", interrupt)
        with pytest.raises(OSError):
            checkpoints.save(
                ChunkStore(documents=[doc], chunks=[chunk, make_chunk("doc", 1, "extra")]),
                [card],
                {},
            )
        assert (
            json.loads((tmp_path / "document_cards.json").read_text())["cards"][0]["doc_id"]
            == "doc"
        )
        assert len(json.loads((tmp_path / "chunks.json").read_text())["chunks"]) == 2
    assert list(tmp_path.glob(".rq-*.tmp")) == []


def _lock_child(path, ready):
    with Checkpoints(path):
        ready.set()
        signal.pause()


def test_writer_lock_released_on_process_death(tmp_path):
    ready = multiprocessing.Event()
    process = multiprocessing.Process(target=_lock_child, args=(tmp_path, ready))
    process.start()
    try:
        assert ready.wait(5)
        with pytest.raises(ValueError), Checkpoints(tmp_path):
            pass
        os.kill(process.pid, signal.SIGKILL)
        process.join(5)
        assert process.exitcode == -signal.SIGKILL
        with Checkpoints(tmp_path):
            assert (tmp_path / ".rq-generator.lock").exists()
    finally:
        if process.is_alive():
            process.kill()
        process.join()


@pytest.mark.parametrize("replace_index", range(1, 6))
@pytest.mark.parametrize("after_replace", [False, True])
def test_checkpoint_fault_matrix_keeps_published_evidence(
    tmp_path, monkeypatch, replace_index, after_replace
):
    import rq_generator.storage as storage

    doc = Document(doc_id="old", source_path="old.pdf", sha256="old")
    chunk = make_chunk("old", 0, "old evidence")
    card = Card(
        doc_id="old",
        main_claims=[Claim(claim_id="claim", text="supported", chunk_id=[chunk.chunk_id])],
        summary=dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"]),
        entities=[],
        candidate_research_questions=[],
    )
    with Checkpoints(tmp_path) as checkpoint:
        checkpoint.save(ChunkStore(documents=[doc], chunks=[chunk]), [card], {})
    original, count = storage.os.replace, 0

    def interrupt(source, destination):
        nonlocal count
        count += 1
        if count == replace_index and not after_replace:
            raise OSError("before replacement")
        original(source, destination)
        if count == replace_index and after_replace:
            raise OSError("after replacement")

    monkeypatch.setattr(storage.os, "replace", interrupt)
    with pytest.raises(OSError), Checkpoints(tmp_path) as checkpoint:
        new_doc = Document(doc_id="new", source_path="new.pdf", sha256="new")
        new_chunk = make_chunk("new", 0, "new evidence")
        checkpoint.save(ChunkStore(documents=[new_doc], chunks=[new_chunk]), [], {})
    saved = ChunkStore.model_validate_json((tmp_path / "chunks.json").read_text())
    cards = [
        Card.model_validate(c)
        for c in json.loads((tmp_path / "document_cards.json").read_text())["cards"]
    ]
    validate_outputs(saved, cards)
    assert list(tmp_path.glob(".rq-*.tmp")) == []


@pytest.mark.parametrize("failure_stage", ["generation", "validation"])
def test_cli_continues_after_generation_or_validation_failure(tmp_path, failure_stage):
    source = tmp_path / "input"
    source.mkdir()
    for name in ["A.pdf", "B.pdf", "C.pdf"]:
        (source / name).write_bytes(name.encode())

    class Services:
        active = None

        def extract(self, path, doc_id):
            self.active = path.name
            return [make_chunk(doc_id, 0, "Supported text")]

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return {"assessments": dict.fromkeys(
                    schema["properties"]["assessments"]["required"])}
            import re

            if self.active == "B.pdf" and failure_stage == "generation":
                raise RuntimeError("controlled generation failure")
            sentence_id = re.findall(r"sentence_[0-9a-f]+", prompt)[0]
            if self.active == "B.pdf":
                sentence_id = "sentence_invented"
            return {
                "main_claims": [{"text": sentence_id}],
                "summary": dict.fromkeys(
                    ["findings", "methods", "conditions", "limitations", "entities"]
                ),
                "entity_mentions": [],
                "candidate_research_questions": [],
            }

    output = tmp_path / "out"
    assert (
        main(
            [str(source), "--output-dir", str(output)],
            services=Services(),
            normalizer=lambda *_: [],
            telemetry=QuietTelemetry(),
        )
        == 1
    )
    assert len(json.loads((output / "document_cards.json").read_text())["cards"]) == 2
    assert len(json.loads((output / "chunks.json").read_text())["chunks"]) == 3
