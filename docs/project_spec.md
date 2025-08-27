# 📜 Project Specification: `plateshapez`

## 1. **Purpose**

A research tool for generating adversarially perturbed license plate overlays on vehicle images, producing structured datasets with reproducibility, transparency, and ethical guardrails.

* **Primary Users:** researchers, ML practitioners, privacy/robustness teams.
* **Design Principle:** *user-first, safe by default, hackable by experts*.

---

## 2. **Core Components**

### 2.1 Configuration

* **Default Config File:** `config.yaml`
* Configurable fields:

  ```yaml
  dataset:
    backgrounds: "./backgrounds"
    overlays: "./overlays"
    output: "./dataset"
    n_variants: 10
    random_seed: 1337

  perturbations:
    - name: shapes
      params:
        num_shapes: 20
        min_size: 2
        max_size: 15
    - name: noise
      params:
        intensity: 25

  logging:
    level: "INFO"
    save_metadata: true
  ```
* Config hierarchy:

  1. Defaults (baked-in)
  2. `config.yaml` (if present)
  3. CLI overrides (`--n_variants 50`)

---

### 2.2 API

Python package should expose:

```python
from plateshapez import DatasetGenerator
from plateshapez.perturbations import register, PERTURBATION_REGISTRY

# Run programmatically
gen = DatasetGenerator(
    bg_dir="backgrounds",
    overlay_dir="overlays",
    out_dir="dataset",
    perturbations=[
        {"name": "shapes", "params": {"num_shapes": 30}},
        {"name": "noise", "params": {"intensity": 10}}
    ]
)
gen.run(n_variants=5)
```

API surfaces:

* `DatasetGenerator` – orchestrates dataset creation.
* `Perturbation` base class – allows custom perturbations.
* `register` decorator – adds new perturbations into registry.
* `load_config(path)` – parse YAML/JSON configs.

---

### 2.3 CLI (Rich-powered)

Command entrypoint: `advplate`

#### Top-level commands

```bash
Usage: advplate [OPTIONS] COMMAND [ARGS]...

Options:
  -c, --config PATH   Path to config file
  -v, --verbose       Verbose logging
  -h, --help          Show this message and exit

Commands:
  generate   Generate a dataset
  list       List available perturbations
  info       Show current configuration
  version    Show version info
```

#### `generate`

```bash
plateshapez generate --backgrounds ./bg --overlays ./plates --out ./dataset --n_variants 20
```

* Displays progress bar for images generated.
* Prints table of applied perturbations with Rich.

#### `list`

```bash
plateshapez list
```

* Shows registered perturbations with docstrings, e.g.:

```
Available Perturbations:
────────────────────────────────────
shapes   Random rectangles, ellipses, triangles
noise    Add Gaussian or salt noise
warp     Mild geometric warping
texture  Overlay texture maps
```

#### UX Principles

* **Errors always show help menu** for current command.
* **Empty input** → display usage guide, not just crash.
* Rich-powered **panels and tables** for readability.
* `--dry-run` mode prints what would be generated without writing files.

---

### 2.4 Testing

Use `pytest`.

#### Unit tests

* Perturbation registry:

  * Adding new perturbation.
  * Duplicate name raises error.
* Perturbation correctness:

  * Shapes draw inside bounds.
  * Noise intensity measurable.
* Pipeline:

  * Generates expected number of images.
  * Metadata file contains valid JSON with correct keys.

#### Integration tests

* Run `DatasetGenerator` with a small config (tiny bg + plate) and validate:

  * Outputs exist.
  * Metadata matches parameters.
  * CLI returns success codes.

---

### 2.5 Documentation

* `README.md` with quickstart.
* `DATASET_CARD.md` (ethical + responsible use).
* `docs/` folder with:

  * Usage examples (CLI + API).
  * Adding new perturbations.
  * Config reference.

---

## 3. **CLI Implementation Sketch**

Using [Rich + Typer](https://typer.tiangolo.com/):

```python
import typer
from rich.console import Console
from rich.table import Table
from plateshapez.pipeline import DatasetGenerator
from plateshapez.config import load_config

app = typer.Typer(add_completion=False)
console = Console()

@app.command()
def list():
    """List available perturbations."""
    from plateshapez.perturbations.base import PERTURBATION_REGISTRY
    table = Table(title="Available Perturbations")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")

    for name, cls in PERTURBATION_REGISTRY.items():
        table.add_row(name, cls.__doc__ or "")
    console.print(table)

@app.command()
def generate(
    config: str = typer.Option(None, "--config", "-c"),
    n_variants: int = typer.Option(None, "--n_variants")
):
    """Generate adversarial dataset."""
    cfg = load_config(config, cli_overrides={"n_variants": n_variants})
    gen = DatasetGenerator(
        cfg["dataset"]["backgrounds"],
        cfg["dataset"]["overlays"],
        cfg["dataset"]["output"],
        cfg["perturbations"]
    )
    gen.run(cfg["dataset"]["n_variants"])
    console.print("[bold green]✓ Dataset generated successfully![/]")

def main():
    try:
        app()
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        typer.echo(app.get_help())  # show help menu always
        raise typer.Exit(1)

if __name__ == "__main__":
    main()
```

---

## 4. **Deliverables**

* **Core library** (`advplate/`)
* **CLI** (`advplate/__main__.py`)
* **Unit + integration tests**
* **Rich-based UX**
* **Dataset Card**
* **Examples**

---

## 5. **Implementation Notes**

### 5.1 CI Pipeline (GitHub Actions + uv)

* **Workflow file**: `.github/workflows/ci.yml`
* **Goals**: fast, deterministic, identical behavior to local checks and pre-commit hooks.
* **Key steps**:
  - Checkout repository
  - Ensure `uv` is available (self-hosted agent provides it; otherwise install)
  - `uv sync --group dev` to install tooling from `pyproject.toml`
  - Run `./scripts/check.sh`, which executes in order:
    - `uv run ruff format .`
    - `uv run ruff check . --fix`
    - `uv run mypy .`
* **Parity**:
  - Local `pre-commit` uses the same tools via `uv` to avoid version drift.
  - Hooks stages are modernized to `[pre-commit, pre-push]` in `.pre-commit-config.yaml`.
* **Runner**:
  - Can run on a self-hosted runner (e.g., label `plateshapez`) or `ubuntu-latest` with a uv install step.
* **Artifacts/Logs**:
  - CI surfaces formatter/linter/type-checker output directly in logs for quick diagnosis.

### 5.2 Code Formatting & Typing

* **Modern typing syntax**:
  - Prefer builtin generics and PEP 604 unions:
    - Use `list[str]`, `dict[str, int]`, `set[str]`, etc. instead of `List[str]`, `Dict[str, int]`.
    - Use `str | None` instead of `Optional[str]`.
    - Use `A | B` instead of `Union[A, B]`.
    - Use default `None` as `param: T | None = None` (not `Optional[T]`).
* **Imports**:
  - Keep imports at file top. No mid-file imports (enforced by review and ruff rules where applicable).
* **Naming**:
  - Avoid single-letter variables and abbreviations (common in ML, but hurts debuggability).
  - Use descriptive, intention-revealing names (e.g., `image_height`, `num_shapes`, `overlay_path`).
* **Formatting**:
  - `ruff format` is the canonical formatter. CI and hooks will enforce it.
  - Line length target: 100 (see `pyproject.toml`).

### 5.3 Logging & Debugging

* **Rich logging**:
  - Provide a `--debug` flag (and/or environment toggle) that enables verbose logs.
  - Debug mode includes module, `file_path:line`, and trace-friendly context to speed up issue isolation.
  - Prefer structured and human-readable messages; avoid cryptic short forms.
* **Error handling**:
  - Exceptions should surface meaningful context; where safe, include parameters that led to the error.
  - Add targeted log lines at critical pipeline steps: loading config, enumerating inputs, applying perturbations, writing outputs/metadata.

### 5.4 CLI UX (User-first)

* **Principles**:
  - Menus should be informative and aesthetically clear (Rich tables/panels where helpful).
  - When a user error occurs (missing arg, bad path, invalid value), the CLI must display the relevant help/usage inline.
    - Do not merely say “see --help”; show the specific command’s synopsis and key options immediately.
  - Empty invocations should show usage guidance rather than failing silently or with a stack trace.
  - Provide `--dry-run` to preview outputs and side effects without writing files.
* **Discoverability**:
  - Include `list` and `info` commands to help users explore available perturbations and current configuration.
* **Consistency**:
  - Ensure CLI messaging mirrors the same terminology as the API and documentation.
