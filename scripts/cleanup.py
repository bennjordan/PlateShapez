#!/usr/bin/env python3
"""
Cleanup script to reset plateshapez project to fresh state.

This script removes all generated files and test data to allow for clean testing
and demonstration of the library from a fresh state.

Usage:
    uv run python scripts/cleanup.py [--all] [--confirm]

Options:
    --all      Remove everything including .venv and build artifacts
    --confirm  Skip interactive confirmation prompts
"""

import argparse
import shutil
import sys
from pathlib import Path


def get_cleanup_paths():
    """Define paths to clean up, organized by category."""
    return {
        "demo_files": [
            "dataset/demo/backgrounds/",
            "dataset/demo/overlays/",
            "dataset/demo/demo_backgrounds/",
            "dataset/demo/demo_overlays/",
            "dataset/demo/create_test_images.py",
            "dataset/demo/demo_config.yaml",
        ],
        "generated_datasets": ["dataset/demo_dataset/", "dataset/demo_dataset_api/", "dataset/demo/demo_dataset/", "dataset/demo/demo_dataset_api/", "outputs/"],
        "build_artifacts": [
            "src/plateshapez.egg-info/",
            "build/",
            "dist/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".pytest_cache/",
            ".coverage",
            ".mypy_cache/",
            ".ruff_cache/",
        ],
        "development_files": [
            ".venv/",
            "uv.lock",
            "walk.py",
            "manifest.md",
            "manifest2.md",
            "diff.md",
        ],
    }


def remove_path(path: Path, dry_run: bool = False) -> bool:
    """Remove a file or directory safely."""
    try:
        if not path.exists():
            return True

        if dry_run:
            print(f"  [DRY RUN] Would remove: {path}")
            return True

        if path.is_file():
            path.unlink()
            print(f"  ✓ Removed file: {path}")
        elif path.is_dir():
            shutil.rmtree(path)
            print(f"  ✓ Removed directory: {path}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to remove {path}: {e}")
        return False


def cleanup_category(category: str, paths: list[str], dry_run: bool = False) -> tuple[int, int]:
    """Clean up a category of files/directories."""
    print(f"\n🧹 Cleaning {category.replace('_', ' ')}...")

    removed = 0
    failed = 0

    for path_str in paths:
        # Handle glob patterns
        if "*" in path_str:
            import glob

            matches = glob.glob(path_str, recursive=True)
            for match in matches:
                path = Path(match)
                if remove_path(path, dry_run):
                    removed += 1
                else:
                    failed += 1
        else:
            path = Path(path_str)
            if remove_path(path, dry_run):
                removed += 1
            else:
                failed += 1

    return removed, failed


def preserve_gitkeep_files():
    """Ensure .gitkeep files are preserved in dataset directories."""
    dataset_dirs = ["dataset/images", "dataset/labels"]

    for dir_path in dataset_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        gitkeep = Path(dir_path) / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"  ✓ Preserved: {gitkeep}")


def main():
    """Main cleanup function."""
    parser = argparse.ArgumentParser(description="Reset plateshapez to fresh state")
    parser.add_argument(
        "--all", action="store_true", help="Remove everything including .venv and build artifacts"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Skip interactive confirmation prompts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be removed without actually removing",
    )

    args = parser.parse_args()

    print("🧹 PlateShapez Cleanup Script")
    print("=" * 40)

    cleanup_paths = get_cleanup_paths()

    # Determine what to clean
    categories_to_clean = ["demo_files", "generated_datasets"]

    if args.all:
        categories_to_clean.extend(["build_artifacts", "development_files"])
        print("⚠️  Full cleanup mode: Will remove .venv, build artifacts, and dev files")
    else:
        print("🔧 Standard cleanup: Will remove demo files and generated datasets")

    # Show what will be cleaned
    print(f"\nCategories to clean: {', '.join(categories_to_clean)}")

    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will actually be removed")

    # Confirmation
    if not args.confirm and not args.dry_run:
        response = input("\nProceed with cleanup? (y/N): ").strip().lower()
        if response not in ["y", "yes"]:
            print("Cleanup cancelled.")
            sys.exit(0)

    # Perform cleanup
    total_removed = 0
    total_failed = 0

    for category in categories_to_clean:
        if category in cleanup_paths:
            removed, failed = cleanup_category(category, cleanup_paths[category], args.dry_run)
            total_removed += removed
            total_failed += failed

    # Preserve important files
    if not args.dry_run:
        print("\n📁 Preserving essential structure...")
        preserve_gitkeep_files()

    # Summary
    print("\n📊 Cleanup Summary:")
    print(f"  ✅ Items processed: {total_removed}")
    if total_failed > 0:
        print(f"  ❌ Failed: {total_failed}")

    if args.dry_run:
        print("\n💡 This was a dry run. Use without --dry-run to actually remove files.")
    else:
        print("\n🎉 Cleanup complete! Project reset to fresh state.")
        print("\nTo reinstall and test:")
        print("  uv sync --group dev")
        print("  uv pip install -e .")
        print("  uv run python examples/demo_full_workflow.py")


if __name__ == "__main__":
    main()
