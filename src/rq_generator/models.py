"""Validated scientific cards and their saved source evidence."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
References = Annotated[list[Text], Field(min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Document(StrictModel):
    doc_id: Text
    source_path: Text
    sha256: Text


class Chunk(StrictModel):
    doc_id: Text
    chunk_id: Text
    ordinal: int = Field(ge=0)
    text: Text
    section: Text | None = None
    page_start: int | None = None
    page_end: int | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)


class ChunkStore(StrictModel):
    documents: list[Document] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)


class Evidence(StrictModel):
    text: Text
    chunk_id: References


class Claim(Evidence):
    claim_id: Text


class Summary(StrictModel):
    findings: Text | None
    methods: Text | None
    conditions: Text | None
    limitations: Text | None
    entities: Text | None


class Question(StrictModel):
    question: Text
    rationale: Text
    chunk_id: References


class Entity(StrictModel):
    group: Literal["GO", "MeSH", "Cell Ontology", "HGNC"]
    normalized_name: Text
    chunk_id: References


class Mention(StrictModel):
    mention: Text
    chunk_id: References


class Generated(StrictModel):
    main_claims: list[Evidence]
    summary: Summary
    entity_mentions: list[Mention]
    candidate_research_questions: list[Question] = Field(max_length=5)


class Card(StrictModel):
    doc_id: Text
    main_claims: list[Claim]
    summary: Summary
    entities: list[Entity]
    candidate_research_questions: list[Question] = Field(max_length=5)


def _unique(values: list[str]) -> None:
    if len(values) != len(set(values)):
        raise ValueError("Duplicate identifier")


def validate_outputs(store: ChunkStore, cards: list[Card]) -> None:
    """Reject dangling evidence, wrong document membership, and duplicate IDs."""
    docs = {d.doc_id for d in store.documents}
    chunks = {c.chunk_id: c.doc_id for c in store.chunks}
    _unique([d.doc_id for d in store.documents])
    _unique([c.chunk_id for c in store.chunks])
    _unique([c.doc_id for c in cards])
    _unique([claim.claim_id for card in cards for claim in card.main_claims])
    if any(chunk.doc_id not in docs for chunk in store.chunks):
        raise ValueError("Chunk references an unknown document")
    for card in cards:
        if card.doc_id not in docs:
            raise ValueError("Card references an unknown document")
        for item in [
            *card.main_claims,
            *card.entities,
            *card.candidate_research_questions,
        ]:
            _unique(item.chunk_id)
            if any(chunks.get(ref) != card.doc_id for ref in item.chunk_id):
                raise ValueError("Evidence must resolve within the card document")
