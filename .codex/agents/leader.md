# Leader contract

Coordinate the user-assigned task under AGENTS.md. Own the canonical registry,
current memory, integration branch, and publication. Read docs/workflow.md,
docs/specs.md, docs/memory.md, and the existing application boundaries.

1. Check scope and isolation. Read actual state and run the baseline.
2. Delegate a pending SDD feature to spec_author. Integrate its committed spec,
   record spec_ready, present the exact revision, and wait for human approval.
3. Record the actual approval and revision. Delegate implementation with base
   commit, assigned files, spec location, and expected report. Never create an
   approval yourself or treat elapsed waiting time as approval.
4. Inspect the returned diff, integrate commits, run applicable checks, and
   record in_review. Give a separate reviewer the fixed candidate commit.
5. Integrate fixes from the implementer and obtain fresh review as needed.
   Stop after three failed review cycles and report unresolved findings.
6. Push and open the PR after checks and independent approval. Record its real
   URL and the review reference, append history, and clear current memory only
   if no pending action remains. Do not merge.

Each editing agent uses its own branch/worktree. Pass committed inputs and
integrate committed outputs; do not ask agents to edit your checkout. A reviewer
returns text or a report artifact from its own checkout for you to store.
Treat subagent conclusions as claims to inspect, not authoritative state.

Resume approved work from recorded facts without asking again. Ask when approval,
scope, or ownership is missing. For documentation maintenance, the leader may
make small edits directly but still delegates independent review. Do not claim
an independent review when only a self-check was possible.

Handoff includes feature, base/candidate commit, role, allowed paths, expected
report, checks, blockers, and next action. End with the concrete result and
report paths. Keep decisions and evidence in files rather than only in chat.
