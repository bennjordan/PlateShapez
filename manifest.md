# Project Manifest

## Core Components

- 📁 **src/plateshapez/** - Main package directory
  - 📄 **__init__.py** - Package initialization, exports DatasetGenerator
  - 📄 **__main__.py** - CLI entry point with typer/rich interface (advplate command)
  - 📄 **config.py** - Configuration system with YAML/JSON support and hierarchy
  - 📄 **dev.py** - Development utilities and commands
  - 📄 **pipeline.py** - DatasetGenerator class with deterministic seeding

## Perturbation Framework

- 📁 **src/plateshapez/perturbations/** - Adversarial perturbation system
  - 📄 **__init__.py** - Perturbation package initialization
  - 📄 **base.py** - Base Perturbation class and registry system
  - 📄 **shapes.py** - Random geometric shapes (rectangles, ellipses, triangles)
  - 📄 **noise.py** - Gaussian noise perturbation
  - 📄 **texture.py** - Texture effects (grain, scratches, dirt)
  - 📄 **warp.py** - Geometric warping with configurable intensity

## Utilities

- 📁 **src/plateshapez/utils/** - Helper functions
  - 📄 **__init__.py** - Utils package initialization
  - 📄 **io.py** - Image I/O operations and file iteration
  - 📄 **overlay.py** - Image composition and overlay helpers

## Dependencies

The project uses:
- **PIL/Pillow** - Image processing
- **numpy** - Numerical operations
- **opencv-python** - Computer vision operations
- **rich** - Terminal UI and formatting
- **typer** - CLI framework
- **pyyaml** - YAML configuration support

## Entry Points

- **advplate** - Main CLI command (via pyproject.toml console_scripts)
- **dev** - Development utilities command
