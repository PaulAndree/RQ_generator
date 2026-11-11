"""Assert bounded extraction/consolidation and evidence integrity."""

import re

import pytest

from rq_generator.config import Settings
from rq_generator.storage import make_chunk


def answer(chunk_id, text="A cautious finding"):
    return {
        "main_claims": [{"text": text}],
        "summary": dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"]),
        "entity_mentions": [],
        "candidate_research_questions": [],
    }



def retained_review(prompt):
    """Default service double keeps each supplied candidate after contextual review."""
    import json

    data = json.loads(prompt.split("Evidence:\n", 1)[1])
    return {"assessments": dict.fromkeys(data["candidates"])}

def test_generation_bounds_every_request_and_assigns_claim_ids():
    from rq_generator.generation import Generator

    settings = Settings(context_tokens=10000, output_tokens=1000)
    chunks = [make_chunk("doc_test", i, "A source finding. " * 1000) for i in range(3)]
    prompts = []

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            prompts.append(prompt)
            assert "uncertainty" in prompt and "already answered" in prompt
            assert schema["$defs"]["SourceSentence"]["enum"]
            return answer(re.findall(r"chunk_[0-9a-f]+", prompt)[0],
                          re.findall(r"sentence_[0-9a-f]+", prompt)[0])

    generator = Generator(settings, Service(), normalizer=lambda *_: [])
    card = generator.card("doc_test", chunks)
    assert len(prompts) > len(chunks)
    assert all(generator.fits(prompt) for prompt in prompts)
    assert card.main_claims[0].claim_id.startswith("claim_")
    assert all(c.chunk_id in " ".join(prompts) for c in chunks)


def test_zero_claims_and_invalid_evidence():
    from rq_generator.generation import Generator

    chunk = make_chunk("doc_test", 0, "No claim")

    class Service:
        invalid = False

        def generate(self, prompt, _):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            result = answer(chunk.chunk_id,
                            "sentence_invented" if self.invalid else re.findall(r"sentence_[0-9a-f]+", prompt)[0])
            if not self.invalid:
                result["main_claims"] = []
            return result

    service = Service()
    generator = Generator(Settings(), service, normalizer=lambda *_: [])
    assert generator.card("doc_test", [chunk]).main_claims == []
    service.invalid = True
    with pytest.raises(ValueError):
        generator.card("doc_test", [chunk])


def test_oversized_intermediate_never_reaches_unbounded_request():
    from rq_generator.generation import Generator

    chunk = make_chunk("doc_test", 0, "It remains unclear why. " * 1000)
    settings = Settings(context_tokens=10000, output_tokens=1000)

    class Service:
        def generate(self, prompt, _):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            assert len(prompt.encode()) < 9000
            result = answer(chunk.chunk_id, re.findall(r"sentence_[0-9a-f]+", prompt)[0])
            result["candidate_research_questions"] = [{
                "question": "Large question " * 10000, "rationale": re.findall(r"sentence_[0-9a-f]+", prompt)[0]}]
            return result

    with pytest.raises(ValueError):
        Generator(settings, Service(), normalizer=lambda *_: []).card("doc_test", [chunk])


def test_multilevel_reduction_bounds_all_requests():
    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", i, "A supported finding " * 30 + ".")
              for i in range(20)]
    prompts = []

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            prompts.append(prompt)
            return answer(re.findall(r"chunk_[0-9a-f]+", prompt)[0],
                          re.findall(r"sentence_[0-9a-f]+", prompt)[0])

    generator = Generator(
        Settings(context_tokens=10000, output_tokens=1000), Service(), normalizer=lambda *_: []
    )
    generator.card("doc_test", chunks)
    assert sum("Operation: consolidate" in p for p in prompts) >= 3
    assert all(generator.fits(p) for p in prompts)


def test_fidelity_prompt_keeps_qualifiers_and_explicit_summary_support():
    from rq_generator.generation import INSTRUCTIONS

    assert "appears" in INSTRUCTIONS
    assert "may" in INSTRUCTIONS
    assert "Do not infer limitations" in INSTRUCTIONS
    assert "null" in INSTRUCTIONS
    assert "Each summary field" in INSTRUCTIONS
    assert "repeat the source wording verbatim" in INSTRUCTIONS
    assert "commentary is not an experimental method" in INSTRUCTIONS


def test_large_intermediate_packets_reduce_via_bounded_evidence_units():
    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", i, "Supported finding " * 50 + ". Another result " * 50 + ".")
              for i in range(2)]
    prompts = []
    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            prompts.append(prompt)
            ref = re.findall(r"chunk_[0-9a-f]+", prompt)[0]
            if "Operation: extract" in prompt:
                ids = list(dict.fromkeys(re.findall(r"sentence_[0-9a-f]+", prompt)))
                result = answer(ref, ids[0])
                result["main_claims"].extend({"text": key} for key in ids[1:])
                return result
            return answer(ref, re.findall(r"sentence_[0-9a-f]+", prompt)[0])
    generator = Generator(Settings(context_tokens=11000, output_tokens=1000), Service(),
                          normalizer=lambda *_: [])
    card = generator.card("doc_test", chunks)
    assert card.main_claims
    assert len(prompts) > len(chunks)
    assert all(generator.fits(p) for p in prompts)


def test_selected_source_sentences_preserve_qualifiers_and_reject_inventions():
    from rq_generator.generation import Generator

    source = "The mutation rate appears to be constant under these conditions."
    chunk = make_chunk("doc_test", 0, source)

    class Service:
        invent = False

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            ids = re.findall(r'sentence_[0-9a-f]+', prompt)
            assert ids, "Extraction must supply Python-generated source sentence IDs"
            result = answer(chunk.chunk_id, "sentence_invented" if self.invent else ids[0])
            result["summary"]["findings"] = ids[0]
            return result

    service = Service()
    generator = Generator(Settings(), service, normalizer=lambda *_: [])
    card = generator.card("doc_test", [chunk])
    assert card.main_claims[0].text == source
    assert card.main_claims[0].chunk_id == [chunk.chunk_id]
    assert card.summary.findings == source
    service.invent = True
    with pytest.raises(ValueError, match="sentence"):
        generator.card("doc_test", [chunk])


def test_oversized_complete_sentence_fails_without_clipping_source():
    from rq_generator.generation import Generator

    class Service:
        def generate(self, *_):
            pytest.fail("An oversized full sentence must never be sent")

    chunk = make_chunk("doc_test", 0, "A qualified source " * 10000)
    with pytest.raises(ValueError, match="complete source sentence"):
        Generator(Settings(context_tokens=10000, output_tokens=1000), Service(),
                  normalizer=lambda *_: []).card("doc_test", [chunk])


def test_consolidation_cannot_select_sentence_from_another_group():
    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", i, "A qualified source finding.") for i in range(2)]

    class Service:
        prior = None

        def generate(self, prompt, _):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            key = re.findall(r"sentence_[0-9a-f]+", prompt)[0]
            ref = re.findall(r"chunk_[0-9a-f]+", prompt)[0]
            if self.prior is None:
                self.prior = key
            elif "Operation: extract" in prompt:
                key = self.prior
            return answer(ref, key)

    with pytest.raises(ValueError, match="source sentence"):
        Generator(Settings(), Service(), normalizer=lambda *_: []).card("doc_test", chunks)


def test_request_schema_constrains_compact_sentence_ids_at_every_stage():
    import json

    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", i, "The rate appears stable. A second finding may hold.")
              for i in range(3)]
    operations = []

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            data = json.loads(prompt.split("Evidence:\n", 1)[1])
            sentences = data if isinstance(data, list) else data["sentences"]
            expected = {sentence["sentence_id"] for sentence in sentences}
            assert set(schema["$defs"]["SourceSentence"]["enum"]) == expected
            assert all(re.fullmatch(r"sentence_\d+", key) for key in expected)
            assert set(schema["$defs"]["SourceChunk"]["enum"]) == {
                sentence["chunk_id"] for sentence in sentences}
            assert "chunk_id" not in schema["$defs"]["SelectedClaim"]["properties"]
            assert "chunk_id" not in schema["$defs"]["SelectedQuestion"]["properties"]
            assert schema["$defs"]["SelectedClaim"]["properties"]["text"] == {
                "$ref": "#/$defs/SourceSentence"}
            assert schema["$defs"]["Summary"]["properties"]["findings"] == {
                "anyOf": [{"$ref": "#/$defs/SourceSentence"}, {"type": "null"}]}
            operations.append("consolidate" if isinstance(data, dict) else "extract")
            return answer(sentences[0]["chunk_id"], sentences[0]["sentence_id"])

    generator = Generator(Settings(), Service(), normalizer=lambda *_: [])
    card = generator.card("doc_test", chunks)
    assert set(operations) == {"extract", "consolidate"}
    assert card.main_claims[0].text == "The rate appears stable."


def test_entity_only_reduction_schema_never_contains_empty_enum():
    from rq_generator.generation import Generator

    generator = Generator(Settings(), None, normalizer=lambda *_: [])
    packet = answer("chunk_test")
    packet["main_claims"] = []
    packet["entity_mentions"] = [{"mention": "DNA repair", "chunk_id": ["chunk_test"]}]
    prompt = generator.prompt([packet], "consolidate")
    schema = generator.request_schema(prompt)
    assert schema["properties"]["main_claims"]["maxItems"] == 0
    assert all(field == {"type": "null"}
               for field in schema["$defs"]["Summary"]["properties"].values())
    import json

    assert '"enum": []' not in json.dumps(schema)


def test_scientific_abbreviations_and_citations_remain_complete_sentences():
    from rq_generator.generation import Generator

    sentences = [
        "Radicella et al. (21 Apr., p. 418) report that reversion may increase.",
        "E. coli was studied by Dr. Smith.",
        "It remains unclear why.",
    ]
    chunk = make_chunk("doc_test", 0, " ".join(sentences))
    generator = Generator(Settings(), None, normalizer=lambda *_: [])
    segments = generator._segments([chunk])
    assert [sentence["text"] for segment in segments for sentence in segment] == sentences


def test_questions_require_explicit_unresolved_source_and_render_rationale():
    import json

    from rq_generator.generation import Generator

    unresolved = "It remains unclear which host factor changes the mutation rate."
    chunk = make_chunk("doc_test", 0, unresolved)

    class Service:
        invented = False

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            sentence = json.loads(prompt.split("Evidence:\n", 1)[1])[0]
            result = answer(chunk.chunk_id, sentence["sentence_id"])
            result["candidate_research_questions"] = [{
                "question": "Which host factor changes the mutation rate?",
                "rationale": "The source proves host factors cause mutation" if self.invented
                             else sentence["sentence_id"],
            }]
            return result

    service = Service()
    generator = Generator(Settings(), service, normalizer=lambda *_: [])
    card = generator.card("doc_test", [chunk])
    assert card.candidate_research_questions[0].rationale == unresolved
    service.invented = True
    with pytest.raises(ValueError, match="unresolved"):
        generator.card("doc_test", [chunk])


def test_answered_source_disallows_questions_in_model_schema():
    import json

    from rq_generator.generation import Generator

    chunk = make_chunk("doc_test", 0, "During prolonged incubation, reversion increases 50-fold.")

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            assert schema["properties"]["candidate_research_questions"]["maxItems"] == 0
            sentence = json.loads(prompt.split("Evidence:\n", 1)[1])[0]
            return answer(chunk.chunk_id, sentence["sentence_id"])

    assert Generator(Settings(), Service(), normalizer=lambda *_: []).card(
        "doc_test", [chunk]).candidate_research_questions == []


def test_selection_prompt_rejects_introductory_claims_revised_by_conclusion():
    from rq_generator.generation import INSTRUCTIONS

    assert "prioritize the final conclusions" in INSTRUCTIONS
    assert "later revised, qualified, or refuted" in INSTRUCTIONS
    assert "introductory" in INSTRUCTIONS


def test_sentence_selection_derives_claim_and_question_evidence_in_python():
    import json

    from rq_generator.generation import Generator

    chunk = make_chunk("doc_test", 0, "It remains unclear which factor controls mutation.")

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            sentence = json.loads(prompt.split("Evidence:\n", 1)[1])[0]
            return {
                "main_claims": [{"text": sentence["sentence_id"]}],
                "summary": dict.fromkeys(["findings", "methods", "conditions", "limitations", "entities"]),
                "entity_mentions": [],
                "candidate_research_questions": [{"question": "Which factor controls mutation?",
                                                  "rationale": sentence["sentence_id"]}],
            }

    card = Generator(Settings(), Service(), normalizer=lambda *_: []).card("doc_test", [chunk])
    assert card.main_claims[0].chunk_id == [chunk.chunk_id]
    assert card.candidate_research_questions[0].chunk_id == [chunk.chunk_id]


def test_reducer_omits_derived_refs_and_deduplicates_equal_units():
    import json

    from rq_generator.generation import Generator
    from rq_generator.models import Generated

    generator = Generator(Settings(), None, normalizer=lambda *_: [])
    generator.sentences = {"sentence_0": {"sentence_id": "sentence_0", "chunk_id": "chunk_test",
                                         "text": "A finding appears supported."}}
    data = answer("chunk_test", "sentence_0")
    data["main_claims"][0]["chunk_id"] = ["chunk_test"]
    packet = Generated.model_validate(data)
    units = generator._units([packet, packet])
    assert len(units) == 1
    evidence = json.loads(generator.prompt([packet.model_dump()], "consolidate").split("Evidence:\n", 1)[1])
    assert "chunk_id" not in evidence["candidates"][0]["main_claims"][0]


def test_reduction_retains_all_extracted_entities_without_model_repetition():
    import json

    from rq_generator.entities import Vocabulary
    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", i, "DNA repair appears protective.") for i in range(2)]
    vocabulary = Vocabulary()
    vocabulary.add("GO", "DNA repair")

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            data = json.loads(prompt.split("Evidence:\n", 1)[1])
            sentences = data if isinstance(data, list) else data["sentences"]
            result = answer(sentences[0]["chunk_id"], sentences[0]["sentence_id"])
            if isinstance(data, list):
                result["entity_mentions"] = [{"mention": "DNA repair",
                                               "chunk_id": [sentences[0]["chunk_id"]]}]
            else:
                assert schema["properties"]["entity_mentions"]["maxItems"] == 0
                assert all(not packet["entity_mentions"] for packet in data["candidates"])
            return result

    card = Generator(Settings(), Service(), vocabulary.normalize).card("doc_test", chunks)
    assert len(card.entities) == 1
    assert card.entities[0].normalized_name == "DNA repair"
    assert card.entities[0].chunk_id == sorted(chunk.chunk_id for chunk in chunks)


def test_sanitized_captured_packet_shapes_fit_pairwise_for_reduction():
    from rq_generator.generation import Generator

    generator = Generator(Settings(context_tokens=16384, output_tokens=4096), None,
                          normalizer=lambda *_: [])
    packets = []
    generator.sentences = {}
    ordinal = 0
    for index, (claims, mentions, summaries) in enumerate(
        zip([7, 9, 5, 9, 2], [8, 14, 6, 1, 6], [2, 2, 3, 1, 2], strict=True)
    ):
        ref = "chunk_" + str(index) * 64
        data = answer(ref)
        data["main_claims"] = []
        ids = []
        for _ in range(claims):
            key = f"sentence_{ordinal}"
            ordinal += 1
            ids.append(key)
            generator.sentences[key] = {"sentence_id": key, "chunk_id": ref,
                                        "text": "A source finding appears supported under explicit "
                                                "conditions. " * 3}
            data["main_claims"].append({"text": key, "chunk_id": [ref]})
        for field, key in zip(list(data["summary"])[:summaries], ids, strict=False):
            data["summary"][field] = key
        data["entity_mentions"] = [{"mention": f"biomedical term {i}", "chunk_id": [ref]}
                                    for i in range(mentions)]
        packets.append(data)
    assert all(generator.fits(generator.prompt(packets[i:i + 2], "consolidate"))
               for i in range(len(packets) - 1))


def test_entity_extraction_instruction_is_separate_from_empty_reducer_output():
    from rq_generator.generation import Generator

    generator = Generator(Settings(), None, normalizer=lambda *_: [])
    extract = generator.prompt([{"sentence_id": "sentence_0", "chunk_id": "chunk_test",
                                 "text": "DNA repair occurs in Escherichia coli."}], "extract")
    assert "Extract explicit biomedical entity mentions" in extract
    assert "entity_mentions=[]" not in extract
    packet = answer("chunk_test")
    packet["main_claims"] = []
    reduce = generator.prompt([packet], "consolidate")
    assert "entity_mentions=[]" in reduce


def compression_fixture(noncompressing=False):
    import json

    from rq_generator.generation import Generator
    from rq_generator.models import Generated

    class Service:
        prompts = []

        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            self.prompts.append(prompt)
            data = json.loads(prompt.split("Evidence:\n", 1)[1])
            claims = data["candidates"][0]["main_claims"]
            limit = len(claims) if noncompressing else data["claim_limit"]
            return {"main_claims": claims[:limit]}

    service = Service()
    generator = Generator(Settings(context_tokens=16384, output_tokens=4096), service,
                          normalizer=lambda *_: [])
    generator.call_limit = 10
    packets = []
    for index, count in enumerate([8, 19]):
        ref = "chunk_" + str(index) * 64
        packet = answer(ref)
        packet["main_claims"] = []
        for ordinal in range(count):
            key = f"sentence_{index * 20 + ordinal}"
            generator.sentences[key] = {
                "sentence_id": key, "chunk_id": ref,
                "text": "A source finding appears supported under explicit conditions " * 2 + ".",
            }
            packet["main_claims"].append({"text": key, "chunk_id": [ref]})
        packet["summary"]["findings"] = packet["main_claims"][0]["text"]
        packets.append(Generated.model_validate(packet))
    return generator, service, packets


def test_adaptive_compression_preserves_summary_and_reduces_stalled_packet_bytes():
    generator, service, packets = compression_fixture()
    assert all(generator.fits(generator.prompt([p.model_dump()], "consolidate")) for p in packets)
    assert not generator.fits(generator.prompt([p.model_dump() for p in packets], "consolidate"))
    reduced = [generator._compress(packet) for packet in packets]
    assert [len(p.main_claims) for p in reduced] == [4, 9]
    assert [p.summary for p in reduced] == [p.summary for p in packets]
    assert generator.fits(generator.prompt([p.model_dump() for p in reduced], "consolidate"))
    assert all(generator.fits(prompt) for prompt in service.prompts)
    assert generator.calls == 2
    for before, after in zip(packets, reduced, strict=True):
        assert generator.request_bytes(generator.prompt([after.model_dump()], "consolidate")) < (
            generator.request_bytes(generator.prompt([before.model_dump()], "consolidate")))
        assert {p.text for p in after.main_claims} <= {p.text for p in before.main_claims}


def test_noncompressing_model_is_rejected_without_retry_loop():
    generator, service, packets = compression_fixture(noncompressing=True)
    with pytest.raises(ValueError, match="Compression"):
        generator._compress(packets[0])
    assert generator.calls == 1
    assert len(service.prompts) == 1


def test_many_chunks_use_adaptive_compression_with_bounded_requests():
    import json

    from rq_generator.generation import Generator

    chunks = [make_chunk("doc_test", index, "A cautious finding appears supported under "
                         "these conditions " * 10 + ".") for index in range(20)]
    prompts = []
    compression_calls = []

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                return retained_review(prompt)
            prompts.append(prompt)
            data = json.loads(prompt.split("Evidence:\n", 1)[1])
            if isinstance(data, list):
                ids = [sentence["sentence_id"] for sentence in data]
            else:
                ids = list(dict.fromkeys(claim["text"] for packet in data["candidates"]
                                         for claim in packet["main_claims"]))
            claims = [{"text": key} for key in ids]
            if isinstance(data, dict) and "claim_limit" in data:
                compression_calls.append(prompt)
                assert schema["properties"]["main_claims"]["maxItems"] == data["claim_limit"]
                return {"main_claims": claims[:data["claim_limit"]]}
            result = answer(chunks[0].chunk_id)
            result["main_claims"] = claims
            return result

    generator = Generator(Settings(context_tokens=10000, output_tokens=1000), Service(),
                          normalizer=lambda *_: [])
    card = generator.card("doc_test", chunks)
    assert compression_calls
    assert 0 < len(card.main_claims) < len(chunks)
    assert all(generator.fits(prompt) for prompt in prompts)
    assert generator.calls < generator.call_limit
    assert all(chunk.chunk_id in " ".join(prompts) for chunk in chunks)
    assert all(claim.chunk_id[0] in {chunk.chunk_id for chunk in chunks}
               for claim in card.main_claims)


def test_compression_rejects_source_substitution_without_mutating_packet():
    generator, service, packets = compression_fixture()
    before = packets[0].model_dump()
    service.generate = lambda *_: {"main_claims": [{"text": "sentence_invented"}]}
    with pytest.raises(ValueError, match="invented"):
        generator._compress(packets[0])
    assert packets[0].model_dump() == before
    assert generator.calls == 1


def test_single_packet_final_selection_omits_superseded_introductory_claim():
    import json

    from rq_generator.entities import Vocabulary
    from rq_generator.generation import Generator

    intro = "There is one noticeable exception to this rule, the F episome."
    conclusion = "The overall rate appears to conform to the rule rather than provide an exception."
    chunk = make_chunk("doc_test", 0, intro + " Escherichia coli was studied. " + conclusion)
    vocabulary = Vocabulary()
    vocabulary.add("MeSH", "Escherichia coli")
    operations = []

    class Service:
        def generate(self, prompt, schema):
            operations.append(prompt.split("Operation: ", 1)[1].split("\n", 1)[0])
            data = json.loads(prompt.split("Evidence:\n", 1)[1])
            sentences = data if isinstance(data, list) else data["sentences"]
            keys = {s["text"]: s["sentence_id"] for s in sentences}
            result = answer(chunk.chunk_id, keys[conclusion])
            result["summary"]["findings"] = keys[conclusion]
            if operations[-1] == "extract":
                result["main_claims"].insert(0, {"text": keys[intro]})
                result["summary"]["findings"] = keys[intro]
                result["summary"]["conditions"] = keys[intro]
                result["summary"]["entities"] = keys["Escherichia coli was studied."]
                result["entity_mentions"] = [{"mention": "Escherichia coli",
                                              "chunk_id": [chunk.chunk_id]}]
            else:
                assert intro in keys and conclusion in keys
                assert "Escherichia coli was studied." in keys
                return {"assessments": {keys[intro]: keys[conclusion], keys[conclusion]: None}}
            return result

    generator = Generator(Settings(), Service(), vocabulary.normalize)
    card = generator.card("doc_test", [chunk])
    assert [claim.text for claim in card.main_claims] == [conclusion]
    assert card.summary.findings == conclusion
    assert card.summary.conditions is None
    assert card.summary.entities == "Escherichia coli was studied."
    assert card.main_claims[0].chunk_id == [chunk.chunk_id]
    assert card.entities[0].normalized_name == "Escherichia coli"
    assert card.entities[0].chunk_id == [chunk.chunk_id]
    assert operations == ["extract", "review"]
    assert generator.calls < generator.call_limit


@pytest.mark.parametrize("assessments", [
    {},
    {"sentence_1": None, "sentence_invented": None},
    {"sentence_1": "sentence_invented"},
    {"sentence_1": "sentence_1"},
    {"sentence_1": "sentence_0"},
])
def test_final_claim_review_rejects_missing_duplicate_or_invalid_resolution(assessments):
    from rq_generator.generation import Generator

    chunk = make_chunk("doc_test", 0, "A preliminary observation. A final result may hold.")

    class Service:
        def generate(self, prompt, schema):
            if "Operation: review" in prompt:
                assert schema["properties"]["assessments"]["required"] == ["sentence_1"]
                assert schema["properties"]["assessments"]["properties"]["sentence_1"] == {
                    "type": "null"}
                return {"assessments": assessments}
            return answer(chunk.chunk_id, "sentence_1")

    with pytest.raises(ValueError, match="Review"):
        Generator(Settings(), Service(), normalizer=lambda *_: []).card("doc_test", [chunk])
