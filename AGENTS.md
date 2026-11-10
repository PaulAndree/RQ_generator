# Agent workflow

This file defines the repository workflow. Apply the sections relevant to
the user's request.

## 1. Scope and working principles

- Make the smallest change that fully solves the requested problem through
  its normal entry point. Preserve unrelated behavior.
- Handle one feature at a time.
- Read-only reviews and investigations do not require a worktree or changes
  to progress files.
- Documentation and configuration maintenance use an isolated task branch
  and relevant checks. They do not automatically require the feature workflow.
- Open a pull request when the authorized task includes shipping changes.
  A review, proposal, or local experiment does not imply publication.
- Write project documentation, specifications, reports, and agent
  instructions in English.

## 2. Repository map

| Path | Purpose | When to read |
|---|---|---|
| `feature_list.json` | Feature definitions and workflow status | Before feature work |
| `progress/current.md` | Active work, evidence, blockers, and next action | At session start |
| `progress/history.md` | Append-only record of completed work | When historical context is needed |
| `specs/<name>/` | Requirements, design, and implementation tasks | Before implementing an SDD feature |
| `docs/architecture.md` | Application scope and architectural requirements | Before specification or implementation |
| `docs/conventions.md` | Coding, configuration, and service conventions | Before writing code |
| `docs/specs.md` | Specification format and approval process | Before specification work |
| `docs/verification.md` | Required checks and evidence | Before implementation and review |
| `.codex/agents/` | Agent definitions and role protocols | Before delegating work |
| `src/` | Application code | During implementation and review |
| `tests/` | Automated tests | During implementation and verification |

## 3. Feature workflow

For features with `"sdd": true`:

pending → spec_author → spec_ready → human approval →
in_progress → implementer → reviewer → PR → done

1. Read the active progress record, feature list, and applicable documents.
2. Validate the selected feature's required fields and status. Report invalid
   or missing prerequisites rather than inventing project state.
3. Before any repository edits, use `/new-feature` to establish isolation.
   Preserve a worktree already assigned to this task. Never build on `main`.
4. The leader passes the feature ID, absolute worktree path, and branch to
   every agent. All agents use that same task worktree.
5. The spec_author creates `specs/<name>/requirements.md`, `design.md`, and
   `tasks.md`, then changes the feature status to `spec_ready`.
6. Stop for explicit human approval. Record which specification revision
   was approved. Substantive specification changes require renewed approval.
7. After approval, the leader changes the status to `in_progress` and
   delegates implementation.
8. The implementer completes the approved tasks, updates their checkboxes,
   and records verification evidence and requirement-to-test mappings.
9. The reviewer inspects the changes, executes applicable checks, and
   verifies acceptance criteria, requirements, tasks, and test assertions.
10. If changes are requested, the implementer addresses them and the reviewer
    reviews the updated revision.
11. After approval, open the pull request when shipping is authorized.
12. Mark the feature `done` only after the required checks, review, and
    authorized delivery are complete. Record the pull request URL when applicable.

Features without SDD follow an explicitly defined non-SDD workflow.
Do not send them to the spec author or assume an approved specification exists.

## 4. Evidence and review

- For bug fixes, reproduce the failure before changing the implementation.
- For new behavior, add a meaningful failing test before implementing it
  when an automated test is appropriate.
- Use checks appropriate to the change. Documentation-only changes require
  relevant content and reference checks.
- Record verification commands, exit codes, and test counts.
- Zero collected tests do not demonstrate runtime correctness.
- Preserve traceability from acceptance criteria to requirements, tasks,
  and tests.
- Check what test assertions establish. Test names and completed task
  checkboxes alone are insufficient evidence.
- Identify the revision reviewed. Code changes after approval require
  another review.
- Report unavailable integrations and unverified behavior explicitly.

## 5. Progress and session closure

During active work, keep `progress/current.md` updated with:

- Feature ID and current phase.
- Task worktree and branch.
- Approved specification revision, when applicable.
- Completed work and verification evidence.
- Latest implementation and review report paths.
- Blockers and the next action.

When work is complete:

1. Append a completion summary to `progress/history.md`.
2. Reset `progress/current.md` to its template.
3. Remove temporary files and debugging artifacts created for the task.
4. Report the outcome, verification results, and delivery location.

When work is paused, blocked, or awaiting approval, preserve enough active
state to resume. Do not clear the progress record or mark the feature done.

Never remove or overwrite unrelated user changes to make the checkout clean.

## 6. Blockers and recovery

- Read the relevant project documents before making assumptions.
- Distinguish a routine, recoverable tool failure from a genuine blocker.
- Retry or use an equivalent supported method when this remains within the
  authorized scope.
- Stop when progress requires missing authorization, unresolved requirements,
  or changes outside the task's scope.
- Record the blocking reason and the next action needed to resume.
- Resume from recorded task state rather than starting a second feature.

## 7. Git and shared resources

- Never commit directly to `main`.
- Before edits, inspect existing worktrees, uncommitted changes, and overlapping
  open pull requests as described in `/new-feature`.
- Never force-push to `main`. On the task branch, use `--force-with-lease`
  only when rewriting published history is necessary and authorized.
- Regenerate conflicting lockfiles instead of merging them by hand.
- Worktrees do not isolate ports, services, databases, or monitoring systems.
  Confirm the target before using shared resources.
- Stop and report conflicts that cannot be resolved confidently.
- Do not merge a pull request unless explicitly instructed.

## 8. Writing and available skills

Use `/unslop` on human-facing text written or changed for the task before
committing, publishing, or sending it.

Repository skills:

| Skill | Location |
|---|---|
| `new-feature` | `.agents/skills/new-feature/SKILL.md` |
| `observability-shared-monitoring` | `.agents/skills/observability/SKILL.md` |
| `unslop` | `.agents/skills/unslop/SKILL.md` |

Read a skill before applying it. Report missing required skills rather than
assuming they are installed.
