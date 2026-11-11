"""Bounded evidence extraction and hierarchical document consolidation."""

import json
import re

from pydantic import Field

from rq_generator.models import (
    Card,
    Claim,
    Generated,
    Mention,
    Question,
    StrictModel,
    Summary,
    Text,
)
from rq_generator.storage import canonical, identifier


class SelectedClaim(StrictModel):
    text: Text


class SelectedQuestion(StrictModel):
    question: Text
    rationale: Text


class ClaimSelection(StrictModel):
    main_claims: list[SelectedClaim] = Field(min_length=1)


class ClaimReview(StrictModel):
    assessments: dict[Text, Text | None]


class Selection(StrictModel):
    main_claims: list[SelectedClaim]
    summary: Summary
    entity_mentions: list[Mention]
    candidate_research_questions: list[SelectedQuestion] = Field(max_length=5)


INSTRUCTIONS = """Return only JSON matching the schema. Extract zero or more supported
central claims per chunk. Keep the card compact; consolidation selects primary
document findings rather than every intermediate supporting example.
Preserve scientific uncertainty and study conditions;
never invent findings, biomedical mentions, or evidence.

main_claims[].text and each non-null summary value MUST be exactly one supplied
sentence_id. Python renders the entire source sentence and derives its evidence.
Do not return claim IDs or chunk_id for claims/questions. For tentative findings,
repeat the source wording verbatim: qualifiers such as appears, may, and likely
remain intact because Python renders the selected sentence exactly.

Each summary field must have explicit source support, otherwise null. Findings,
methods, conditions, limitations, and entities each select one sentence or null.
Do not infer limitations from missing information or unanswered questions.
Methods requires an explicit experimental technique or study design; a comparison
or commentary is not an experimental method. Commentary without experiments has
methods=null. Summary.entities selects a sentence naming explicit biomedical mentions.

For claims and findings, prioritize the final conclusions. Exclude introductory
positions later revised, qualified, or refuted by the final conclusions. Do not
select titles, references, affiliations, or rhetorical setups as established findings.

Entity mentions require explicit source text and supplied chunk_id arrays.

Return zero to five specific investigable questions only about an explicitly
unresolved issue in the source, not an already answered result. Question.rationale
MUST select the supplied unresolved sentence_id; Python renders that full sentence
and derives its references. The question must investigate its unresolved aspect,
not restate an answered question. Return zero questions without an explicit
unresolved source sentence. Never cite an unprovided sentence or chunk ID.
"""

UNRESOLVED = re.compile(
    r"\b(?:unknown|unclear|unresolved|unanswered|remains? to be|"
    r"(?:further|future) (?:research|study|studies)|"
    r"not (?:yet )?(?:known|understood|clear|established|determined))\b", re.IGNORECASE,
)
ABBREVIATION = re.compile(
    r"(?:\b[A-Za-z]\.|\b(?:al|Fig|Figs|Dr|Mr|Mrs|Ms|Prof|vs|cf|approx|vol|No|pp|St)\.)$",
    re.IGNORECASE,
)


def source_sentences(text):
    """Keep citation abbreviations and scientific initials attached to their text."""
    start = 0
    for boundary in re.finditer(r"(?<=[.!?])\s+(?=[A-Z])", text):
        if ABBREVIATION.search(text[:boundary.start()]):
            continue
        yield text[start:boundary.start()].strip()
        start = boundary.end()
    yield text[start:].strip()


class Generator:
    def __init__(self, settings, services, normalizer):
        self.settings = settings
        self.services = services
        self.normalizer = normalizer
        self.schema = Selection.model_json_schema()
        self.calls = 0
        self.call_limit = 0
        self.sentences = {}

    def request_schema(self, prompt):
        """Constrain selection to the complete source sentences in this request."""
        data = json.loads(prompt.split("Evidence:\n", 1)[1])
        sentences = data if isinstance(data, list) else data["sentences"]
        if "\nOperation: review\n" in prompt:
            schema = ClaimReview.model_json_schema()
            positions = {sentence["sentence_id"]: i for i, sentence in enumerate(sentences)}
            properties = {}
            for key in data["candidates"]:
                later = [sentence["sentence_id"] for sentence in sentences
                         if positions[sentence["sentence_id"]] > positions[key]]
                properties[key] = ({"anyOf": [{"type": "string", "enum": later},
                                              {"type": "null"}]}
                                   if later else {"type": "null"})
            schema["properties"]["assessments"] = {
                "type": "object", "properties": properties,
                "required": data["candidates"], "additionalProperties": False,
            }
            return schema
        if isinstance(data, dict) and "claim_limit" in data:
            schema = ClaimSelection.model_json_schema()
            schema["properties"]["main_claims"]["maxItems"] = data["claim_limit"]
            schema["$defs"]["SourceSentence"] = {
                "type": "string", "enum": sorted({
                    claim["text"] for packet in data["candidates"]
                    for claim in packet["main_claims"]
                }),
            }
            schema["$defs"]["SelectedClaim"]["properties"]["text"] = {
                "$ref": "#/$defs/SourceSentence",
            }
            return schema
        schema = Selection.model_json_schema()
        chunk_ids = {s["chunk_id"] for s in sentences}
        if isinstance(data, dict):
            for packet in data["candidates"]:
                for mention in packet["entity_mentions"]:
                    chunk_ids.update(mention["chunk_id"])
        if chunk_ids:
            schema["$defs"]["SourceChunk"] = {"type": "string", "enum": sorted(chunk_ids)}
            schema["$defs"]["Mention"]["properties"]["chunk_id"]["items"] = {
                "$ref": "#/$defs/SourceChunk",
            }
        else:
            schema["properties"]["entity_mentions"]["maxItems"] = 0
        if isinstance(data, dict):
            schema["properties"]["entity_mentions"]["maxItems"] = 0
        unresolved = sorted(s["sentence_id"] for s in sentences if UNRESOLVED.search(s["text"]))
        if unresolved:
            schema["$defs"]["UnresolvedSentence"] = {"type": "string", "enum": unresolved}
            schema["$defs"]["SelectedQuestion"]["properties"]["rationale"] = {
                "$ref": "#/$defs/UnresolvedSentence",
            }
        else:
            schema["properties"]["candidate_research_questions"]["maxItems"] = 0
        if not sentences:
            schema["properties"]["main_claims"]["maxItems"] = 0
            for field in schema["$defs"]["Summary"]["properties"]:
                schema["$defs"]["Summary"]["properties"][field] = {"type": "null"}
            return schema
        schema["$defs"]["SourceSentence"] = {
            "type": "string", "enum": sorted({s["sentence_id"] for s in sentences}),
        }
        schema["$defs"]["SelectedClaim"]["properties"]["text"] = {
            "$ref": "#/$defs/SourceSentence",
        }
        for field in schema["$defs"]["Summary"]["properties"]:
            schema["$defs"]["Summary"]["properties"][field] = {
                "anyOf": [{"$ref": "#/$defs/SourceSentence"}, {"type": "null"}],
            }
        return schema

    def request_bytes(self, prompt):
        # One UTF-8 byte per token is deliberately conservative for the text budget.
        payload = {
            "model": self.settings.ollama_model,
            "messages": [{"role": "user", "content": prompt}],
            "format": self.request_schema(prompt),
            "stream": False,
            "think": False,
            "options": {
                "num_ctx": self.settings.context_tokens,
                "num_predict": self.settings.output_tokens,
                "temperature": 0,
            },
        }
        return len(canonical(payload))

    def fits(self, prompt):
        budget = self.settings.context_tokens - self.settings.output_tokens - 1024
        return self.request_bytes(prompt) <= budget

    def _sentence_ids(self, packet):
        return {q.rationale for q in packet.candidate_research_questions} | {
            claim.text for claim in packet.main_claims
        } | {
            value for value in packet.summary.model_dump().values() if value is not None
        }

    def prompt(self, data, operation, claim_limit=None):
        if operation in {"consolidate", "compress"}:
            ids = set()
            for packet in data:
                ids.update(self._sentence_ids(Generated.model_validate(packet)))
            candidates = []
            for packet in data:
                candidate = {**packet, "entity_mentions": []}
                for field in ["main_claims", "candidate_research_questions"]:
                    candidate[field] = [
                        {key: value for key, value in item.items() if key != "chunk_id"}
                        for item in packet[field]
                    ]
                candidates.append(candidate)
            data = {"candidates": candidates,
                    "sentences": [self.sentences[key] for key in sorted(ids)]}
        if claim_limit is not None:
            data["claim_limit"] = claim_limit
        if operation == "extract":
            instruction = (
                "Extract explicit biomedical entity mentions, including organisms, genes, "
                "cell types and biological processes when present, with their supplied chunk_id."
            )
        elif operation == "compress":
            instruction = (
                f"Select at most {claim_limit} primary claims from the input main_claims. "
                "Prioritize final document conclusions. Return only main_claims; Python "
                "preserves the other fields and their evidence unchanged."
            )
        else:
            instruction = (
                "Return entity_mentions=[]; Python retains all extracted mentions independently."
            )
        return (
            INSTRUCTIONS + "\nOperation: " + operation + "\n" + instruction + "\nEvidence:\n"
            + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        )

    def _call(self, prompt, allowed, sentence_ids):
        if not self.fits(prompt) or self.calls >= self.call_limit:
            raise ValueError("Bounded generation budget exceeded")
        self.calls += 1
        result = Selection.model_validate(self.services.generate(prompt, self.request_schema(prompt)))
        for question in result.candidate_research_questions:
            sentence = self.sentences.get(question.rationale)
            if (question.rationale not in sentence_ids or sentence is None
                    or not UNRESOLVED.search(sentence["text"])):
                raise ValueError("Question lacks an explicit unresolved source sentence")
        if not self._sentence_ids(result) <= sentence_ids:
            raise ValueError("Model invented a source sentence reference")
        for item in result.entity_mentions:
            if any(ref not in allowed for ref in item.chunk_id):
                raise ValueError("Model invented an evidence reference")
        data = result.model_dump()
        for claim in data["main_claims"]:
            claim["chunk_id"] = [self.sentences[claim["text"]]["chunk_id"]]
        for question in data["candidate_research_questions"]:
            question["chunk_id"] = [self.sentences[question["rationale"]]["chunk_id"]]
        return Generated.model_validate(data)

    def _review(self, packet, sentences):
        """Check candidate claims against the complete single-segment document."""
        candidates = {claim.text for claim in packet.main_claims}
        if not candidates:
            return packet
        prompt = (
            "Review candidate claims against the complete document, in source order. "
            "For EACH candidate sentence, identify whether a later source sentence revises, "
            "qualifies, refutes or resolves that position. An introductory apparent anomaly "
            "is superseded when the conclusion explains its conformity. Return its resolving "
            "sentence_id as that candidate's assessment value. Compatible later detail or confirmation of a "
            "general principle is not supersession. Only mark a candidate whose independent "
            "presentation conflicts with that later source sentence. Otherwise return null. "
            "Do not treat introductory "
            "setups as independent conclusions. Return assessments as an object keyed by "
            "candidate sentence_id, with a later resolving sentence_id or null for each. "
            "Return only JSON matching the schema.\nOperation: review\nEvidence:\n"
            + json.dumps({"candidates": sorted(candidates), "sentences": sentences},
                         ensure_ascii=False, separators=(",", ":"))
        )
        if not self.fits(prompt) or self.calls >= self.call_limit:
            raise ValueError("Bounded generation budget exceeded")
        self.calls += 1
        review = ClaimReview.model_validate(
            self.services.generate(prompt, self.request_schema(prompt))
        )
        if set(review.assessments) != candidates:
            raise ValueError("Review must assess each candidate exactly once")
        superseded = {}
        source_order = {sentence["sentence_id"]: i for i, sentence in enumerate(sentences)}
        for key, resolving in review.assessments.items():
            if resolving is not None:
                if (resolving not in source_order
                        or source_order[resolving] <= source_order[key]):
                    raise ValueError("Review invented a resolving source sentence")
                superseded[key] = resolving
        summary = packet.summary.model_dump()
        for field, value in summary.items():
            if value in superseded:
                summary[field] = superseded[value] if field == "findings" else None
        return packet.model_copy(update={
            "main_claims": [claim for claim in packet.main_claims if claim.text not in superseded],
            "summary": Summary(**summary),
        })

    def _compress(self, packet):
        """Prune claim selections only when complete packets cannot be combined."""
        limit = len(packet.main_claims) // 2
        if limit < 1:
            raise ValueError("Consolidation cannot reduce within the context budget")
        before = self.request_bytes(self.prompt([packet.model_dump()], "consolidate"))
        prompt = self.prompt([packet.model_dump()], "compress", claim_limit=limit)
        if not self.fits(prompt) or self.calls >= self.call_limit:
            raise ValueError("Bounded generation budget exceeded")
        self.calls += 1
        result = ClaimSelection.model_validate(
            self.services.generate(prompt, self.request_schema(prompt))
        )
        if len(result.main_claims) > limit:
            raise ValueError("Compression exceeded its claim limit")
        retained = {claim.text: claim for claim in packet.main_claims}
        selected = {claim.text for claim in result.main_claims}
        if not selected <= retained.keys():
            raise ValueError("Compression invented a source sentence reference")
        reduced = packet.model_copy(update={
            "main_claims": [claim for key, claim in retained.items() if key in selected],
        })
        after = self.request_bytes(self.prompt([reduced.model_dump()], "consolidate"))
        if after >= before:
            raise ValueError("Compression did not reduce source packet bytes")
        return reduced

    def _segments(self, chunks):
        """Batch whole source sentences, never turn a clipped qualifier into a claim."""
        segments = []
        self.sentences = {}
        for chunk in chunks:
            current = []
            for text in source_sentences(chunk.text):
                text = text.strip()
                if not text:
                    continue
                key = f"sentence_{len(self.sentences)}"
                sentence = {"sentence_id": key, "chunk_id": chunk.chunk_id, "text": text}
                self.sentences[key] = sentence
                if not self.fits(self.prompt([*current, sentence], "extract")):
                    if current:
                        segments.append(current)
                        current = []
                    if not self.fits(self.prompt([sentence], "extract")):
                        raise ValueError("A complete source sentence exceeds the context budget")
                current.append(sentence)
            if current:
                segments.append(current)
        return segments

    def _units(self, packets):
        """Partition intermediate evidence without discarding text or references."""
        units = []
        empty = {"main_claims": [], "entity_mentions": [], "candidate_research_questions": [],
                 "summary": dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"])}
        for packet in packets:
            data = packet.model_dump()
            for field in ["main_claims", "entity_mentions", "candidate_research_questions"]:
                for item in data[field]:
                    unit = {**empty, field: [item]}
                    units.append(Generated.model_validate(unit))
            for field, value in data["summary"].items():
                if value is not None:
                    unit = {**empty, "summary": {**empty["summary"], field: value}}
                    units.append(Generated.model_validate(unit))
        unique = {canonical(unit.model_dump()): unit for unit in units}
        return list(unique.values()) or [packets[0]]

    def card(self, doc_id, chunks):
        segments = self._segments(chunks)
        self.calls = 0
        self.call_limit = max(8, len(segments) * 8)
        packets = [
            self._call(
                self.prompt(segment, "extract"), {s["chunk_id"] for s in segment},
                {s["sentence_id"] for s in segment},
            )
            for segment in segments
        ]
        mentions = [mention for packet in packets for mention in packet.entity_mentions]
        packets = [packet.model_copy(update={"entity_mentions": []}) for packet in packets]
        allowed = {c.chunk_id for c in chunks}
        if len(segments) == 1:
            # A single extraction still needs document-level contextual selection.
            packets = [self._review(packets[0], segments[0])]
        if len(packets) > 1:
            packets = self._units(packets)
        while len(packets) > 1:
            groups, current = [], []
            for packet in packets:
                proposed = [*current, packet]
                prompt = self.prompt([p.model_dump() for p in proposed], "consolidate")
                if not self.fits(prompt):
                    if not current:
                        raise ValueError("Intermediate result exceeds consolidation budget")
                    groups.append(current)
                    current = [packet]
                    if not self.fits(self.prompt([packet.model_dump()], "consolidate")):
                        raise ValueError("Intermediate result exceeds consolidation budget")
                else:
                    current = proposed
            if current:
                groups.append(current)
            if len(groups) >= len(packets):
                if not any(len(packet.main_claims) > 1 for packet in packets):
                    raise ValueError("Consolidation cannot reduce within the context budget")
                packets = [
                    self._compress(packet) if len(packet.main_claims) > 1 else packet
                    for packet in packets
                ]
                continue
            packets = [
                self._call(
                    self.prompt([p.model_dump() for p in group], "consolidate"), allowed,
                    set().union(*(self._sentence_ids(p) for p in group)),
                )
                for group in groups
            ]
        result = packets[0]
        claims = {}
        for claim in result.main_claims:
            sentence = self.sentences[claim.text]
            refs = [sentence["chunk_id"]]
            claim_id = identifier("claim", [doc_id, sentence["text"], refs])
            claims[claim_id] = Claim(claim_id=claim_id, text=sentence["text"], chunk_id=refs)
        entities = self.normalizer(mentions, chunks)
        return Card(
            doc_id=doc_id,
            main_claims=list(claims.values()),
            summary=Summary(**{
                field: self.sentences[value]["text"] if value is not None else None
                for field, value in result.summary.model_dump().items()
            }),
            entities=entities,
            candidate_research_questions=[
                Question(question=q.question, rationale=self.sentences[q.rationale]["text"],
                         chunk_id=[self.sentences[q.rationale]["chunk_id"]])
                for q in result.candidate_research_questions
            ],
        )
