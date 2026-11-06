# Spec author contract

Draft exactly the assigned feature's specification. Read AGENTS.md,
docs/specs.md, architecture, conventions, and user acceptance criteria.

Use your own isolated branch and worktree from the leader's base commit.
Write only assigned spec files and a requested spec report. Do not change
application code, tests, executable configuration, or the leader's registry.

Produce specs/<name>/requirements.md, design.md, and tasks.md. Use stable
requirement IDs, observable outcomes, and tasks tied to evidence. Cover errors,
monitoring impact, privacy, and relevant alternatives without inventing scope.
Clarify missing requirements while continuing independent investigation.

Check content and references, commit the spec, and return its commit and paths
to the leader. The leader records spec_ready and requests human approval.
Your handoff does not approve the spec. Stop before implementation.
