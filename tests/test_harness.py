"""Validate workflow records and prove the check entrypoint propagates failures."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
module_spec = importlib.util.spec_from_file_location("check_harness", ROOT / "scripts/check_harness.py")
checker = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(checker)


def feature(**overrides):
    result = {
        "id": 1,
        "name": "example-feature",
        "sdd": True,
        "status": "in_progress",
        "acceptance": ["A concrete observable result"],
        "spec_revision": "a0204f2",
        "approval": {
            "approved_by": "human",
            "approved_at": "2026-11-06T15:00:00Z",
            "spec_revision": "a0204f2",
            "source": "Human approval message in task session",
        },
        "review": None,
        "pr_url": None,
        "blocked_reason": None,
        "resume_status": None,
    }
    result.update(overrides)
    return result


def write_registry(root, features):
    (root / "feature_list.json").write_text(json.dumps({"schema_version": 1, "features": features}))


@pytest.fixture
def registry(tmp_path):
    directory = tmp_path / "specs/example-feature"
    directory.mkdir(parents=True)
    for name in ("requirements.md", "design.md", "tasks.md"):
        (directory / name).write_text("Concrete specification\n")
    write_registry(tmp_path, [feature()])
    return tmp_path


def test_valid_approved_and_maintenance_records(registry):
    assert checker.validate_registry(registry) == []
    write_registry(registry, [feature(sdd=False, spec_revision=None, approval=None)])
    assert checker.validate_registry(registry) == []


@pytest.mark.parametrize("payload", ["{", "[]", '{}', '{"schema_version": true, "features": []}', '{"schema_version": 2, "features": []}', '{"schema_version": 1, "features": {}}'])
def test_invalid_registry_shape(registry, payload):
    (registry / "feature_list.json").write_text(payload)
    assert checker.validate_registry(registry)


def test_missing_registry_is_a_diagnostic(tmp_path):
    assert "feature_list.json" in checker.validate_registry(tmp_path)[0]


@pytest.mark.parametrize("field,value", [
    ("id", True), ("id", 0), ("id", []), ("name", "../outside"),
    ("name", []), ("name", "Invalid_name"), ("sdd", "true"),
    ("status", "unknown"), ("status", []), ("acceptance", []),
    ("acceptance", [""]), ("acceptance", [4]), ("spec_revision", "not-a-commit"),
    ("approval", None), ("approval", []), ("review", []),
    ("pr_url", "https://example.com/pull/1"), ("blocked_reason", "old reason"),
    ("resume_status", "in_review"),
])
def test_invalid_feature_fields(registry, field, value):
    write_registry(registry, [feature(**{field: value})])
    assert checker.validate_registry(registry), field


def test_nonobject_feature(registry):
    write_registry(registry, [None])
    assert "expected an object" in checker.validate_registry(registry)[0]


@pytest.mark.parametrize("duplicate", ["id", "name"])
def test_duplicate_identity(registry, duplicate):
    first = feature(status="pending", approval=None)
    second = feature(id=2, name="another-feature", status="pending", approval=None)
    second[duplicate] = first[duplicate]
    write_registry(registry, [first, second])
    assert any("duplicate" in error for error in checker.validate_registry(registry))


def test_only_one_active_feature(registry):
    write_registry(registry, [feature(sdd=False, spec_revision=None, approval=None),
                             feature(id=2, name="another-feature", sdd=False, status="in_review", spec_revision=None, approval=None)])
    assert any("at most one" in error for error in checker.validate_registry(registry))


@pytest.mark.parametrize("status", ["spec_ready", "in_progress", "in_review", "done"])
@pytest.mark.parametrize("problem", ["missing", "empty", "escaping"])
def test_required_spec_files(registry, tmp_path, status, problem):
    current = feature(status=status, approval=None if status == "spec_ready" else feature()["approval"])
    write_registry(registry, [current])
    path = registry / "specs/example-feature/requirements.md"
    path.unlink()
    if problem == "empty":
        path.write_text(" \n")
    elif problem == "escaping":
        outside = tmp_path / "outside-requirements.md"
        outside.write_text("Not an approved spec\n")
        path.symlink_to(outside)
    assert any("requirements.md" in error for error in checker.validate_registry(registry))


def test_spec_directory_cannot_be_symlinked_outside_registry(registry, tmp_path_factory):
    outside = tmp_path_factory.mktemp("external-specs")
    shutil.rmtree(registry / "specs/example-feature")
    (registry / "specs/example-feature").symlink_to(outside, target_is_directory=True)
    assert any("escapes" in error for error in checker.validate_registry(registry))


@pytest.mark.parametrize("field,value", [("approved_by", ""), ("source", None), ("approved_at", "yesterday"), ("approved_at", "2026-11-06T12:00:00"), ("spec_revision", "bbbbbbb")])
def test_incomplete_or_stale_approval(registry, field, value):
    current = feature()
    current["approval"][field] = value
    write_registry(registry, [current])
    assert any("approval" in error for error in checker.validate_registry(registry))


@pytest.mark.parametrize("status", ["pending", "spec_ready"])
def test_approval_cannot_be_preclaimed(registry, status):
    write_registry(registry, [feature(status=status)])
    assert any("before human approval" in error for error in checker.validate_registry(registry))


def test_maintenance_cannot_claim_spec_approval(registry):
    write_registry(registry, [feature(sdd=False)])
    assert any("sdd=false" in error for error in checker.validate_registry(registry))


def reviewed_feature(registry):
    (registry / "review.md").write_text("APPROVED by independent reviewer for a0204f2\n")
    return feature(status="done", review={"verdict": "APPROVED", "reviewer": "reviewer", "implementer": "implementer", "code_commit": "a0204f2", "report": "review.md"}, pr_url="https://github.com/owner/repo/pull/1")


def test_done_requires_review_and_pr(registry):
    write_registry(registry, [feature(status="done")])
    errors = checker.validate_registry(registry)
    assert any("review" in error for error in errors)
    assert any("pr_url" in error for error in errors)
    write_registry(registry, [reviewed_feature(registry)])
    assert checker.validate_registry(registry) == []


@pytest.mark.parametrize("field,value", [("verdict", "CHANGES_REQUESTED"), ("reviewer", "implementer"), ("reviewer", ""), ("implementer", None), ("code_commit", "bad"), ("report", "missing.md"), ("report", "/etc/passwd"), ("report", "../outside.md")])
def test_invalid_review(registry, field, value):
    current = reviewed_feature(registry)
    current["review"][field] = value
    write_registry(registry, [current])
    assert any("review" in error for error in checker.validate_registry(registry))


def test_blocked_records_preserve_gate(registry):
    write_registry(registry, [feature(status="blocked")])
    assert checker.validate_registry(registry)
    current = feature(status="blocked", blocked_reason="Awaiting dependency", resume_status="in_progress")
    write_registry(registry, [current])
    assert checker.validate_registry(registry) == []
    current["approval"] = None
    write_registry(registry, [current])
    assert any("approval" in error for error in checker.validate_registry(registry))


@pytest.fixture
def check_fixture(tmp_path):
    shutil.copy2(ROOT / "init.sh", tmp_path / "init.sh")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    (tmp_path / ".venv/bin").mkdir(parents=True)
    python = tmp_path / ".venv/bin/python"
    python.write_text('''#!/bin/bash
printf '%s|%s\\n' "$PWD" "$*" >> "$INIT_LOG"
if [[ "$*" == *sys.version_info* && "${FAIL_STAGE:-}" == version ]]; then exit 1; fi
if [[ "$*" == *'import pytest'* && "${FAIL_STAGE:-}" == deps ]]; then exit 1; fi
if [[ "$*" == scripts/* && "${FAIL_STAGE:-}" == validator ]]; then exit 1; fi
if [[ "$*" == '-m pytest tests/ -q' ]]; then
  if [[ "${FAIL_STAGE:-}" == pytest ]]; then exit 1; fi
  if [[ "${FAIL_STAGE:-}" == zero-tests ]]; then exit 5; fi
fi
''')
    python.chmod(0o755)
    for name in ("uv", "git"):
        path = bindir / name
        path.write_text('#!/bin/bash\nif [[ "${FAIL_STAGE:-}" == whitespace ]]; then exit 2; fi\n')
        path.chmod(0o755)
    env = {**os.environ, "PATH": f"{bindir}:/usr/bin:/bin", "INIT_LOG": str(tmp_path / "commands.log")}
    return tmp_path, env


def run_init(check_fixture, fail_stage="", cwd=None):
    root, env = check_fixture
    return subprocess.run(["/bin/bash", str(root / "init.sh")], cwd=cwd or root, env={**env, "FAIL_STAGE": fail_stage}, text=True, capture_output=True)


def test_init_uses_own_checkout_from_other_directory(check_fixture):
    root, _ = check_fixture
    result = run_init(check_fixture, cwd="/")
    assert result.returncode == 0, result.stderr
    assert "[OK] Environment ready" in result.stdout
    assert all(line.startswith(f"{root}|") for line in (root / "commands.log").read_text().splitlines())


@pytest.mark.parametrize("stage", ["version", "deps", "validator", "pytest", "zero-tests", "whitespace"])
def test_init_propagates_failures(check_fixture, stage):
    result = run_init(check_fixture, stage)
    assert result.returncode != 0
    assert "[OK] Environment ready" not in result.stdout
    if stage in ("version", "deps"):
        assert "uv sync --extra dev" in result.stderr


def test_init_missing_uv(check_fixture):
    root, _ = check_fixture
    (root / "bin/uv").unlink()
    result = run_init(check_fixture)
    assert result.returncode != 0
    assert "uv is required" in result.stderr


def test_init_missing_prepared_environment(check_fixture):
    root, _ = check_fixture
    (root / ".venv/bin/python").unlink()
    result = run_init(check_fixture)
    assert result.returncode != 0
    assert "uv sync --extra dev" in result.stderr


def test_real_pytest_zero_collection_is_not_success(tmp_path):
    shutil.copy2(ROOT / "init.sh", tmp_path / "init.sh")
    (tmp_path / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/check_harness.py", tmp_path / "scripts/check_harness.py")
    (tmp_path / "tests").mkdir()
    write_registry(tmp_path, [])
    (tmp_path / ".venv/bin").mkdir(parents=True)
    wrapper = tmp_path / ".venv/bin/python"
    wrapper.write_text(f'#!/bin/bash\nexec "{sys.executable}" "$@"\n')
    wrapper.chmod(0o755)
    result = subprocess.run(["/bin/bash", str(tmp_path / "init.sh")], text=True, capture_output=True)
    assert result.returncode == 5, result.stdout + result.stderr
    assert "no tests ran" in result.stdout
    assert "[OK] Environment ready" not in result.stdout


def test_native_role_configurations_parse_and_reference_contracts():
    config = tomllib.loads((ROOT / ".codex/config.toml").read_text())
    for role in ("leader", "spec_author", "implementer", "reviewer"):
        entry = config["agents"][role]
        layer = tomllib.loads((ROOT / ".codex" / entry["config_file"]).read_text())
        assert f".codex/agents/{role}.md" in layer["developer_instructions"]
    reviewer = tomllib.loads((ROOT / ".codex/agents/reviewer.toml").read_text())
    assert reviewer["sandbox_mode"] == "read-only"
