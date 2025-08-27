# PlateShapez

Dataset generator for adversarial plate overlay.

## Quick Start

- Prereqs: uv (Python package manager) installed.
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- Clone and set up dev environment:
  ```bash
  git clone https://github.com/benjordan/plateshapez.git
  cd plateshapez

  # Setup environment
  uv venv
  source .venv/bin/activate

  # Install dev dependencies
  uv sync --dev
  ```

## Development (npm-like commands)

You can use either the console script (after `uv sync`) or the Bash wrapper.

- Console script (requires one-time `uv sync`):
  ```bash
  # Format / Lint / Type-check / All checks
  uv run dev format
  uv run dev lint
  uv run dev type
  uv run dev check

  # Pre-commit hooks
  uv run dev hooks install   # installs pre-commit & pre-push hooks
  uv run dev pre-commit      # run hooks on all files
  ```

- Bash wrapper (works without installing the package):
  ```bash
  ./scripts/dev format
  ./scripts/dev lint
  ./scripts/dev type
  ./scripts/dev check
  ./scripts/dev hooks install
  ./scripts/dev pre-commit
  ```

These map to the same underlying tools and are aligned with CI and `scripts/check.sh`.

## What the commands do

- `format`: `ruff format .`
- `lint`: `ruff check . --fix`
- `type`: `mypy .`
- `check`: runs format, lint, and type in sequence (same as `scripts/check.sh`)
- `hooks install`: `pre-commit install --hook-type pre-commit --hook-type pre-push`
- `pre-commit`: `pre-commit run --all-files`

## CI

GitHub Actions runs the same checks via `./scripts/check.sh`. Local pre-commit hooks use the same tools via uv to avoid version drift.
