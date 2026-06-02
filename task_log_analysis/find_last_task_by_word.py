#!/usr/bin/env python3
"""Find the most recent task whose chat logs contain a given word."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from find_last_task import DEFAULT_TASKS_ROOT
from json_metrics import load_history_item, load_json, summarize_task_directory


def iter_chat_log_paths(task_dir: Path) -> list[Path]:
    return [task_dir / "api_conversation_history.json", task_dir / "ui_messages.json"]


def string_contains_word(value: str, pattern: re.Pattern[str]) -> bool:
    return bool(pattern.search(value))


def object_contains_word(data: Any, pattern: re.Pattern[str]) -> bool:
    if isinstance(data, str):
        return string_contains_word(data, pattern)
    if isinstance(data, dict):
        return any(object_contains_word(value, pattern) for value in data.values())
    if isinstance(data, list):
        return any(object_contains_word(item, pattern) for item in data)
    return False


def task_logs_contain_word(task_dir: Path, pattern: re.Pattern[str]) -> bool:
    for log_path in iter_chat_log_paths(task_dir):
        if not log_path.exists():
            continue
        try:
            data = load_json(log_path)
        except (OSError, json.JSONDecodeError):
            continue
        if object_contains_word(data, pattern):
            return True
    return False


def find_last_task_by_word(tasks_root: Path, word: str) -> Path:
    if not tasks_root.exists():
        raise FileNotFoundError(f"Tasks root does not exist: {tasks_root}")
    if not tasks_root.is_dir():
        raise NotADirectoryError(f"Tasks root is not a directory: {tasks_root}")

    pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    latest_task_dir: Path | None = None
    latest_key: tuple[int, str] | None = None

    for task_dir in tasks_root.iterdir():
        if not task_dir.is_dir():
            continue

        history = load_history_item(task_dir / "history_item.json")
        if history is None:
            continue
        if not task_logs_contain_word(task_dir, pattern):
            continue

        ts = int(history.get("ts") or 0)
        key = (ts, task_dir.name)
        if latest_key is None or key > latest_key:
            latest_key = key
            latest_task_dir = task_dir

    if latest_task_dir is None:
        raise FileNotFoundError(f'No task chat logs containing the word "{word}" found in {tasks_root}')

    return latest_task_dir


def build_output(task_dir: Path, word: str) -> dict[str, Any]:
    summary = summarize_task_directory(task_dir)
    summary["task_dir"] = str(task_dir)
    summary["matched_word"] = word
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Print the most recent task whose chat logs contain a given word."
    )
    parser.add_argument("word", help="Case-insensitive whole word to search for in task chat logs")
    parser.add_argument("--tasks-root", type=Path, default=DEFAULT_TASKS_ROOT, help="Root directory that contains task folders")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of only the task id")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    task_dir = find_last_task_by_word(args.tasks_root, args.word)
    if not args.json:
        print(task_dir.name)
        return

    print(json.dumps(build_output(task_dir, args.word), indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
