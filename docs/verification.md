# Verification

## Baseline and setup

Requires Python 3.12+ and uv. Install the local development environment explicitly:

```bash
uv sync --extra dev
```

Run the repository check entrypoint:

```bash
./init.sh
```

It uses the prepared `.venv` without installing packages or downloading Python.
It checks Python 3.12+, required development imports, workflow metadata, pytest
collection and execution, and patch whitespace. It also works when invoked by
absolute path from another directory. Missing tools or dependencies return a
nonzero exit status with a setup command. Zero collected tests is a failure.

Useful focused commands are:

```bash
.venv/bin/python scripts/check_harness.py
.venv/bin/python -m pytest tests/ -q
git diff --check
uv run --no-sync --offline rq-generator --help
```

GitHub Actions prepares Python and dependencies explicitly, then runs the same
`./init.sh`. A local green run is distinct from a hosted CI result. Required
branch protection remains a repository-owner setting.

Do not use `unittest discover`: these tests use pytest and a unittest invocation
can report success without collecting the intended suite. Normal checks must
not depend on deployed OCR, Ollama, or monitoring services.

## Evidence by change

| Change | Required proof |
| --- | --- |
| Documentation | Inspect instructions for consistency; check changed local links, referenced files, and runnable examples |
| Bug fix | Capture failing behavior before the fix; demonstrate passing behavior after it |
| CLI/API behavior | Relevant pytest cases and captured real command/request outputs with exit statuses |
| UI behavior | Hands-on assertions and screenshots or recording using the evidence skills |
| Executable workflow | Positive run and negative fixtures proving failures propagate |
| Telemetry | Representative success and controlled failure, plus backend query results |

For SDD work, store requirement-to-test or requirement-to-inspection mappings
in `progress/impl_<name>.md`. Every requirement needs concrete evidence, but
legacy tests do not need retroactive spec IDs. Describe what fixtures prove and
what still requires live integration or human scientific review.

Evidence includes command, worktree/commit, expected result, actual result,
exit status, and limitations. Keep temporary outputs in `.artifacts/<task>/`.
Commit a sanitized short report or publish artifacts with the PR. An ignored
local path alone is not reviewable by another machine.

## Independent review and shipping

The reviewer runs applicable checks on the candidate commit and inspects the
full diff, spec approval, traceability, security/privacy, and monitoring impact.
Record `APPROVED` or `CHANGES_REQUESTED`, the code commit, commands/results,
findings with paths and lines, and anything untested. Resolve actionable
findings before publication. Documentation changes also receive an independent
agent review under this repository's chosen workflow; external bot review is
optional and must not be claimed unless it ran.

After integrating fixes or rebasing, rerun checks and review any changed diff.
The final PR must identify the reviewed code commit. A later metadata-only
commit may store its report and PR URL, as described in `AGENTS.md`.

Never claim a live backend is healthy because a mock passed. Record an
unavailable integration separately; if the approved acceptance criteria require
it, work cannot be marked done until it is verified or the human revises scope.
