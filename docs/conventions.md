# Code and documentation conventions

Use Python 3.12 or newer, matching `pyproject.toml` and `.python-version`.
Use `uv` for an isolated environment. Dependencies belong in `pyproject.toml`;
regenerate lockfiles with the dependency tool when applicable.

Follow the surrounding code style. Use snake_case for functions and modules,
PascalCase for classes, and UPPER_SNAKE_CASE for constants. Prefer double quoted
strings. Group standard library, third-party, and package-relative imports.
The installed package is `rq_generator`, not `src.cli` or a notes application.

Use pytest and the fixtures in `tests/conftest.py`. Test observable outcomes
and meaningful failures. Use temporary paths for file behavior and local HTTP
fixtures for service contracts. Do not add tests that merely repeat an
implementation or impose one test class per function.

Preserve the CLI's exit status contract and structured error logging. Never
log credentials, full service exception bodies, or document content by default.
Comments explain a constraint or decision that names alone cannot explain.
Avoid debug prints and unexplained TODOs.

Write project guidance in English. Keep stable requirement IDs and descriptive
feature names. Apply `.agents/skills/unslop/SKILL.md` to prose you write or edit.
Leave vendored skill bodies and licenses unchanged unless the task concerns
them. Use Markdown links for navigation and code spans for literal commands.
