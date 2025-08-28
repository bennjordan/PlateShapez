from __future__ import annotations

from typing import Tuple

from PIL import Image


def calculate_center_position(background: Image.Image, overlay: Image.Image) -> Tuple[int, int]:
    """Calculate position to center overlay on background."""
    bg_w, bg_h = background.size
    ov_w, ov_h = overlay.size
    x = (bg_w - ov_w) // 2
    y = (bg_h - ov_h) // 2
    return (x, y)


def paste_overlay(
    background: Image.Image, overlay: Image.Image, position: Tuple[int, int] | None = None
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
    return image.convert("RGB") if image.mode != "RGB" else image


def ensure_rgba(image: Image.Image) -> Image.Image:
    """Ensure image is in RGBA mode."""
    return image.convert("RGBA") if image.mode != "RGBA" else image
