from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


def sh(cmd: List[str]) -> int:
    """Run a shell command, stream output, and return exit code."""
    try:
        proc = subprocess.run(cmd, check=False)
        return proc.returncode
    except FileNotFoundError as e:
        print(f"Command not found: {cmd[0]}\n{e}")
        return 127


def cmd_format() -> int:
    return sh(["uv", "run", "ruff", "format", "."])


def cmd_lint() -> int:
    return sh(["uv", "run", "ruff", "check", ".", "--fix"])  # keep parity with scripts/check.sh


def cmd_type() -> int:
    return sh(["uv", "run", "mypy", "."])


def cmd_check() -> int:
    rc = cmd_format()
    if rc != 0:
        return rc
    rc = cmd_lint()
    if rc != 0:
        return rc
    rc = cmd_type()
    return rc


def cmd_hooks_install() -> int:
    # Install both pre-commit and pre-push
    return sh(
        [
            "uv",
            "run",
            "pre-commit",
            "install",
            "--hook-type",
            "pre-commit",
            "--hook-type",
            "pre-push",
        ]
    )


def cmd_hooks_run() -> int:
    return sh(["uv", "run", "pre-commit", "run", "--all-files"])


def cmd_cleanup() -> int:
    """Run the cleanup script to reset project to fresh state."""
    cleanup_script = Path("scripts/cleanup.py")
    if not cleanup_script.exists():
        print(f"Cleanup script not found: {cleanup_script}")
        return 1
    return sh(["python", str(cleanup_script)])


def cmd_cleanup_all() -> int:
    """Run full cleanup including .venv and build artifacts."""
    cleanup_script = Path("scripts/cleanup.py")
    if not cleanup_script.exists():
        print(f"Cleanup script not found: {cleanup_script}")
        return 1
    return sh(["python", str(cleanup_script), "--all"])


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="dev", description="Developer task runner for plateshapez")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("format", help="Run ruff formatter")
    sub.add_parser("lint", help="Run ruff linter with autofix")
    sub.add_parser("type", help="Run mypy type checker")
    sub.add_parser("check", help="Run format, lint, and type checks")

    hooks = sub.add_parser("hooks", help="Manage pre-commit hooks")
    hooks_sub = hooks.add_subparsers(dest="hooks_cmd", required=True)
    hooks_sub.add_parser("install", help="Install pre-commit and pre-push hooks")
    hooks_sub.add_parser("run", help="Run pre-commit on all files")

    # Convenience alias: `dev pre-commit` => run hooks on all files
    sub.add_parser("pre-commit", help="Alias of hooks run (pre-commit run --all-files)")
    
    # Cleanup commands
    cleanup = sub.add_parser("cleanup", help="Reset project to fresh state")
    cleanup_sub = cleanup.add_subparsers(dest="cleanup_cmd", required=False)
    cleanup_sub.add_parser("all", help="Full cleanup including .venv and build artifacts")

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "format":
        return cmd_format()
    if args.command == "lint":
        return cmd_lint()
    if args.command == "type":
        return cmd_type()
    if args.command == "check":
        return cmd_check()
    if args.command == "pre-commit":
        return cmd_hooks_run()
    if args.command == "hooks":
        if args.hooks_cmd == "install":
            return cmd_hooks_install()
        if args.hooks_cmd == "run":
            return cmd_hooks_run()
    if args.command == "cleanup":
        if hasattr(args, 'cleanup_cmd') and args.cleanup_cmd == "all":
            return cmd_cleanup_all()
        else:
            return cmd_cleanup()

    print("Unknown command")
    return 2


if __name__ == "__main__":
    sys.exit(main())
