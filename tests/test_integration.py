import subprocess
import tempfile
from pathlib import Path

import pytest
from PIL import Image

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
            cwd=str(REPO_ROOT)
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
            cwd=str(REPO_ROOT)
        )
        
        assert result.returncode == 0
        assert "plateshapez" in result.stdout

    def test_cli_info_command(self):
        """Test that 'advplate info' command shows configuration."""
        result = subprocess.run(
            ["uv", "run", "python", "-m", "plateshapez", "info"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
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
        
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--dry-run",
            "--n_variants", "2"
        ], capture_output=True, text=True, cwd=str(REPO_ROOT))
        
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
  backgrounds: "{sample_data['bg_dir']}"
  overlays: "{sample_data['overlay_dir']}"
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
        
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--config", str(config_file)
        ], capture_output=True, text=True, cwd=str(REPO_ROOT))
        
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
        
        # Check that images are valid
        for img_path in images:
            img = Image.open(img_path)
            assert img.size == (300, 200)  # Same as background

    def test_cli_error_handling_missing_directories(self):
        """Test CLI error handling for missing directories."""
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--n_variants", "1"
        ], capture_output=True, text=True, cwd=str(REPO_ROOT))
        
        # Should fail gracefully
        assert result.returncode == 1
        assert "Configuration error" in result.stdout or "Error" in result.stdout or "Error" in result.stderr

    def test_cli_verbose_flag(self, sample_data):
        """Test that verbose flag produces more output."""
        config_file = sample_data["temp_dir"] / "config.yaml"
        config_content = f"""
dataset:
  backgrounds: "{sample_data['bg_dir']}"
  overlays: "{sample_data['overlay_dir']}"
  output: "{sample_data['temp_dir'] / 'output'}"
  n_variants: 1
"""
        config_file.write_text(config_content)
        
        # Run with verbose flag
        result = subprocess.run([
            "uv", "run", "python", "-m", "plateshapez", "generate",
            "--config", str(config_file),
            "--verbose"
        ], capture_output=True, text=True, cwd=str(REPO_ROOT))
        
        assert result.returncode == 0
        
        # Verbose output should contain additional information
        output = result.stdout
        assert len(output) > 0  # Should have some output


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
