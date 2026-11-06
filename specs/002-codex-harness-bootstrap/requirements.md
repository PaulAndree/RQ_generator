# Codex workflow bootstrap requirements

Revision: draft 1. Human approval pending.

## Purpose and boundary

Make the documented workflow executable for this repository. The initial
inspection found no `init.sh` or `feature_list.json`. The existing application
has 32 passing pytest tests. Draft hook settings describe another tool's
configuration and cannot establish Codex enforcement.

This feature adds local checks, registry validation, CI, and Codex role
configuration. It does not change the PDF pipeline, build an unattended agent
runner, deploy monitoring, or authenticate a human's identity. Workflow event
export and dashboards need a separate approved spec. Existing application
telemetry remains unchanged.

## R1

WHEN a prepared developer environment invokes `./init.sh` from any working
directory, the check command SHALL run the repository checks against the
checkout containing that script.

## R2

IF Python is older than 3.12, uv is unavailable, or prepared development
dependencies are unavailable, THEN `./init.sh` SHALL exit nonzero with an
actionable diagnostic without installing packages or downloading a runtime.

## R3

WHEN `./init.sh` runs, the check command SHALL report success only after
registry validation, pytest collection and execution, and `git diff --check`
all succeed, with at least one collected test.

## R4

IF the feature registry has invalid JSON, an unsupported schema version,
duplicate IDs or names, invalid field types, an unknown status, or more than
one active feature, THEN the metadata validator SHALL exit nonzero with the
relevant field or feature identified.

## R5

WHEN an SDD feature has status `spec_ready`, `in_progress`, `in_review`, or
`done`, the metadata validator SHALL require its three nonempty spec files
inside `specs/<name>/`.

## R6

WHEN an SDD feature has status `in_progress`, `in_review`, or `done`, the
metadata validator SHALL require an approval record that references the
current declared spec revision and an identifiable human approval source.

## R7

WHEN a feature has status `done`, the metadata validator SHALL require an
approved independent review record and a PR URL; WHEN a feature has status
`blocked`, it SHALL require a reason and a valid resume status.

## R8

WHEN a pull request changes this repository, GitHub Actions SHALL run the
same `./init.sh` checks using Python 3.12 and explicitly installed development
dependencies without requiring live OCR, Ollama, monitoring, or tracing
services.

## R9

WHEN the installed supported Codex runtime loads the project configuration,
Codex SHALL receive the leader, spec_author, implementer, and reviewer role
instructions through its documented configuration format.

## Acceptance evidence

| Requirement | Required proof |
| --- | --- |
| R1 | Invoke script from checkout and another directory; compare results. |
| R2 | Controlled missing-tool, old-Python, and missing-dependency failures. |
| R3 | Successful baseline plus validator, pytest, zero-test, and whitespace failure probes. |
| R4 | Temporary registry fixtures for each invalid structure and active-feature count. |
| R5 | Missing, empty, and escaping spec path fixtures plus valid spec fixture. |
| R6 | Missing, stale, and complete approval fixtures. |
| R7 | Missing review, reviewer identity, PR URL, and blocked metadata fixtures. |
| R8 | Workflow inspection and local execution of its check command; report CI separately. |
| R9 | Parse TOML and perform a local Codex config-load check against the recorded CLI version. |

The application suite must retain its existing 32 passing tests. New tests
verify the validator and command failure behavior. They do not replace the
application suite or prove that a live monitoring integration works.
