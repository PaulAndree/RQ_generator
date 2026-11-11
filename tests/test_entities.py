"""Validate official-name matching, ambiguity, and explicit source mentions."""

from rq_generator.entities import Vocabulary
from rq_generator.models import Mention
from rq_generator.storage import make_chunk


def test_normalization_supported_aliases_and_vocabulary_overlap():
    vocabulary = Vocabulary()
    vocabulary.add("GO", "DNA repair", ["repair of DNA"])
    vocabulary.add("MeSH", "DNA Repair", [])
    vocabulary.add("HGNC", "TP53", ["P53"])
    chunks = [make_chunk("doc_test", 0, "DNA repair involves TP53 and P53.")]
    mentions = [
        Mention(mention=term, chunk_id=[chunks[0].chunk_id])
        for term in ["DNA repair", "P53", "invented"]
    ]
    entities = vocabulary.normalize(mentions, chunks)
    assert {(e.group, e.normalized_name) for e in entities} == {
        ("GO", "DNA repair"),
        ("MeSH", "DNA Repair"),
        ("HGNC", "TP53"),
    }
    assert all(e.chunk_id == [chunks[0].chunk_id] for e in entities)


def test_ambiguous_aliases_case_and_explicit_evidence():
    vocabulary = Vocabulary()
    vocabulary.add("HGNC", "GENE1", ["SHARED"])
    vocabulary.add("HGNC", "GENE2", ["SHARED"])
    vocabulary.add("HGNC", "TP53")
    chunk = make_chunk("doc_test", 0, "SHARED, tp53 and XTP53 are mentioned.")
    mentions = [Mention(mention=term, chunk_id=[chunk.chunk_id]) for term in ["SHARED", "TP53"]]
    assert vocabulary.normalize(mentions, [chunk]) == []


def test_reference_load_filters_go_namespace(tmp_path):
    from rq_generator.entities import parse_obo

    source = tmp_path / "go.obo"
    source.write_text("""format-version: 1.2
data-version: test-release

[Term]
id: GO:1
name: DNA repair
namespace: biological_process
synonym: "repair of DNA" EXACT []

[Term]
id: GO:2
name: binding
namespace: molecular_function

[Term]
id: GO:3
name: obsolete process
namespace: biological_process
is_obsolete: true
""")
    vocabulary = Vocabulary()
    parse_obo(source, "GO", vocabulary)
    chunk = make_chunk("doc_test", 0, "repair of DNA binding obsolete process")
    entities = vocabulary.normalize(
        [
            Mention(mention=t, chunk_id=[chunk.chunk_id])
            for t in ["repair of DNA", "binding", "obsolete process"]
        ],
        [chunk],
    )
    assert [(e.group, e.normalized_name) for e in entities] == [("GO", "DNA repair")]


def test_reference_provenance_and_offline_failure(tmp_path, monkeypatch):
    import hashlib
    import json

    import pytest

    import rq_generator.entities as entities

    sources = {
        "go.obo": "[Term]\nid: GO:1\nname: DNA repair\nnamespace: biological_process\n",
        "cl.obo": "[Term]\nid: CL:1\nname: T cell\n",
        "mesh.xml": "<DescriptorRecordSet><DescriptorRecord><DescriptorName>"
                    "<String>DNA Repair</String></DescriptorName></DescriptorRecord></DescriptorRecordSet>",
        "hgnc.tsv": "symbol\tstatus\talias_symbol\tprev_symbol\nTP53\tApproved\tP53\t\n",
    }
    for name, content in sources.items():
        (tmp_path / name).write_text(content)
    vocabulary = entities.load_vocabulary(tmp_path)
    provenance = json.loads((tmp_path / "provenance.json").read_text())
    assert len(vocabulary.terms) > 0
    assert {p["file"] for p in provenance} == set(sources)
    for record in provenance:
        assert record["sha256"] == hashlib.sha256((tmp_path / record["file"]).read_bytes()).hexdigest()
        assert record["url"] == entities.SOURCES[record["file"]]
    (tmp_path / "go.obo").unlink()

    def unavailable(*args):
        raise OSError("offline reference unavailable")

    monkeypatch.setattr(entities, "_download", unavailable)
    with pytest.raises(OSError, match="offline reference"):
        entities.load_vocabulary(tmp_path)
