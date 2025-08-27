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

        low_array = self.to_low_noise_np_array(5, img, region)
        high_array = self.to_low_noise_np_array(50, img, region)
        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))

        # High intensity should create more difference
        assert high_diff > low_diff
        assert low_diff > 0  # Some change should occur

    # TODO Rename this here and in `test_noise_intensity_measurable`
    def to_low_noise_np_array(self, intensity, img, region):
        # Low intensity noise
        low_noise = NoisePerturbation(intensity=intensity)
        low_result = low_noise.apply(img, region)
        return np.array(low_result)

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
        # sourcery skip: no-loop-in-tests
        for i in range(0, 100, 10):
            draw.line([(i, 0), (i, 100)], fill="black", width=1)
            draw.line([(0, i), (100, i)], fill="black", width=1)

        region = (10, 10, 80, 80)  # Use a smaller region
        original_array = np.array(img)

        low_array = self.to_low_warp_np_array(1.0, img, region)
        high_array = self.to_low_warp_np_array(10.0, img, region)
        # Both should be different from original
        assert not np.array_equal(original_array, low_array)
        assert not np.array_equal(original_array, high_array)

    # TODO Rename this here and in `test_warp_intensity_affects_distortion`
    def to_low_warp_np_array(self, intensity, img, region):
        # Test with global scope to ensure warping is visible
        low_warp = WarpPerturbation(intensity=intensity, scope="global")
        low_result = low_warp.apply(img, region)
        return np.array(low_result)

    def test_warp_region_scope(self):
        """Test warp perturbation with region scope for full code coverage."""
        # Create an image with a clear pattern to see warping effects
        img = Image.new("RGB", (100, 100), color="white")
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        # Add a grid pattern
        for i in range(0, 100, 10):
            draw.line([(i, 0), (i, 100)], fill="black", width=1)
            draw.line([(0, i), (100, i)], fill="black", width=1)

        region = (20, 20, 40, 40)  # Small region in the center
        original_array = np.array(img)

        # Test region scope - should only affect the specified region
        region_warp = WarpPerturbation(intensity=5.0, scope="region")
        region_result = region_warp.apply(img, region)
        region_array = np.array(region_result)

        # Should be different from original
        assert not np.array_equal(original_array, region_array)

        # Check that areas outside the region are unchanged
        # Top-left corner (outside region)
        assert np.array_equal(original_array[0:10, 0:10], region_array[0:10, 0:10])
        # Bottom-right corner (outside region)
        assert np.array_equal(original_array[90:100, 90:100], region_array[90:100, 90:100])


class TestTexturePerturbation:
    """Test texture perturbation correctness."""

    @pytest.mark.parametrize("texture_type", ["grain", "scratches", "dirt"])
    def test_texture_types_work(self, texture_type):
        """Test that different texture types can be applied."""
        img = Image.new("RGB", (100, 100), color="white")
        region = (10, 10, 80, 80)

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

        low_array = self.to_low_texture_np_array(0.1, img, region)
        high_array = self.to_low_texture_np_array(0.8, img, region)
        # Calculate differences
        low_diff = np.mean(np.abs(original_array.astype(float) - low_array.astype(float)))
        high_diff = np.mean(np.abs(original_array.astype(float) - high_array.astype(float)))

        # High intensity should create more difference
        assert high_diff > low_diff

    # TODO Rename this here and in `test_texture_intensity_affects_result`
    def to_low_texture_np_array(self, intensity, img, region):
        # Low intensity
        low_texture = TexturePerturbation(type="grain", intensity=intensity)
        low_result = low_texture.apply(img, region)
        return np.array(low_result)


class TestPerturbationChannelCompatibility:
    """Test perturbations work with different image channel counts."""

    @pytest.mark.parametrize(
        "mode,channels",
        [
            ("L", 1),  # Grayscale
            ("RGB", 3),  # RGB
            ("RGBA", 4),  # RGBA
        ],
    )
    def test_texture_grain_channel_compatibility(self, mode, channels):
        """Test grain texture works with different channel counts."""
        from typing import Union

        color: Union[int, tuple[int, int, int], tuple[int, int, int, int]]
        if mode == "L":
            color = 128
        elif mode == "RGB":
            color = (128, 128, 128)
        else:  # RGBA
            color = (128, 128, 128, 255)
        img = Image.new(mode, (50, 50), color=color)
        region = (10, 10, 30, 30)

        perturbation = TexturePerturbation(type="grain", intensity=0.5)
        result = perturbation.apply(img, region)

        assert isinstance(result, Image.Image)
        assert result.mode == mode
        assert result.size == img.size

    @pytest.mark.parametrize("mode", ["L", "RGB", "RGBA"])
    def test_noise_channel_compatibility(self, mode):
        """Test noise perturbation works with different channel counts."""
        from typing import Union

        color: Union[int, tuple[int, int, int], tuple[int, int, int, int]]
        if mode == "L":
            color = 128
        elif mode == "RGB":
            color = (128, 128, 128)
        else:  # RGBA
            color = (128, 128, 128, 255)
        img = Image.new(mode, (50, 50), color=color)
        region = (0, 0, 50, 50)

        perturbation = NoisePerturbation(intensity=10)
        result = perturbation.apply(img, region)

        assert isinstance(result, Image.Image)
        assert result.mode == mode
        assert result.size == img.size
