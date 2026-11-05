"""Sequential folder orchestration and atomic output checkpoints."""

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from .models import validate_outputs
from .telemetry import logger


def atomic_json(path: Path, value):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix="." + path.name,
            delete=False,
        ) as file:
            temporary = Path(file.name)
            json.dump(value, file, ensure_ascii=False, indent=2, allow_nan=False)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def checkpoint(output, chunks, cards, progress):
    validate_outputs(chunks, cards)
    # Each JSON file is atomic; the three files are not one transaction.
    atomic_json(output / "chunks.json", {"chunks": [c.model_dump() for c in chunks]})
    atomic_json(
        output / "document_cards.json", {"cards": [c.model_dump() for c in cards]}
    )
    atomic_json(output / "progress.json", {"documents": progress})


def run(directory: Path, output: Path, services) -> int:
    directory = directory.resolve()
    if not directory.is_dir():
        raise ValueError("PDF directory does not exist")
    paths = sorted(
        (p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"),
        key=lambda p: p.name,
    )
    output.mkdir(parents=True, exist_ok=True)
    # Exclusive ownership avoids mixing checkpoints from simultaneous invocations.
    lock = output / ".rq-generator.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(descriptor)
        return process(paths, output, services)
    finally:
        lock.unlink()


def process(paths, output, services):
    services.telemetry.reset()
    chunks, cards, progress = [], [], []
    completed = set()
    checkpoint(output, chunks, cards, progress)
    failures = 0
    for path in paths:
        started = time.monotonic()
        doc_id = None
        success = False
        try:
            with path.open("rb") as file:
                doc_id = "doc_" + hashlib.file_digest(file, "sha256").hexdigest()
            if doc_id in completed:
                progress.append(
                    {"source_path": str(path), "doc_id": doc_id, "status": "duplicate"}
                )
            else:
                logger.info("document_started", extra={"fields": {"doc_id": doc_id}})
                with services.telemetry.span("document", doc_id=doc_id):
                    extracted = services.chunks(path, doc_id)
                    # Retain successful extraction even if model generation fails.
                    chunks[:] = [c for c in chunks if c.doc_id != doc_id]
                    chunks.extend(extracted)
                    card = services.card(doc_id, extracted)
                    validate_outputs(chunks, [*cards, card])
                    cards.append(card)
                completed.add(doc_id)
                success = True
                progress.append(
                    {"source_path": str(path), "doc_id": doc_id, "status": "completed"}
                )
                logger.info(
                    "document_completed",
                    extra={"fields": {"doc_id": doc_id, "chunks": len(extracted)}},
                )
        except Exception as exc:
            failures += 1
            # Error classes are safe to log; HTTP exception text may contain URL credentials.
            progress.append(
                {
                    "source_path": str(path),
                    "doc_id": doc_id,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                }
            )
            logger.error(
                "document_failed",
                extra={"fields": {"doc_id": doc_id, "error_type": type(exc).__name__}},
            )
        if progress[-1]["status"] != "duplicate":
            services.telemetry.job(success, time.monotonic() - started)
        # Storage errors are fatal: continuing would claim progress that was not saved.
        checkpoint(output, chunks, cards, progress)
    services.telemetry.publish()
    logger.info(
        "run_completed", extra={"fields": {"cards": len(cards), "failures": failures}}
    )
    return int(failures > 0)
