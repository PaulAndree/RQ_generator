# RQ Generator

This repository contains an agent workflow for specification-driven development
of a scientific PDF processing application.

The planned application produces extracted chunks and evidence-linked document
cards. Application requirements are described in Instructions.md and
docs/architecture.md.

The current checkout contains the workflow configuration and documentation.
Application source files and tests are not currently present.

## Workflow

For SDD features:

pending → specification → spec_ready → human approval →
in_progress → implementation → review → authorized delivery → done

The main conversation coordinates the work through four roles:

- leader: selects or resumes a feature and coordinates handoffs.
- spec_author: writes requirements, design, and tasks.
- implementer: implements and verifies approved work.
- reviewer: independently checks the implementation and evidence.

These roles follow repository instructions. Workflow rules are not enforced
by a standalone orchestration program.

## Before starting

1. Read AGENTS.md.
2. Define a real feature in feature_list.json with a unique ID and name,
   acceptance criteria, pending status, and "sdd": true.
3. Remove or complete invalid placeholder entries.
4. Ensure required workflow files are available in the task's Git base.
   A new worktree does not inherit another checkout's uncommitted files.
5. Configure the repository remote and task isolation required by /new-feature.

Do not enter credentials in specifications or progress reports.

## Start an SDD feature

Ask the agent:

"Prepare the specification for feature <id>. Stop for my approval before
implementation."

The leader assigns a task worktree and delegates specification drafting.

Review these files:

- specs/<name>/requirements.md
- specs/<name>/design.md
- specs/<name>/tasks.md

Approve the specific feature and specification, or request revisions.
Implementation begins only after approval is recorded.

Specify whether delivery should remain local or include a pull request.
Pull requests are not merged without an explicit instruction.

## Resume work

Ask the agent to resume the feature recorded in progress/current.md.

The progress record identifies the worktree, branch, execution phase,
approval evidence, reports, blockers, and next action.

Preserve this record when work is interrupted or awaiting approval.
After completion, append a summary to progress/history.md and reset the
active template.

## Project documents

| Document | Purpose |
|---|---|
| AGENTS.md | Repository workflow and role boundaries |
| Instructions.md | Application brief |
| docs/architecture.md | Application requirements and open decisions |
| docs/specs.md | Specification format and approval rules |
| docs/conventions.md | Python, service, and observability conventions |
| docs/verification.md | Required checks and delivery verification |
| .codex/config.toml | Main conversation instructions and agent settings |
| .codex/agents/ | Agent configurations and protocols |

The project targets Python 3.12 or later.
Follow docs/verification.md for test setup requirements and commands.
Application usage instructions should be added once the implementation exists.
