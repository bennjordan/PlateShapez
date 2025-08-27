import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from plateshapez import DatasetGenerator

# Get repository root dynamically
REPO_ROOT = Path(__file__).resolve().parents[1]


class TestCLIIntegration:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def sample_data(self):
        """Create sample background and overlay images for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "backgrounds"
            overlay_dir = temp_path / "overlays"

            bg_dir.mkdir()
            overlay_dir.mkdir()

            # Create sample background
            bg_img = Image.new("RGB", (300, 200), color="green")
            bg_img.save(bg_dir / "sample_bg.jpg")

            # Create sample overlay with transparency
            overlay_img = Image.new("RGBA", (80, 40), color=(255, 255, 0, 200))
            overlay_img.save(overlay_dir / "sample_overlay.png")

            yield {
                "bg_dir": bg_dir,
                "overlay_dir": overlay_dir,
                "temp_dir": temp_path,
            }

    def test_cli_list_command(self):
        """Test that 'advplate list' command works and shows perturbations."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "list"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0
        output = result.stdout

        # Should contain built-in perturbations
        assert "shapes" in output
        assert "noise" in output
        assert "warp" in output
        assert "texture" in output

    def test_cli_version_command(self):
        """Test that 'advplate version' command works."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "version"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0
        assert "plateshapez" in result.stdout

    def test_cli_info_command(self):
        """Test that 'advplate info' command shows configuration."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "info"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0
        output = result.stdout

        # Should show configuration sections
        assert "dataset" in output
        assert "perturbations" in output
        assert "logging" in output

    def test_cli_generate_dry_run(self, sample_data):
        """Test that 'advplate generate --dry-run' works without creating files."""
        output_dir = sample_data["temp_dir"] / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "plateshapez",
                "generate",
                "--dry-run",
                "--n_variants",
                "2",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0

        # Should not have created any files
        assert not output_dir.exists()

        # Should show dry run information
        assert "Dry Run" in result.stdout

    def test_cli_generate_with_sample_data(self, sample_data):
        """Test full generation pipeline with sample data."""
        output_dir = sample_data["temp_dir"] / "dataset"

        # Create a simple config file
        config_file = sample_data["temp_dir"] / "config.yaml"
        config_content = f"""
dataset:
  backgrounds: "{sample_data["bg_dir"]}"
  overlays: "{sample_data["overlay_dir"]}"
  output: "{output_dir}"
  n_variants: 2
  random_seed: 42

perturbations:
  - name: shapes
    params:
      num_shapes: 3
      min_size: 2
      max_size: 5
"""
        config_file.write_text(config_content)

        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "generate", "--config", str(config_file)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0

        # Check that files were created
        img_dir = output_dir / "images"
        label_dir = output_dir / "labels"

        assert img_dir.exists()
        assert label_dir.exists()

        # Should have 2 variants (1 bg × 1 overlay × 2 variants)
        images = list(img_dir.glob("*.png"))
        labels = list(label_dir.glob("*.json"))

        assert len(images) == 2
        assert len(labels) == 2

        # Check that images are valid - test first and last to verify all are correct
        first_img = Image.open(images[0])
        last_img = Image.open(images[-1])
        assert first_img.size == (300, 200)  # Same as background
        assert last_img.size == (300, 200)  # Same as background

        # Verify all images can be opened without error
        assert all(Image.open(img_path).size == (300, 200) for img_path in images)

        # Check metadata structure - test first and last to verify schema
        def verify_metadata_structure(label_path):
            with open(label_path) as f:
                metadata = json.load(f)

            # Verify expected metadata fields
            required_fields = [
                "background",
                "overlay",
                "overlay_position",
                "overlay_size",
                "perturbations",
                "random_seed",
                "variant_index",
            ]
            assert all(field in metadata for field in required_fields)

            # Verify data types
            assert isinstance(metadata["overlay_position"], list)
            assert len(metadata["overlay_position"]) == 2
            assert isinstance(metadata["overlay_size"], list)
            assert len(metadata["overlay_size"]) == 2
            assert isinstance(metadata["perturbations"], list)
            assert isinstance(metadata["random_seed"], int)
            assert isinstance(metadata["variant_index"], int)
            return metadata

        # Verify first and last metadata files
        verify_metadata_structure(labels[0])
        verify_metadata_structure(labels[-1])

    def test_cli_error_handling_missing_directories(self):
        """Test CLI error handling for missing directories."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "generate", "--n_variants", "1"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        # Should fail gracefully
        assert result.returncode == 1
        assert (
            "Configuration error" in result.stdout
            or "Error" in result.stdout
            or "Error" in result.stderr
        )

    def test_cli_verbose_flag(self, sample_data):
        """Test that verbose flag produces more output."""
        config_file = sample_data["temp_dir"] / "config.yaml"
        config_content = f"""
dataset:
  backgrounds: "{sample_data["bg_dir"]}"
  overlays: "{sample_data["overlay_dir"]}"
  output: "{sample_data["temp_dir"] / "output"}"
  n_variants: 1
"""
        config_file.write_text(config_content)

        # Run with verbose flag
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-m",
                "plateshapez",
                "generate",
                "--config",
                str(config_file),
                "--verbose",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result.returncode == 0

        # Verbose output should contain additional information
        output = result.stdout
        assert len(output) > 0  # Should have some output

        # Should contain verbose-specific content
        assert "Generated" in output or "✓" in output

    def test_deterministic_behavior_with_metadata_consistency(self, sample_data):
        """Test that same seed produces identical results including metadata."""
        output_dir1 = sample_data["temp_dir"] / "dataset1"
        output_dir2 = sample_data["temp_dir"] / "dataset2"

        # Create identical config for both runs
        config_content1 = f"""
dataset:
  backgrounds: "{sample_data["bg_dir"]}"
  overlays: "{sample_data["overlay_dir"]}"
  output: "{output_dir1}"
  n_variants: 2
  random_seed: 12345

perturbations:
  - name: shapes
    params:
      num_shapes: 5
      min_size: 3
      max_size: 8
  - name: noise
    params:
      intensity: 10
"""

        config_content2 = f"""
dataset:
  backgrounds: "{sample_data["bg_dir"]}"
  overlays: "{sample_data["overlay_dir"]}"
  output: "{output_dir2}"
  n_variants: 2
  random_seed: 12345

perturbations:
  - name: shapes
    params:
      num_shapes: 5
      min_size: 3
      max_size: 8
  - name: noise
    params:
      intensity: 10
"""

        config_file1 = sample_data["temp_dir"] / "config1.yaml"
        config_file2 = sample_data["temp_dir"] / "config2.yaml"
        config_file1.write_text(config_content1)
        config_file2.write_text(config_content2)

        # Run first generation
        result1 = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "generate", "--config", str(config_file1)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        # Run second generation
        result2 = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "generate", "--config", str(config_file2)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

        assert result1.returncode == 0
        assert result2.returncode == 0

        # Compare generated files
        images1 = sorted(list((output_dir1 / "images").glob("*.png")))
        images2 = sorted(list((output_dir2 / "images").glob("*.png")))
        labels1 = sorted(list((output_dir1 / "labels").glob("*.json")))
        labels2 = sorted(list((output_dir2 / "labels").glob("*.json")))

        assert len(images1) == len(images2)
        assert len(labels1) == len(labels2)

        # Compare image content (pixel-perfect) - verify all pairs match
        def images_are_identical(img1_path, img2_path):
            img1 = Image.open(img1_path)
            img2 = Image.open(img2_path)
            return list(img1.getdata()) == list(img2.getdata())

        assert all(images_are_identical(img1, img2) for img1, img2 in zip(images1, images2))

        # Compare metadata content - verify all pairs match
        def metadata_are_identical(label1_path, label2_path):
            with open(label1_path) as f1, open(label2_path) as f2:
                metadata1 = json.load(f1)
                metadata2 = json.load(f2)
            return metadata1 == metadata2

        assert all(metadata_are_identical(l1, l2) for l1, l2 in zip(labels1, labels2))


class TestAPIIntegration:
    """Integration tests for Python API."""

    def test_api_basic_usage(self):
        """Test basic API usage as shown in project spec."""
        from plateshapez import DatasetGenerator
        from plateshapez.perturbations import PERTURBATION_REGISTRY

        # Should be able to import main components
        assert DatasetGenerator is not None
        assert PERTURBATION_REGISTRY is not None
        assert len(PERTURBATION_REGISTRY) >= 4  # At least shapes, noise, warp, texture

    def test_api_dataset_generator_instantiation(self):
        """Test DatasetGenerator instantiation and method calls."""
        import tempfile

        from plateshapez import DatasetGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "bg"
            overlay_dir = temp_path / "overlay"
            output_dir = temp_path / "output"

            bg_dir.mkdir()
            overlay_dir.mkdir()

            # Create sample files
            bg_img = Image.new("RGB", (100, 100), "white")
            bg_img.save(bg_dir / "test.jpg")

            overlay_img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
            overlay_img.save(overlay_dir / "test.png")

            # Test instantiation
            generator = DatasetGenerator(
                bg_dir=bg_dir,
                overlay_dir=overlay_dir,
                out_dir=output_dir,
                perturbations=[{"name": "shapes", "params": {"num_shapes": 2}}],
                random_seed=42,
                verbose=True,
            )

            # Test basic attributes
            assert generator.bg_dir == bg_dir
            assert generator.ov_dir == overlay_dir
            assert generator.out_dir == output_dir
            assert generator.random_seed == 42
            assert generator.verbose is True

            # Test run method
            generator.run(n_variants=1)

            # Verify output
            assert (output_dir / "images").exists()
            assert (output_dir / "labels").exists()
            assert len(list((output_dir / "images").glob("*.png"))) == 1

    def test_api_perturbation_registry_access(self):
        """Test accessing perturbation registry via API."""
        from plateshapez.perturbations.base import PERTURBATION_REGISTRY

        # Should contain expected perturbations
        expected = {"shapes", "noise", "warp", "texture"}
        actual = set(PERTURBATION_REGISTRY.keys())
        assert expected.issubset(actual)

    def test_api_config_loading(self):
        """Test config loading via API."""
        from plateshapez.config import load_config

        # Should load defaults without error
        cfg = load_config()
        assert "dataset" in cfg
        assert "perturbations" in cfg
        assert "logging" in cfg

    def test_api_verbose_output_content(self):
        """Test that verbose flag produces expected content."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            bg_dir = temp_path / "bg"
            overlay_dir = temp_path / "overlay"
            output_dir = temp_path / "output"

            bg_dir.mkdir()
            overlay_dir.mkdir()

            # Create sample files
            bg_img = Image.new("RGB", (100, 100), "white")
            bg_img.save(bg_dir / "test.jpg")

            overlay_img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
            overlay_img.save(overlay_dir / "test.png")

            # Capture stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output

            try:
                generator = DatasetGenerator(
                    bg_dir=bg_dir,
                    overlay_dir=overlay_dir,
                    out_dir=output_dir,
                    verbose=True,
                )
                generator.run(n_variants=1)
            finally:
                sys.stdout = sys.__stdout__

            output = captured_output.getvalue()

            # Should contain verbose-specific content
            assert "Generated" in output or "✓" in output
            assert "complete" in output
