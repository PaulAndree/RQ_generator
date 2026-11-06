# Bootstrap implementation evidence

Task: `002-codex-harness-bootstrap`, approved spec commit `a0204f2`.
Worktree: `/tmp/rq-harness-impl-1106`, branch `agent/harness-impl-1106`.
Implementation files are identified by the Git commit containing this report.

## Baseline and scope

Before implementation, `./init.sh` exited 127 because it did not exist.
`uv run --extra dev python3 -m pytest tests/ -q` passed the existing 32 tests.
No PDF application behavior or application telemetry changed.

Added a no-install check entrypoint, a standard-library metadata validator,
negative fixtures, GitHub Actions, and native Codex role registration. The leader
owns the registry, spec task updates, role Markdown contracts, and documentation.
The registry and role Markdown were copied into this worktree only as untracked
local fixtures for integration checks and are not part of this implementation
commit. Approval date validation accepts an ISO date or a timezone timestamp;
it does not invent time precision absent from the human approval record.

## Requirements and evidence

| Requirement | Evidence |
| --- | --- |
| R1 | `test_init_uses_own_checkout_from_other_directory`; real invocation `/tmp/rq-harness-impl-1106/init.sh` from `/tmp` passed. |
| R2 | `test_init_missing_uv`, `test_init_missing_prepared_environment`, version/dependency cases in `test_init_propagates_failures`. Diagnostics point to explicit environment setup. |
| R3 | `test_init_propagates_failures` covers validator, pytest, zero-test, and whitespace failures. `test_real_pytest_zero_collection_is_not_success` runs actual pytest and receives exit 5. Full `./init.sh` passed 105 tests and whitespace checks. |
| R4 | Registry shape, feature field, duplicate identity, nonobject feature, and active-feature tests reject invalid fixtures. |
| R5 | `test_required_spec_files` covers missing, empty, and escaping files across required states; external directory symlink is rejected. |
| R6 | Approval fixtures cover missing identity/source/date, stale revision, missing approval, and premature approval. |
| R7 | Done-state fixtures require an independent approved review and HTTPS GitHub PR URL; blocked fixtures retain spec approval requirements. |
| R8 | Workflow inspection confirms read-only contents permission, Python 3.12, uv 0.12.13, explicit `uv sync --extra dev`, and `./init.sh`. Local execution of the same check entrypoint passed; hosted CI is pending PR publication. |
| R9 | TOML role test checks all four paths and instruction contracts. Installed `codex-cli 0.167.0` accepted the project configuration through `codex app-server --strict-config --print-startup-config`. The same loader accepted each role layer's actual settings supplied as CLI overrides. An invalid sandbox setting exited 1 as a negative control. |

## Commands and results

- `uv run --extra dev python3 -m pytest tests/test_harness.py -q`: 73 passed.
- `./init.sh`: workflow metadata valid; 105 passed; exit 0.
- From `/tmp`, `/tmp/rq-harness-impl-1106/init.sh`: 105 passed; exit 0.
- Codex strict project configuration load and four role layer load probes: exit 0.
- `git diff --check`: exit 0.

The 105 tests comprise the existing 32 application tests and 73 new harness
cases. Init uses the prepared `.venv/bin/python` directly; it never invokes
package installation, downloads a runtime, or contacts live services. uv is
required for the documented preparation workflow. CI uses the installed local
uv version explicitly rather than selecting an unspecified latest release.

## Limits and handoff

The Codex startup loader defers opening named agent role files until the role
is used. A malformed referenced role file did not fail startup. Therefore these
probes verify recognized project configuration and each layer's supported
settings, not a live spawned-agent session. The TOML files wire role instructions
through `developer_instructions`, which asks the role to read its Markdown
contract. They do not install an automatic dispatcher or hooks.

No hosted CI, live PDF service, monitoring ingestion, or model session was run.
Workflow telemetry exporters remain outside this approved feature. Human
identity, approval authenticity, remote PR existence, and the truth of review
claims cannot be established by local metadata validation alone. The leader
must integrate this commit, rerun checks, obtain independent review, publish the
PR, and update canonical state before marking the feature done.
