import json
import tempfile
from pathlib import Path

import pytest
import yaml

from plateshapez.config import load_config, DEFAULTS


class TestConfigSystem:
    """Test configuration loading and merging."""

    def test_defaults_loaded_without_file(self):
        """Test that defaults are loaded when no config file is provided."""
        cfg = load_config()
        
        # Should match DEFAULTS
        assert cfg == DEFAULTS
        assert cfg["dataset"]["n_variants"] == 10
        assert cfg["dataset"]["random_seed"] == 1337

    def test_yaml_config_file_loading(self):
        """Test loading YAML configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 25,
                    "backgrounds": "./custom_bg",
                }
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Should merge with defaults
            assert cfg["dataset"]["n_variants"] == 25
            assert cfg["dataset"]["backgrounds"] == "./custom_bg"
            # Defaults should still be present
            assert cfg["dataset"]["random_seed"] == 1337
            assert cfg["dataset"]["overlays"] == "./overlays"
            
            Path(f.name).unlink()

    def test_json_config_file_loading(self):
        """Test loading JSON configuration files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_config = {
                "dataset": {
                    "output": "./custom_output",
                    "random_seed": 9999,
                }
            }
            json.dump(json_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Should merge with defaults
            assert cfg["dataset"]["output"] == "./custom_output"
            assert cfg["dataset"]["random_seed"] == 9999
            # Defaults should still be present
            assert cfg["dataset"]["n_variants"] == 10
            
            Path(f.name).unlink()

    def test_cli_overrides_precedence(self):
        """Test that CLI overrides have highest precedence."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 50,
                }
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            # CLI override should win
            cfg = load_config(f.name, cli_overrides={"n_variants": 100})
            
            assert cfg["dataset"]["n_variants"] == 100
            
            Path(f.name).unlink()

    def test_verbose_debug_cli_overrides(self):
        """Test that verbose/debug flags affect logging level."""
        cfg_verbose = load_config(cli_overrides={"verbose": True})
        cfg_debug = load_config(cli_overrides={"debug": True})
        
        assert cfg_verbose["logging"]["level"] == "DEBUG"
        assert cfg_debug["logging"]["level"] == "DEBUG"

    def test_nonexistent_config_file_raises_error(self):
        """Test that nonexistent config files raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_unsupported_config_format_raises_error(self):
        """Test that unsupported config formats raise ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("not a config file")
            f.flush()
            
            with pytest.raises(ValueError, match="Unsupported config format"):
                load_config(f.name)
            
            Path(f.name).unlink()

    def test_deep_merge_behavior(self):
        """Test that deep merging works correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_config = {
                "dataset": {
                    "n_variants": 30,  # Override this
                    # Don't specify other dataset fields
                },
                "perturbations": [
                    {"name": "custom", "params": {"value": 123}}
                ],
                # Don't specify logging section
            }
            yaml.dump(yaml_config, f)
            f.flush()
            
            cfg = load_config(f.name)
            
            # Dataset section should be merged
            assert cfg["dataset"]["n_variants"] == 30  # Overridden
            assert cfg["dataset"]["backgrounds"] == "./backgrounds"  # From defaults
            assert cfg["dataset"]["overlays"] == "./overlays"  # From defaults
            assert cfg["dataset"]["random_seed"] == 1337  # From defaults
            
            # Perturbations should be completely replaced
            assert len(cfg["perturbations"]) == 1
            assert cfg["perturbations"][0]["name"] == "custom"
            
            # Logging should remain from defaults
            assert cfg["logging"]["level"] == "INFO"
            assert cfg["logging"]["save_metadata"] is True
            
            Path(f.name).unlink()
