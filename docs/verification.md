# Verification

Demonstrate the required behavior with evidence appropriate to the change.
Do not claim success from task checkboxes, test names, or configuration alone.

AGENTS.md defines the workflow. The approved specification defines the
feature's acceptance criteria and required verification.

## 1. Select applicable checks

Before implementation, identify:

- Requirements and acceptance criteria affected by the change.
- Relevant existing tests and regression checks.
- New tests needed for changed behavior.
- Normal-entry-point, integration, and observability checks.
- Required services and configuration.

For documentation-only changes, check content, references, examples, and
consistency. Runtime tests are required only when the change affects runtime
behavior or executable instructions.

## 2. Automated tests

Use pytest as the project test runner.

Run checks using the project's supported Python version and an environment
containing the declared development dependencies.

Full test suite:

```bash
python -m pytest -q
```

Targeted tests:

```bash
python -m pytest -q tests/test_<module>.py
```

Test the required behavior through stable interfaces.

- Cover the successful path and relevant failures and boundary conditions.
- Add regression coverage for bug fixes.
- Keep tests deterministic and independent of execution order.
- Isolate temporary files and other mutable test state.
- Use test doubles where appropriate for unit tests.
- Verify real service compatibility separately when required.

For bug fixes, reproduce the failure before changing the implementation.
For new behavior, add meaningful failing tests first when automated tests
are appropriate.

Confirm that an initial failure demonstrates the missing behavior rather
than an unrelated environment problem.

Zero collected tests do not establish runtime correctness.
Skipped tests do not count as successful verification of their requirements.

## 3. Normal-entry-point and integration checks

When behavior spans components, exercise the normal application entry point
or relevant integration boundary.

- Use representative inputs and inspect observable outputs.
- Verify applicable validation and failure handling.
- Check persisted output structure and references when relevant.
- Use the configured services and models.
- Verify connectivity before service-dependent checks.
- Record the configuration needed to reproduce the check without secrets.

Do not silently substitute another provider or model.

If a required service is unavailable, record the blocked check and the
action needed to complete it. Do not report full verification.

## 4. Code review

Inspect the feature diff and enough surrounding code to understand its impact.

Check:

- Duplicated logic, confusing names, unnecessary indirection, and
  abstractions without a current need.
- Accidental changes and debugging artifacts.

Recommend simplifications only after confirming that they preserve behavior.

## 5. Observability

For runtime changes, verify the observability required by the approved
specification and project conventions.

Where applicable:

- Run a representative successful operation and a controlled failure.
- Confirm expected logs arrive in the configured logging backend.
- Confirm expected metrics appear in the metrics backend.
- Confirm dashboard panels display the relevant data.
- Confirm LLM traces arrive in Langfuse.
- Verify telemetry failures do not break application work unless explicitly
  required by the specification.

Record which signals were observed and where.
Configuration validation alone does not demonstrate telemetry delivery.

Avoid changing shared infrastructure or exposing sensitive content as
part of verification.


## 6. Delivery checks

Implementation review occurs before PR creation.

When shipping is authorized:

1. Open the pull request and verify its target branch and included changes.
2. Record the URL and delivered revision.

Mark the feature done only after required verification, review, and
authorized delivery are complete.