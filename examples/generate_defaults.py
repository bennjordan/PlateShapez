from src.plateshapez.pipeline import DatasetGenerator

perturbations: list[DatasetGenerator.PerturbationConf] = [
    {"name": "shapes", "params": {"num_shapes": 20, "max_size": 15}},
    {"name": "noise", "params": {"intensity": 20}},
]

gen = DatasetGenerator("backgrounds", "overlays", "dataset", perturbations)
gen.run(n_variants=10)
