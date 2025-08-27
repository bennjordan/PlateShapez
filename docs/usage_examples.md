# Usage Examples

This document provides comprehensive examples of using plateshapez for generating adversarial license plate datasets.

## Region vs Global Perturbation Scope

All perturbations support a `scope` parameter that controls where the effect is applied:

- **`scope: region`** (default): Apply perturbation only to the overlay region (license plate area)
- **`scope: global`**: Apply perturbation to the entire image

### Example Configuration

```yaml
perturbations:
  - name: noise
    params:
      intensity: 25
      scope: region  # Only affect the license plate area
  - name: warp
    params:
      intensity: 5.0
      scope: global  # Warp the entire image
```

### Research Considerations

- **Region scope** is recommended for most adversarial research as it focuses perturbations on the target object
- **Global scope** can be useful for testing robustness to environmental effects like camera distortion

## CLI Usage

### Basic Generation

```bash
# Generate dataset with default settings
advplate generate

# Generate with custom number of variants
advplate generate --n_variants 20

# Use a custom config file
advplate generate --config my_config.yaml

# Dry run to preview what would be generated
advplate generate --dry-run --n_variants 10
```

### Exploring Available Options

```bash
# List all available perturbations
advplate list

# Show current configuration
advplate info

# Show version information
advplate version
```

### Advanced CLI Usage

```bash
# Generate with verbose output
advplate generate --verbose --n_variants 5

# Generate with debug information
advplate generate --debug --config custom.yaml

# Override config file settings via CLI
advplate generate --config base.yaml --n_variants 50
```

## Python API Usage

### Basic API Usage

```python
from plateshapez import DatasetGenerator

# Create generator with custom settings
gen = DatasetGenerator(
    bg_dir="path/to/backgrounds",
    overlay_dir="path/to/overlays",
    out_dir="path/to/output",
    perturbations=[
        {"name": "shapes", "params": {"num_shapes": 20}},
        {"name": "noise", "params": {"intensity": 25}}
    ],
    random_seed=1337
)

# Generate dataset
gen.run(n_variants=10)
```

### Using Configuration Files

```python
from plateshapez import DatasetGenerator
from plateshapez.config import load_config

# Load configuration from file
cfg = load_config("config.yaml")

# Create generator from config
gen = DatasetGenerator(
    bg_dir=cfg["dataset"]["backgrounds"],
    overlay_dir=cfg["dataset"]["overlays"],
    out_dir=cfg["dataset"]["output"],
    perturbations=cfg["perturbations"],
    random_seed=cfg["dataset"]["random_seed"]
)

gen.run(n_variants=cfg["dataset"]["n_variants"])
```

### Working with Perturbations

```python
from plateshapez.perturbations.base import PERTURBATION_REGISTRY

# List available perturbations
print("Available perturbations:")
for name, cls in PERTURBATION_REGISTRY.items():
    print(f"  {name}: {cls.__doc__}")

# Create custom perturbation configuration
perturbations = [
    {
        "name": "shapes",
        "params": {
            "num_shapes": 15,
            "min_size": 3,
            "max_size": 12
        }
    },
    {
        "name": "noise", 
        "params": {
            "intensity": 20
        }
    },
    {
        "name": "texture",
        "params": {
            "type": "scratches",
            "intensity": 0.4
        }
    },
    {
        "name": "warp",
        "params": {
            "intensity": 3.0,
            "frequency": 25.0
        }
    }
]
```

## Configuration Files

### YAML Configuration

```yaml
# config.yaml
dataset:
  backgrounds: "./backgrounds"
  overlays: "./overlays"
  output: "./dataset"
  n_variants: 15
  random_seed: 42

perturbations:
  - name: shapes
    params:
      num_shapes: 25
      min_size: 2
      max_size: 10
  - name: noise
    params:
      intensity: 30
  - name: texture
    params:
      type: grain
      intensity: 0.3

logging:
  level: INFO
  save_metadata: true
```

### JSON Configuration

```json
{
  "dataset": {
    "backgrounds": "./backgrounds",
    "overlays": "./overlays", 
    "output": "./dataset",
    "n_variants": 15,
    "random_seed": 42
  },
  "perturbations": [
    {
      "name": "shapes",
      "params": {
        "num_shapes": 25,
        "min_size": 2,
        "max_size": 10
      }
    },
    {
      "name": "noise",
      "params": {
        "intensity": 30
      }
    }
  ],
  "logging": {
    "level": "INFO",
    "save_metadata": true
  }
}
```

## Directory Structure

Your project should be organized as follows:

```
project/
├── backgrounds/          # Background vehicle images (JPG)
│   ├── car1.jpg
│   ├── car2.jpg
│   └── ...
├── overlays/            # License plate overlays (PNG with alpha)
│   ├── plate1.png
│   ├── plate2.png
│   └── ...
├── config.yaml          # Configuration file (optional)
└── dataset/             # Generated output (created automatically)
    ├── images/          # Generated composite images
    │   ├── car1_plate1_000.png
    │   ├── car1_plate1_001.png
    │   └── ...
    └── labels/          # Metadata JSON files
        ├── car1_plate1_000.json
        ├── car1_plate1_001.json
        └── ...
```

## Perturbation Types

### Shapes Perturbation
Adds random geometric shapes (rectangles, ellipses, triangles) to simulate occlusion.

```python
{"name": "shapes", "params": {"num_shapes": 20, "min_size": 2, "max_size": 15}}
```

### Noise Perturbation
Adds Gaussian noise to simulate camera sensor noise or compression artifacts.

```python
{"name": "noise", "params": {"intensity": 25}}
```

### Texture Perturbation
Applies texture effects like grain, scratches, or dirt spots.

```python
{"name": "texture", "params": {"type": "grain", "intensity": 0.3}}
# Types: "grain", "scratches", "dirt"
```

### Warp Perturbation
Applies mild geometric warping to simulate perspective distortion.

```python
{"name": "warp", "params": {"intensity": 5.0, "frequency": 20.0}}
```

## Tips and Best Practices

1. **Use consistent random seeds** for reproducible results across runs
2. **Start with small n_variants** when testing configurations
3. **Use --dry-run** to preview generation plans before running
4. **Organize images** with descriptive filenames in backgrounds/ and overlays/
5. **Check metadata files** to understand what perturbations were applied
6. **Use verbose/debug flags** when troubleshooting issues
