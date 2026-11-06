# Completion checklist

Evaluate the applicable rows against a candidate commit. Record results in the
review report; do not treat these unchecked template boxes as a failed test.
Use `not applicable` with a reason where scope excludes a check.

## Repository and scope

- [ ] Task branch/worktree is isolated; user work is preserved.
- [ ] Registry and current memory identify the task and next action.
- [ ] Commands, package paths, and Python version match this repository.
- [ ] Changes stay inside the assigned scope.

## Specification

- [ ] SDD feature has requirements, design, tasks, and a recorded human approval.
- [ ] Approval matches the substantive spec revision.
- [ ] Requirements map to concrete evidence; completed tasks are checked.
- [ ] Legacy or documentation exemptions are explicit and not fabricated approvals.

## Verification and monitoring

- [ ] Applicable checks pass and test collection is nonzero.
- [ ] Changed behavior has before/after evidence where applicable.
- [ ] Monitoring impact is covered; live delivery claims have backend evidence.
- [ ] Reports state unavailable integrations and other verification limits.
- [ ] No secrets, source documents, debug output, or temporary evidence enter Git.

## Review and publication

- [ ] Independent agent reviewed the candidate code commit.
- [ ] Actionable findings are resolved; later code changes have fresh review.
- [ ] PR includes changes, checks, evidence, review reference, and limitations.
- [ ] PR URL is recorded before the feature becomes done.
- [ ] History preserves the outcome; pending approvals/blockers remain in current memory.
- [ ] Branch is clean and worktree retained; merge remains a human action.
