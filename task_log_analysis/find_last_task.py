#!/usr/bin/env python3
"""Identify the most recent Roo task in the tasks directory."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from json_metrics import load_history_item, summarize_task_directory


DEFAULT_TASKS_ROOT = (
    Path.home() / ".vscode-server" / "data" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "tasks"
)


def iso_from_ms(ts: int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()


def find_last_task(tasks_root: Path) -> Path:
    if not tasks_root.exists():
        raise FileNotFoundError(f"Tasks root does not exist: {tasks_root}")
    if not tasks_root.is_dir():
        raise NotADirectoryError(f"Tasks root is not a directory: {tasks_root}")

    latest_task_dir: Path | None = None
    latest_key: tuple[int, str] | None = None

    for task_dir in tasks_root.iterdir():
        if not task_dir.is_dir():
            continue

        history = load_history_item(task_dir / "history_item.json")
        if history is None:
            continue

        ts = int(history.get("ts") or 0)
        key = (ts, task_dir.name)
        if latest_key is None or key > latest_key:
            latest_key = key
            latest_task_dir = task_dir

    if latest_task_dir is None:
        raise FileNotFoundError(f"No task folders with readable history_item.json found in {tasks_root}")

    return latest_task_dir


def build_output(task_dir: Path) -> dict[str, Any]:
    summary = summarize_task_directory(task_dir)
    summary["task_dir"] = str(task_dir)
    summary["task_ts_iso"] = iso_from_ms(summary.get("task_ts"))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the most recent task found in the Roo tasks directory.")
    parser.add_argument("--tasks-root", type=Path, default=DEFAULT_TASKS_ROOT, help="Root directory that contains task folders")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of only the task id")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    task_dir = find_last_task(args.tasks_root)
    if not args.json:
        print(task_dir.name)
        return

    print(json.dumps(build_output(task_dir), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
