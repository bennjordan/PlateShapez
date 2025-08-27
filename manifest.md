# Directory Structure

- 📁 **./**
  - 📄 **DATASET_CARD.md**
  - 📄 **LICENSE**
  - 📄 **README.md**
  - 📁 **dataset/**
    - 📁 **images/**
    - 📁 **labels/**
  - 📁 **docs/**
    - 📄 **project_spec.md**
    - 📄 **usage_examples.md**
  - 📁 **examples/**
    - 📄 **generate_defaults.py**

      📄 *File Path*: `./examples/generate_defaults.py`

      ```
      #!/usr/bin/env python3
"""
Example: Generate dataset using the Python API with default configuration.

This example demonstrates how to use the plateshapez library programmatically
to generate adversarial license plate datasets.
"""

from plateshapez import DatasetGenerator
from plateshapez.config import load_config


def main():
    """Generate a dataset using the Python API."""
    print("🚀 Generating dataset using Python API...")
    
    # Option 1: Use DatasetGenerator directly with custom parameters
    gen = DatasetGenerator(
        bg_dir="backgrounds",
        overlay_dir="overlays", 
        out_dir="dataset",
        perturbations=[
            {"name": "shapes", "params": {"num_shapes": 30, "min_size": 2, "max_size": 8}},
            {"name": "noise", "params": {"intensity": 15}},
            {"name": "texture", "params": {"type": "grain", "intensity": 0.2}}
        ],
        random_seed=42  # For reproducible results
    )
    gen.run(n_variants=5)
    
    print("\n" + "="*50)
    
    # Option 2: Use configuration file approach
    print("📁 Generating dataset using config file approach...")
    
    cfg = load_config()  # Load defaults
    gen2 = DatasetGenerator(
        bg_dir=cfg["dataset"]["backgrounds"],
        overlay_dir=cfg["dataset"]["overlays"],
        out_dir="dataset_from_config",
        perturbations=cfg["perturbations"],
        random_seed=cfg["dataset"]["random_seed"]
    )
    gen2.run(n_variants=cfg["dataset"]["n_variants"])
    
    print("✅ Dataset generation complete!")
    print("Check the 'dataset' and 'dataset_from_config' directories for results.")


if __name__ == "__main__":
    main()

      ```

  - 📄 **manifest.md**
  - 📁 **outputs/**
  - 📁 **plate-shapes/**
    - 📄 **PlateShapez.pde**
    - 📄 **README.md**
  - 📄 **pyproject.toml**
  - 📁 **scripts/**
    - 📄 **check.sh**
    - 📄 **dev**
    - 📄 **setup_runner.sh**
  - 📁 **src/**
    - 📄 **__init__.py**

      📄 *File Path*: `./src/__init__.py`

      ```
      
      ```

    - 📁 **plateshapez/**
      - 📄 **__init__.py**

        📄 *File Path*: `./src/plateshapez/__init__.py`

        ```
        from .pipeline import DatasetGenerator
from .config import load_config

__all__ = ["DatasetGenerator", "load_config"]
        ```

      - 📄 **__main__.py**

        📄 *File Path*: `./src/plateshapez/__main__.py`

        ```
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

        ```

      - 📄 **config.py**

        📄 *File Path*: `./src/plateshapez/config.py`

        ```
        from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import os

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover - handled by dependency install
    raise RuntimeError("Missing dependency 'pyyaml'. Please run: uv add pyyaml") from e


DEFAULTS: dict[str, Any] = {
    "dataset": {
        "backgrounds": "./backgrounds",
        "overlays": "./overlays",
        "output": "./dataset",
        "n_variants": 10,
        "random_seed": 1337,
    },
    "perturbations": [
        {
            "name": "shapes",
            "params": {"num_shapes": 20, "min_size": 2, "max_size": 15},
        },
        {"name": "noise", "params": {"intensity": 25}},
    ],
    "logging": {"level": "INFO", "save_metadata": True},
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def _load_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported config format: {path.suffix}")


def load_config(path: str | os.PathLike[str] | None = None, *, cli_overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Merge config with precedence: DEFAULTS < file (if provided) < CLI overrides.
    """
    cfg = dict(DEFAULTS)
    if path:
        file_cfg = _load_file(Path(path))
        cfg = _deep_merge(cfg, file_cfg)
    if cli_overrides:
        # Handle CLI overrides more comprehensively
        override_dict = {}
        if "n_variants" in cli_overrides and cli_overrides["n_variants"] is not None:
            override_dict.setdefault("dataset", {})["n_variants"] = cli_overrides["n_variants"]
        if "verbose" in cli_overrides and cli_overrides["verbose"]:
            override_dict.setdefault("logging", {})["level"] = "DEBUG"
        if "debug" in cli_overrides and cli_overrides["debug"]:
            override_dict.setdefault("logging", {})["level"] = "DEBUG"
        cfg = _deep_merge(cfg, override_dict)
    return cfg

        ```

      - 📄 **dev.py**

        📄 *File Path*: `./src/plateshapez/dev.py`

        ```
        from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List


def sh(cmd: List[str]) -> int:
    """Run a shell command, stream output, and return exit code."""
    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except FileNotFoundError as e:
        print(f"Command not found: {cmd[0]}\n{e}")
        return 127


def cmd_format() -> int:
    return sh(["uv", "run", "ruff", "format", "."])


def cmd_lint() -> int:
    return sh(["uv", "run", "ruff", "check", ".", "--fix"])  # keep parity with scripts/check.sh


def cmd_type() -> int:
    return sh(["uv", "run", "mypy", "."])


def cmd_check() -> int:
    rc = cmd_format()
    if rc != 0:
        return rc
    rc = cmd_lint()
    if rc != 0:
        return rc
    rc = cmd_type()
    return rc


def cmd_hooks_install() -> int:
    # Install both pre-commit and pre-push
    return sh(
        [
            "uv",
            "run",
            "pre-commit",
            "install",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "pre-push",
        ]
    )


def cmd_hooks_run() -> int:
    return sh(["uv", "run", "pre-commit", "run", "--all-files"])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dev", description="Developer task runner for plateshapez")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("format", help="Run ruff formatter")
    sub.add_parser("lint", help="Run ruff linter with autofix")
    sub.add_parser("type", help="Run mypy type checker")
    sub.add_parser("check", help="Run format, lint, and type checks")

    hooks = sub.add_parser("hooks", help="Manage pre-commit hooks")
    hooks_sub = hooks.add_subparsers(dest="hooks_cmd", required=True)
    hooks_sub.add_parser("install", help="Install pre-commit and pre-push hooks")
    hooks_sub.add_parser("run", help="Run pre-commit on all files")

    # Convenience alias: `dev pre-commit` => run hooks on all files
    sub.add_parser("pre-commit", help="Alias of hooks run (pre-commit run --all-files)")

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "format":
        return cmd_format()
    if args.command == "lint":
        return cmd_lint()
    if args.command == "type":
        return cmd_type()
    if args.command == "check":
        return cmd_check()
    if args.command == "pre-commit":
        return cmd_hooks_run()
    if args.command == "hooks":
        if args.hooks_cmd == "install":
            return cmd_hooks_install()
        if args.hooks_cmd == "run":
            return cmd_hooks_run()

    print("Unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())

        ```

      - 📁 **perturbations/**
        - 📄 **__init__.py**

          📄 *File Path*: `./src/plateshapez/perturbations/__init__.py`

          ```
          # Import all perturbations to ensure they are registered
from . import shapes, noise, warp, texture
from .base import PERTURBATION_REGISTRY, register

__all__ = ["PERTURBATION_REGISTRY", "register"]
          ```

        - 📄 **base.py**

          📄 *File Path*: `./src/plateshapez/perturbations/base.py`

          ```
          from typing import Any

from PIL import Image


class Perturbation:
    name = "base"

    def __init__(self, **kwargs: Any) -> None:
        self.params: dict[str, Any] = kwargs

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        """Apply perturbation to img inside region=(x,y,w,h). Must return Image."""
        raise NotImplementedError

    def serialize(self) -> dict[str, Any]:
        return {"type": self.name, "params": self.params}


# registry
PERTURBATION_REGISTRY: dict[str, type[Perturbation]] = {}


def register(perturbation_cls: type[Perturbation]) -> type[Perturbation]:
    """Class decorator to register a perturbation by its unique name."""
    name = getattr(perturbation_cls, "name", perturbation_cls.__name__).strip()
    if not name:
        raise ValueError("Perturbation class must define a non-empty 'name'.")
    if name in PERTURBATION_REGISTRY:
        raise ValueError(f"Duplicate perturbation name: {name}")
    PERTURBATION_REGISTRY[name] = perturbation_cls
    return perturbation_cls


def get(name: str) -> type[Perturbation]:
    return PERTURBATION_REGISTRY[name]

          ```

        - 📄 **noise.py**

          📄 *File Path*: `./src/plateshapez/perturbations/noise.py`

          ```
          import numpy as np
from PIL import Image

from .base import Perturbation, register


@register
class NoisePerturbation(Perturbation):
    name = "noise"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        intensity: int = int(self.params.get("intensity", 15))
        arr: np.ndarray = np.array(img)
        noise: np.ndarray = np.random.randint(-intensity, intensity, arr.shape, dtype="int16")
        arr = np.clip(arr.astype("int16") + noise, 0, 255).astype("uint8")
        return Image.fromarray(arr)

          ```

        - 📄 **shapes.py**

          📄 *File Path*: `./src/plateshapez/perturbations/shapes.py`

          ```
          import random

from PIL import Image, ImageDraw

from .base import Perturbation, register


@register
class ShapesPerturbation(Perturbation):
    name = "shapes"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        x, y, w, h = region
        draw = ImageDraw.Draw(img, "RGBA")
        num_shapes: int = int(self.params.get("num_shapes", 15))
        min_size: int = int(self.params.get("min_size", 2))
        max_size: int = int(self.params.get("max_size", 10))

        for _ in range(num_shapes):
            sx = random.randint(x, x + w)
            sy = random.randint(y, y + h)
            size = random.randint(min_size, max_size)
            shape_type = random.choice(["rect", "ellipse", "triangle"])

            if shape_type == "rect":
                draw.rectangle((sx, sy, sx + size, sy + size), fill=(0, 0, 0, 255))
            elif shape_type == "ellipse":
                draw.ellipse((sx, sy, sx + size, sy + size), fill=(0, 0, 0, 255))
            else:
                draw.polygon(
                    [
                        (sx, sy),
                        (sx + random.randint(-size, size), sy + size),
                        (sx + size, sy + random.randint(-size, size)),
                    ],
                    fill=(0, 0, 0, 255),
                )

        return img

          ```

        - 📄 **texture.py**

          📄 *File Path*: `./src/plateshapez/perturbations/texture.py`

          ```
          import random
from typing import Literal

import numpy as np
from PIL import Image, ImageDraw

from .base import Perturbation, register


@register
class TexturePerturbation(Perturbation):
    """Overlay texture maps like scratches, dirt, or grain."""
    name = "texture"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        x, y, w, h = region
        texture_type: str = self.params.get("type", "grain")
        intensity: float = float(self.params.get("intensity", 0.3))
        
        if texture_type == "grain":
            return self._apply_grain(img, region, intensity)
        elif texture_type == "scratches":
            return self._apply_scratches(img, region, intensity)
        elif texture_type == "dirt":
            return self._apply_dirt(img, region, intensity)
        else:
            return img

    def _apply_grain(self, img: Image.Image, region: tuple[int, int, int, int], intensity: float) -> Image.Image:
        """Apply film grain texture."""
        x, y, w, h = region
        arr = np.array(img)
        
        # Generate grain noise
        grain = np.random.normal(0, intensity * 255, (h, w, 3))
        
        # Apply only to the overlay region
        region_slice = arr[y:y+h, x:x+w]
        region_slice = np.clip(region_slice.astype(np.float32) + grain, 0, 255).astype(np.uint8)
        arr[y:y+h, x:x+w] = region_slice
        
        return Image.fromarray(arr)

    def _apply_scratches(self, img: Image.Image, region: tuple[int, int, int, int], intensity: float) -> Image.Image:
        """Apply scratch texture."""
        x, y, w, h = region
        draw = ImageDraw.Draw(img, "RGBA")
        
        num_scratches = int(intensity * 20)
        for _ in range(num_scratches):
            # Random scratch within region
            sx1 = random.randint(x, x + w)
            sy1 = random.randint(y, y + h)
            sx2 = sx1 + random.randint(-20, 20)
            sy2 = sy1 + random.randint(-20, 20)
            
            # Ensure scratch stays within region
            sx2 = max(x, min(x + w, sx2))
            sy2 = max(y, min(y + h, sy2))
            
            # Dark scratch line
            alpha = int(intensity * 128)
            draw.line([(sx1, sy1), (sx2, sy2)], fill=(0, 0, 0, alpha), width=1)
        
        return img

    def _apply_dirt(self, img: Image.Image, region: tuple[int, int, int, int], intensity: float) -> Image.Image:
        """Apply dirt spots texture."""
        x, y, w, h = region
        draw = ImageDraw.Draw(img, "RGBA")
        
        num_spots = int(intensity * 15)
        for _ in range(num_spots):
            # Random dirt spot within region
            spot_x = random.randint(x, x + w - 5)
            spot_y = random.randint(y, y + h - 5)
            spot_size = random.randint(2, 8)
            
            # Dark dirt spot
            alpha = int(intensity * 100)
            color = (random.randint(20, 60), random.randint(20, 60), random.randint(20, 60), alpha)
            draw.ellipse(
                [(spot_x, spot_y), (spot_x + spot_size, spot_y + spot_size)],
                fill=color
            )
        
        return img
          ```

        - 📄 **warp.py**

          📄 *File Path*: `./src/plateshapez/perturbations/warp.py`

          ```
          import cv2
import numpy as np
from PIL import Image

from .base import Perturbation, register


@register
class WarpPerturbation(Perturbation):
    """Mild geometric warping perturbation."""
    name = "warp"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        """Apply a mild geometric warp."""
        x, y, w, h = region
        intensity: float = float(self.params.get("intensity", 5.0))
        frequency: float = float(self.params.get("frequency", 20.0))
        
        arr: np.ndarray = np.array(img)
        img_h, img_w, _ = arr.shape
        
        # Create displacement maps
        dx, dy = np.meshgrid(np.arange(img_w), np.arange(img_h))
        dx = dx + np.sin(dy / frequency) * intensity
        dy = dy + np.cos(dx / frequency) * intensity
        dx = np.clip(dx, 0, img_w - 1).astype(np.float32)
        dy = np.clip(dy, 0, img_h - 1).astype(np.float32)
        
        remap: np.ndarray = cv2.remap(arr, dx, dy, interpolation=cv2.INTER_LINEAR)
        return Image.fromarray(remap)

          ```

      - 📄 **pipeline.py**

        📄 *File Path*: `./src/plateshapez/pipeline.py`

        ```
        import json
import random
import time
from pathlib import Path
from typing import Any, TypedDict

import numpy as np
from PIL import Image

from plateshapez.perturbations.base import PERTURBATION_REGISTRY
from plateshapez.utils.io import iter_backgrounds, iter_overlays, save_image, save_metadata
from plateshapez.utils.overlay import calculate_center_position, ensure_rgb, ensure_rgba


class DatasetGenerator:
    class PerturbationConf(TypedDict, total=False):
        name: str
        params: dict[str, Any]

    def __init__(
        self,
        bg_dir: str | Path,
        overlay_dir: str | Path,
        out_dir: str | Path,
        perturbations: list["DatasetGenerator.PerturbationConf"] | None = None,
        random_seed: int | None = None,
    ) -> None:
        self.bg_dir: Path = Path(bg_dir)
        self.ov_dir: Path = Path(overlay_dir)
        self.out_dir: Path = Path(out_dir)
        self.img_dir: Path = self.out_dir / "images"
        self.label_dir: Path = self.out_dir / "labels"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.label_dir.mkdir(parents=True, exist_ok=True)
        self.perturbations: list[DatasetGenerator.PerturbationConf] = perturbations or []
        self.random_seed: int | None = random_seed

    def run(self, n_variants: int = 5) -> None:
        """Generate dataset with deterministic seeding."""
        # Deterministic seeding for reproducibility
        if self.random_seed is not None:
            random.seed(self.random_seed)
            np.random.seed(self.random_seed)
            # Also seed PIL's internal random for consistent image operations
            try:
                from PIL import ImageFilter
                # PIL uses Python's random module internally
            except ImportError:
                pass

        backgrounds = list(iter_backgrounds(self.bg_dir))
        overlays = list(iter_overlays(self.ov_dir))
        
        if not backgrounds:
            raise ValueError(f"No background images found in {self.bg_dir}")
        if not overlays:
            raise ValueError(f"No overlay images found in {self.ov_dir}")

        total_images = 0
        for bg_path in backgrounds:
            bg = ensure_rgb(Image.open(bg_path))
            for ov_path in overlays:
                overlay = ensure_rgba(Image.open(ov_path))
                position = calculate_center_position(bg, overlay)
                ow, oh = overlay.size
                bx, by = position

                for i in range(n_variants):
                    # Create composite image
                    img = bg.copy()
                    img.paste(overlay, position, overlay)

                    # Apply perturbations
                    applied: list[dict[str, Any]] = []
                    for perturbation_conf in self.perturbations:
                        name = perturbation_conf["name"]
                        if name not in PERTURBATION_REGISTRY:
                            raise ValueError(f"Unknown perturbation: {name}")
                        
                        cls = PERTURBATION_REGISTRY[name]
                        pert = cls(**perturbation_conf.get("params", {}))
                        img = pert.apply(img, (bx, by, ow, oh))
                        applied.append(pert.serialize())

                    # Generate deterministic filename
                    fname = f"{bg_path.stem}_{ov_path.stem}_{i:03d}.png"
                    
                    # Save image and metadata
                    save_image(img, self.img_dir / fname)
                    
                    metadata: dict[str, Any] = {
                        "background": bg_path.name,
                        "overlay": ov_path.name,
                        "overlay_position": [bx, by],
                        "overlay_size": [ow, oh],
                        "perturbations": applied,
                        "random_seed": self.random_seed,
                        "variant_index": i,
                    }
                    save_metadata(metadata, self.label_dir / fname.replace(".png", ".json"))
                    
                    total_images += 1
                    print(f"✓ Generated {fname} ({total_images} total)")
        
        print(f"\n🎉 Dataset generation complete! Generated {total_images} images.")

        ```

      - 📁 **utils/**
        - 📄 **__init__.py**

          📄 *File Path*: `./src/plateshapez/utils/__init__.py`

          ```
          
          ```

        - 📄 **io.py**

          📄 *File Path*: `./src/plateshapez/utils/io.py`

          ```
          from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from PIL import Image


def load_image(path: str | Path) -> Image.Image:
    """Load an image from file path."""
    return Image.open(path)


def save_image(image: Image.Image, path: str | Path) -> None:
    """Save an image to file path."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    image.save(path)


def save_metadata(metadata: dict, path: str | Path) -> None:
    """Save metadata as JSON to file path."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)


def iter_images(directory: str | Path, extensions: list[str] | None = None) -> Iterator[Path]:
    """Iterate over image files in a directory."""
    if extensions is None:
        extensions = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"]
    
    directory = Path(directory)
    if not directory.exists():
        return
    
    for ext in extensions:
        yield from directory.glob(f"*{ext}")
        yield from directory.glob(f"*{ext.upper()}")


def iter_backgrounds(directory: str | Path) -> Iterator[Path]:
    """Iterate over background images (typically JPG)."""
    return iter_images(directory, [".jpg", ".jpeg"])


def iter_overlays(directory: str | Path) -> Iterator[Path]:
    """Iterate over overlay images (typically PNG with alpha)."""
    return iter_images(directory, [".png"])
          ```

        - 📄 **overlay.py**

          📄 *File Path*: `./src/plateshapez/utils/overlay.py`

          ```
          from __future__ import annotations

from typing import Tuple

from PIL import Image


def calculate_center_position(
    background: Image.Image, overlay: Image.Image
) -> Tuple[int, int]:
    """Calculate position to center overlay on background."""
    bg_w, bg_h = background.size
    ov_w, ov_h = overlay.size
    x = (bg_w - ov_w) // 2
    y = (bg_h - ov_h) // 2
    return (x, y)


def paste_overlay(
    background: Image.Image, 
    overlay: Image.Image, 
    position: Tuple[int, int] | None = None
) -> Image.Image:
    """Paste overlay onto background at specified position (or center if None)."""
    result = background.copy()
    
    if position is None:
        position = calculate_center_position(background, overlay)
    
    # Ensure overlay has alpha channel for proper compositing
    if overlay.mode != "RGBA":
        overlay = overlay.convert("RGBA")
    
    result.paste(overlay, position, overlay)
    return result


def get_overlay_region(
    overlay: Image.Image, position: Tuple[int, int]
) -> Tuple[int, int, int, int]:
    """Get the region (x, y, width, height) occupied by overlay at position."""
    x, y = position
    w, h = overlay.size
    return (x, y, w, h)


def ensure_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is in RGB mode."""
    if image.mode != "RGB":
        return image.convert("RGB")
    return image


def ensure_rgba(image: Image.Image) -> Image.Image:
    """Ensure image is in RGBA mode."""
    if image.mode != "RGBA":
        return image.convert("RGBA")
    return image
          ```

    - 📁 **plateshapez.egg-info/**
      - 📄 **PKG-INFO**
      - 📄 **SOURCES.txt**
      - 📄 **dependency_links.txt**
      - 📄 **entry_points.txt**
      - 📄 **requires.txt**
      - 📄 **top_level.txt**
  - 📁 **tests/**
    - 📄 **__init__.py**

      📄 *File Path*: `./tests/__init__.py`

      ```
      
      ```

    - 📄 **test_config.py**

      📄 *File Path*: `./tests/test_config.py`

      ```
      import json
import tempfile
from pathlib import Path

import pytest
import yaml

from plateshapez.config import load_config, DEFAULTS


class TestConfigSystem:
    """Test configuration loading and merging."""

    def test_defaults_loaded_without_file(self):
        """Test that defaults are loaded when no config file is provided."""
        cfg = load_config()
        
        # Should match DEFAULTS
        assert cfg == DEFAULTS
        assert cfg["dataset"]["n_variants"] == 10
        assert cfg["dataset"]["random_seed"] == 1337

    def test_yaml_config_file_loading(self):
        """Test loading YAML configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 25,
                    "backgrounds": "./custom_bg",
                }
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Should merge with defaults
            assert cfg["dataset"]["n_variants"] == 25
            assert cfg["dataset"]["backgrounds"] == "./custom_bg"
            # Defaults should still be present
            assert cfg["dataset"]["random_seed"] == 1337
            assert cfg["dataset"]["overlays"] == "./overlays"
            
            Path(f.name).unlink()

    def test_json_config_file_loading(self):
        """Test loading JSON configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_config = {
                "dataset": {
                    "output": "./custom_output",
                    "random_seed": 9999,
                }
            }
            json.dump(json_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Should merge with defaults
            assert cfg["dataset"]["output"] == "./custom_output"
            assert cfg["dataset"]["random_seed"] == 9999
            # Defaults should still be present
            assert cfg["dataset"]["n_variants"] == 10
            
            Path(f.name).unlink()

    def test_cli_overrides_precedence(self):
        """Test that CLI overrides have highest precedence."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 50,
                }
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            # CLI override should win
            cfg = load_config(f.name, cli_overrides={"n_variants": 100})
            
            assert cfg["dataset"]["n_variants"] == 100
            
            Path(f.name).unlink()

    def test_verbose_debug_cli_overrides(self):
        """Test that verbose/debug flags affect logging level."""
        cfg_verbose = load_config(cli_overrides={"verbose": True})
        cfg_debug = load_config(cli_overrides={"debug": True})
        
        assert cfg_verbose["logging"]["level"] == "DEBUG"
        assert cfg_debug["logging"]["level"] == "DEBUG"

    def test_nonexistent_config_file_raises_error(self):
        """Test that nonexistent config files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_unsupported_config_format_raises_error(self):
        """Test that unsupported config formats raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("not a config file")
            f.flush()
            
            with pytest.raises(ValueError, match="Unsupported config format"):
                load_config(f.name)
            
            Path(f.name).unlink()

    def test_deep_merge_behavior(self):
        """Test that deep merging works correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 30,  # Override this
                    # Don't specify other dataset fields
                },
                "perturbations": [
                    {"name": "custom", "params": {"value": 123}}
                ],
                # Don't specify logging section
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Dataset section should be merged
            assert cfg["dataset"]["n_variants"] == 30  # Overridden
            assert cfg["dataset"]["backgrounds"] == "./backgrounds"  # From defaults
            assert cfg["dataset"]["overlays"] == "./overlays"  # From defaults
            assert cfg["dataset"]["random_seed"] == 1337  # From defaults
            
            # Perturbations should be completely replaced
            assert len(cfg["perturbations"]) == 1
            assert cfg["perturbations"][0]["name"] == "custom"
            
            # Logging should remain from defaults
            assert cfg["logging"]["level"] == "INFO"
            assert cfg["logging"]["save_metadata"] is True
            
            Path(f.name).unlink()

      ```

    - 📄 **test_integration.py**

      📄 *File Path*: `./tests/test_integration.py`

      ```
      import subprocess
import tempfile
from pathlib import Path

import pytest
from PIL import Image


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def sample_data(self):
        """Create sample background and overlay images for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "backgrounds"
            overlay_dir = temp_path / "overlays"
            
            bg_dir.mkdir()
            overlay_dir.mkdir()
            
            # Create sample background
            bg_img = Image.new("RGB", (300, 200), color="green")
            bg_img.save(bg_dir / "sample_bg.jpg")
            
            # Create sample overlay with transparency
            overlay_img = Image.new("RGBA", (80, 40), color=(255, 255, 0, 200))
            overlay_img.save(overlay_dir / "sample_overlay.png")
            
            yield {
                "bg_dir": bg_dir,
                "overlay_dir": overlay_dir,
                "temp_dir": temp_path,
            }

    def test_cli_list_command(self):
        """Test that 'advplate list' command works and shows perturbations."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "list"],
            capture_output=True,
            text=True,
            cwd="/home/bakobi/repos/music/benjordan/plateshapez"
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should contain built-in perturbations
        assert "shapes" in output
        assert "noise" in output
        assert "warp" in output
        assert "texture" in output

    def test_cli_version_command(self):
        """Test that 'advplate version' command works."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "version"],
            capture_output=True,
            text=True,
            cwd="/home/bakobi/repos/music/benjordan/plateshapez"
        )
        
        assert result.returncode == 0
        assert "plateshapez" in result.stdout

    def test_cli_info_command(self):
        """Test that 'advplate info' command shows configuration."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "info"],
            capture_output=True,
            text=True,
            cwd="/home/bakobi/repos/music/benjordan/plateshapez"
        )
        
        assert result.returncode == 0
        output = result.stdout
        
        # Should show configuration sections
        assert "dataset" in output
        assert "perturbations" in output
        assert "logging" in output

    def test_cli_generate_dry_run(self, sample_data):
        """Test that 'advplate generate --dry-run' works without creating files."""
        output_dir = sample_data["temp_dir"] / "output"
        
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--dry-run",
            "--n_variants", "2"
        ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
        
        assert result.returncode == 0
        
        # Should not have created any files
        assert not output_dir.exists()
        
        # Should show dry run information
        assert "Dry Run" in result.stdout

    def test_cli_generate_with_sample_data(self, sample_data):
        """Test full generation pipeline with sample data."""
        output_dir = sample_data["temp_dir"] / "dataset"
        
        # Create a simple config file
        config_file = sample_data["temp_dir"] / "config.yaml"
        config_content = f"""
dataset:
  backgrounds: "{sample_data['bg_dir']}"
  overlays: "{sample_data['overlay_dir']}"
  output: "{output_dir}"
  n_variants: 2
  random_seed: 42

perturbations:
  - name: shapes
    params:
      num_shapes: 3
      min_size: 2
      max_size: 5
"""
        config_file.write_text(config_content)
        
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--config", str(config_file)
        ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
        
        assert result.returncode == 0
        
        # Check that files were created
        img_dir = output_dir / "images"
        label_dir = output_dir / "labels"
        
        assert img_dir.exists()
        assert label_dir.exists()
        
        # Should have 2 variants (1 bg × 1 overlay × 2 variants)
        images = list(img_dir.glob("*.png"))
        labels = list(label_dir.glob("*.json"))
        
        assert len(images) == 2
        assert len(labels) == 2
        
        # Check that images are valid
        for img_path in images:
            img = Image.open(img_path)
            assert img.size == (300, 200)  # Same as background

    def test_cli_error_handling_missing_directories(self):
        """Test CLI error handling for missing directories."""
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--n_variants", "1"
        ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
        
        # Should fail gracefully
        assert result.returncode == 1
        assert "Configuration error" in result.stdout or "Error" in result.stdout or "Error" in result.stderr

    def test_cli_verbose_flag(self, sample_data):
        """Test that verbose flag produces more output."""
        config_file = sample_data["temp_dir"] / "config.yaml"
        config_content = f"""
dataset:
  backgrounds: "{sample_data['bg_dir']}"
  overlays: "{sample_data['overlay_dir']}"
  output: "{sample_data['temp_dir'] / 'output'}"
  n_variants: 1
"""
        config_file.write_text(config_content)
        
        # Run with verbose flag
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--config", str(config_file),
            "--verbose"
        ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
        
        assert result.returncode == 0
        
        # Verbose output should contain additional information
        output = result.stdout
        assert len(output) > 0  # Should have some output


class TestAPIIntegration:
    """Integration tests for Python API."""

    def test_api_basic_usage(self):
        """Test basic API usage as shown in project spec."""
        from plateshapez import DatasetGenerator
        from plateshapez.perturbations import PERTURBATION_REGISTRY
        
        # Should be able to import main components
        assert DatasetGenerator is not None
        assert PERTURBATION_REGISTRY is not None
        assert len(PERTURBATION_REGISTRY) >= 4  # At least shapes, noise, warp, texture

    def test_api_perturbation_registry_access(self):
        """Test accessing perturbation registry via API."""
        from plateshapez.perturbations.base import PERTURBATION_REGISTRY
        
        # Should contain expected perturbations
        expected = {"shapes", "noise", "warp", "texture"}
        actual = set(PERTURBATION_REGISTRY.keys())
        assert expected.issubset(actual)

    def test_api_config_loading(self):
        """Test config loading via API."""
        from plateshapez.config import load_config
        
        # Should load defaults without error
        cfg = load_config()
        assert "dataset" in cfg
        assert "perturbations" in cfg
        assert "logging" in cfg

      ```

    - 📄 **test_perturbations.py**

      📄 *File Path*: `./tests/test_perturbations.py`

      ```
      import pytest
from PIL import Image
import numpy as np

from plateshapez.perturbations.base import PERTURBATION_REGISTRY, register, Perturbation
from plateshapez.perturbations.shapes import ShapesPerturbation
from plateshapez.perturbations.noise import NoisePerturbation
from plateshapez.perturbations.warp import WarpPerturbation
from plateshapez.perturbations.texture import TexturePerturbation


class TestPerturbationRegistry:
    """Test perturbation registry behavior."""

    def test_registry_contains_built_ins(self):
        """Test that all built-in perturbations are registered."""
        expected_perturbations = {"shapes", "noise", "warp", "texture"}
        registered_names = set(PERTURBATION_REGISTRY.keys())
        assert expected_perturbations.issubset(registered_names)

    def test_duplicate_registration_raises_error(self):
        """Test that registering duplicate names raises ValueError."""
        
        with pytest.raises(ValueError, match="Duplicate perturbation name"):
            @register
            class DuplicateShapes(Perturbation):
                name = "shapes"  # Duplicate name
                
                def apply(self, img, region):
                    return img

    def test_registry_get_perturbation(self):
        """Test getting perturbations from registry."""
        shapes_cls = PERTURBATION_REGISTRY["shapes"]
        assert shapes_cls == ShapesPerturbation
        assert shapes_cls.name == "shapes"


class TestShapesPerturbation:
    """Test shapes perturbation correctness."""

    def test_shapes_stay_within_bounds(self):
        """Test that shapes are drawn within the specified region."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 30, 30)  # x, y, w, h
        
        perturbation = ShapesPerturbation(num_shapes=5, min_size=2, max_size=5)
        result = perturbation.apply(img, region)
        
        assert isinstance(result, Image.Image)
        assert result.size == img.size

    def test_shapes_intensity_affects_count(self):
        """Test that num_shapes parameter affects the number of shapes drawn."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 50, 50)
        
        # Convert to array to check for changes
        original_array = np.array(img)
        
        perturbation = ShapesPerturbation(num_shapes=20)
        result = perturbation.apply(img, region)
        result_array = np.array(result)
        
        # Should have some differences due to shapes being drawn
        assert not np.array_equal(original_array, result_array)

    def test_shapes_serialization(self):
        """Test perturbation serialization."""
        params = {"num_shapes": 15, "min_size": 3, "max_size": 8}
        perturbation = ShapesPerturbation(**params)
        serialized = perturbation.serialize()
        
        assert serialized["type"] == "shapes"
        assert serialized["params"] == params


class TestNoisePerturbation:
    """Test noise perturbation correctness."""

    def test_noise_intensity_measurable(self):
        """Test that noise intensity affects the image measurably."""
        img = Image.new("RGB", (50, 50), color=(128, 128, 128))
        region = (0, 0, 50, 50)
        
        original_array = np.array(img)
        
        # Low intensity noise
        low_noise = NoisePerturbation(intensity=5)
        low_result = low_noise.apply(img, region)
        low_array = np.array(low_result)
        
        # High intensity noise
        high_noise = NoisePerturbation(intensity=50)
        high_result = high_noise.apply(img, region)
        high_array = np.array(high_result)
        
        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))
        
        # High intensity should create more difference
        assert high_diff > low_diff
        assert low_diff > 0  # Some change should occur

    def test_noise_bounds_respected(self):
        """Test that noise doesn't push pixels outside valid range."""
        img = Image.new("RGB", (50, 50), color="white")
        region = (0, 0, 50, 50)
        
        perturbation = NoisePerturbation(intensity=100)  # High intensity
        result = perturbation.apply(img, region)
        result_array = np.array(result)
        
        # All values should be in valid range [0, 255]
        assert np.all(result_array >= 0)
        assert np.all(result_array <= 255)


class TestWarpPerturbation:
    """Test warp perturbation correctness."""

    def test_warp_preserves_image_size(self):
        """Test that warping preserves image dimensions."""
        img = Image.new("RGB", (100, 100), color="red")
        region = (20, 20, 60, 60)
        
        perturbation = WarpPerturbation(intensity=5.0, frequency=20.0)
        result = perturbation.apply(img, region)
        
        assert result.size == img.size
        assert isinstance(result, Image.Image)

    def test_warp_intensity_affects_distortion(self):
        """Test that warp intensity affects the amount of distortion."""
        img = Image.new("RGB", (100, 100), color="blue")
        region = (0, 0, 100, 100)
        
        original_array = np.array(img)
        
        # Low intensity warp
        low_warp = WarpPerturbation(intensity=1.0)
        low_result = low_warp.apply(img, region)
        low_array = np.array(low_result)
        
        # High intensity warp
        high_warp = WarpPerturbation(intensity=10.0)
        high_result = high_warp.apply(img, region)
        high_array = np.array(high_result)
        
        # Both should be different from original
        assert not np.array_equal(original_array, low_array)
        assert not np.array_equal(original_array, high_array)


class TestTexturePerturbation:
    """Test texture perturbation correctness."""

    def test_texture_types_work(self):
        """Test that different texture types can be applied."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 80, 80)
        
        texture_types = ["grain", "scratches", "dirt"]
        
        for texture_type in texture_types:
            perturbation = TexturePerturbation(type=texture_type, intensity=0.5)
            result = perturbation.apply(img, region)
            
            assert isinstance(result, Image.Image)
            assert result.size == img.size

    def test_texture_intensity_affects_result(self):
        """Test that texture intensity affects the result."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (0, 0, 100, 100)
        
        original_array = np.array(img)
        
        # Low intensity
        low_texture = TexturePerturbation(type="grain", intensity=0.1)
        low_result = low_texture.apply(img, region)
        low_array = np.array(low_result)
        
        # High intensity
        high_texture = TexturePerturbation(type="grain", intensity=0.8)
        high_result = high_texture.apply(img, region)
        high_array = np.array(high_result)
        
        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))
        
        # High intensity should create more difference
        assert high_diff > low_diff

      ```

    - 📄 **test_pipeline.py**

      📄 *File Path*: `./tests/test_pipeline.py`

      ```
      import json
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from plateshapez.pipeline import DatasetGenerator


class TestDatasetGenerator:
    """Test DatasetGenerator pipeline behavior."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "backgrounds"
            overlay_dir = temp_path / "overlays"
            output_dir = temp_path / "output"
            
            bg_dir.mkdir()
            overlay_dir.mkdir()
            output_dir.mkdir()
            
            # Create test images
            bg_img = Image.new("RGB", (200, 150), color="blue")
            bg_img.save(bg_dir / "test_bg.jpg")
            
            overlay_img = Image.new("RGBA", (50, 30), color=(255, 0, 0, 128))
            overlay_img.save(overlay_dir / "test_overlay.png")
            
            yield {
                "bg_dir": bg_dir,
                "overlay_dir": overlay_dir,
                "output_dir": output_dir,
            }

    def test_pipeline_generates_expected_count(self, temp_dirs):
        """Test that pipeline generates expected number of images."""
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=[],
            random_seed=42,
        )
        
        n_variants = 3
        gen.run(n_variants=n_variants)
        
        # Check generated files
        img_dir = temp_dirs["output_dir"] / "images"
        label_dir = temp_dirs["output_dir"] / "labels"
        
        assert img_dir.exists()
        assert label_dir.exists()
        
        # Should have n_variants images (1 bg × 1 overlay × n_variants)
        images = list(img_dir.glob("*.png"))
        labels = list(label_dir.glob("*.json"))
        
        assert len(images) == n_variants
        assert len(labels) == n_variants

    def test_metadata_contains_correct_keys(self, temp_dirs):
        """Test that metadata JSON contains all required keys."""
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=[{"name": "shapes", "params": {"num_shapes": 5}}],
            random_seed=42,
        )
        
        gen.run(n_variants=1)
        
        # Check metadata
        label_dir = temp_dirs["output_dir"] / "labels"
        metadata_files = list(label_dir.glob("*.json"))
        assert len(metadata_files) == 1
        
        with open(metadata_files[0]) as f:
            metadata = json.load(f)
        
        required_keys = {
            "background",
            "overlay", 
            "overlay_position",
            "overlay_size",
            "perturbations",
            "random_seed",
            "variant_index",
        }
        
        assert set(metadata.keys()) >= required_keys
        assert metadata["random_seed"] == 42
        assert metadata["variant_index"] == 0
        assert len(metadata["perturbations"]) == 1
        assert metadata["perturbations"][0]["type"] == "shapes"

    def test_deterministic_behavior_with_seed(self, temp_dirs):
        """Test that same seed produces identical results."""
        perturbations = [{"name": "noise", "params": {"intensity": 10}}]
        
        # First run
        gen1 = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"] / "run1",
            perturbations=perturbations,
            random_seed=123,
        )
        gen1.run(n_variants=2)
        
        # Second run with same seed
        gen2 = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"] / "run2",
            perturbations=perturbations,
            random_seed=123,
        )
        gen2.run(n_variants=2)
        
        # Compare generated images
        run1_images = sorted((temp_dirs["output_dir"] / "run1" / "images").glob("*.png"))
        run2_images = sorted((temp_dirs["output_dir"] / "run2" / "images").glob("*.png"))
        
        assert len(run1_images) == len(run2_images) == 2
        
        # Images should be identical (deterministic)
        for img1_path, img2_path in zip(run1_images, run2_images):
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            
            # Convert to arrays and compare
            import numpy as np
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            assert np.array_equal(arr1, arr2), f"Images {img1_path.name} and {img2_path.name} differ"

    def test_error_on_missing_directories(self):
        """Test that missing directories raise appropriate errors."""
        with pytest.raises(ValueError, match="No background images found"):
            gen = DatasetGenerator(
                bg_dir="/nonexistent/bg",
                overlay_dir="/nonexistent/overlay", 
                out_dir="/tmp/test_out",
                random_seed=42,
            )
            gen.run(n_variants=1)

    def test_unknown_perturbation_raises_error(self, temp_dirs):
        """Test that unknown perturbation names raise ValueError."""
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=[{"name": "nonexistent_perturbation"}],
            random_seed=42,
        )
        
        with pytest.raises(ValueError, match="Unknown perturbation"):
            gen.run(n_variants=1)

      ```

  - 📄 **uv.lock**
  - 📄 **walk.py**

    📄 *File Path*: `./walk.py`

    ```
    import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import argparse


class DirectoryMapper:
    def __init__(
        self,
        ignore_patterns: Optional[List[str]]=None,
        max_depth: int = 10,
        include_content: bool = False,
        content_extensions: Optional[List[str]]=None,
        ignore_hidden: bool = True
    ):
        self.ignore_patterns = ignore_patterns or ['node_modules', '.git', 'dist', 'build', '__pycache__']
        self.max_depth = max_depth
        self.include_content = include_content
        self.content_extensions = content_extensions  # Allow None to include all extensions
        self.ignore_hidden = ignore_hidden

    def should_ignore(self, name: str) -> bool:
        """Check if a file or directory should be ignored."""
        if self.ignore_hidden and name.startswith('.'):
            return True
        return any(pattern in name for pattern in self.ignore_patterns)

    def create_file_node(self, file_path: str) -> Dict:
        """Create a node representing a file."""
        stats = os.stat(file_path)
        node = {
            'type': 'file',
            'name': os.path.basename(file_path),
            'path': file_path,
            'size': stats.st_size,
            'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
        }
    
        if self.include_content:
            file_ext = os.path.splitext(file_path)[1].lower()  # Get the file extension
            if self.content_extensions is None or file_ext in self.content_extensions:
                print(f"Reading content for: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        node['content'] = content
                        print(f"Successfully read {len(content)} bytes from {file_path}")
                except Exception as e:
                    print(f"Warning: Could not read content of {file_path}: {e}")
            else:
                print(f"Skipping content for {file_path} - extension not in allowed list")
    
        return node

    def map_directory(self, dir_path: str, depth: int = 0) -> Dict:
        """Recursively map a directory structure."""
        if depth >= self.max_depth:
            return {
                'type': 'directory',
                'name': os.path.basename(dir_path),
                'path': dir_path,
                'children': {'[MAX_DEPTH_REACHED]': {'type': 'file', 'name': '', 'path': ''}}
            }

        result = {
            'type': 'directory',
            'name': os.path.basename(dir_path),
            'path': dir_path,
            'children': {}
        }

        try:
            for entry in os.listdir(dir_path):
                if self.should_ignore(entry):
                    continue

                full_path = os.path.join(dir_path, entry)
                if os.path.isdir(full_path):
                    result['children'][entry] = self.map_directory(full_path, depth + 1)
                else:
                    result['children'][entry] = self.create_file_node(full_path)
        except Exception as e:
            print(f"Error mapping directory {dir_path}: {e}")

        return result

    def generate_markdown(self, node: Dict, level: int = 0) -> str:
        """Generate a markdown representation of the directory structure with file contents."""
        indent = '  ' * level
        output = ''

        if node['type'] == 'directory':
            output += f"{indent}- 📁 **{node['name']}/**\n"
            if 'children' in node:
                for child in sorted(node['children'].values(), key=lambda x: x['name']):
                    output += self.generate_markdown(child, level + 1)
        else:
            output += f"{indent}- 📄 **{node['name']}**\n"
            if self.include_content and 'content' in node:
                file_path = node['path']
                content = node['content']
                # Escape backticks in content
                content = content.replace('```', '```')
                output += f"\n{indent}  📄 *File Path*: `{file_path}`\n\n"
                output += f"{indent}  ```\n"
                output += f"{indent}  {content}\n"
                output += f"{indent}  ```\n\n"

        return output

    def save_map(self, node: Dict, output_path: str, file_format: str = 'json'):
        """Save the directory map to a file."""
        if file_format == 'markdown':
            content = "# Directory Structure\n\n" + self.generate_markdown(node)
        else:
            content = json.dumps(node, indent=2)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)


def main():
    parser = argparse.ArgumentParser(description='Map a directory structure')
    parser.add_argument('directory', help='Directory to map')
    parser.add_argument('output', help='Output file path')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown', help='Output format (default: markdown)')
    parser.add_argument('--max-depth', type=int, default=10, help='Maximum depth to traverse (default: 10)')
    parser.add_argument('--include-content', action='store_true', help='Include file contents in the map')
    parser.add_argument('--no-ignore-hidden', action='store_true', help='Do not ignore hidden files')
    parser.add_argument('--content-extensions', nargs='*', help='File extensions to include content from (default: all files if --include-content is used)')

    args = parser.parse_args()
    
    # Debug: Print arguments
    print("Arguments received:")
    print(f"  Directory: {args.directory}")
    print(f"  Output: {args.output}")
    print(f"  Format: {args.format}")
    print(f"  Include content: {args.include_content}")
    print(f"  Max depth: {args.max_depth}")
    print(f"  Ignore hidden: {not args.no_ignore_hidden}")
    print(f"  Content extensions: {args.content_extensions}")

    if args.include_content and args.content_extensions is None:
        # Include content from all files
        content_extensions = None
    else:
        content_extensions = args.content_extensions

    mapper = DirectoryMapper(
        max_depth=args.max_depth,
        include_content=args.include_content,
        content_extensions=content_extensions,
        ignore_hidden=not args.no_ignore_hidden
    )

    print(f"\nMapping directory: {args.directory}")
    dir_map = mapper.map_directory(args.directory)
    first_child = None
    # Debug: Print a sample of the map structure
    print("\nMap structure sample:")
    if 'children' in dir_map:
        first_child = next(iter(dir_map['children'].values()), None)
    if first_child:
        print(f"Sample child node: {json.dumps(first_child, indent=2)[:200]}...")

    mapper.save_map(dir_map, args.output, args.format)
    print(f"\nMap saved to: {args.output}")


if __name__ == '__main__':
    main()

    ```

