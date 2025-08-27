from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as e:  # pragma: no cover - handled by dependency install
    raise RuntimeError("Missing dependency 'pyyaml'. Please run: uv add pyyaml") from e


DEFAULTS: dict[str, Any] = {
    "dataset": {
        "backgrounds": "./backgrounds",
        "overlays": "./overlays",
        "output": "./dataset",
        "n_variants": 10,
        "random_seed": 1337,
    },
    "perturbations": [
        {
            "name": "shapes",
            "params": {"num_shapes": 20, "min_size": 2, "max_size": 15},
        },
        {"name": "noise", "params": {"intensity": 25}},
    ],
    "logging": {"level": "INFO", "save_metadata": True},
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        elif v is not None:
            out[k] = v
    return out


def _load_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == ".json":
        return json.loads(text)
    raise ValueError(f"Unsupported config format: {path.suffix}")


def load_config(
    path: str | os.PathLike[str] | None = None, *, cli_overrides: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Merge config with precedence: DEFAULTS < file (if provided) < CLI overrides.
    """
    cfg = dict(DEFAULTS)
    if path:
        file_cfg = _load_file(Path(path))
        cfg = _deep_merge(cfg, file_cfg)
    if cli_overrides:
        # Handle CLI overrides more comprehensively
        override_dict: dict[str, dict[str, Any]] = {}
        if "n_variants" in cli_overrides and cli_overrides["n_variants"] is not None:
            override_dict.setdefault("dataset", {})["n_variants"] = cli_overrides["n_variants"]
        if "seed" in cli_overrides and cli_overrides["seed"] is not None:
            override_dict.setdefault("dataset", {})["random_seed"] = cli_overrides["seed"]
        if "verbose" in cli_overrides and cli_overrides["verbose"]:
            override_dict.setdefault("logging", {})["level"] = "DEBUG"
        if "debug" in cli_overrides and cli_overrides["debug"]:
            override_dict.setdefault("logging", {})["level"] = "DEBUG"
        cfg = _deep_merge(cfg, override_dict)
    return cfg
