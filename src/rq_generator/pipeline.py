"""Process PDFs sequentially and checkpoint each completed attempt."""

from rq_generator.models import ChunkStore, validate_outputs
from rq_generator.storage import Checkpoints, document_record


def run(paths, settings, services, generator, telemetry):
    chunks, cards, attempts = ChunkStore(), [], []
    with Checkpoints(settings.output_dir) as checkpoints:
        checkpoints.save(chunks, cards, {"run_id": telemetry.run_id, "attempts": attempts})
        for path in paths:
            doc_id, card, error_type = None, None, None
            try:
                document = document_record(path)
                doc_id = document.doc_id
                chunks.documents.append(document)
                extracted = services.extract(path, doc_id)
                validate_outputs(ChunkStore(documents=[document], chunks=extracted), [])
                chunks.chunks.extend(extracted)
                card = generator.card(doc_id, extracted)
                validate_outputs(chunks, [*cards, card])
                cards.append(card)
            except Exception as exc:
                card = None
                error_type = type(exc).__name__
            attempts.append(
                {
                    "source_path": path.name,
                    "doc_id": doc_id,
                    "status": "success" if card else "failed",
                    "error_type": error_type,
                }
            )
            # Persistence errors are fatal and must escape document failure isolation.
            checkpoints.save(chunks, cards, {"run_id": telemetry.run_id, "attempts": attempts})
            if card:
                telemetry.event(
                    "card_completed",
                    doc_id=doc_id,
                    status="success",
                    claim_count=len(card.main_claims),
                    entity_count=len(card.entities),
                    question_count=len(card.candidate_research_questions),
                )
                if settings.capture_content:
                    telemetry.event("card_content", doc_id=doc_id, card=card.model_dump())
            else:
                telemetry.event(
                    "document_failed",
                    doc_id=doc_id,
                    status="failed",
                    error_type=error_type,
                )
    return len(cards), len(paths) - len(cards)
