"""Run the same complete quality checks locally and in CI.

Includes every versioned Python file and new Python files outside historical
experiment artifacts. Untracked docs/experiments files are local archived data;
versioned scripts there remain linted and formatted.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def python_files() -> list[str]:
    """Include new code as well as versioned scripts without scanning local archives."""
    tracked = subprocess.check_output(["git", "ls-files", "-z", "--cached", "--", "*.py"], cwd=ROOT)
    new = subprocess.check_output(
        [
            "git",
            "ls-files",
            "-z",
            "--others",
            "--exclude-standard",
            "--exclude=docs/experiments/**",
            "--",
            "*.py",
        ],
        cwd=ROOT,
    )
    return sorted(
        {
            path
            for path in os.fsdecode(tracked + new).split("\0")
            if path and (ROOT / path).is_file()
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "check", nargs="?", choices=["all", "lint", "format", "types", "tests"], default="all"
    )
    args = parser.parse_args()
    files = python_files()
    commands = {
        "lint": [sys.executable, "-m", "ruff", "check", *files],
        "format": [sys.executable, "-m", "ruff", "format", "--check", *files],
        "types": [sys.executable, "-m", "mypy"],
        "tests": [sys.executable, "-m", "pytest"],
    }
    results = {}
    for name, command in commands.items():
        if args.check not in ("all", name):
            continue
        print(f"\n=== {name} ===", flush=True)
        results[name] = subprocess.run(command, cwd=ROOT, check=False).returncode
    print("\nQuality results:", flush=True)
    for name, code in results.items():
        print(f"  {name}: {'PASS' if code == 0 else 'FAIL'}", flush=True)
    return int(any(results.values()))


if __name__ == "__main__":
    raise SystemExit(main())
