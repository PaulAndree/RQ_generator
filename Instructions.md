Build a minimal Python pipeline that accepts a folder containing scientific PDFs, iterates over each PDF, and saves the resulting document cards in one JSON file.


Instructions:

1. Discover all PDFs in the supplied directory and process them in order.

2. Reuse the existing OCR and section-aware chunking services available in the project/server.

3. Generate stable document and chunk IDs. Save the extracted chunks and their source metadata in `chunks.json`.

4. Use an Ollama Qwen3:14b model to extract the central claims for each chunk if exists and generate one compact card per document. Assign claim IDs in Python and retain their supporting chunk IDs.

5. Save all cards in `document_cards.json`, following the accompanying card example:
   - Root: `{"cards": [...]}`.
   - `doc_id`: stable document identifier.
   - `main_claims`: central claims with `claim_id` and `chunk_id` evidence references.
   - `summary`: `findings`, `methods`, `conditions`, and `limitations`, forming an abstract-like summary.
   - `candidate_research_questions`: maximum five per document, each containing `question`, `rationale`, and supporting `chunk_id` references.

Generation rules:
- Preserve scientific uncertainty and study conditions.
- Use `null` for unsupported summary fields.
- Generate specific, investigable questions motivated by the document.
- Avoid questions already answered by the document.
- Do not invent findings, evidence, or references.
- For documents exceeding the model context window, process bounded batches and consolidate results while preserving evidence references.

Implementation:
- The PDF directory is the only required data input; create all intermediate representations internally.
- Configure service URLs and the Ollama model through environment variables or optional flags.
- Save outputs in a default output directory, with an optional output-path override.
- Validate JSON structure and all document, chunk, and claim references.
- Save progress after each PDF. Log failures and continue with the remaining documents.
- Include the executable script, dependencies, configuration example, and short usage instructions.

Implement this folder-to-document-cards stage. Cross-document discovery and ranking will be added afterward.