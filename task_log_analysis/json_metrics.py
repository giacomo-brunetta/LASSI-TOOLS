#!/usr/bin/env python3
"""Extract basic usage metrics from Roo/Codex JSON dumps."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def detect_format(data: Any) -> str:
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict) and "role" in first and "content" in first:
            return "api_conversation_history"
        if isinstance(first, dict) and "type" in first and ("say" in first or "ask" in first):
            return "ui_messages"
    raise ValueError("Unsupported JSON dump format")


def maybe_load_sibling_json(base_path: Path, name: str) -> Any | None:
    sibling = base_path.with_name(name)
    if not sibling.exists():
        return None
    try:
        return load_json(sibling)
    except (OSError, json.JSONDecodeError):
        return None


def extract_environment_details_text(data: list[dict[str, Any]]) -> list[str]:
    blocks: list[str] = []
    for entry in data:
        for item in entry.get("content", []):
            if item.get("type") != "text":
                continue
            text = item.get("text") or ""
            if "<environment_details>" in text:
                blocks.append(text)
    return blocks


def parse_environment_details(blocks: list[str]) -> dict[str, Any]:
    provider = None
    model = None
    mode_slug = None
    mode_name = None

    for block in blocks:
        protocol_match = re.search(r'"apiProtocol"\s*:\s*"([^"]+)"', block)
        if protocol_match and provider is None:
            provider = protocol_match.group(1)

        model_match = re.search(r"<model>([^<]+)</model>", block)
        if model_match and model is None:
            model = model_match.group(1).strip()

        slug_match = re.search(r"<slug>([^<]+)</slug>", block)
        if slug_match and mode_slug is None:
            mode_slug = slug_match.group(1).strip()

        name_match = re.search(r"<name>([^<]+)</name>", block)
        if name_match and mode_name is None:
            mode_name = name_match.group(1).strip()

    summary: dict[str, Any] = {}
    if provider is not None:
        summary["llm_provider"] = provider
    if model is not None:
        summary["llm_model"] = model
    if mode_slug is not None:
        summary["roo_mode_slug"] = mode_slug
    if mode_name is not None:
        summary["roo_mode_name"] = mode_name
    return summary


def is_environment_text(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("<environment_details>")


def is_user_request_entry(entry: dict[str, Any]) -> bool:
    if entry.get("role") != "user":
        return False

    saw_tool_result = False
    for item in entry.get("content", []):
        item_type = item.get("type")
        if item_type == "tool_result":
            saw_tool_result = True
            continue
        if item_type != "text":
            continue

        text = (item.get("text") or "").strip()
        if not text or is_environment_text(text):
            continue

        if "<task>" in text or "<user_message>" in text:
            return True

        # In plain user-only entries, free text is a real request.
        if not saw_tool_result:
            return True

    return False


def extract_user_request_text(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in entry.get("content", []):
        if item.get("type") != "text":
            continue
        text = (item.get("text") or "").strip()
        if not text or is_environment_text(text):
            continue
        if "<task>" in text or "<user_message>" in text:
            parts.append(text)
        elif not any(content_item.get("type") == "tool_result" for content_item in entry.get("content", [])):
            parts.append(text)
    return "\n".join(parts).strip()


def summarize_text(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def format_duration_ms(duration_ms: int) -> str:
    seconds = duration_ms / 1000
    if seconds < 60:
        return f"{seconds:.3f}s"
    minutes, rem = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {rem:.3f}s"
    hours, rem = divmod(minutes, 60)
    return f"{int(hours)}h {int(rem)}m"


def build_api_turn_durations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    current_turn: dict[str, Any] | None = None

    for entry in data:
        if is_user_request_entry(entry):
            if current_turn and current_turn.get("end_ts") is not None:
                turns.append(current_turn)
            current_turn = {
                "request_ts": entry.get("ts"),
                "request_preview": summarize_text(extract_user_request_text(entry)),
                "end_ts": None,
            }
            continue

        if entry.get("role") == "assistant" and current_turn is not None:
            current_turn["end_ts"] = entry.get("ts")

    if current_turn and current_turn.get("end_ts") is not None:
        turns.append(current_turn)

    result: list[dict[str, Any]] = []
    for index, turn in enumerate(turns, start=1):
        duration_ms = int(turn["end_ts"] - turn["request_ts"])
        result.append(
            {
                "turn_index": index,
                "request_ts": turn["request_ts"],
                "end_ts": turn["end_ts"],
                "duration_ms": duration_ms,
                "duration_human": format_duration_ms(duration_ms),
                "request_preview": turn["request_preview"],
            }
        )
    return result


def is_ui_user_request(entry: dict[str, Any]) -> bool:
    return entry.get("type") == "say" and entry.get("say") in {"text", "user_feedback"}


def is_ui_assistant_step(entry: dict[str, Any]) -> bool:
    return entry.get("type") == "say" and entry.get("say") == "reasoning"


def build_ui_turn_durations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    current_turn: dict[str, Any] | None = None

    for entry in data:
        if is_ui_user_request(entry):
            if current_turn and current_turn.get("end_ts") is not None:
                turns.append(current_turn)
            current_turn = {
                "request_ts": entry.get("ts"),
                "request_preview": summarize_text((entry.get("text") or "").strip()),
                "end_ts": None,
            }
            continue

        if is_ui_assistant_step(entry) and current_turn is not None:
            current_turn["end_ts"] = entry.get("ts")

    if current_turn and current_turn.get("end_ts") is not None:
        turns.append(current_turn)

    result: list[dict[str, Any]] = []
    for index, turn in enumerate(turns, start=1):
        duration_ms = int(turn["end_ts"] - turn["request_ts"])
        result.append(
            {
                "turn_index": index,
                "request_ts": turn["request_ts"],
                "end_ts": turn["end_ts"],
                "duration_ms": duration_ms,
                "duration_human": format_duration_ms(duration_ms),
                "request_preview": turn["request_preview"],
            }
        )
    return result


def summarize_api_conversation(data: list[dict[str, Any]]) -> dict[str, Any]:
    tool_counts: Counter[str] = Counter()
    assistant_turns = 0
    user_requests = 0

    for entry in data:
        role = entry.get("role")
        if role == "assistant":
            assistant_turns += 1
            for item in entry.get("content", []):
                if item.get("type") == "tool_use":
                    tool_name = item.get("name", "unknown")
                    tool_counts[tool_name] += 1
        elif is_user_request_entry(entry):
            user_requests += 1

    turn_durations = build_api_turn_durations(data)
    total_turn_duration_ms = sum(turn["duration_ms"] for turn in turn_durations)

    return {
        "format": "api_conversation_history",
        "turns": assistant_turns + user_requests,
        "assistant_turns": assistant_turns,
        "user_requests": user_requests,
        "tool_uses_total": sum(tool_counts.values()),
        "tool_uses_by_type": dict(sorted(tool_counts.items())),
        "turn_durations": turn_durations,
        "turn_duration_total_ms": total_turn_duration_ms,
        "turn_duration_total_human": format_duration_ms(total_turn_duration_ms),
    }


def summarize_ui_messages(data: list[dict[str, Any]]) -> dict[str, Any]:
    tool_counts: Counter[str] = Counter()
    assistant_turns = 0
    user_requests = 0
    api_request_count = 0
    retry_error_count = 0
    tokens_in_total = 0
    tokens_out_total = 0
    cache_reads_total = 0
    cache_writes_total = 0
    cost_total = 0.0
    providers: set[str] = set()

    for entry in data:
        entry_type = entry.get("type")
        say_kind = entry.get("say")
        ask_kind = entry.get("ask")

        if entry_type == "say" and say_kind == "reasoning":
            assistant_turns += 1
        elif entry_type == "say" and say_kind in {"text", "user_feedback"}:
            user_requests += 1
        elif entry_type == "say" and say_kind == "api_req_started":
            api_request_count += 1
            try:
                payload = json.loads(entry.get("text") or "{}")
            except json.JSONDecodeError:
                payload = {}
            if payload.get("apiProtocol"):
                providers.add(str(payload["apiProtocol"]))
            tokens_in_total += int(payload.get("tokensIn", 0) or 0)
            tokens_out_total += int(payload.get("tokensOut", 0) or 0)
            cache_reads_total += int(payload.get("cacheReads", 0) or 0)
            cache_writes_total += int(payload.get("cacheWrites", 0) or 0)
            cost_total += float(payload.get("cost", 0) or 0)
        elif entry_type == "say" and say_kind == "api_req_retry_delayed":
            retry_error_count += 1
        elif entry_type == "ask" and ask_kind == "tool":
            try:
                payload = json.loads(entry.get("text") or "{}")
            except json.JSONDecodeError:
                payload = {}
            tool_name = payload.get("tool", "unknown")
            tool_counts[tool_name] += 1

    turn_durations = build_ui_turn_durations(data)
    total_turn_duration_ms = sum(turn["duration_ms"] for turn in turn_durations)

    return {
        "format": "ui_messages",
        "turns": assistant_turns + user_requests,
        "assistant_turns": assistant_turns,
        "user_requests": user_requests,
        "tool_uses_total": sum(tool_counts.values()),
        "tool_uses_by_type": dict(sorted(tool_counts.items())),
        "turn_durations": turn_durations,
        "turn_duration_total_ms": total_turn_duration_ms,
        "turn_duration_total_human": format_duration_ms(total_turn_duration_ms),
        "api_requests": api_request_count,
        "tokens_in_total": tokens_in_total,
        "tokens_out_total": tokens_out_total,
        "cache_reads_total": cache_reads_total,
        "cache_writes_total": cache_writes_total,
        "cost_total": round(cost_total, 12),
        "retry_error_count": retry_error_count,
        "llm_provider": sorted(providers)[0] if providers else None,
        "note": "UI message dumps are less precise than api_conversation_history dumps.",
    }


def summarize_task_metadata(data: dict[str, Any]) -> dict[str, Any]:
    files = data.get("files_in_context", [])
    read_files = 0
    written_files = 0
    user_written_files = 0
    roo_written_files = 0

    for entry in files:
        if entry.get("roo_read_date") is not None:
            read_files += 1
        if entry.get("roo_edit_date") is not None or entry.get("user_edit_date") is not None:
            written_files += 1
        if entry.get("user_edit_date") is not None:
            user_written_files += 1
        if entry.get("roo_edit_date") is not None:
            roo_written_files += 1

    return {
        "files_in_context_total": len(files),
        "files_read_count": read_files,
        "files_written_count": written_files,
        "files_written_by_user_count": user_written_files,
        "files_written_by_roo_count": roo_written_files,
    }


def attach_related_metrics(summary: dict[str, Any], json_path: Path) -> dict[str, Any]:
    ui_data = None
    metadata_data = None
    api_data = None

    if json_path.name == "ui_messages.json":
        ui_data = load_json(json_path)
    else:
        ui_data = maybe_load_sibling_json(json_path, "ui_messages.json")

    if json_path.name == "task_metadata.json":
        metadata_data = load_json(json_path)
    else:
        metadata_data = maybe_load_sibling_json(json_path, "task_metadata.json")

    if json_path.name == "api_conversation_history.json":
        api_data = load_json(json_path)
    else:
        api_data = maybe_load_sibling_json(json_path, "api_conversation_history.json")

    if isinstance(ui_data, list):
        ui_summary = summarize_ui_messages(ui_data)
        for key in [
            "api_requests",
            "tokens_in_total",
            "tokens_out_total",
            "cache_reads_total",
            "cache_writes_total",
            "cost_total",
            "retry_error_count",
            "llm_provider",
        ]:
            summary[key] = ui_summary[key]

    if isinstance(api_data, list):
        summary.update(parse_environment_details(extract_environment_details_text(api_data)))

    if isinstance(metadata_data, dict):
        summary.update(summarize_task_metadata(metadata_data))

    return summary


def load_history_item(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = load_json(path)
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def summarize_task_directory(task_dir: Path) -> dict[str, Any]:
    api_path = task_dir / "api_conversation_history.json"
    ui_path = task_dir / "ui_messages.json"
    history_path = task_dir / "history_item.json"

    summary: dict[str, Any]
    if api_path.exists():
        data = load_json(api_path)
        summary = summarize_api_conversation(data)
        summary = attach_related_metrics(summary, api_path)
    elif ui_path.exists():
        data = load_json(ui_path)
        summary = summarize_ui_messages(data)
        summary = attach_related_metrics(summary, ui_path)
    else:
        summary = {"format": "task_directory", "note": "No conversation dumps found."}
        summary = attach_related_metrics(summary, task_dir / "task_metadata.json")

    history_item = load_history_item(history_path)
    if history_item is not None:
        summary.update(
            {
                "task_id": history_item.get("id", task_dir.name),
                "parent_task_id": history_item.get("parentTaskId"),
                "task_number": history_item.get("number"),
                "task_ts": history_item.get("ts"),
                "task_text": history_item.get("task"),
                "task_status": history_item.get("status"),
                "roo_code_mode": history_item.get("mode"),
                "api_config_name": history_item.get("apiConfigName"),
                "workspace": history_item.get("workspace"),
                "history_tokens_in": history_item.get("tokensIn"),
                "history_tokens_out": history_item.get("tokensOut"),
                "history_cache_reads": history_item.get("cacheReads"),
                "history_cache_writes": history_item.get("cacheWrites"),
                "history_total_cost": history_item.get("totalCost"),
                "history_size": history_item.get("size"),
            }
        )
    else:
        summary["task_id"] = task_dir.name

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract turns, tool-usage counts, and user-request counts from a JSON dump."
    )
    parser.add_argument("json_file", type=Path, help="Path to api_conversation_history.json or ui_messages.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the JSON output")
    args = parser.parse_args()

    if args.json_file.is_dir():
        summary = summarize_task_directory(args.json_file)
    else:
        data = load_json(args.json_file)
        dump_format = detect_format(data)

        if dump_format == "api_conversation_history":
            summary = summarize_api_conversation(data)
        else:
            summary = summarize_ui_messages(data)

        summary = attach_related_metrics(summary, args.json_file)

    output = json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True)
    print(output)


if __name__ == "__main__":
    main()
