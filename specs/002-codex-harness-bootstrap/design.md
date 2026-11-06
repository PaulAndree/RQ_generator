# Codex workflow bootstrap design

Revision: draft 1. Human approval pending.

## Files and ownership

| File | Responsibility |
| --- | --- |
| `init.sh` | Read-only local verification entry point. |
| `scripts/check_harness.py` | Standard-library registry and spec consistency checks. |
| `tests/test_harness.py` | Temporary fixtures and controlled command failure checks. |
| `.github/workflows/checks.yml` | Install dev environment explicitly and call `./init.sh`. |
| `.codex/config.toml` and role config files | Native Codex role registration. |
| `.codex/agents/*.md` | Role instructions referenced by supported configuration. |
| `feature_list.json` | Versioned workflow state and approval references. |
| `docs/verification.md` | Installation, checks, and evidence limits. |

Documentation cleanup is already authorized work. Executable files described
here require human approval of this spec first. Do not repair the missing
startup script before that gate. During drafting, the explicitly reported
baseline command is `uv run --extra dev python3 -m pytest tests/ -q`.

## Verification entry point

Use Bash with `set -euo pipefail`. Locate the checkout from the script path,
then change to that directory. Check uv, the prepared Python version, and
pytest availability before running checks. A separate, documented
`uv sync --extra dev` prepares dependencies. The check command must use
no-sync and no-runtime-download behavior; it must never install silently.

Run the validator, pytest, and `git diff --check`. Preserve failures and print
`[OK] Environment ready` only after every check passes. Pytest's no-tests
exit status must remain a failure. Avoid pipelines that hide an earlier
command's exit status. Unit tests may substitute controlled commands through
a temporary PATH to prove the shell stops on failures. Run the real baseline
as well.

## Metadata validator

Proposed API:

```python
def validate_registry(root: Path) -> list[str]: ...
def main() -> int: ...
```

The command prints diagnostics on stderr and returns 1 for invalid metadata,
0 for a valid registry. Filesystem and JSON errors become diagnostics rather
than uncaught tracebacks. Use only the Python standard library. Resolve paths
and reject names that escape `specs/`.

The registry has `schema_version: 1` and a `features` array. Each feature has
unique integer `id`, unique slug `name`, boolean `sdd`, nonempty string
`acceptance` entries, and a status from this set:

`pending`, `spec_ready`, `in_progress`, `in_review`, `done`, `blocked`.

Only one feature may be `in_progress` or `in_review` at a time. Names select
spec directories. SDD records beyond pending declare `spec_revision` as the Git commit that
contains the requirements, design, and task text submitted for approval.
Implementation task checkbox changes do not invalidate approval. A substantive
spec edit changes the revision and requires renewed approval. Features marked
`sdd: false` are maintenance exemptions with null approval and spec revision.
Pending and spec_ready records have null approval.

An `approval` record contains `approved_by`, `approved_at`, `spec_revision`,
and `source`. The source identifies the actual human message or review.
An agent must never manufacture approval. The validator checks record shape
and revision equality. It cannot prove identity or authenticate the source.

A `review` record contains `verdict`, `reviewer`, `implementer`,
`code_commit`, and `report`; `done` requires `APPROVED`, distinct reviewer
and implementer identities, and a repository-relative report that exists.
The report identifies the exact application and workflow commit reviewed.
Final state or PR metadata may follow in a separate commit; code changes
invalidate the review and require a new one. `pr_url` is an HTTPS GitHub pull
request URL. These checks prove metadata presence, not remote PR existence.

A blocked record has nonempty `blocked_reason` and `resume_status` from the
nonblocked statuses. Validation applies approval and spec requirements to
the resume status as well. Recovering a session requires checking Git and
actual evidence before restoring that state.

`done` means checks passed, independent review approved, and a PR was opened.
It does not mean merged or deployed. A human merges the PR.

## Codex configuration

Use the installed CLI version and current official documentation to choose
the supported native TOML configuration. Validate the actual loader locally,
not just TOML syntax. Register four roles, reference the role instructions,
and make reviewer access read-only where the runtime supports it. Do not
copy Claude-style hook JSON into `.codex/`. Remove the misleading settings
file during migration, preserving its origin in the documentation audit.

Role instructions are workflow policy. They do not by themselves provide
an automatic dispatcher or a security boundary. Do not claim a mandatory
post-edit hook or stop hook unless the installed runtime supports it and
its execution is tested. CI supplies a separate executable check boundary;
required branch-protection settings remain a repository-owner action.

## CI and review

Use checkout, Python 3.12, and an explicitly versioned uv installation. Run
`uv sync --extra dev` before `./init.sh`; keep the dependency lockfile if
created. Use read-only repository permissions and no secrets for checks.
Do not add a live-service prerequisite.

An independent reviewer examines the exact code commit, requirements-to-test
map, check output, and limitations before the leader publishes the PR. The
leader writes canonical registry and session state. Agents work on their
own branches and exchange commits and report paths.

## Observability boundary

This bootstrap records evidence through test output, review reports, and
versioned state. Existing RQ logs, metrics, and Langfuse traces describe PDF
processing. They do not measure agent handoffs or review decisions. A later
workflow-telemetry feature should specify run IDs, role and phase events,
durations, failure states, delivery behavior, retention, and shared dashboards.
No telemetry exporter or running workflow dashboard is promised here.

## Alternative considered

A fully automatic orchestration service could own transitions, approvals,
agent dispatch, and event export. It would add runtime dependencies and a
larger failure model before the repository has consistent state. Start with
verified local checks and explicit handoffs. Keep automated orchestration as
a separate feature once the manual Codex workflow has evidence.
