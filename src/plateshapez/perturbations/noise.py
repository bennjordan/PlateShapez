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
