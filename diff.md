111a112
> import sys
114a116
> import click
127a130,176
> def _print_app_help() -> None:
>     """Print main app help."""
>     help_text = """Usage: advplate [OPTIONS] COMMAND [ARGS]...
> 
> Commands:
>   list      List available perturbations
>   info      Show merged configuration (defaults < file < CLI)
>   generate  Generate adversarial dataset
>   examples  Print example configuration YAML
>   version   Show version info
> 
> Options:
>   --help    Show this message and exit
> 
> For help on a specific command: advplate COMMAND --help"""
>     console.print(Panel.fit(help_text, title="Usage"))
> 
> 
> def _print_command_help(command_name: str) -> None:
>     """Print specific command help."""
>     help_texts = {
>         "generate": """Usage: advplate generate [OPTIONS]
> 
> Generate adversarial dataset.
> 
> Options:
>   -c, --config PATH       Path to config file
>   --n_variants INTEGER    Override number of variants
>   --seed INTEGER          Random seed for reproducible results
>   -v, --verbose           Verbose logging
>   --debug                 Debug logging
>   --dry-run               Preview without writing files
>   --help                  Show this message and exit""",
>         "info": """Usage: advplate info [OPTIONS]
> 
> Show merged configuration (defaults < file < CLI).
> 
> Options:
>   -c, --config PATH       Path to config file
>   --n_variants INTEGER    Override number of variants
>   --as TEXT               Output format: json|yaml
>   --help                  Show this message and exit""",
>     }
>     help_text = help_texts.get(command_name, "No help available for this command.")
>     console.print(Panel.fit(help_text, title="Usage"))
> 
> 
143a193
>     format: str = typer.Option("json", "--as", help="Output format: json|yaml"),
148c198,203
<         console.print(Panel.fit(json.dumps(cfg, indent=2), title="Configuration", border_style="cyan"))
---
>         if format == "yaml":
>             import yaml
>             output = yaml.safe_dump(cfg, default_flow_style=False)
>         else:
>             output = json.dumps(cfg, indent=2)
>         console.print(Panel.fit(output, title="Configuration", border_style="cyan"))
150a206
>         _print_command_help("info")
157a214
>     seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducible results"),
165a223
>             "seed": seed,
175,182d232
<         gen = DatasetGenerator(
<             bg_dir=cfg["dataset"]["backgrounds"],
<             overlay_dir=cfg["dataset"]["overlays"],
<             out_dir=cfg["dataset"]["output"],
<             perturbations=cfg.get("perturbations", []),
<             random_seed=int(cfg["dataset"].get("random_seed", 1337)),
<         )
< 
198a249,258
>         # Create generator after dry-run check
>         gen = DatasetGenerator(
>             bg_dir=cfg["dataset"]["backgrounds"],
>             overlay_dir=cfg["dataset"]["overlays"],
>             out_dir=cfg["dataset"]["output"],
>             perturbations=cfg.get("perturbations", []),
>             random_seed=int(cfg["dataset"].get("random_seed", 1337)),
>             save_metadata=cfg.get("logging", {}).get("save_metadata", True),
>         )
> 
208a269
>         _print_command_help("generate")
212a274
>         _print_command_help("generate")
213a276,278
>     except typer.Exit:
>         # Re-raise typer.Exit without handling (for dry-run and other intentional exits)
>         raise
217a283
>         _print_command_help("generate")
221a288,326
> def examples() -> None:
>     """Print example configuration YAML."""
>     example_config = """# Example plateshapez configuration
> dataset:
>   backgrounds: "./backgrounds"
>   overlays: "./overlays"
>   output: "./dataset"
>   n_variants: 10
>   random_seed: 1337
> 
> perturbations:
>   - name: shapes
>     params:
>       num_shapes: 20
>       min_size: 2
>       max_size: 15
>       scope: region  # or "global"
>   - name: noise
>     params:
>       intensity: 25
>       scope: region  # or "global"
>   - name: warp
>     params:
>       intensity: 5.0
>       frequency: 20.0
>       scope: region  # or "global"
>   - name: texture
>     params:
>       type: grain  # grain, scratches, dirt
>       intensity: 0.3
> 
> logging:
>   level: INFO
>   save_metadata: true
> """
>     console.print(example_config)
> 
> 
> @app.command()
241c346
<         console.print(Panel.fit(app.get_help(), title="Usage"))
---
>         _print_app_help()
321a427,428
>         if "seed" in cli_overrides and cli_overrides["seed"] is not None:
>             override_dict.setdefault("dataset", {})["random_seed"] = cli_overrides["seed"]
518a626
>         scope: str = self.params.get("scope", "region")
520,521c628,640
<         noise: np.ndarray = np.random.randint(-intensity, intensity, arr.shape, dtype="int16")
<         arr = np.clip(arr.astype("int16") + noise, 0, 255).astype("uint8")
---
>         
>         if scope == "global":
>             # Apply noise to entire image
>             noise: np.ndarray = np.random.randint(-intensity, intensity, arr.shape, dtype="int16")
>             arr = np.clip(arr.astype("int16") + noise, 0, 255).astype("uint8")
>         else:
>             # Apply noise only to region
>             x, y, w, h = region
>             target = arr[y:y+h, x:x+w]
>             noise = np.random.randint(-intensity, intensity, target.shape, dtype="int16")
>             target = np.clip(target.astype("int16") + noise, 0, 255).astype("uint8")
>             arr[y:y+h, x:x+w] = target
>             
579d697
< from typing import Literal
688a807
>         scope: str = self.params.get("scope", "region")
693,701c812,836
<         # Create displacement maps
<         dx, dy = np.meshgrid(np.arange(img_w), np.arange(img_h))
<         dx = dx + np.sin(dy / frequency) * intensity
<         dy = dy + np.cos(dx / frequency) * intensity
<         dx = np.clip(dx, 0, img_w - 1).astype(np.float32)
<         dy = np.clip(dy, 0, img_h - 1).astype(np.float32)
<         
<         remap: np.ndarray = cv2.remap(arr, dx, dy, interpolation=cv2.INTER_LINEAR)
<         return Image.fromarray(remap)
---
>         if scope == "global":
>             # Apply warp to entire image
>             dx, dy = np.meshgrid(np.arange(img_w), np.arange(img_h))
>             dx = dx + np.sin(dy / frequency) * intensity
>             dy = dy + np.cos(dx / frequency) * intensity
>             dx = np.clip(dx, 0, img_w - 1).astype(np.float32)
>             dy = np.clip(dy, 0, img_h - 1).astype(np.float32)
>             
>             remap: np.ndarray = cv2.remap(arr, dx, dy, interpolation=cv2.INTER_LINEAR)
>             return Image.fromarray(remap)
>         else:
>             # Apply warp only to region
>             region_arr = arr[y:y+h, x:x+w].copy()
>             
>             # Create displacement maps for region only
>             dx, dy = np.meshgrid(np.arange(w), np.arange(h))
>             dx = dx + np.sin(dy / frequency) * intensity
>             dy = dy + np.cos(dx / frequency) * intensity
>             dx = np.clip(dx, 0, w - 1).astype(np.float32)
>             dy = np.clip(dy, 0, h - 1).astype(np.float32)
>             
>             warped_region = cv2.remap(region_arr, dx, dy, interpolation=cv2.INTER_LINEAR)
>             arr[y:y+h, x:x+w] = warped_region
>             
>             return Image.fromarray(arr)
710,712c845
<         import json
< import random
< import time
---
>         import random
735a869
>         save_metadata: bool = True,
745a880
>         self.save_metadata: bool = save_metadata
800,809c935,946
<                     metadata: dict[str, Any] = {
<                         "background": bg_path.name,
<                         "overlay": ov_path.name,
<                         "overlay_position": [bx, by],
<                         "overlay_size": [ow, oh],
<                         "perturbations": applied,
<                         "random_seed": self.random_seed,
<                         "variant_index": i,
<                     }
<                     save_metadata(metadata, self.label_dir / fname.replace(".png", ".json"))
---
>                     # Only save metadata if enabled in config
>                     if self.save_metadata:
>                         metadata: dict[str, Any] = {
>                             "background": bg_path.name,
>                             "overlay": ov_path.name,
>                             "overlay_position": [bx, by],
>                             "overlay_size": [ow, oh],
>                             "perturbations": applied,
>                             "random_seed": self.random_seed,
>                             "variant_index": i,
>                         }
>                         save_metadata(metadata, self.label_dir / fname.replace(".png", ".json"))
1125a1263,1265
> # Get repository root dynamically
> REPO_ROOT = Path(__file__).resolve().parents[1]
> 
1161c1301
<             cwd="/home/bakobi/repos/music/benjordan/plateshapez"
---
>             cwd=str(REPO_ROOT)
1179c1319
<             cwd="/home/bakobi/repos/music/benjordan/plateshapez"
---
>             cwd=str(REPO_ROOT)
1191c1331
<             cwd="/home/bakobi/repos/music/benjordan/plateshapez"
---
>             cwd=str(REPO_ROOT)
1210c1350
<         ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
---
>         ], capture_output=True, text=True, cwd=str(REPO_ROOT))
1246c1386
<         ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
---
>         ], capture_output=True, text=True, cwd=str(REPO_ROOT))
1274c1414
<         ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
---
>         ], capture_output=True, text=True, cwd=str(REPO_ROOT))
1297c1437
<         ], capture_output=True, text=True, cwd="/home/bakobi/repos/music/benjordan/plateshapez")
---
>         ], capture_output=True, text=True, cwd=str(REPO_ROOT))
1480,1481c1620,1627
<         img = Image.new("RGB", (100, 100), color="blue")
<         region = (0, 0, 100, 100)
---
>         # Create an image with a pattern that will show warping effects
>         img = Image.new("RGB", (100, 100), color="white")
>         # Add a simple pattern
>         from PIL import ImageDraw
>         draw = ImageDraw.Draw(img)
>         for i in range(0, 100, 10):
>             draw.line([(i, 0), (i, 100)], fill="black", width=1)
>             draw.line([(0, i), (100, i)], fill="black", width=1)
1482a1629
>         region = (10, 10, 80, 80)  # Use a smaller region
1485,1486c1632,1633
<         # Low intensity warp
<         low_warp = WarpPerturbation(intensity=1.0)
---
>         # Test with global scope to ensure warping is visible
>         low_warp = WarpPerturbation(intensity=1.0, scope="global")
1490,1491c1637
<         # High intensity warp
<         high_warp = WarpPerturbation(intensity=10.0)
---
>         high_warp = WarpPerturbation(intensity=10.0, scope="global")
