import random

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

    def _apply_grain(
        self, img: Image.Image, region: tuple[int, int, int, int], intensity: float
    ) -> Image.Image:
        """Apply film grain texture."""
        x, y, w, h = region
        arr = np.array(img)

        # Apply only to the overlay region
        region_slice = arr[y : y + h, x : x + w]

        # Generate grain noise with same shape as region slice
        grain = np.random.normal(0, intensity * 255, region_slice.shape)

        region_slice = np.clip(region_slice.astype(np.float32) + grain, 0, 255).astype(np.uint8)
        arr[y : y + h, x : x + w] = region_slice

        return Image.fromarray(arr)

    def _apply_scratches(
        self, img: Image.Image, region: tuple[int, int, int, int], intensity: float
    ) -> Image.Image:
        """Apply scratch texture."""
        x, y, w, h = region
        draw = ImageDraw.Draw(img, "RGBA")

        num_scratches = int(intensity * 20)
        for _ in range(num_scratches):
            # Random scratch within region
            sx1 = random.randint(x, x + w - 1)
            sy1 = random.randint(y, y + h - 1)
            sx2 = sx1 + random.randint(-20, 20)
            sy2 = sy1 + random.randint(-20, 20)

            # Ensure scratch stays within region
            sx2 = max(x, min(x + w, sx2))
            sy2 = max(y, min(y + h, sy2))

            # Dark scratch line
            alpha = int(intensity * 128)
            draw.line([(sx1, sy1), (sx2, sy2)], fill=(0, 0, 0, alpha), width=1)

        return img

    def _apply_dirt(
        self, img: Image.Image, region: tuple[int, int, int, int], intensity: float
    ) -> Image.Image:
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
            draw.ellipse([(spot_x, spot_y), (spot_x + spot_size, spot_y + spot_size)], fill=color)

        return img
