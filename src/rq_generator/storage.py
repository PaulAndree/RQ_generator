"""Deterministic IDs and reference-safe JSON checkpoints."""

import fcntl
import hashlib
import json
import os
import tempfile
from pathlib import Path

from rq_generator.models import Card, Chunk, ChunkStore, Document, validate_outputs


def canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def identifier(prefix: str, value) -> str:
    return prefix + "_" + hashlib.sha256(canonical(value)).hexdigest()


def discover(directory: Path) -> list[Path]:
    if not directory.is_dir() or not os.access(directory, os.R_OK | os.X_OK):
        raise ValueError("Input must be a readable directory")
    return sorted(
        (
            p
            for p in directory.iterdir()
            if not p.is_symlink() and p.is_file() and p.suffix.lower() == ".pdf"
        ),
        key=lambda p: p.name,
    )


def document_record(path: Path) -> Document:
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    return Document(
        doc_id=identifier("doc", [path.name, digest]),
        source_path=path.name,
        sha256=digest,
    )


def make_chunk(doc_id: str, ordinal: int, text: str, section=None, metadata=None) -> Chunk:
    metadata = metadata or {}
    fields = {
        "doc_id": doc_id,
        "ordinal": ordinal,
        "text": text.strip(),
        "section": section.strip() or None if isinstance(section, str) else None,
        "page_start": metadata.get("page_start"),
        "page_end": metadata.get("page_end"),
    }
    return Chunk(chunk_id=identifier("chunk", fields), source_metadata=metadata, **fields)


def atomic_json(path: Path, value) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".rq-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class Checkpoints:
    def __init__(self, directory: Path):
        self.directory = directory
        self.lock = None

    def __enter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = (self.directory / ".rq-generator.lock").open("a")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lock.close()
            raise ValueError("Output directory already has an active writer") from None
        try:
            atomic_json(self.directory / "document_cards.json", {"cards": []})
            atomic_json(self.directory / "chunks.json", ChunkStore().model_dump())
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def save(self, chunks: ChunkStore, cards: list[Card], state: dict):
        validate_outputs(chunks, cards)
        atomic_json(self.directory / "chunks.json", chunks.model_dump(mode="json"))
        atomic_json(
            self.directory / "document_cards.json",
            {"cards": [card.model_dump(mode="json") for card in cards]},
        )
        atomic_json(self.directory / "run_state.json", state)

    def __exit__(self, *_):
        if self.lock:
            self.lock.close()
