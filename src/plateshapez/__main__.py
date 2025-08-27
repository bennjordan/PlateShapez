from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from plateshapez.pipeline import DatasetGenerator
from plateshapez.config import load_config
from plateshapez.perturbations.base import PERTURBATION_REGISTRY

app = typer.Typer(add_completion=False)
console = Console()


@app.command()
def list() -> None:  # noqa: A001 - CLI command name
    """List available perturbations."""
    table = Table(title="Available Perturbations")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="green")

    for name, cls in PERTURBATION_REGISTRY.items():
        table.add_row(name, (cls.__doc__ or "").strip())
    console.print(table)


@app.command()
def info(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    n_variants: Optional[int] = typer.Option(None, "--n_variants", help="Override number of variants"),
) -> None:
    """Show merged configuration (defaults < file < CLI)."""
    try:
        cfg = load_config(str(config) if config else None, cli_overrides={"n_variants": n_variants})
        console.print(Panel.fit(json.dumps(cfg, indent=2), title="Configuration", border_style="cyan"))
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/]")
        raise typer.Exit(1)


@app.command()
def generate(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    n_variants: Optional[int] = typer.Option(None, "--n_variants", help="Override number of variants"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Debug logging"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
) -> None:
    """Generate adversarial dataset."""
    try:
        cli_overrides = {
            "n_variants": n_variants,
            "verbose": verbose,
            "debug": debug,
        }
        cfg = load_config(str(config) if config else None, cli_overrides=cli_overrides)

        if debug or verbose:
            console.print(f"[dim]Loading config from: {config or 'defaults'}[/]")
            console.print(f"[dim]Random seed: {cfg['dataset'].get('random_seed', 1337)}[/]")

        gen = DatasetGenerator(
            bg_dir=cfg["dataset"]["backgrounds"],
            overlay_dir=cfg["dataset"]["overlays"],
            out_dir=cfg["dataset"]["output"],
            perturbations=cfg.get("perturbations", []),
            random_seed=int(cfg["dataset"].get("random_seed", 1337)),
        )

        if dry_run:
            table = Table(title="Dry Run: Generation Plan")
            table.add_column("Backgrounds", style="cyan")
            table.add_column("Overlays", style="green")
            table.add_column("Output Dir", style="yellow")
            table.add_column("Variants", style="magenta")
            table.add_row(
                str(cfg["dataset"]["backgrounds"]),
                str(cfg["dataset"]["overlays"]),
                str(cfg["dataset"]["output"]),
                str(cfg["dataset"]["n_variants"]),
            )
            console.print(table)
            console.print(Panel.fit(json.dumps(cfg.get("perturbations", []), indent=2), title="Perturbations", border_style="blue"))
            raise typer.Exit(0)

        if debug:
            console.print("[dim]Starting generation with full config:[/]")
            console.print(Panel.fit(json.dumps(cfg, indent=2), title="Debug Config", border_style="red"))

        gen.run(n_variants=int(cfg["dataset"]["n_variants"]))
        console.print("[bold green]✓ Dataset generated successfully![/]")
        
    except FileNotFoundError as e:
        console.print(f"[red]File not found: {e}[/]")
        console.print("[yellow]Tip: Check that background and overlay directories exist and contain images[/]")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/]")
        console.print("[yellow]Tip: Use 'advplate info' to check your configuration[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/]")
        if debug:
            console.print_exception()
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show version info."""
    try:
        from importlib.metadata import version as _v

        v = _v("plateshapez")
    except Exception:
        # Fallback if metadata not available
        v = "0.1.0"
    console.print(f"plateshapez {v}")


def main() -> None:
    try:
        app()
    except typer.Exit:
        raise
    except Exception as e:  # Show help on error per spec
        console.print(f"[red]Error: {e}[/]")
        console.print(Panel.fit(app.get_help(), title="Usage"))
        raise typer.Exit(1)


if __name__ == "__main__":
    main()
