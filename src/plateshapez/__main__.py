from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from plateshapez.config import load_config
from plateshapez.perturbations.base import PERTURBATION_REGISTRY
from plateshapez.pipeline import DatasetGenerator

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


def _print_app_help() -> None:
    """Print main app help."""
    help_text = """Usage: advplate [OPTIONS] COMMAND [ARGS]...

Commands:
  list      List available perturbations
  info      Show merged configuration (defaults < file < CLI)
  generate  Generate adversarial dataset
  demo      Run interactive demo with synthetic images
  examples  Print example configuration YAML
  version   Show version info

Options:
  --help    Show this message and exit

For help on a specific command: advplate COMMAND --help"""
    console.print(Panel.fit(help_text, title="Usage"))


def _print_command_help(command_name: str) -> None:
    """Print specific command help."""
    help_texts = {
        "generate": """Usage: advplate generate [OPTIONS]

Generate adversarial dataset.

Options:
  -c, --config PATH       Path to config file
  --n_variants INTEGER    Override number of variants
  --seed INTEGER          Random seed for reproducible results
  -v, --verbose           Verbose logging
  --debug                 Debug logging
  --dry-run               Preview without writing files
  --help                  Show this message and exit""",
        "info": """Usage: advplate info [OPTIONS]

Show merged configuration (defaults < file < CLI).

Options:
  -c, --config PATH       Path to config file
  --n_variants INTEGER    Override number of variants
  --as TEXT               Output format: json|yaml
  --help                  Show this message and exit""",
        "demo": """Usage: advplate demo [OPTIONS]

Run interactive demo with synthetic images.

Options:
  --cleanup               Clean up demo files after completion
  --help                  Show this message and exit""",
    }
    help_text = help_texts.get(command_name, "No help available for this command.")
    console.print(Panel.fit(help_text, title="Usage"))


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
    n_variants: Optional[int] = typer.Option(
        None, "--n_variants", help="Override number of variants"
    ),
    format: str = typer.Option("json", "--as", help="Output format: json|yaml"),
) -> None:
    """Show merged configuration (defaults < file < CLI)."""
    try:
        cfg = load_config(str(config) if config else None, cli_overrides={"n_variants": n_variants})
        if format == "yaml":
            import yaml

            output = yaml.safe_dump(cfg, default_flow_style=False)
        else:
            output = json.dumps(cfg, indent=2)
        console.print(Panel.fit(output, title="Configuration", border_style="cyan"))
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/]")
        _print_command_help("info")
        raise typer.Exit(1)


@app.command()
def generate(
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    n_variants: Optional[int] = typer.Option(
        None, "--n_variants", help="Override number of variants"
    ),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducible results"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Debug logging"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview without writing files"),
) -> None:
    """Generate adversarial dataset."""
    try:
        cli_overrides = {
            "n_variants": n_variants,
            "seed": seed,
            "verbose": verbose,
            "debug": debug,
        }
        cfg = load_config(str(config) if config else None, cli_overrides=cli_overrides)

        if debug or verbose:
            console.print(f"[dim]Loading config from: {config or 'defaults'}[/]")
            console.print(f"[dim]Random seed: {cfg['dataset'].get('random_seed', 1337)}[/]")

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
            console.print(
                Panel.fit(
                    json.dumps(cfg.get("perturbations", []), indent=2),
                    title="Perturbations",
                    border_style="blue",
                )
            )
            raise typer.Exit(0)

        # Create generator after dry-run check
        gen = DatasetGenerator(
            bg_dir=cfg["dataset"]["backgrounds"],
            overlay_dir=cfg["dataset"]["overlays"],
            out_dir=cfg["dataset"]["output"],
            perturbations=cfg.get("perturbations", []),
            random_seed=int(cfg["dataset"].get("random_seed", 1337)),
            save_metadata=cfg.get("logging", {}).get("save_metadata", True),
        )

        if debug:
            console.print("[dim]Starting generation with full config:[/]")
            console.print(
                Panel.fit(json.dumps(cfg, indent=2), title="Debug Config", border_style="red")
            )

        gen.run(n_variants=int(cfg["dataset"]["n_variants"]))
        console.print("[bold green]✓ Dataset generated successfully![/]")

    except FileNotFoundError as e:
        console.print(f"[red]File not found: {e}[/]")
        console.print(
            "[yellow]Tip: Check that background and overlay directories exist and contain images[/]"
        )
        _print_command_help("generate")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration error: {e}[/]")
        console.print("[yellow]Tip: Use 'advplate info' to check your configuration[/]")
        _print_command_help("generate")
        raise typer.Exit(1)
    except typer.Exit:
        # Re-raise typer.Exit without handling (for dry-run and other intentional exits)
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/]")
        if debug:
            console.print_exception()
        _print_command_help("generate")
        raise typer.Exit(1)


@app.command()
def examples() -> None:
    """Print example configuration YAML."""
    example_config = """# Example plateshapez configuration
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
      scope: region  # or "global"
  - name: noise
    params:
      intensity: 25
      scope: region  # or "global"
  - name: warp
    params:
      intensity: 5.0
      frequency: 20.0
      scope: region  # or "global"
  - name: texture
    params:
      type: grain  # grain, scratches, dirt
      intensity: 0.3

logging:
  level: INFO
  save_metadata: true
"""
    console.print(example_config)


@app.command()
def demo(
    cleanup: bool = typer.Option(False, "--cleanup", help="Clean up demo files after completion"),
) -> None:
    """Run interactive demo with synthetic images."""
    demo_script = Path("examples/demo_full_workflow.py")

    if not demo_script.exists():
        console.print(f"[red]Demo script not found: {demo_script}[/]")
        console.print("[yellow]Make sure you're running from the project root directory[/]")
        raise typer.Exit(1)

    console.print("[bold green]🎬 Starting PlateShapez Interactive Demo...[/]")
    console.print("[dim]This will create test images and demonstrate the full workflow[/]")

    try:
        # Run the demo script
        result = subprocess.run([sys.executable, str(demo_script)], check=False)

        if result.returncode == 0:
            console.print("[bold green]✅ Demo completed successfully![/]")

            if cleanup:
                console.print("[yellow]🧹 Cleaning up demo files...[/]")
                cleanup_script = Path("scripts/cleanup.py")
                if cleanup_script.exists():
                    subprocess.run([sys.executable, str(cleanup_script), "--confirm"], check=False)
                    console.print("[green]✓ Cleanup complete[/]")
            else:
                console.print(
                    "[dim]Demo files preserved. Use 'uv run dev cleanup' or "
                    "'python scripts/cleanup.py' to clean up.[/]"
                )
        else:
            console.print(f"[red]Demo failed with exit code {result.returncode}[/]")
            raise typer.Exit(result.returncode)

    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted by user[/]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/]")
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
        _print_app_help()
        raise typer.Exit(1) from e


if __name__ == "__main__":
    main()
