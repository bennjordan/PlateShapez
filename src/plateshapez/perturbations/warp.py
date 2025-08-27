import cv2
import numpy as np
from PIL import Image

from .base import Perturbation, register


@register
class WarpPerturbation(Perturbation):
    name = "warp"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        """Apply a mild geometric warp."""
        arr: np.ndarray = np.array(img)
        h, w, _ = arr.shape
        dx, dy = np.meshgrid(np.arange(w), np.arange(h))
        dx = dx + np.sin(dy / 20.0) * 5
        dy = dy + np.cos(dx / 20.0) * 5
        dx = np.clip(dx, 0, w - 1).astype(np.float32)
        dy = np.clip(dy, 0, h - 1).astype(np.float32)
        remap: np.ndarray = cv2.remap(arr, dx, dy, interpolation=cv2.INTER_LINEAR)
        return Image.fromarray(remap)
