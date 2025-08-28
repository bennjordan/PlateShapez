# Dataset Card: Adversarial Plate Overlay Dataset

## Reproducibility

The dataset generation process is deterministic when using the same:
- Random seed (`random_seed` in config or `--seed` CLI option)
- Input images (backgrounds and overlays)
- Perturbation parameters
- Software version

### Reproducible Generation

```bash
# Generate identical datasets with same seed
advplate generate --seed 42 --config my_config.yaml

# Or specify in config file
# dataset:
#   random_seed: 42
```

All perturbations respect the random seed for consistent results across runs.

## Purpose
This dataset generator is designed for **research into adversarial robustness** of Optical Character Recognition (OCR) and Automated License Plate Recognition (ALPR) models.  
The goal is **not to conceal license plates in real-world use**, but to provide controlled, reproducible data for studying:
- Model brittleness under adversarial overlays.
- How adversarial training affects generalization.
- Privacy-preserving methods for resisting surveillance capitalism and corporate misuse.

## NOT for:
- Evading law enforcement.
- Facilitating illegal activity.
- Deployment in production systems without ethical review.

## Composition
- **Inputs:** Background vehicle images, plate overlays (cropped PNGs).
- **Outputs:** Composite images with adversarial perturbations + JSON metadata.

## Use Cases
- Benchmarking ALPR/OCR adversarial robustness.
- Training defense models against adversarial perturbations.
- Privacy/ethics research on surveillance systems.

## Risks & Limitations
- Generated examples are synthetic and may not reflect real-world conditions.
- Misuse is possible if applied outside research contexts.

## License
Released for academic and research use under MIT, subject to responsible disclosure and ethical use.
