# Persistent project memory

Git-tracked files preserve the project across sessions and machines. Chat context
and native agent memory can help, but they do not replace approval or evidence.

| File | Owner and purpose |
| --- | --- |
| `feature_list.json` | Leader; current feature state and approval/review/PR references |
| `progress/current.md` | Leader; active task, checkout, facts, blockers, and next action |
| `progress/history.md` | Leader; append-only dated phase and shipping summaries |
| `specs/<name>/` | Spec author; versioned requirements, design, and task checklist |
| `progress/impl_<name>.md` | Implementer; changes, commands/results, and requirement evidence |
| `progress/review_<name>.md` | Leader stores independent review; candidate commit and verdict |
| `docs/decisions/` | Create when needed; durable decisions with reason and consequences |

At startup read current memory and registry, then confirm their claims against
Git and actual files. A stale completion line is not evidence. Only the leader
integrates shared registry and memory updates; subagents return committed reports
from their own branches or read-only review text.

Update current memory after a decision, test result, handoff, blocker, or review.
Record a branch, worktree, feature ID, last tested commit, approval reference,
report paths, and exact next command when known. A pause for approval keeps the
pending spec and next action visible. A blocked task keeps the reason and
`resume_status`; record failed attempts without overwriting the last good result.

At phase end append the date, task, outcome, evidence, and remaining work to
history. Reset current memory to its template only after the task has no pending
action. Never erase another task's checkout or history. Resolve shared history
integration by retaining both dated entries.

Keep credentials, source PDFs, model prompts, full transcripts, and sensitive
content out of memory. Link sanitized artifacts with retention/access notes.
When a durable decision changes, supersede it explicitly rather than silently
rewriting history. The feature registry is current state; history explains how
that state was reached.
