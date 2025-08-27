import json
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from plateshapez.pipeline import DatasetGenerator


class TestDatasetGenerator:
    """Test DatasetGenerator pipeline behavior."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "backgrounds"
            overlay_dir = temp_path / "overlays"
            output_dir = temp_path / "output"

            bg_dir.mkdir()
            overlay_dir.mkdir()
            output_dir.mkdir()

            # Create test images
            bg_img = Image.new("RGB", (200, 150), color="blue")
            bg_img.save(bg_dir / "test_bg.jpg")

            overlay_img = Image.new("RGBA", (50, 30), color=(255, 0, 0, 128))
            overlay_img.save(overlay_dir / "test_overlay.png")

            yield {
                "bg_dir": bg_dir,
                "overlay_dir": overlay_dir,
                "output_dir": output_dir,
            }

    def test_pipeline_generates_expected_count(self, temp_dirs):
        """Test that pipeline generates expected number of images."""
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=[],
            random_seed=42,
        )

        n_variants = 3
        gen.run(n_variants=n_variants)

        # Check generated files
        img_dir = temp_dirs["output_dir"] / "images"
        label_dir = temp_dirs["output_dir"] / "labels"

        assert img_dir.exists()
        assert label_dir.exists()

        # Should have n_variants images (1 bg × 1 overlay × n_variants)
        images = list(img_dir.glob("*.png"))
        labels = list(label_dir.glob("*.json"))

        assert len(images) == n_variants
        assert len(labels) == n_variants

    def test_metadata_contains_correct_keys(self, temp_dirs):
        """Test that metadata JSON contains all required keys."""
        perturbations: list[DatasetGenerator.PerturbationConf] = [
            {"name": "noise", "params": {"intensity": 5}}
        ]
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=perturbations,
            random_seed=42,
        )

        gen.run(n_variants=1)

        # Check metadata
        label_dir = temp_dirs["output_dir"] / "labels"
        metadata_files = list(label_dir.glob("*.json"))
        assert len(metadata_files) == 1

        with open(metadata_files[0]) as f:
            metadata = json.load(f)

        required_keys = {
            "background",
            "overlay",
            "overlay_position",
            "overlay_size",
            "perturbations",
            "random_seed",
            "variant_index",
        }

        assert set(metadata.keys()) >= required_keys
        assert metadata["random_seed"] == 42
        assert metadata["variant_index"] == 0
        assert len(metadata["perturbations"]) == 1
        assert metadata["perturbations"][0]["type"] == "noise"

    def test_deterministic_behavior_with_seed(self, temp_dirs):
        """Test that same seed produces identical results."""
        perturbations: list[DatasetGenerator.PerturbationConf] = [
            {"name": "noise", "params": {"intensity": 10}}
        ]

        # First run
        gen1 = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"] / "run1",
            perturbations=perturbations,
            random_seed=123,
        )
        gen1.run(n_variants=2)

        # Second run with same seed
        gen2 = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"] / "run2",
            perturbations=perturbations,
            random_seed=123,
        )
        gen2.run(n_variants=2)

        # Compare generated images
        run1_images = sorted((temp_dirs["output_dir"] / "run1" / "images").glob("*.png"))
        run2_images = sorted((temp_dirs["output_dir"] / "run2" / "images").glob("*.png"))

        assert len(run1_images) == len(run2_images) == 2

        # Images should be identical (deterministic)
        for img1_path, img2_path in zip(run1_images, run2_images):
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)

            # Convert to arrays and compare
            import numpy as np

            arr1 = np.array(img1)
            arr2 = np.array(img2)

            assert np.array_equal(arr1, arr2), (
                f"Images {img1_path.name} and {img2_path.name} differ"
            )

    def test_error_on_missing_directories(self):
        """Test that missing directories raise appropriate errors."""
        # Test missing background images
        with pytest.raises(ValueError, match="No background images found"):
            gen = DatasetGenerator(
                bg_dir="/nonexistent/bg",
                overlay_dir="/nonexistent/overlay",
                out_dir="/tmp/test_out",
                random_seed=42,
            )
            gen.run(n_variants=1)

        # Test missing overlay images
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as bg_dir:
            # Create a dummy background image so bg_dir is not empty
            from PIL import Image
            img_path = os.path.join(bg_dir, "dummy_bg.png")
            Image.new("RGB", (10, 10)).save(img_path)

            with pytest.raises(ValueError, match="No overlay images found"):
                gen = DatasetGenerator(
                    bg_dir=bg_dir,
                    overlay_dir="/nonexistent/overlay",
                    out_dir="/tmp/test_out",
                    random_seed=42,
                )
                gen.run(n_variants=1)

    def test_unknown_perturbation_raises_error(self, temp_dirs):
        """Test that unknown perturbation names raise ValueError."""
        gen = DatasetGenerator(
            bg_dir=temp_dirs["bg_dir"],
            overlay_dir=temp_dirs["overlay_dir"],
            out_dir=temp_dirs["output_dir"],
            perturbations=[{"name": "nonexistent_perturbation"}],
            random_seed=42,
        )

        with pytest.raises(ValueError, match="Unknown perturbation"):
            gen.run(n_variants=1)
