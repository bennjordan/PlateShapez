#!/usr/bin/env python3
"""
Complete plateshapez demo: Create test images and generate adversarial dataset.

This script demonstrates the full workflow of the plateshapez library:
1. Creates synthetic car background images
2. Creates license plate overlay images with transparency
3. Generates adversarial datasets using CLI and Python API
4. Shows output structure and metadata

Run with: uv run python examples/demo_full_workflow.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_test_images():
    """Create synthetic test images for the demo."""
    print("🎨 Creating test images...")

    # Create directories in dataset/demo folder
    os.makedirs("dataset/demo/backgrounds", exist_ok=True)
    os.makedirs("dataset/demo/overlays", exist_ok=True)

    # Create background car images
    colors = [
        ("red_car", (180, 50, 50)),
        ("blue_car", (50, 100, 180)),
        ("gray_car", (120, 120, 120)),
    ]

    for name, color in colors:
        # Create a 800x600 image
        img = Image.new("RGB", (800, 600), color=(240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Draw a simple car shape
        # Car body
        draw.rectangle((200, 300, 600, 450), fill=color, outline=(0, 0, 0), width=3)
        # Car roof
        draw.rectangle((250, 250, 550, 300), fill=color, outline=(0, 0, 0), width=3)
        # Wheels
        draw.ellipse([220, 430, 280, 490], fill=(40, 40, 40), outline=(0, 0, 0), width=2)
        draw.ellipse([520, 430, 580, 490], fill=(40, 40, 40), outline=(0, 0, 0), width=2)
        # Windows
        draw.rectangle((270, 260, 530, 290), fill=(150, 200, 255), outline=(0, 0, 0), width=2)

        img.save(f"dataset/demo/backgrounds/{name}.jpg", "JPEG", quality=95)
        print(f"  ✓ Created background: {name}.jpg")

    # Create license plate overlays
    plates = [("plate_abc123", "ABC 123"), ("plate_xyz789", "XYZ 789"), ("plate_test01", "TEST 01")]

    for name, text in plates:
        # Create a 200x60 image with transparency
        img = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw plate background
        draw.rectangle((5, 5, 195, 55), fill=(255, 255, 255, 240), outline=(0, 0, 0, 255), width=2)

        # Try to use a font, fall back to default
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        except OSError:
            font = ImageFont.load_default()  # type: ignore[assignment]

        # Draw text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (200 - text_width) // 2
        y = (60 - text_height) // 2

        draw.text((x, y), text, fill=(0, 0, 0, 255), font=font)

        img.save(f"dataset/demo/overlays/{name}.png", "PNG")
        print(f"  ✓ Created overlay: {name}.png")


def run_cli_demo():
    """Demonstrate CLI usage."""
    print("\n🚀 Running CLI demo...")

    # Show available perturbations
    print("\n📋 Available perturbations:")
    result = subprocess.run(["uv", "run", "advplate", "list"], capture_output=True, text=True)
    print(result.stdout)

    # Show current configuration
    print("⚙️ Current configuration:")
    result = subprocess.run(
        ["uv", "run", "advplate", "info", "--as", "yaml"], capture_output=True, text=True
    )
    print(result.stdout)

    # Dry run first
    print("🔍 Dry run preview:")
    result = subprocess.run(
        [
            "uv",
            "run",
            "advplate",
            "generate",
            "--dry-run",
            "--n_variants",
            "2",
            "--config",
            "/dev/null",  # Use defaults
        ],
        capture_output=True,
        text=True,
        cwd=".",
    )
    print(result.stdout)

    # Create custom config for demo
    demo_config = {
        "dataset": {
            "backgrounds": "./dataset/demo/backgrounds",
            "overlays": "./dataset/demo/overlays",
            "output": "./dataset/demo/demo_dataset",
            "n_variants": 2,
            "random_seed": 42,
        },
        "perturbations": [
            {"name": "shapes", "params": {"num_shapes": 15, "min_size": 3, "max_size": 12}},
            {"name": "noise", "params": {"intensity": 20}},
            {"name": "texture", "params": {"type": "grain", "intensity": 0.2}},
        ],
        "logging": {"level": "INFO", "save_metadata": True},
    }

    # Save config
    with open("dataset/demo/demo_config.yaml", "w") as f:
        import yaml

        yaml.safe_dump(demo_config, f, default_flow_style=False)

    # Generate dataset
    print("🎯 Generating dataset with CLI...")
    result = subprocess.run(
        ["uv", "run", "advplate", "generate", "--config", "dataset/demo/demo_config.yaml", "--verbose"],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ CLI generation successful!")
        print(result.stdout)
    else:
        print("❌ CLI generation failed:")
        print(result.stderr)


def run_python_api_demo():
    """Demonstrate Python API usage."""
    print("\n🐍 Running Python API demo...")

    from plateshapez import DatasetGenerator

    # Create generator with different settings
    gen = DatasetGenerator(
        bg_dir="dataset/demo/backgrounds",
        overlay_dir="dataset/demo/overlays",
        out_dir="dataset/demo/demo_dataset_api",
        perturbations=[
            {"name": "shapes", "params": {"num_shapes": 25, "min_size": 2, "max_size": 8}},
            {"name": "noise", "params": {"intensity": 30, "scope": "region"}},
            {"name": "warp", "params": {"intensity": 3.0, "frequency": 15.0}},
        ],
        random_seed=1337,
        verbose=True,
    )

    print("🎯 Generating dataset with Python API...")
    gen.run(n_variants=2)
    print("✅ Python API generation successful!")


def show_results():
    """Display results and analysis."""
    print("\n📊 Results Analysis:")

    # Show CLI results
    cli_path = Path("demo_dataset")
    if cli_path.exists():
        if labels := get_image_data(
            cli_path, '📁 CLI Dataset: '
        ):
            with open(labels[0]) as f:
                sample_meta = json.load(f)
            print("📋 Sample metadata:")
            print(json.dumps(sample_meta, indent=2))

    # Show API results
    api_path = Path("demo_dataset_api")
    if api_path.exists():
        labels = get_image_data(api_path, '\n📁 API Dataset: ')


def get_image_data(arg0, arg1):
    """Get images and labels"""
    images = list((arg0 / "images").glob("*.png"))
    result = list((arg0 / "labels").glob("*.json"))
    print(f"{arg1}{len(images)} images, {len(result)} metadata files")

    return result


def cleanup():
    """Clean up demo files."""
    print("\n🧹 Cleaning up demo files...")
    import shutil

    cleanup_paths = [
        "demo_backgrounds",
        "demo_overlays",
        "demo_dataset",
        "demo_dataset_api",
        "demo_config.yaml",
    ]

    for path in cleanup_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"  ✓ Removed {path}")


def main():
    """Run the complete demo workflow."""
    print("🎬 PlateShapez Complete Demo")
    print("=" * 50)

    try:
        # Step 1: Create test images
        create_test_images()

        # Step 2: CLI demo
        run_cli_demo()

        # Step 3: Python API demo
        run_python_api_demo()

        # Step 4: Show results
        show_results()

        print("\n🎉 Demo completed successfully!")
        print("\nWhat was demonstrated:")
        print("• Created synthetic car backgrounds and license plate overlays")
        print("• Used CLI with custom configuration")
        print("• Used Python API with different perturbations")
        print("• Generated datasets with reproducible seeds")
        print("• Showed metadata structure and output organization")

        print("\n📁 Demo files preserved for inspection.")
        print("\n💡 To clean up demo files, run:")
        print("   uv run dev cleanup")
        print("   # or")
        print("   python scripts/cleanup.py")
        sys.exit(0)

    except KeyboardInterrupt as e:
        print("\n\n⏹️  Demo interrupted by user")
        raise KeyboardInterrupt("User interrupted process") from e
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        raise Exception(f"Demo failed: {e}") from e


if __name__ == "__main__":
    main()
