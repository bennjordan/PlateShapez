import json
import time
from pathlib import Path
from typing import Any, TypedDict

from PIL import Image

from src.plateshapez.perturbations.base import PERTURBATION_REGISTRY


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
    ) -> None:
        self.bg_dir: Path = Path(bg_dir)
        self.ov_dir: Path = Path(overlay_dir)
        self.out_dir: Path = Path(out_dir)
        self.img_dir: Path = self.out_dir / "images"
        self.label_dir: Path = self.out_dir / "labels"
        self.img_dir.mkdir(parents=True, exist_ok=True)
        self.label_dir.mkdir(parents=True, exist_ok=True)
        self.perturbations: list[DatasetGenerator.PerturbationConf] = perturbations or []

    def run(self, n_variants: int = 5) -> None:
        backgrounds: list[Path] = list(self.bg_dir.glob("*.jpg"))
        overlays: list[Path] = list(self.ov_dir.glob("*.png"))

        for bg_path in backgrounds:
            bg: Image.Image = Image.open(bg_path).convert("RGB")
            for ov_path in overlays:
                overlay: Image.Image = Image.open(ov_path).convert("RGBA")
                ow, oh = overlay.size
                bx, by = (bg.width // 2 - ow // 2, bg.height // 2 - oh // 2)

                for i in range(n_variants):
                    img: Image.Image = bg.copy()
                    img.paste(overlay, (bx, by), overlay)

                    applied: list[dict[str, Any]] = []
                    for perturbation_conf in self.perturbations:
                        name: str = perturbation_conf["name"]
                        cls = PERTURBATION_REGISTRY[name]
                        pert = cls(**perturbation_conf.get("params", {}))
                        img = pert.apply(img, (bx, by, ow, oh))
                        applied.append(pert.serialize())

                    fname = f"{bg_path.stem}_{ov_path.stem}_{i}_{int(time.time() * 1000)}.png"
                    img.save(self.img_dir / fname)

                    metadata: dict[str, Any] = {
                        "background": bg_path.name,
                        "overlay": ov_path.name,
                        "overlay_position": [bx, by],
                        "overlay_size": [ow, oh],
                        "perturbations": applied,
                    }
                    with open(self.label_dir / fname.replace(".png", ".json"), "w") as f:
                        json.dump(metadata, f, indent=2)
                    print("✓", fname)
