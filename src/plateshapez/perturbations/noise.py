import numpy as np
from PIL import Image

from .base import Perturbation, register


@register
class NoisePerturbation(Perturbation):
    name = "noise"

    def apply(self, img: Image.Image, region: tuple[int, int, int, int]) -> Image.Image:
        intensity: int = int(self.params.get("intensity", 15))
        scope: str = self.params.get("scope", "region")
        arr: np.ndarray = np.array(img)

        if scope == "global":
            # Apply noise to entire image
            noise: np.ndarray = np.random.randint(-intensity, intensity, arr.shape, dtype="int16")
            arr = np.clip(arr.astype("int16") + noise, 0, 255).astype("uint8")
        else:
            # Apply noise only to region
            x, y, w, h = region
            target = arr[y : y + h, x : x + w]
            noise = np.random.randint(-intensity, intensity, target.shape, dtype="int16")
            target = np.clip(target.astype("int16") + noise, 0, 255).astype("uint8")
            arr[y : y + h, x : x + w] = target

        return Image.fromarray(arr)
