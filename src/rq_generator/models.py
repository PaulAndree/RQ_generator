"""Output schemas and evidence validation."""

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Claim(Model):
    claim: str = Field(min_length=1)
    chunk_id: list[str] = Field(min_length=1)


class IdentifiedClaim(Claim):
    claim_id: str = Field(min_length=1)


class Summary(Model):
    findings: str | None
    methods: str | None
    conditions: str | None
    limitations: str | None


class Question(Model):
    question: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    chunk_id: list[str] = Field(min_length=1)


class Draft(Model):
    main_claims: list[Claim]
    summary: Summary
    candidate_research_questions: list[Question] = Field(max_length=5)


class Card(Model):
    doc_id: str
    main_claims: list[IdentifiedClaim]
    summary: Summary
    candidate_research_questions: list[Question] = Field(max_length=5)


class Chunk(Model):
    doc_id: str
    chunk_id: str
    text: str = Field(min_length=1)
    source_path: str
    section: str
    index: int = Field(ge=0)
    token_count: int | None = Field(ge=0)
    language: str | None


def validate_references(card: Draft | Card, allowed: set[str]) -> None:
    for item in [*card.main_claims, *card.candidate_research_questions]:
        if not item.chunk_id or not set(item.chunk_id) <= allowed:
            raise ValueError("Unknown or missing chunk evidence reference")
        if len(item.chunk_id) != len(set(item.chunk_id)):
            raise ValueError("Duplicate chunk evidence reference")


def validate_outputs(chunks: list[Chunk], cards: list[Card]) -> None:
    chunk_ids = [c.chunk_id for c in chunks]
    if len(set(chunk_ids)) != len(chunk_ids):
        raise ValueError("Duplicate chunk IDs")
    doc_ids = [c.doc_id for c in cards]
    if len(set(doc_ids)) != len(doc_ids):
        raise ValueError("Duplicate document IDs")
    claim_ids = []
    for card in cards:
        allowed = {c.chunk_id for c in chunks if c.doc_id == card.doc_id}
        if not allowed:
            raise ValueError("Card has no source document chunks")
        validate_references(card, allowed)
        claim_ids.extend(c.claim_id for c in card.main_claims)
    if len(set(claim_ids)) != len(claim_ids):
        raise ValueError("Duplicate claim IDs")
