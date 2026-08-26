"""Resumable target-local compatibility probing."""

# ruff: noqa: TC003

from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from compat_tool.io import atomic_json, load_json, stable_hash
from compat_tool.target import load_target

TERMINAL_STATUSES = {"compiled", "compile_rejected", "not_applicable"}


def _worker_payload(command: list[str], timeout_s: float) -> tuple[dict[str, Any], int]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": f"probe exceeded {timeout_s:g}s"}, 124
    if completed.returncode < 0:
        return {
            "status": "compiler_crash",
            "error": f"worker terminated by signal {-completed.returncode}",
        }, completed.returncode
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        return {
            "status": "compiler_crash",
            "error": (completed.stderr or completed.stdout or "worker produced no JSON")[-4000:],
        }, completed.returncode
    if not payload.get("ok"):
        return {
            "status": "environment_error",
            "error": str(payload.get("error")),
        }, completed.returncode
    return dict(payload["result"]), completed.returncode


def _metadata(target_path: Path, timeout_s: float) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "compat_tool.probe_worker",
        "--target",
        str(target_path),
        "--metadata",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=min(timeout_s, 60))
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        raise RuntimeError((completed.stderr or completed.stdout)[-4000:]) from error
    if completed.returncode != 0 or not payload.get("ok"):
        raise RuntimeError(str(payload.get("error") or "checker metadata failed"))
    return dict(payload["metadata"])


def run_probe(
    manifest_path: Path,
    target_path: Path,
    run_dir: Path,
    *,
    resume: bool = False,
    selected_ops: set[str] | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    target = load_target(target_path)
    target_precisions = list(target["precisions"])
    missing = sorted(set(target_precisions) - set(manifest["precisions"]))
    if missing:
        raise ValueError("manifest does not contain target precisions: " + ", ".join(missing))

    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "results.json"
    previous = load_json(result_path, default={}) if resume else {}
    results: dict[str, Any] = dict(previous.get("results") or {})
    target_hash = stable_hash({key: value for key, value in target.items() if key != "config_path"})
    header = {
        "schema_version": 1,
        "kind": "compatibility-probe-results",
        "target": {key: value for key, value in target.items() if key != "config_path"},
        "target_hash": target_hash,
        "manifest_hash": manifest["manifest_hash"],
        "started_at": previous.get("started_at") or datetime.now(UTC).isoformat(),
        "environment": _metadata(target_path, float(target["timeout_s"])),
        "results": results,
    }

    cells: list[tuple[str, str, str, dict[str, Any]]] = []
    for op_name, record in sorted(manifest["operators"].items()):
        if selected_ops is not None and op_name not in selected_ops:
            continue
        if not record["included"]:
            continue
        for precision in target_precisions:
            for case_name, case in sorted(record["cases"][precision].items()):
                cells.append((op_name, precision, case_name, case))
    if limit is not None:
        cells = cells[:limit]

    def persist() -> None:
        header["updated_at"] = datetime.now(UTC).isoformat()
        atomic_json(result_path, header)

    pending: list[tuple[str, str, str, list[str]]] = []
    expected_keys: set[str] = set()
    for op_name, precision, case_name, case in cells:
        key = f"{op_name}|{precision}|{case_name}"
        expected_keys.add(key)
        expected_key = stable_hash(
            {
                "manifest_hash": manifest["manifest_hash"],
                "target": {item: value for item, value in target.items() if item != "config_path"},
                "op": op_name,
                "precision": precision,
                "case": case,
            }
        )
        old = results.get(key)
        if (
            resume
            and old
            and old.get("cache_key") == expected_key
            and old.get("status") in TERMINAL_STATUSES
        ):
            continue
        validation = case["validation"]
        if validation["status"] != "valid":
            results[key] = {
                "status": validation["status"],
                "error": validation.get("error"),
                "cache_key": expected_key,
            }
            persist()
            continue
        cell_dir = run_dir / "cells" / stable_hash(key)[:16]
        cell_dir.mkdir(parents=True, exist_ok=True)
        command = [
            sys.executable,
            "-m",
            "compat_tool.probe_worker",
            "--target",
            str(target_path),
            "--manifest",
            str(manifest_path),
            "--op",
            op_name,
            "--precision",
            precision,
            "--case",
            case_name,
            "--work-dir",
            str(cell_dir),
        ]
        pending.append((key, op_name, precision, command))

    with ThreadPoolExecutor(max_workers=int(target["max_workers"])) as executor:
        future_map = {
            executor.submit(_worker_payload, command, float(target["timeout_s"])): key
            for key, _op_name, _precision, command in pending
        }
        for future in as_completed(future_map):
            key = future_map[future]
            result, returncode = future.result()
            result["worker_returncode"] = returncode
            results[key] = result
            persist()

    persist()
    header["summary"] = {
        status: sum(result.get("status") == status for result in results.values())
        for status in sorted({str(result.get("status")) for result in results.values()})
    }
    header["complete"] = all(
        results.get(key, {}).get("status") in TERMINAL_STATUSES for key in expected_keys
    ) and len(expected_keys) == len(cells)
    persist()
    return header
