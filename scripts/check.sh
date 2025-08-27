#!/usr/bin/env bash
set -euo pipefail

# Run format, lint (with fixes), and type-check using uv-managed tools

# Ensure dev tools are installed
uv sync --group dev

# Auto-format
uv run ruff format .

# Lint and fix
uv run ruff check . --fix

# Type check
uv run mypy .

echo "All checks passed."
