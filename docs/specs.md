# Spec driven development

New application behavior and executable workflow changes require a specification
and human approval before implementation. Documentation repairs and maintenance
can use an explicit `sdd: false` exemption. Do not label new behavior maintenance
to bypass approval. Do not retrofit approval onto legacy code.

## Files and approval

Each feature name selects `specs/<name>/` with three files:

- `requirements.md` states observable behavior with stable IDs `R1`, `R2`, etc.
- `design.md` explains the approach, affected boundaries, failure behavior,
  monitoring, alternatives, and verification plan.
- `tasks.md` lists ordered checkbox tasks `T1`, `T2`, etc. Each task cites its
  requirements and specifies the expected evidence.

The spec author drafts these files and commits them. The leader records that
commit as `spec_revision`, sets `spec_ready`, and presents the files to the
human. The human approves that revision or requests changes. Only then may the
leader record `approval` and transition to `in_progress`.

The approval object has `approved_by`, `approved_at`, `spec_revision`, and
`source`. Store a reference to the actual human reply, not an invented approval.
A substantive change to requirements, design, or task scope needs a new spec
revision and human approval. Checking implementation tasks does not change the
approved scope. The declared revision points to the spec commit; validation of
record shape cannot authenticate the approver or detect every semantic change.
The reviewer compares the actual diff against the approved version.

## Requirement style

Use one observable obligation per requirement. EARS patterns help identify the
trigger, state, or failure condition:

| Pattern | Form |
| --- | --- |
| Ubiquitous | The system SHALL perform an action. |
| Event | WHEN an event occurs, the system SHALL produce an outcome. |
| State | WHILE a condition holds, the system SHALL preserve an invariant. |
| Optional | WHERE an option is enabled, the system SHALL perform an action. |
| Unwanted | IF a failure occurs, THEN the system SHALL respond predictably. |

For example, `R1: WHEN a PDF fails evidence validation, the pipeline SHALL
exclude its card from document_cards.json.` Its evidence should execute that
failure and inspect the saved output. Requirements about review or documentation
can map to a concrete inspection rather than a fabricated unit test.

Keep requirements scoped and testable. Do not demand retroactive requirement IDs
for every existing test. The implementer records new requirement evidence in
`progress/impl_<name>.md`; the reviewer verifies the mapping and any documented
exceptions. A checked task is progress, not proof.

## Registry contract

`feature_list.json` has `schema_version: 1` and a `features` array. Each entry has
unique integer `id`, unique slug `name`, boolean `sdd`, nonempty string entries
in `acceptance`, and `status`. Additional state fields are:

| Field | Meaning |
| --- | --- |
| `spec_revision` | Git commit containing the submitted spec, or null for pending/exempt work |
| `approval` | Human approval record, or null before approval/exempt work |
| `review` | Verdict, reviewer, implementer, code_commit, and repository-relative report |
| `pr_url` | Real GitHub PR URL once created |
| `blocked_reason` | Concrete blocker when blocked |
| `resume_status` | Nonblocked state to restore after resolving a blocker |

| State | Entry condition and next step |
| --- | --- |
| `pending` | Scoped request exists; draft spec or start exempt work |
| `spec_ready` | Three spec files and revision exist; human approval pending |
| `in_progress` | Approved SDD revision or explicit maintenance scope; implement |
| `in_review` | Candidate commit and evidence ready; independent review pending |
| `done` | Checks pass, independent review approved, and PR exists; human merge remains |
| `blocked` | Reason and resume_status recorded; requirements of resume state still apply |

Only one feature may be `in_progress` or `in_review`. The leader is the canonical
registry writer. `pending -> in_progress` is allowed only for `sdd: false`.
`spec_ready -> in_progress` requires the human approval record. Findings return
`in_review -> in_progress`; changed approved scope returns to `spec_ready`
without an active approval. Any unfinished phase may become blocked; recovery
restores its recorded state after checking the actual checkout.

A review record contains `verdict`, `reviewer`, `implementer`, `code_commit`,
and `report`. `done` requires `APPROVED`, different reviewer/implementer
identities, an existing report, and `pr_url`. Final metadata commits may follow
the reviewed code commit. Changes to code, specs, tests, or executable
configuration require fresh review. An HTTPS PR link in JSON is a record;
confirm it exists remotely before claiming publication.

## Migration

The initial folder-to-document-cards draft described a different notes app.
It is archived under `docs/archive/` and is not a specification for existing RQ
code. Existing application behavior is described by README, architecture, and
tests. The first active executable spec is `002-codex-harness-bootstrap`.
Its implementation follows the same human approval gate as future work.
