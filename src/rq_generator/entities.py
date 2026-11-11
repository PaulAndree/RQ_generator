"""Normalize explicit biomedical mentions against official reference releases."""

import csv
import hashlib
import os
import re
import tempfile
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

import httpx

from rq_generator.models import Entity
from rq_generator.storage import atomic_json

SOURCES = {
    "go.obo": "https://current.geneontology.org/ontology/go-basic.obo",
    "cl.obo": "https://purl.obolibrary.org/obo/cl.obo",
    "mesh.xml": "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.xml",
    "hgnc.tsv": "https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt",
}


class Vocabulary:
    def __init__(self):
        self.terms = {}
        self.provenance = []

    def add(self, group, name, aliases=()):
        for term in [name, *aliases]:
            if term:
                key = (group, term if group == "HGNC" else term.casefold())
                self.terms.setdefault(key, set()).add(name)

    def normalize(self, mentions, chunks):
        texts = {c.chunk_id: c.text for c in chunks}
        retained = {}
        for mention in mentions:
            for group in ["GO", "MeSH", "Cell Ontology", "HGNC"]:
                key = mention.mention if group == "HGNC" else mention.mention.casefold()
                names = self.terms.get((group, key), set())
                if len(names) != 1:
                    continue
                expression = r"(?<!\w)" + re.escape(mention.mention) + r"(?!\w)"
                refs = [
                    ref
                    for ref in mention.chunk_id
                    if ref in texts
                    and re.search(
                        expression,
                        texts[ref],
                        flags=0 if group == "HGNC" else re.IGNORECASE,
                    )
                ]
                if refs:
                    retained.setdefault((group, next(iter(names))), set()).update(refs)
        return [
            Entity(group=group, normalized_name=name, chunk_id=sorted(refs))
            for (group, name), refs in sorted(retained.items())
        ]


def parse_obo(path: Path, group: str, vocabulary: Vocabulary):
    prefix = "GO:" if group == "GO" else "CL:"

    def retain(term):
        if (
            term.get("id", "").startswith(prefix)
            and term.get("name")
            and term.get("is_obsolete") != "true"
            and (group != "GO" or term.get("namespace") == "biological_process")
        ):
            vocabulary.add(group, term["name"], term.get("synonyms", []))

    current = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            line = line.rstrip()
            if line.startswith("["):
                retain(current)
                current = {} if line == "[Term]" else {"is_obsolete": "true"}
            elif ": " in line:
                key, value = line.split(": ", 1)
                if key == "synonym":
                    match = re.match(r'^"(.*)" EXACT ', value)
                    if match:
                        current.setdefault("synonyms", []).append(match.group(1))
                else:
                    current[key] = value
        retain(current)


def _download(path: Path, url: str):
    fd, temporary = tempfile.mkstemp(prefix=".vocab-", dir=path.parent)
    try:
        with (
            os.fdopen(fd, "wb") as stream,
            httpx.stream("GET", url, follow_redirects=True, timeout=180) as response,
        ):
            response.raise_for_status()
            for data in response.iter_bytes():
                stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_vocabulary(directory: Path) -> Vocabulary:
    directory.mkdir(parents=True, exist_ok=True)
    vocabulary = Vocabulary()
    for name, url in SOURCES.items():
        path = directory / name
        if not path.exists():
            _download(path, url)
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        vocabulary.provenance.append(
            {
                "file": name,
                "url": url,
                "sha256": digest,
                "loaded_at": datetime.now(UTC).isoformat(),
            }
        )
    parse_obo(directory / "go.obo", "GO", vocabulary)
    parse_obo(directory / "cl.obo", "Cell Ontology", vocabulary)
    # Clear complete descriptor records while retaining child elements until read.
    for _, record in ET.iterparse(directory / "mesh.xml", events=("end",)):
        if record.tag == "DescriptorRecord":
            name = record.findtext("DescriptorName/String")
            if name:
                vocabulary.add(
                    "MeSH",
                    name,
                    [
                        n.text
                        for n in record.findall("ConceptList/Concept/TermList/Term/String")
                        if n.text
                    ],
                )
            record.clear()
    with (directory / "hgnc.tsv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream, delimiter="\t"):
            if row.get("status") == "Approved":
                aliases = (row.get("alias_symbol", "") + "|" + row.get("prev_symbol", "")).split(
                    "|"
                )
                vocabulary.add("HGNC", row["symbol"], aliases)
    if not vocabulary.terms:
        raise ValueError("Vocabulary resources contain no usable terms")
    # Preserve exact snapshots and their checksums; never silently replace releases.
    atomic_json(directory / "provenance.json", vocabulary.provenance)
    return vocabulary
