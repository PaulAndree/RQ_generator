# Specification-driven development

SDD features follow this sequence:

requirements → design → tasks → human approval → implementation → review

AGENTS.md defines the repository workflow. This document defines the
specification format, approval rules, and traceability requirements.

Write specifications in English.

## 1. Applicability and location

A feature with `"sdd": true` in feature_list.json requires a specification.

The leader establishes the task worktree before specification edits.
All agents use that same worktree.

Each specification contains:

```text
specs/<name>/
├── requirements.md
├── design.md
└── tasks.md
```

The directory name matches the feature's name in feature_list.json.
Draft files may exist while the feature remains pending.

## 2. Feature statuses

| Status | Meaning |
|---|---|
| pending | Awaiting specification or being drafted |
| spec_ready | Specification complete and awaiting human approval |
| in_progress | Approved work undergoing implementation, review, or delivery |
| blocked | Work cannot continue; the reason and resume action are recorded |
| done | Required verification, review, and authorized delivery are complete |

Record the execution phase separately in progress/current.md.
Status alone does not establish specification approval or review approval.

The normal SDD flow is:

pending → spec_ready → human approval → in_progress →
implementation → review → authorized delivery → done

Only the leader decides when to enter or leave blocked status.
Record the previous status and phase so work can resume correctly.

## 3. Human approval

The specification author completes the three files and marks the feature
spec_ready. The leader presents them to the user and waits for explicit approval.

Before implementation, the leader records:

- Feature ID and name.
- The user's approval and the specification it applies to.
- A reproducible identifier for the approved content.
- The task worktree and branch.

A content digest can identify uncommitted specifications. A commit hash is
sufficient only when it identifies the complete approved content.

Approval covers requirements, design decisions, and task scope.
Updating task completion checkboxes does not change the approved scope.

If substantive specification changes are needed:

1. Stop implementation that depends on those changes.
2. Have the leader assign the revision to the specification author.
3. Preserve stable requirement and task identifiers.
4. Summarize the changes and return the feature to spec_ready.
5. Obtain renewed human approval before continuing affected implementation.

Approval is not inferred from feature status, silence, or an unrelated request.

## 4. requirements.md

Use the following EARS patterns:

| Pattern | Template |
|---|---|
| Ubiquitous | The system SHALL <behavior>. |
| Event-driven | WHEN <trigger>, the system SHALL <behavior>. |
| State-driven | WHILE <state>, the system SHALL <behavior>. |
| Optional feature | WHERE <optional feature applies>, the system SHALL <behavior>. |
| Unwanted behavior | IF <unwanted condition>, THEN the system SHALL <response>. |

Requirements must:

- Have stable identifiers such as R1 and R2.
- State one independently verifiable obligation.
- Use SHALL or SHALL NOT for required behavior.
- Define observable outcomes and relevant conditions.
- Cover every acceptance criterion.
- Preserve applicable architectural and compatibility constraints.
- Identify concrete tests or another explicitly approved verification method.

Include an acceptance-to-requirement mapping. Quote acceptance criteria when
they do not have stable identifiers.

Do not invent product requirements or hide unresolved ambiguity.
Report conflicting or insufficient acceptance criteria as blockers.

Example:

```text
## R1

WHEN discovery runs on an input directory, the system SHALL return its
direct-child PDF files in filename order.

Verification: test_discovery_orders_pdf_files.

## Acceptance mapping

"Discover PDFs in order" → R1
```

Examples illustrate the format. They do not add project requirements.

## 5. design.md

Inspect existing code and the applicable project documents before writing
the design.

Describe:

- Files to create or modify.
- The implementation approach and components to reuse.
- New or changed interfaces, data formats, and configuration.
- Validation, error handling, and compatibility considerations.
- Applicable integration and observability behavior.
- At least one reasonable alternative and why it was rejected.

Keep the design proportional to the feature.
Mark irrelevant sections as not applicable instead of inventing work.

## 6. tasks.md

Use an ordered checklist with stable task identifiers.
Each task references the requirements it covers.

Example:

```text
- [ ] T1: Add a failing discovery-order test. Covers: R1.
- [ ] T2: Implement deterministic discovery. Covers: R1.
- [ ] T3: Run the discovery tests and relevant regression checks. Covers: R1.
```

For bug fixes, reproduce the failure before changing the implementation.
For new behavior, place meaningful failing tests before implementation when
automated tests are appropriate.

Include normal-entry-point and integration checks when unit tests alone
cannot establish the required behavior.

The implementer checks a task only after completing its work and applicable
verification. The reviewer checks the evidence behind that completion.

PR creation and final workflow bookkeeping follow implementation review.
Do not make them prerequisites for approving the implementation checklist.

During revisions, preserve valid completed work and identify tasks that
must be repeated because the specification changed.

## 7. Traceability

Maintain the complete chain:

acceptance criterion → requirement → task → test or approved verification

The specification author records acceptance mappings and planned verification.
The implementer records concrete evidence in progress/impl_<name>.md.
The reviewer independently verifies the chain in progress/review_<name>.md.

Check test assertions, not only test names.
Shared and existing regression tests do not need artificial mappings to
requirements from an unrelated feature.

An unchecked task or documented exception cannot waive an approved requirement.
Scope changes require specification revision and renewed approval.

## 8. Features without SDD

Features with `"sdd": false` or no sdd field do not automatically enter
this specification workflow.

They still follow applicable scope, isolation, and verification rules.
The leader must use an explicitly documented non-SDD workflow.
If none exists, report the missing prerequisite rather than assuming a
specification or approval exists.
