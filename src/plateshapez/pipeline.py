import random
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
        save_metadata: bool = True,
        verbose: bool = False,
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
        self.save_metadata: bool = save_metadata
        self.verbose: bool = verbose

    def run(self, n_variants: int = 5) -> None:
        """Generate dataset with deterministic seeding."""
        # Deterministic seeding for reproducibility
        if self.random_seed is not None:
            random.seed(self.random_seed)
            np.random.seed(self.random_seed)
            # Also seed PIL's internal random for consistent image operations
            # PIL uses Python's random module internally

        backgrounds = list(iter_backgrounds(self.bg_dir))
        overlays = list(iter_overlays(self.ov_dir))

        if not backgrounds:
            raise ValueError(f"No background images found in {self.bg_dir}")
        if not overlays:
            raise ValueError(f"No overlay images found in {self.ov_dir}")

        total_images = 0
        for bg_path in backgrounds:
            try:
                bg = ensure_rgb(Image.open(bg_path))
            except (IOError, OSError, ValueError) as e:
                if self.verbose:
                    print(f"Warning: Could not load background {bg_path}: {e}")
                continue

            for ov_path in overlays:
                try:
                    overlay = ensure_rgba(Image.open(ov_path))
                except (IOError, OSError, ValueError) as e:
                    if self.verbose:
                        print(f"Warning: Could not load overlay {ov_path}: {e}")
                    continue
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

                    # Only save metadata if enabled in config
                    if self.save_metadata:
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
                    if self.verbose:
                        print(f"✓ Generated {fname} ({total_images} total)")
                    elif total_images % 100 == 0:
                        print(f"✓ Generated {total_images} images so far...")

        print(f"\n🎉 Dataset generation complete! Generated {total_images} images.")
