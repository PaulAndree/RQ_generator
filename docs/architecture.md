# Architecture and application requirements

This document describes the application scope and architectural constraints.
Use it alongside Instructions.md, project conventions, and the approved
feature specification.

If these documents conflict, report the conflict before implementing the
affected behavior. Do not silently discard requirements.

## 1. Objective

Given a directory of scientific PDFs, produce extracted chunks and one
evidence-linked card for each successfully processed document.

## 2. Scope

Includes:

- PDF discovery.
- Integration with the existing OCR and section-aware chunking services.
- Central claim extraction.
- Biomedical entity extraction.
- Document-card and candidate research-question generation.
- Output validation and persistence.

Cross-document discovery and ranking are deferred.

## 3. Inputs and outputs

The PDF directory is the only required data input.
Create intermediate representations internally.

Read service endpoints and model settings from configuration.
Use the configured Ollama Qwen3:14b model for generation.

Outputs:

- chunks.json: extracted chunks and source metadata.
- document_cards.json: an object containing a cards array.

Use a default output directory and allow an optional output-path override.

## 4. Application requirements

### IN-001: Deterministic discovery

Discover PDFs in the supplied directory and process them in a defined,
deterministic order.

### CLAIM-001: Evidence-linked claims

Each retained claim must have:

- A claim ID assigned by Python.
- Nonempty claim text.
- At least one supporting chunk reference.

Every supporting chunk must belong to the same document as the claim.

A chunk with no supported central claim may produce zero claims.
Preserve the claim as stated in the source, including scientific uncertainty
and study conditions. Do not invent findings or evidence.

### ENTITY-001: Biomedical entities

Extract biomedical entities explicitly mentioned in the chunks.

Assign each entity to one or more supported vocabulary groups:

- GO: biological processes only.
- MeSH: biomedical concepts matching a MeSH term.
- Cell Ontology: cell types.
- HGNC: human genes, including aliases that map unambiguously to an
  approved gene symbol.

Each entity includes group and normalized_name.
Use the official term or gene symbol for normalized_name.

When a mention clearly matches more than one vocabulary, return a separate
object for each group. Skip ambiguous or unsupported matches.

The entity evidence-reference format remains an open schema decision.

### CARD-001: One card per successful document

Each successfully processed PDF contributes exactly one card.

Each card contains:

- doc_id
- main_claims
- summary
- entities
- candidate_research_questions

The current architecture describes summary fields as findings, entities,
and methods. Instructions.md instead specifies findings, methods,
conditions, and limitations.

Resolve this difference before implementing the card schema.
Use null for unsupported summary fields in the approved schema.

### CARD-002: Research questions

Each card contains zero to five candidate research questions.

Each question contains:

- question
- rationale
- Supporting chunk references.

Questions must be specific, investigable, and motivated by the document.
They must address an unresolved issue rather than restate a question the
document already answers.

Do not invent supporting evidence or references.

### REF-001: Identifiers and referential integrity

Generate stable document and chunk IDs.
Define their stability guarantees in the approved feature specification.

Before publishing outputs, validate that:

- Output structures match the approved schemas.
- Every card references an existing document.
- Every claim and question evidence reference resolves to a saved chunk.
- Evidence references remain within the associated document.
- Document, chunk, and claim references are valid.
- IDs are unique within their defined scope.

### GEN-001: Bounded generation

For documents exceeding the model context window, process bounded batches
and consolidate results while preserving evidence references.

### FAIL-001: Failure isolation and progress

Log failures while processing individual PDFs and continue with subsequent
documents.

A failed PDF must not contribute a partially valid card.
Save progress after each processed PDF.

Define checkpoint and output-consistency behavior in the approved
feature specification.

## 5. Open decisions

Resolve these before implementing the affected behavior:

- Document and chunk ID stability guarantees.
- Exact chunks.json schema and source metadata.
- Service timeouts and retry policy.
- Checkpoint and output-consistency behavior.
