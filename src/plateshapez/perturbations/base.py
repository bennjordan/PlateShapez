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
