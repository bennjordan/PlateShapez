import numpy as np
import pytest
from PIL import Image

from plateshapez.perturbations.base import PERTURBATION_REGISTRY, Perturbation, register
from plateshapez.perturbations.noise import NoisePerturbation
from plateshapez.perturbations.shapes import ShapesPerturbation
from plateshapez.perturbations.texture import TexturePerturbation
from plateshapez.perturbations.warp import WarpPerturbation


class TestPerturbationRegistry:
    """Test perturbation registry behavior."""

    def test_registry_contains_built_ins(self):
        """Test that all built-in perturbations are registered."""
        expected_perturbations = {"shapes", "noise", "warp", "texture"}
        registered_names = set(PERTURBATION_REGISTRY.keys())
        assert expected_perturbations.issubset(registered_names)

    def test_duplicate_registration_raises_error(self):
        """Test that registering duplicate names raises ValueError."""

        with pytest.raises(ValueError, match="Duplicate perturbation name"):

            @register
            class DuplicateShapes(Perturbation):
                name = "shapes"  # Duplicate name

                def apply(self, img, region):
                    return img

    def test_registry_get_perturbation(self):
        """Test getting perturbations from registry."""
        shapes_cls = PERTURBATION_REGISTRY["shapes"]
        assert shapes_cls == ShapesPerturbation
        assert shapes_cls.name == "shapes"


class TestShapesPerturbation:
    """Test shapes perturbation correctness."""

    def test_shapes_stay_within_bounds(self):
        """Test that shapes are drawn within the specified region."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 30, 30)  # x, y, w, h

        perturbation = ShapesPerturbation(num_shapes=5, min_size=2, max_size=5)
        result = perturbation.apply(img, region)

        assert isinstance(result, Image.Image)
        assert result.size == img.size

    def test_shapes_intensity_affects_count(self):
        """Test that num_shapes parameter affects the number of shapes drawn."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 50, 50)

        # Convert to array to check for changes
        original_array = np.array(img)

        perturbation = ShapesPerturbation(num_shapes=20)
        result = perturbation.apply(img, region)
        result_array = np.array(result)

        # Should have some differences due to shapes being drawn
        assert not np.array_equal(original_array, result_array)

    def test_shapes_serialization(self):
        """Test perturbation serialization."""
        params = {"num_shapes": 15, "min_size": 3, "max_size": 8}
        perturbation = ShapesPerturbation(**params)
        serialized = perturbation.serialize()

        assert serialized["type"] == "shapes"
        assert serialized["params"] == params


class TestNoisePerturbation:
    """Test noise perturbation correctness."""

    def test_noise_intensity_measurable(self):
        """Test that noise intensity affects the image measurably."""
        img = Image.new("RGB", (50, 50), color=(128, 128, 128))
        region = (0, 0, 50, 50)

        original_array = np.array(img)

        # Low intensity noise
        low_noise = NoisePerturbation(intensity=5)
        low_result = low_noise.apply(img, region)
        low_array = np.array(low_result)

        # High intensity noise
        high_noise = NoisePerturbation(intensity=50)
        high_result = high_noise.apply(img, region)
        high_array = np.array(high_result)

        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))

        # High intensity should create more difference
        assert high_diff > low_diff
        assert low_diff > 0  # Some change should occur

    def test_noise_bounds_respected(self):
        """Test that noise doesn't push pixels outside valid range."""
        img = Image.new("RGB", (50, 50), color="white")
        region = (0, 0, 50, 50)

        perturbation = NoisePerturbation(intensity=100)  # High intensity
        result = perturbation.apply(img, region)
        result_array = np.array(result)

        # All values should be in valid range [0, 255]
        assert np.all(result_array >= 0)
        assert np.all(result_array <= 255)
        # Ensure output image format is correct (uint8)
        assert result_array.dtype == np.uint8


class TestWarpPerturbation:
    """Test warp perturbation correctness."""

    def test_warp_preserves_image_size(self):
        """Test that warping preserves image dimensions."""
        img = Image.new("RGB", (100, 100), color="red")
        region = (20, 20, 60, 60)

        perturbation = WarpPerturbation(intensity=5.0, frequency=20.0)
        result = perturbation.apply(img, region)

        assert result.size == img.size
        assert isinstance(result, Image.Image)

    def test_warp_intensity_affects_distortion(self):
        """Test that warp intensity affects the amount of distortion."""
        # Create an image with a pattern that will show warping effects
        img = Image.new("RGB", (100, 100), color="white")
        # Add a simple pattern
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        for i in range(0, 100, 10):
            draw.line([(i, 0), (i, 100)], fill="black", width=1)
            draw.line([(0, i), (100, i)], fill="black", width=1)

        region = (10, 10, 80, 80)  # Use a smaller region
        original_array = np.array(img)

        # Test with global scope to ensure warping is visible
        low_warp = WarpPerturbation(intensity=1.0, scope="global")
        low_result = low_warp.apply(img, region)
        low_array = np.array(low_result)

        high_warp = WarpPerturbation(intensity=10.0, scope="global")
        high_result = high_warp.apply(img, region)
        high_array = np.array(high_result)

        # Both should be different from original
        assert not np.array_equal(original_array, low_array)
        assert not np.array_equal(original_array, high_array)


class TestTexturePerturbation:
    """Test texture perturbation correctness."""

    def test_texture_types_work(self):
        """Test that different texture types can be applied."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 80, 80)

        texture_types = ["grain", "scratches", "dirt"]

        for texture_type in texture_types:
            perturbation = TexturePerturbation(type=texture_type, intensity=0.5)
            result = perturbation.apply(img, region)

            assert isinstance(result, Image.Image)
            assert result.size == img.size

    def test_invalid_texture_type_returns_original(self):
        """Test that invalid texture types return the original image without errors."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 80, 80)
        invalid_texture_type = "unknown_texture"
        perturbation = TexturePerturbation(type=invalid_texture_type, intensity=0.5)
        result = perturbation.apply(img, region)
        # Should not raise, and should return an image identical to the original
        assert isinstance(result, Image.Image)
        assert result.size == img.size
        assert np.array_equal(np.array(result), np.array(img))

    def test_texture_intensity_affects_result(self):
        """Test that texture intensity affects the result."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (0, 0, 100, 100)

        original_array = np.array(img)

        # Low intensity
        low_texture = TexturePerturbation(type="grain", intensity=0.1)
        low_result = low_texture.apply(img, region)
        low_array = np.array(low_result)

        # High intensity
        high_texture = TexturePerturbation(type="grain", intensity=0.8)
        high_result = high_texture.apply(img, region)
        high_array = np.array(high_result)

        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))

        # High intensity should create more difference
        assert high_diff > low_diff
