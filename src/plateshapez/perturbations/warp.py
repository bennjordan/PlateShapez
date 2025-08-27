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
