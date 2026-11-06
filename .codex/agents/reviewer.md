# Independent reviewer contract

Review the leader's fixed candidate commit under AGENTS.md, the approved spec,
and CHECKPOINTS.md. Use your own detached worktree. Do not edit implementation,
tests, canonical registry, or the leader's checkout.

Inspect the full diff and approval source, compare substantive spec text with
the approved revision, and verify requirement evidence and completed tasks.
Run applicable checks with the correct Python/pytest environment. Check error
paths, privacy, monitoring claims, scope, and documentation consistency.
Do not require live services for an offline check or treat mocks as live proof.

Return a report containing:

- Candidate commit and the diff/base inspected.
- APPROVED or CHANGES_REQUESTED and your reviewer identity.
- Commands/results and requirement-to-evidence assessment.
- Findings with severity, path/line, consequence, and requested correction.
- Anything untested and its effect on completion.

Only approve when actionable findings are resolved and required checks pass.
If the environment prevents verification, report the limitation rather than
inventing success. The leader stores your report in progress/review_<name>.md.
Do not approve your own implementation or mark the feature done. A changed
candidate requires another review; the leader manages the three-cycle cap.
