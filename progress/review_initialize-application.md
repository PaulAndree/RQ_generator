# Feature 1 implementation review

Verdict: APPROVED

## Current review identity

- Feature: 1, initialize-application, status in_progress.
- Worktree: /tmp/rq-initialize-application-1110a.
- Branch: agent/initialize-application-1110a.
- Review date: 2026-11-11, Europe/Madrid.
- Base and HEAD: 6b9de636dfb838a9d1543dcbf8baa20c2761428b.
- All implementation changes are uncommitted. Approved implementation content
  SHA-256: 678c5c1a9fc128a887df65c03e304090a02b21b861e8188938dd7b48864ac072.
  Independently verified all 24 paths and their hashes in
  .artifacts/initialize-application/final-implementation-manifest.json, then
  recomputed the canonical manifest digest. Source, tests, scripts, monitoring,
  README.md, pyproject.toml, uv.lock and .env.example are covered. Progress and
  specification records were also inspected; their administrative edits do not
  change this implementation digest.
- Specification revision 1 remains approved. Recomputed requirements/design/task
  hashes match the values recorded in the historical review below, normalizing
  only task completion checkboxes. No substantive specification changed.
- User authorization covers delivery and PR publication. It does not cover merging.

## Renewed findings and verdict

F1 is corrected. A complete-source review now runs after single-segment extraction.
Its structured response must assess every candidate exactly once and can only
name a later supplied source sentence as the resolution, or null. Python rejects
missing/extra candidates and unknown, self or earlier resolving references. It
omits superseded claims, replaces affected findings with the resolving sentence,
and clears other superseded summary selections. Supported unchanged summaries,
all extracted entity evidence and exact source rendering remain intact. Both the
review request and response validation use the existing finite call and complete
payload budgets. The multisegment path is unchanged.

The new test_single_packet_final_selection_omits_superseded_introductory_claim
asserts the produced card rather than prompt wording. Its extraction double
returns the introductory exception and final qualified conclusion, then the
review resolves the former to the latter. Assertions check omission, qualified
conclusion, updated findings, cleared superseded conditions, unchanged supported
entity summary and normalized entity evidence. Five parameterized negative cases
reject incomplete/extra candidate assessments and invalid resolution references.
Original pipeline, outage and failure-isolation assertions remain present after
service doubles were adapted to the new review response schema.

Independently compared the corrected complete A.pdf source, extraction/review
requests and responses, and persisted card. Run
6d16245fb71940ed946492b51173d342, environment integration-review-delivery,
produced one card with four claims and three official entities. The introductory
exception is absent; the general rule retains "appears", its interpretation
retains "likely", life-cycle dependence remains, and the conclusion retains
"appears to conform". Every claim and non-null summary is an exact complete
source sentence. Methods and limitations are null and questions are empty.
MeSH Bacteria, Escherichia coli and Yeasts have explicit source mentions and
same-document evidence. The review assessment maps sentence_2 to sentence_10;
all other candidate assessments are null. The review prompt includes the entire
single-segment source in source order. Input PDF hash and saved chunk match the
original A input/source, so this is a recheck of the failure rather than a changed
fixture or manually edited output. The diagnostic CLI wrapper calls real
Services/Generator and does not alter generation decisions.

F2 is corrected. The updated implementation report identifies the first A result
as rejected history, records the successful corrected A result and current digest,
and removes stale T15/T16 and publication restrictions. Current acceptance results
and remaining workflow steps are consistent.

No unresolved correction or verification blocker remains for this content.
Approval applies to this implementation identity. Subsequent application, test,
configuration or executable documentation changes need renewed review.

## Renewed executed checks

All checks ran in the assigned worktree with its Python 3.12 environment.

| Command or check | Exit | Observed result |
| --- | --- | --- |
| .venv/bin/python -m pytest -q | 0 | 87 passed in 9.93 seconds, no skips |
| .venv/bin/ruff check src tests scripts | 0 | All checks passed |
| git diff --check | 0 | No whitespace errors |
| .venv/bin/python tests/integration/check_live_outputs.py .artifacts/initialize-application/review-delivery-output --environment integration-review-delivery | 0 | 1 card, 1 chunk, Loki card/run events, Prometheus successes=1, 2 real qwen3:14b generations with usage, no content, no error observations |
| Independent manifest/specification digest check | 0 | All 24 implementation files and revision 1 specification hashes match |
| Independent source/input/request/reference assertions | 0 | 4 faithful claims, contradiction omitted, complete source supplied to review, valid saved references and matching input/source identities; extraction 7702 bytes and review 5300 bytes, both within 11264 |

The original successful multibatch C, controlled failed B, model-error usage,
Grafana panels and explicit opt-in privacy checks were independently verified in
the first review and remain applicable to unchanged paths. The only application
changes since that baseline are services.py usage-before-length-error handling,
already reviewed and tested against a real failure, and the generation.py
single-segment review now exercised by real A. Unchanged telemetry and multisegment
processing do not require another full twelve-minute model run. The updated full
suite verifies their regressions with the new code present.

## Acceptance traceability and task completion

The independent acceptance-to-requirement-to-task-to-assertion table in the
historical review remains the detailed mapping. Its previous scientific-fidelity
gap is closed by the behavior regression, validation cases and corrected real A
source comparison above. The six added test cases cover R7/R8/R10/R13/R14/R16
and T6/T7/T14/T15/T17. Updated service doubles preserve earlier runtime assertions.
All five acceptance criteria have applicable unit, normal-entry-point and live
integration evidence. R1-R25 and T1-T17 have no unresolved coverage or completion
gap identified by this review.

The implementation report's recorded initial failing tests were inspected; this
review did not revert code to recreate them. The real-source verification uses
the implementer's saved current run and independently validates the full artifacts
and delivered backends. The reviewer did not initiate another generation run.
Grafana verification uses authenticated dashboard queries and configuration,
not a browser screenshot. These limits do not leave a required acceptance check
unverified.

Scientific selection can still vary for future documents; exact quotations alone
do not guarantee semantic correctness. The approved result is supported by the
required representative scientific source review, including correction of the
specific contradiction found. Oversized complete sentences or nonprogressing
reductions fail visibly within bounded limits as documented. No requirement is
waived and no shared infrastructure was changed during review.

Next action: leader confirms approval applies to the current content, then delegates
authorized commit, push and PR creation to the implementer. Finalization follows
authorized delivery. Do not merge the PR.

# Historical first review

Historical verdict: CHANGES_REQUESTED, superseded by the renewed review above.

## Review identity

- Feature: 1, initialize-application, status in_progress.
- Worktree: /tmp/rq-initialize-application-1110a.
- Branch: agent/initialize-application-1110a.
- Review date: 2026-11-11, Europe/Madrid.
- Base and HEAD: 6b9de636dfb838a9d1543dcbf8baa20c2761428b.
- Implementation is uncommitted. Reviewed content SHA-256:
  9e87dce2ff8b5d7b6242a93523013a6c90c3bd0aa80ff944ff537a950bd66098.
  Independently verified all 24 file hashes in
  .artifacts/initialize-application/final-implementation-manifest.json and its
  canonical JSON digest. This covers source, tests, scripts, monitoring,
  README.md, pyproject.toml, uv.lock, and .env.example. Also reviewed the
  specifications, feature state, progress records, and relevant ignored evidence.
- Specification revision 1 approval is recorded in progress/current.md.
  Requirements SHA-256 8307e3049c00bd8d08d52c18ecb763f2844140a7bc8cbb8debb7d72869ac0068;
  design f6e6da7fb0008170597853127e4af0165d102360a9e5e7b552c2777ca76f5e9b;
  tasks with completed checkboxes normalized to unchecked
  64321b785f81151bdbfa1c3757e39cd0ccc7dfa6e46f199188fbbdee159664b0.
  These match the recorded approval. No renewed approval is needed for the
  corrections below within the existing scientific fidelity requirement.
- The user has now authorized delivery and PR publication. No PR is approved
  by this report, and no merge is authorized.

## Findings

### F1, high: A published central claim contradicts the document conclusion

Location: src/rq_generator/generation.py:317 and :366, single-segment path and
final claim rendering. Reproduction evidence is
.artifacts/initialize-application/complete-output/document_cards.json, A.pdf's
third main_claims item, claim_a98b195593135f2496141e4bb2f3da8a5ebfa9bf9cddd6856b32504c42470861.

The card publishes "There is one noticeable exception to this rule, the F episome."
as an independent main claim. The same source ends by explaining that the overall
mutation rate appears to conform to the rule rather than provide an exception.
That final sentence is also in the card. The introduction is a position the
article goes on to resolve, not a second established conclusion. Publishing both
as main findings leaves consumers with contradictory assertions and loses the
scientific qualification supplied by the document's argument.

This is a failure of R7/R13 and T15 scientific source comparison, not merely an
imperfect ranking. Exact source sentence rendering proves lexical fidelity but
does not establish support for a sentence presented as a central document claim.
For one extraction packet, card() bypasses consolidation, and the only guard
against this problem is an instruction in the extraction prompt. The existing
test_selection_prompt_rejects_introductory_claims_revised_by_conclusion asserts
prompt words only; it does not test resulting claim selection. The saved real
Qwen run demonstrates the resulting behavior despite those instructions.

Required correction: make final claim selection reject or omit introductory
positions superseded by the source conclusion while retaining that conclusion
and its uncertainty. Add a meaningful regression that exercises the resulting
behavior for this pattern, including the single-segment path. Repeat the actual
A.pdf source comparison using qwen3:14b and inspect the complete resulting card.
Preserve bounded calls, valid evidence, and entity extraction. Do not delete the
unwanted item manually from output or waive scientific fidelity as ranking noise.

### F2, medium: implementation evidence contains conflicting completion claims

Location: progress/impl_initialize-application.md:191, traceability table.

The report's outcome says no integration checks remain, but the table still says
manual scientific review is "currently failing" and that T15/T16 checks remain.
The opening publication restriction is also obsolete after the user's delivery
authorization. These contradictions make it unclear which evidence is current.

Required correction: update the report to state the final observed outcome and
remaining review status consistently after F1 is corrected. Keep historical
failures clearly identified as historical. Preserve the source-selection issue
until a new real run establishes its correction.

## Executed verification

All commands ran in the assigned worktree with the task Python 3.12 environment.

| Command or check | Exit | Observed result |
| --- | --- | --- |
| .venv/bin/python -m pytest -q | 0 | 81 passed in 9.26 seconds, no skips |
| .venv/bin/ruff check src tests scripts | 0 | All checks passed |
| git diff --check | 0 | No whitespace errors |
| .venv/bin/rq-generator --help | 0 | Installed console entry point works |
| .venv/bin/python -m rq_generator --help | 0 | Module entry point works |
| .venv/bin/python tests/integration/check_live_outputs.py .artifacts/initialize-application/complete-output --environment integration-complete | 0 | 2 cards, 5 chunks, Loki success/failure/completion events, Prometheus successes=2, 18 qwen3:14b generations, 3 OCR error observations |
| Read-only execution of check_complete_grafana.py with its evidence-file write removed | 0 | Authenticated shared Grafana 3005 queries: 2 card rows, 6 log rows, success/failure and duration/model metrics present, zero full-content rows |
| Direct authenticated Langfuse observation queries | 0 | Error run 0001c54f5ec54f12913a7faf539d187b has one ERROR generation, exact 1564 input/128 output usage, no content; prior explicit content run a724d52246084f75a2ac6736cda3feea has 10 generations with content |
| Manifest, input hashes, saved schema/reference and complete-request checks | 0 | All 24 implementation file hashes match; all 3 PDF hashes match; all 18 claims and non-null summary values are exact source sentences; 18 serialized live requests fit 11264 bytes, maximum 11104 |

The existing successful real-service run used ef55cba1a7f0457f8e5475716d98086e,
with successful A, deliberately failed B, and successful multibatch C. Inspected
its normal CLI diagnostic wrapper, saved requests/responses, output pair, state,
source text, and integration report. The wrapper captures diagnostics without
changing processing decisions. Requeried the delivered backend evidence directly.
A fresh twelve-minute full inference run was not repeated because the saved run
already reproduces F1 and delivery evidence remains queryable. A corrected A run
is required before approval. No service or monitoring infrastructure was changed.

## Independent acceptance traceability

Inspected assertions rather than relying on test names or completed checkboxes.

| Acceptance and requirements | Tasks | Assertions and evidence assessed |
| --- | --- | --- |
| Ordered PDF discovery and service processing, R1-R6/R17-R19 | T1-T5, T9-T10, T13-T15 | test_discovery_filters_and_orders excludes symlinks/subdirectories and sorts mixed-case names. CLI tests inspect OCR call order, saved documents/cards and success/failed/success state. ID tests change bytes, names, ordinals, metadata and roots. Adapter tests assert actual multipart/form routes and metadata; real saved inputs and outputs verify those contracts. |
| Qwen central claims and compact cards, R7-R10/R12-R14/R16 | T6-T7, T14-T15 | Request tests inspect model/configuration, all chunk coverage and complete serialized budgets. Source-selection tests reject invented IDs and preserve exact qualifiers. Schema/reference tests mutate unknown, empty, duplicate and cross-document evidence. Summary has exactly five fields; questions have 0-5 bounds and explicit unresolved-source rationales. Multilevel/compression tests assert shrinking packets and finite safe failures. C live output preserves may/probably/up-to-half/normal-human-cell context and final conclusion. A source comparison fails F1. |
| Official biomedical entities, R11/R13/R16 | T8, T14-T15 | Vocabulary tests assert official aliases, ambiguous rejection, exact mention evidence, GO biological-process filtering and overlapping vocabularies. Loader tests verify source hashes and offline failure. Reduction test proves entities/evidence survive without model repetition. Live examples include MeSH Escherichia coli/Yeasts, GO and MeSH DNA replication, and GO protein biosynthetic process with source mentions and versioned official resources. |
| Single card JSON and reference-safe persistence, R9/R15-R19 | T2-T3, T9-T10, T13-T15 | CLI assertions inspect cards root/order, no partial failed cards and empty-folder output. Ten replacement fault cases validate saved references and temporary-file cleanup. Lock test kills a writer and verifies OS lock recovery. Saved live schemas/references and success/failed/success attempts pass. |
| Grafana cards/logs/metrics and privacy, R20-R22/R24-R25 | T11-T16 | Telemetry tests inspect JSON lifecycle fields, service/environment labels, token units, stable metrics groups, content opt-in and suppressed secrets. Backend-outage tests assert valid final card outputs independently. Direct Loki/Prometheus/Grafana queries establish actual delivery, card IDs/counts/status, failures and metadata-only defaults. |
| Langfuse tracing, R23-R25 | T11-T16 | Observation tests assert model, exact usage, sanitized errors and flush. Truncation test asserts one available-usage update before failure. Direct success/error/content queries confirm real delivery and privacy; unit tests cover independent tracing outage behavior. |

## Task completion and limits

T1-T17 are checked. T1-T14 and T16 have implementation and execution evidence
supporting their technical scope. T15 is incomplete as an acceptance result
because of F1; T17's report needs the F2 corrections. Earlier failing test evidence
is recorded in the implementation report but was not recreated by reverting code.
No zero-test or skipped check is counted as a success.

Scientific review evaluated the provided representative commentaries and saved
source text. Exact quotation and valid references cannot prove arbitrary future
model selections are correct. C's OCR formatting artifacts remain visible and
are not silently rewritten. This review does not claim browser-rendered visual
inspection; Grafana verification used authenticated panel queries and dashboard
configuration. No new live generation was performed during this review. The
required next step is implementer corrections followed by another review of the
new content identity and updated real-source evidence.
