# Repository workflow

This repository contains the RQ generator application and a Codex workflow for
changing it. Keep one task per branch. Follow the user's assigned task rather
than starting unrelated backlog work.

## Start and resume

1. Read `progress/current.md` and `feature_list.json`. Confirm their branch,
   worktree, feature, and next action against Git before trusting them.
2. Use `.agents/skills/new-feature/SKILL.md` before edits. Fetch `origin`, inspect
   open PR files and shared checkout status, and isolate from `origin/main`.
   Preserve an existing worktree only when it belongs to this task. Delegated
   agents start their own worktrees at the leader's supplied base or candidate
   commit so they receive the approved spec and integrated task changes.
3. Run `./init.sh`. If it is missing or fails, record the failure. Environment
   repair may address that failure; application implementation waits for a
   passing baseline. During initial workflow migration use the explicit commands
   in `docs/verification.md` and report the missing entrypoint.
4. Read `docs/architecture.md`, `docs/conventions.md`, and the relevant spec.
   Read `docs/specs.md` before drafting or changing a spec.

## Choose the work

- Read-only investigation needs no branch, commit, or PR.
- Documentation repairs and maintenance use `sdd: false` with a recorded scope.
  They require relevant checks, not invented runtime proof.
- New behavior and executable workflow changes use `sdd: true`. A spec author
  drafts requirements, design, and tasks. Stop at `spec_ready` for human approval.
- The user's approval must identify the spec revision. Approval of a plan or
  general goal does not approve a later, unseen spec.
- Resume approved work from its recorded next action. Ask again only when
  approval is missing, requirements changed, or ownership is unclear.

## Implement, review, and publish

The leader owns registry transitions and integration. Delegate specification,
implementation, and independent review using the contracts in `.codex/agents/`.
These Markdown files are role instructions; native role registration requires
supported Codex TOML configuration. See `docs/codex.md`.

```text
pending -> spec_ready -> human approval -> in_progress -> in_review -> done
                                            ^              |
                                            +-- findings --+
```

`done` means applicable checks passed, an independent agent approved the reviewed
code revision, and the task PR exists. It does not mean merged. Never merge
without explicit user instruction. `blocked` records a reason and resume state.
See `docs/specs.md` for fields and allowed transitions.

- Capture a bug failure before fixing it. Use evidence appropriate to the change.
- Follow the existing module boundaries. Use the code-structure skill when
  choosing shared operations or extracting repeated logic.
- Run the verification commands and map each new requirement to evidence.
- The reviewer inspects a fixed commit in a separate worktree and reports
  findings. The reviewer does not edit the implementation or approve their own work.
- Fix findings, rerun affected checks, and request a fresh review after code
  changes or rebase changes the reviewed diff. Limit review/fix cycles to three;
  report unresolved findings and stop publication if the cap is reached.
- After approval, push the task branch and open the PR with scope, checks,
  before/after evidence, review reference, and limitations. No extra publication
  confirmation is required under the user's chosen policy.
- Complete the registry and history after PR creation. A final metadata-only
  commit may add the PR URL and review report; review its diff and rerun checks.
  It may also check off a shipping task after publication, without changing
  its text or scope. It must not change implementation, substantive specs,
  executable configuration, or tests.

## Agent isolation

Each editing agent owns its branch and worktree. Pass a base commit, assigned
paths, inputs, and expected report path. Integrate committed results with
cherry-pick after inspecting their diff. Agents do not write in another agent's
checkout. Read-only reviewers use their own detached worktree and return their
report to the leader for storage. Keep review reports outside their reviewed
commit to avoid a circular commit reference.

Independent tasks may run in parallel only when their edits and external
resources do not conflict. Worktrees do not isolate ports or databases. Check
process ownership before using a dev server. Never reset user work, force-push
main, or hand-merge lockfiles. Use `--force-with-lease` only on your task branch
when a rebase requires it.

## Memory and monitoring

Update `progress/current.md` at milestones and before yielding. Keep decisions,
approval references, test results, review findings, blockers, and next commands
on disk. At a phase boundary append a dated entry to `progress/history.md`.
Only reset current memory when there is no pending action. Never discard an
approval wait or blocker. See `docs/memory.md`.

For runtime changes use `.agents/skills/observability/SKILL.md` and
`docs/observability.md`. Reuse the shared Grafana, Prometheus, Loki, Pushgateway,
and Langfuse services. Resolve endpoints from configuration. Application
telemetry and workflow telemetry have different verification requirements.
Never claim ingestion from configuration alone. Missing optional telemetry
must not break application requests; missing required verification blocks a
completion claim.

## Final checks

Use `CHECKPOINTS.md` and `docs/verification.md`. Run the unslop skill on prose you
write. Keep temporary evidence in ignored `.artifacts/`; publish sanitized
proof in the PR or a durable report because ignored files are not portable
memory. Retain the worktree until the PR closes. End shipping tasks with the PR
URL, check result, review result, and any remaining limitation.

If a tool fails, diagnose the specific failure and use supported recovery.
Record unresolved blockers and the command needed to resume. Do not invent
success, substitute a provider silently, or stop unrelated read-only diagnosis.
