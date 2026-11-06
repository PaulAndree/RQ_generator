#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd -- "$repository_root"

if ! command -v uv >/dev/null 2>&1; then
    echo "[ERROR] uv is required. Install uv, then run: uv sync --extra dev" >&2
    exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
    echo "[ERROR] Development environment missing. Run: uv sync --extra dev" >&2
    exit 1
fi
if ! .venv/bin/python -c 'import sys; raise SystemExit(sys.version_info < (3, 12))'; then
    echo "[ERROR] Python 3.12+ is required. Prepare it with: uv sync --extra dev" >&2
    exit 1
fi
if ! .venv/bin/python -c 'import pytest, httpx, pydantic' >/dev/null 2>&1; then
    echo "[ERROR] Development dependencies missing. Run: uv sync --extra dev" >&2
    exit 1
fi

.venv/bin/python scripts/check_harness.py
.venv/bin/python -m pytest tests/ -q
git diff --check
printf '%s\n' '[OK] Environment ready'
