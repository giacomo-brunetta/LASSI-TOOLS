#!/usr/bin/env python3
"""Analyze a Roo task family starting from a task id."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from json_metrics import load_history_item, summarize_task_directory


TASKS_ROOT = Path("/home/gbrun/.vscode-server/data/User/globalStorage/rooveterinaryinc.roo-cline/tasks")


def iso_from_ms(ts: int | None) -> str | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat()


def collect_history_items(tasks_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for task_dir in tasks_root.iterdir():
        if not task_dir.is_dir():
            continue
        history = load_history_item(task_dir / "history_item.json")
        if history is None:
            continue
        history["_task_dir"] = str(task_dir)
        items.append(history)
    return items


def sort_task_summaries(task_summaries: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    def key(summary: dict[str, Any]) -> tuple[int, int, str, str]:
        task_id = str(summary.get("task_id") or "")
        return (
            0 if task_id == parent_id else 1,
            int(summary.get("task_ts") or 0),
            int(summary.get("task_number") or 0),
            task_id,
        )

    return sorted(task_summaries, key=key)


def build_task_family(task_id: str, tasks_root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    input_dir = tasks_root / task_id
    input_history = load_history_item(input_dir / "history_item.json")
    if input_history is None:
        raise FileNotFoundError(f"Missing or unreadable history_item.json for task {task_id}")
    input_history["_task_dir"] = str(input_dir)

    all_items = collect_history_items(tasks_root)
    history_by_id = {item["id"]: item for item in all_items if item.get("id")}

    parent_id = input_history.get("parentTaskId") or input_history.get("id")
    if not parent_id:
        raise ValueError(f"Task {task_id} does not have an id in history_item.json")

    parent_history = history_by_id.get(parent_id)
    if parent_history is None:
        raise FileNotFoundError(f"Missing or unreadable parent history_item.json for task {parent_id}")

    family_histories: list[dict[str, Any]] = [parent_history]
    family_histories.extend(
        history
        for history in all_items
        if history.get("parentTaskId") == parent_id and history.get("id")
    )

    dedup: dict[str, dict[str, Any]] = {item["id"]: item for item in family_histories if item.get("id")}
    task_summaries = [summarize_task_directory(Path(item["_task_dir"])) for item in dedup.values()]
    ordered = sort_task_summaries(task_summaries, parent_id)
    return input_history, parent_history, ordered


def aggregate_totals(task_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    total_keys = [
        "turns",
        "assistant_turns",
        "user_requests",
        "tool_uses_total",
        "turn_duration_total_ms",
        "api_requests",
        "tokens_in_total",
        "tokens_out_total",
        "cache_reads_total",
        "cache_writes_total",
        "cost_total",
        "retry_error_count",
        "files_in_context_total",
        "files_read_count",
        "files_written_count",
        "files_written_by_user_count",
        "files_written_by_roo_count",
    ]
    totals: dict[str, Any] = {}
    for key in total_keys:
        if key == "cost_total":
            totals[key] = round(
                sum(float(summary.get(key, 0) or 0) for summary in task_summaries),
                12,
            )
        else:
            totals[key] = sum(int(summary.get(key, 0) or 0) for summary in task_summaries)
    tool_counts: Counter[str] = Counter()
    for summary in task_summaries:
        for tool_name, count in (summary.get("tool_uses_by_type") or {}).items():
            tool_counts[str(tool_name)] += int(count or 0)
    totals["tool_uses_by_type"] = dict(sorted(tool_counts.items()))
    return totals


def build_subtask_timeline(task_summaries: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for summary in task_summaries:
        if summary.get("task_id") == parent_id:
            continue
        timeline.append(
            {
                "task_id": summary.get("task_id"),
                "task_number": summary.get("task_number"),
                "task_ts": summary.get("task_ts"),
                "task_ts_iso": iso_from_ms(summary.get("task_ts")),
                "task_status": summary.get("task_status"),
                "roo_code_mode": summary.get("roo_code_mode"),
                "llm_model": summary.get("llm_model"),
                "llm_provider": summary.get("llm_provider"),
            }
        )
    timeline.sort(key=lambda item: (item.get("task_ts") or 0, item.get("task_id") or ""))
    return timeline


def extract_subtask_metrics(task_summaries: list[dict[str, Any]], parent_id: str) -> list[dict[str, Any]]:
    subtasks = [summary for summary in task_summaries if summary.get("task_id") != parent_id]
    return sort_task_summaries(subtasks, parent_id)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyze a task family: parent task plus all subtasks that share that parent."
    )
    parser.add_argument("task_id", help="Task id to analyze")
    parser.add_argument("--tasks-root", type=Path, default=TASKS_ROOT, help="Root directory that contains task folders")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    input_history, parent_history, task_summaries = build_task_family(args.task_id, args.tasks_root)
    parent_id = str(parent_history["id"])
    parent_summary = next(summary for summary in task_summaries if summary.get("task_id") == parent_id)
    per_subtask_metrics = extract_subtask_metrics(task_summaries, parent_id)
    subtask_timeline = build_subtask_timeline(task_summaries, parent_id)

    output = {
        "input_task_id": args.task_id,
        "parent_task_id": parent_id,
        "related_task_ids": [summary.get("task_id") for summary in task_summaries],
        "related_task_count": len(task_summaries),
        "subtask_count": len(subtask_timeline),
        "parent_task_metrics": parent_summary,
        "subtask_timeline": subtask_timeline,
        "subtask_totals": aggregate_totals(per_subtask_metrics),
        "totals": aggregate_totals(task_summaries),
        "per_subtask_metrics": per_subtask_metrics,
        "tasks": task_summaries,
        "input_task_has_parent": bool(input_history.get("parentTaskId")),
    }

    print(json.dumps(output, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
