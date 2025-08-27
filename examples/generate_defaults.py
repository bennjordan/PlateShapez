#!/usr/bin/env python3
"""
Example: Generate dataset using the Python API with default configuration.

This example demonstrates how to use the plateshapez library programmatically
to generate adversarial license plate datasets.
"""

from plateshapez import DatasetGenerator
from plateshapez.config import load_config


def main():
    """Generate a dataset using the Python API."""
    print("🚀 Generating dataset using Python API...")

    # Option 1: Use DatasetGenerator directly with custom parameters
    gen = DatasetGenerator(
        bg_dir="backgrounds",
        overlay_dir="overlays",
        out_dir="dataset",
        perturbations=[
            {"name": "shapes", "params": {"num_shapes": 30, "min_size": 2, "max_size": 8}},
            {"name": "noise", "params": {"intensity": 15}},
            {"name": "texture", "params": {"type": "grain", "intensity": 0.2}},
        ],
        random_seed=42,  # For reproducible results
    )
    gen.run(n_variants=5)

    print("\n" + "=" * 50)

    # Option 2: Use configuration file approach
    print("📁 Generating dataset using config file approach...")

    cfg = load_config()  # Load defaults
    gen2 = DatasetGenerator(
        bg_dir=cfg["dataset"]["backgrounds"],
        overlay_dir=cfg["dataset"]["overlays"],
        out_dir="dataset_from_config",
        perturbations=cfg["perturbations"],
        random_seed=cfg["dataset"]["random_seed"],
    )
    gen2.run(n_variants=cfg["dataset"]["n_variants"])

    print("✅ Dataset generation complete!")
    print("Check the 'dataset' and 'dataset_from_config' directories for results.")


if __name__ == "__main__":
    main()
