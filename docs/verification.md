# Verification

## Baseline and setup

Requires Python 3.12+ and uv. Install the local development environment explicitly:

```bash
uv sync --extra dev
```

The intended entrypoint is `./init.sh`, specified in
`specs/002-codex-harness-bootstrap/`. Until that executable spec is approved and
implemented, use the real application checks below and report that bootstrap
validation is not yet installed:

```bash
uv run --extra dev python3 -m pytest tests/ -q
git diff --check
uv run rq-generator --help
```

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
