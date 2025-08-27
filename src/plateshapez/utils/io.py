from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from PIL import Image


def load_image(path: str | Path) -> Image.Image | None:
    """Load an image from file path. Returns None if file cannot be read."""
    try:
        return Image.open(path)
    except (IOError, OSError, ValueError) as e:
        print(f"Warning: Could not load image {path}: {e}")
        return None


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
