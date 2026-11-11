# Implementation tasks

Feature 1, initialize-application. Revision 1, awaiting human approval.
All tasks are pending. Do not implement until the leader records approval
of requirements.md, design.md, and this task scope.

Tests below are planned verification, not existing or passing tests.
Each implementation task follows its relevant failing-test task.

- [x] T1: Establish Python 3.12 environment from pyproject.toml; verify live
  OCR/chunking request and response contracts using a representative PDF,
  including the required OCR type_name. Record sanitized fixtures and exact
  service versions/contracts. Confirm official vocabulary release sources,
  formats, licenses, version identifiers, and checksums. Covers R3, R11, R19.
- [x] T2: Add meaningful failing tests for ordered discovery, invalid inputs,
  configuration precedence, output override, ID stability, chunk metadata,
  strict card models, reference integrity, and CLI result statuses. Assert
  actual outputs and rejected malformed/cross-document references. Covers
  R1, R2, R4, R5, R6, R8, R9, R10, R12, R15, R16, R19.
- [x] T3: Implement package entry points, validated settings, discovery, IDs,
  chunk/card schemas, and cross-reference checks. Make T2 tests pass.
  Covers R1, R2, R4, R5, R6, R8, R9, R10, R12, R15, R16, R19.
- [x] T4: Add failing service adapter tests against the verified fixtures,
  including request fields, response validation, timeouts, retry limits,
  unsupported errors, and section/page preservation. Covers R3, R6, R7, R17.
- [x] T5: Implement OCR, section-aware chunking, and configured Ollama HTTP
  clients with bounded retries. Make T4 tests pass. Covers R3, R6, R7, R17.
- [x] T6: Add failing generation tests for zero-claim chunks, exact configured
  model, Python-assigned claims, invalid evidence, question limits, scientific
  fidelity instructions, and all five summary fields. Cover oversized single
  chunks, many batches, every reduction request, oversized intermediate
  output, and failure to make reduction progress. Covers R7, R8, R9, R10,
  R12, R13, R14, R16.
- [x] T7: Implement bounded extraction and hierarchical consolidation with
  evidence-preserving segments, strict structured responses, and finite call
  budgets. Make T6 tests pass. Covers R7, R8, R9, R10, R12, R13, R14, R16.
- [x] T8: Add failing entity-normalization tests for explicit mentions,
  official names, unambiguous/ambiguous aliases, GO namespace filtering,
  vocabulary overlap, provenance, and unavailable reference resources.
  Implement versioned official reference loading/cache and validated entity
  lookup after demonstrating those failures. Covers R11, R13, R16.
- [x] T9: Add failing normal-entry-point and checkpoint tests with multiple
  PDFs, an empty directory, and OCR/chunking/generation/validation failures
  in a middle document. Inject crashes and write failures around every file
  replacement, including a preexisting output pair with different input
  paths/content, concurrent writer detection, and recovery after the writer
  process dies without manually deleting its lock file. Assert parseable files,
  no dangling references, no partial cards, deterministic order, correct
  attempt statuses, and a fatal exit on persistence failure. Covers R1, R3,
  R6, R9, R15, R16, R17, R18, R19.
- [x] T10: Implement the sequential pipeline, single-writer lock, ordered
  atomic output replacement, fresh-run policy, cumulative chunks/cards,
  and run_state.json. Make T9 tests pass. Covers R1, R3, R6, R9, R15, R16,
  R17, R18, R19.
- [x] T11: Add failing tests for JSON log fields/redaction, stable low-cardinality
  metrics, card metadata events, opt-in content events, Langfuse observations
  and flush, retry/error traces, and independent telemetry outages. Assert
  that no prompt/response/document text is emitted by default and that
  backend failures leave processing outputs valid. Covers R20, R21, R22,
  R23, R24, R25.
- [x] T12: Implement logging, bounded Loki delivery, batch Pushgateway metrics,
  optional Langfuse integration, and the version-controlled Grafana dashboard
  with card IDs/counts/status, logs, aggregate metrics, and opt-in text.
  Make T11 tests pass and validate dashboard JSON and queries. Covers R20,
  R21, R22, R23, R24, R25.
- [x] T13: Add non-secret .env.example settings and concise README usage,
  output schema/ID guarantees, fresh-run policy, vocabulary resources,
  telemetry privacy and installation, dashboard provisioning, and checks.
  Install the package in the task environment and verify both console and
  module entry points, documented help, and configuration examples.
  Covers R4, R5, R18, R19, R20, R21, R22, R23, R24.
- [x] T14: Run the complete unit suite and configured lint checks on Python
  3.12. Record commands, exit codes, test counts, initial failing evidence,
  and requirement-to-assertion mappings in progress/impl_initialize-application.md.
  Zero collected tests or skipped integration checks do not prove behavior.
  Covers R1 through R25.
- [x] T15: Confirm actual shared-service targets, then run the installed CLI
  on representative scientific PDFs with real OCR, section-aware chunking,
  qwen3:14b, and official vocabularies. Include a long multi-batch PDF and
  a controlled failed PDF between successes. Inspect output schemas,
  reference integrity, one card per success, unsupported summary fields,
  scientific uncertainty, entities, and unresolved research questions.
  Record specific source comparisons and results. Covers R1, R3, R6, R7,
  R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19.
- [x] T16: For successful and controlled failing live runs, query Loki,
  Pushgateway, and Prometheus, inspect card/log panels in shared Grafana,
  and inspect generation/error traces in Langfuse. Verify metadata-only
  defaults and deliberate opt-in full-text behavior with approved test
  content. Record dashboard identifiers, non-secret queries, timestamps,
  and observed signals. Report missing services or credentials as blocked
  acceptance checks, never as a pass. Covers R20, R21, R22, R23, R24, R25.
- [x] T17: Complete the implementation evidence report with commands,
  statuses, counts, acceptance-to-requirement-to-task-to-test/assertion
  traceability, integration observations, limitations, and the exact
  implementation content identifier. Update active progress for independent
  reviewer handoff. Covers R1 through R25.

The leader assigns the independent reviewer after implementation. PR
publication and final status bookkeeping follow review and separate delivery
authorization; neither is a prerequisite for reviewing this checklist.
