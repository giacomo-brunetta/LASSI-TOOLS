#!/usr/bin/env python3
"""Run the complete paper benchmark matrix sequentially and journal every result."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from generate_configs import HERE, REPO, generate


def _arguments() -> argparse.Namespace:
    """Parse suite controls.

    Returns:
        Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--kernel", action="append", dest="kernels")
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-doctor", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    return args


def _append(path: Path, record: dict[str, Any]) -> None:
    """Append and fsync one JSONL journal record.

    Args:
        path: Session journal path.
        record: JSON-serializable event.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _completed(path: Path | None) -> set[tuple[str, str, int]]:
    """Load successful model/kernel/repetition keys from a prior journal.

    Args:
        path: Existing journal or ``None``.

    Returns:
        Keys that need not be rerun.
    """
    if path is None or not path.is_file():
        return set()
    result = set()
    for line in path.read_text().splitlines():
        event = json.loads(line)
        if event.get("event") == "finish" and event.get("exit_code") == 0:
            result.add((event["model"], event["kernel"], int(event["repetition"])))
    return result


def _run(command: list[str], log_path: Path) -> int:
    """Execute one command while preserving a complete combined log.

    Args:
        command: Argument vector to execute.
        log_path: File receiving stdout and stderr.

    Returns:
        Child exit code.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as stream:
        process = subprocess.run(
            command,
            cwd=REPO,
            stdout=stream,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return process.returncode


def _run_dir(log_path: Path) -> str | None:
    """Extract the run artifact path from the CLI's final JSON envelope.

    Args:
        log_path: Combined command log.

    Returns:
        Recorded run directory, or ``None`` when the command failed before one
        was returned.
    """
    text = log_path.read_text(errors="replace")
    decoder = json.JSONDecoder()
    envelopes: list[dict[str, Any]] = []
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("tool") == "run":
            envelopes.append(value)
    if not envelopes:
        return None
    value = envelopes[-1].get("run_dir")
    return str(value) if value else None


def main() -> int:
    """Generate configs, run GPT before Claude, and persist a resumable journal.

    Returns:
        Zero only when every requested experiment succeeds.
    """
    args = _arguments()
    generated = generate()
    manifest = yaml.safe_load((HERE / "benchmarks.yaml").read_text())
    model_order = [str(item["id"]) for item in manifest["models"]]
    kernel_order = [str(item["id"]) for item in manifest["kernels"]]
    if args.models:
        unknown = set(args.models) - set(model_order)
        if unknown:
            raise SystemExit(f"unknown models: {', '.join(sorted(unknown))}")
        model_order = [model for model in model_order if model in args.models]
    if args.kernels:
        unknown = set(args.kernels) - set(kernel_order)
        if unknown:
            raise SystemExit(f"unknown kernels: {', '.join(sorted(unknown))}")
        kernel_order = [kernel for kernel in kernel_order if kernel in args.kernels]
    generated_set = {path.resolve() for path in generated}
    timestamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    journal = args.resume or REPO / "runs" / "paper-suite" / f"session-{timestamp}.jsonl"
    done = _completed(args.resume)
    python = sys.executable
    first_config = HERE / "configs" / model_order[0] / f"{kernel_order[0]}.yaml"
    if not args.skip_doctor and not args.dry_run:
        doctor_log = journal.with_suffix(".doctor.log")
        doctor_code = _run(
            [python, "-m", "lassi_x.cli", "execution", "doctor", "--config", str(first_config)],
            doctor_log,
        )
        _append(journal, {"event": "doctor", "exit_code": doctor_code, "log": str(doctor_log)})
        if doctor_code:
            print(f"Execution doctor failed; see {doctor_log}", file=sys.stderr)
            return doctor_code
    failures = 0
    for model in model_order:  # Manifest order is GPT first, then Claude.
        for kernel in kernel_order:
            config = HERE / "configs" / model / f"{kernel}.yaml"
            if config.resolve() not in generated_set:
                raise RuntimeError(f"generator did not produce {config}")
            for repetition in range(1, args.repetitions + 1):
                key = (model, kernel, repetition)
                if key in done:
                    print(f"SKIP {model} {kernel} repetition {repetition}")
                    continue
                command = [python, "-m", "lassi_x.cli", "run", str(config)]
                print(f"RUN  {model} {kernel} repetition {repetition}", flush=True)
                if args.dry_run:
                    print(" ".join(command))
                    continue
                log_path = (
                    journal.parent / "logs" / (f"{journal.stem}-{model}-{kernel}-r{repetition}.log")
                )
                started = dt.datetime.now(dt.UTC).isoformat()
                _append(
                    journal,
                    {
                        "event": "start",
                        "model": model,
                        "kernel": kernel,
                        "repetition": repetition,
                        "config": str(config),
                        "started_at": started,
                    },
                )
                code = _run(command, log_path)
                _append(
                    journal,
                    {
                        "event": "finish",
                        "model": model,
                        "kernel": kernel,
                        "repetition": repetition,
                        "exit_code": code,
                        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
                        "log": str(log_path),
                        "run_dir": _run_dir(log_path),
                    },
                )
                if code:
                    failures += 1
                    print(f"FAIL {model} {kernel}; see {log_path}", file=sys.stderr)
                    if args.stop_on_failure:
                        return code
    print(f"Journal: {journal}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
