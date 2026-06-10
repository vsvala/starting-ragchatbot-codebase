#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Resolve black: project venv → repo root venv → PATH
if [[ -x "$ROOT/.venv/bin/black" ]]; then
    BLACK="$ROOT/.venv/bin/black"
elif [[ -x "$ROOT/../../.venv/bin/black" ]]; then
    BLACK="$ROOT/../../.venv/bin/black"
elif command -v black &>/dev/null; then
    BLACK="black"
else
    echo "black not found — run: uv add --dev black"
    exit 1
fi

TARGETS="$ROOT/backend $ROOT/main.py"

if [[ "${1:-}" == "--fix" ]]; then
    echo "Formatting..."
    $BLACK $TARGETS
    echo "Done."
else
    echo "Checking formatting..."
    $BLACK --check $TARGETS
    echo "All files are properly formatted."
fi
