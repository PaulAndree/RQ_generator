"""Check versioned workflow state without external services or dependencies."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

STATUSES = {"pending", "spec_ready", "in_progress", "in_review", "done", "blocked"}
ACTIVE = {"in_progress", "in_review"}
SPEC_REQUIRED = {"spec_ready", "in_progress", "in_review", "done"}
APPROVAL_REQUIRED = {"in_progress", "in_review", "done"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
COMMIT = re.compile(r"[0-9a-f]{7,40}\Z")
PR_URL = re.compile(r"https://github\.com/[^/\s?#]+/[^/\s?#]+/pull/[1-9][0-9]*\Z")


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _commit(value: object) -> bool:
    return isinstance(value, str) and bool(COMMIT.fullmatch(value))


def _contained_file(root: Path, relative: str) -> bool:
    path = Path(relative)
    if path.is_absolute():
        return False
    resolved = (root / path).resolve()
    return resolved.is_relative_to(root.resolve()) and resolved.is_file()


def _approval_errors(feature: dict, label: str, status: str) -> list[str]:
    errors = []
    revision = feature.get("spec_revision")
    approval = feature.get("approval")
    if not feature["sdd"]:
        if revision is not None or approval is not None:
            errors.append(f"{label}: sdd=false requires null spec_revision and approval")
        return errors
    if status in SPEC_REQUIRED and not _commit(revision):
        errors.append(f"{label}.spec_revision: expected a Git commit")
    if status in {"pending", "spec_ready"}:
        if approval is not None:
            errors.append(f"{label}.approval: must be null before human approval")
        return errors
    if status not in APPROVAL_REQUIRED:
        return errors
    if not isinstance(approval, dict):
        return errors + [f"{label}.approval: expected a human approval record"]
    for field in ("approved_by", "approved_at", "source"):
        if not _text(approval.get(field)):
            errors.append(f"{label}.approval.{field}: expected nonempty text")
    date = approval.get("approved_at")
    if _text(date):
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                datetime.strptime(date, "%Y-%m-%d")
            else:
                parsed = datetime.fromisoformat(date.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone missing")
        except ValueError:
            errors.append(f"{label}.approval.approved_at: expected ISO date or timestamp with timezone")
    if not _commit(approval.get("spec_revision")) or approval.get("spec_revision") != revision:
        errors.append(f"{label}.approval.spec_revision: must match declared spec_revision")
    return errors


def _review_errors(root: Path, feature: dict, label: str, status: str) -> list[str]:
    errors = []
    review = feature.get("review")
    if review is not None or status == "done":
        if not isinstance(review, dict):
            errors.append(f"{label}.review: expected an independent review record")
        else:
            verdict = review.get("verdict")
            if verdict not in ("APPROVED", "CHANGES_REQUESTED"):
                errors.append(f"{label}.review.verdict: unknown verdict")
            if status == "done" and verdict != "APPROVED":
                errors.append(f"{label}.review.verdict: done requires APPROVED")
            for field in ("reviewer", "implementer"):
                if not _text(review.get(field)):
                    errors.append(f"{label}.review.{field}: expected agent identity")
            if _text(review.get("reviewer")) and review.get("reviewer") == review.get("implementer"):
                errors.append(f"{label}.review.reviewer: must differ from implementer")
            if not _commit(review.get("code_commit")):
                errors.append(f"{label}.review.code_commit: expected a Git commit")
            report = review.get("report")
            if not _text(report) or not _contained_file(root, report):
                errors.append(f"{label}.review.report: expected existing repository-relative report")
    pr_url = feature.get("pr_url")
    if pr_url is not None or status == "done":
        if not isinstance(pr_url, str) or not PR_URL.fullmatch(pr_url):
            errors.append(f"{label}.pr_url: expected HTTPS GitHub pull request URL")
    return errors


def validate_registry(root: Path) -> list[str]:
    """Return actionable errors; this checks records, not human identity or remote PRs."""
    root = root.resolve()
    try:
        registry = json.loads((root / "feature_list.json").read_text())
    except (OSError, UnicodeError, ValueError) as exc:
        return [f"feature_list.json: cannot read valid JSON ({type(exc).__name__})"]
    if not isinstance(registry, dict):
        return ["feature_list.json: expected an object"]
    if type(registry.get("schema_version")) is not int or registry["schema_version"] != 1:
        return ["schema_version: expected supported version 1"]
    features = registry.get("features")
    if not isinstance(features, list):
        return ["features: expected an array"]
    errors = []
    ids, names = set(), set()
    active = 0
    for index, feature in enumerate(features):
        label = f"features[{index}]"
        if not isinstance(feature, dict):
            errors.append(f"{label}: expected an object")
            continue
        identifier, name = feature.get("id"), feature.get("name")
        if type(identifier) is not int or identifier < 1:
            errors.append(f"{label}.id: expected positive integer")
        elif identifier in ids:
            errors.append(f"{label}.id: duplicate {identifier}")
        else:
            ids.add(identifier)
        valid_name = isinstance(name, str) and bool(SLUG.fullmatch(name))
        if not valid_name:
            errors.append(f"{label}.name: expected a lowercase slug inside specs/")
        elif name in names:
            errors.append(f"{label}.name: duplicate {name}")
        else:
            names.add(name)
        if type(feature.get("sdd")) is not bool:
            errors.append(f"{label}.sdd: expected boolean")
            continue
        acceptance = feature.get("acceptance")
        if not isinstance(acceptance, list) or not acceptance or not all(map(_text, acceptance)):
            errors.append(f"{label}.acceptance: expected nonempty list of nonempty strings")
        status = feature.get("status")
        if not isinstance(status, str) or status not in STATUSES:
            errors.append(f"{label}.status: unknown status")
            continue
        if status in ACTIVE:
            active += 1
        if status == "blocked":
            if not _text(feature.get("blocked_reason")):
                errors.append(f"{label}.blocked_reason: expected reason")
            resume = feature.get("resume_status")
            if not isinstance(resume, str) or resume not in STATUSES - {"blocked"}:
                errors.append(f"{label}.resume_status: expected nonblocked status")
                continue
            status = resume
        else:
            for field in ("blocked_reason", "resume_status"):
                if feature.get(field) is not None:
                    errors.append(f"{label}.{field}: must be null unless blocked")
        try:
            if feature["sdd"] and status in SPEC_REQUIRED and valid_name:
                spec_root = root / "specs"
                directory = spec_root / name
                if not directory.resolve().is_relative_to(spec_root.resolve()) or not spec_root.resolve().is_relative_to(root):
                    errors.append(f"{label}.name: spec directory escapes specs/")
                else:
                    for filename in ("requirements.md", "design.md", "tasks.md"):
                        path = directory / filename
                        if not _contained_file(spec_root, f"{name}/{filename}"):
                            errors.append(f"{label}: missing or escaping specs/{name}/{filename}")
                        elif not path.read_text().strip():
                            errors.append(f"{label}: empty specs/{name}/{filename}")
            errors.extend(_approval_errors(feature, label, status))
            errors.extend(_review_errors(root, feature, label, status))
        except (OSError, UnicodeError, ValueError, RuntimeError):
            errors.append(f"{label}: cannot read a referenced file safely")
    if active > 1:
        errors.append("features: at most one in_progress or in_review feature is allowed")
    return errors


def main() -> int:
    errors = validate_registry(Path(__file__).resolve().parents[1])
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("[OK] Workflow metadata valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
