#!/usr/bin/env python3
"""Run the complete paper benchmark matrix sequentially and journal every result."""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml
from generate_configs import HERE, REPO, generate

# A stalled child must not block the whole matrix.  This is the outer backstop
# only: each measurement is already bounded by its backend's timeout_s in
# generate_configs.py (CUDA 180s, Groq 1800s to cover a cold GroqFlow compile),
# so a run that reaches this ceiling is hung somewhere those bounds do not
# reach -- agent transport, teardown, an endpoint that stopped answering.
# Healthy kernels in the first full session took 10-26 minutes end to end, so
# one hour is ~2.3x the slowest observed run and still fails fast enough that a
# wedged kernel costs an hour rather than the rest of the evening.
DEFAULT_RUN_TIMEOUT_S = 3600.0

# Grace period between SIGTERM and SIGKILL when reaping a timed-out run.
TERM_GRACE_S = 30.0

# A matrix cell that fails for the same reason as the two before it is not going
# to start working on the fourth try. A dead LLM endpoint once produced fifteen
# consecutive identical failures at ~2 minutes each; three bounds that at ~6.
DEFAULT_MAX_CONSECUTIVE_FAILURES = 3


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
    parser.add_argument("--skip-model-preflight", action="store_true")
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=DEFAULT_MAX_CONSECUTIVE_FAILURES,
        help=(
            "Abort the matrix after this many consecutive failures that share one "
            "error signature. Use 0 to disable."
        ),
    )
    parser.add_argument(
        "--run-timeout-s",
        type=float,
        default=DEFAULT_RUN_TIMEOUT_S,
        help=(
            "Wall-clock ceiling for one kernel run. The run is terminated and "
            "journaled as a failure instead of stalling the matrix. Use 0 to disable."
        ),
    )
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    if args.run_timeout_s < 0:
        parser.error("--run-timeout-s must not be negative")
    if args.max_consecutive_failures < 0:
        parser.error("--max-consecutive-failures must not be negative")
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


def _reap(process: subprocess.Popen[bytes]) -> None:
    """Terminate a timed-out run and every process it spawned.

    The child leads its own process group, so signalling the group also reaps
    MCP servers, Academy agents, and endpoint workers that would otherwise
    survive the parent and hold the log file open.

    Args:
        process: Running child that exceeded its deadline.
    """
    for number in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(process.pid, number)
        except ProcessLookupError:  # Already gone; nothing left to signal.
            return
        try:
            process.wait(timeout=TERM_GRACE_S)
            return
        except subprocess.TimeoutExpired:
            continue  # Escalate to SIGKILL.
    process.wait()


def _run(command: list[str], log_path: Path, timeout_s: float) -> tuple[int, bool]:
    """Execute one command under a deadline while preserving a combined log.

    Args:
        command: Argument vector to execute.
        log_path: File receiving stdout and stderr.
        timeout_s: Wall-clock ceiling, or zero to wait indefinitely.

    Returns:
        Pair of the child exit code and whether the deadline was hit. A timed
        out run reports a negative signal-style code from the reap.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w") as stream:
        process = subprocess.Popen(
            command,
            cwd=REPO,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # Own process group so _reap can signal it.
        )
        try:
            return process.wait(timeout=timeout_s or None), False
        except subprocess.TimeoutExpired:
            _reap(process)
            return process.returncode or 1, True
        except KeyboardInterrupt:
            _reap(process)
            raise


def _envelope(log_path: Path) -> dict[str, Any] | None:
    """Extract the CLI's final JSON result envelope from a combined log.

    Args:
        log_path: Combined command log.

    Returns:
        Last ``tool: run`` envelope, or ``None`` when the command failed before
        emitting one.
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
    return envelopes[-1] if envelopes else None


def _error(envelope: dict[str, Any] | None) -> str:
    """Read the failure cause out of a result envelope.

    Args:
        envelope: Envelope from :func:`_envelope`, or ``None``.

    Returns:
        The recorded ``"Type: message"`` error, or an empty string when the run
        failed before emitting one.
    """
    return str((envelope or {}).get("error") or "")


def _signature(error: str, timed_out: bool) -> str:
    """Reduce a failure to a value comparable across matrix cells.

    Kernel names and paths leak into error text, so only the exception type is
    kept: fifteen runs killed by one dead endpoint must collapse to one
    signature for the circuit breaker to see them as the same fault.

    Args:
        error: Full error text from the envelope.
        timed_out: Whether the run was reaped at its deadline.

    Returns:
        A short stable signature, empty when the run succeeded.
    """
    if timed_out:
        return "timeout"
    if not error:
        return ""
    head, separator, _ = error.partition(":")
    return head.strip() if separator else error.strip()[:60]


def _preflight_models(
    model_order: list[str],
    kernel: str,
    timeout_s: float,
) -> dict[str, dict[str, Any]]:
    """Probe each model's LLM endpoint before committing to its block of cells.

    A model whose endpoint is unreachable, unauthorized, or does not accept
    tool-call replay will fail every one of its kernels identically. Probing
    once costs about a second and reports the cause by name.

    Args:
        model_order: Model identifiers scheduled to run.
        kernel: Kernel whose config supplies the model block to probe.
        timeout_s: Ceiling for one probe.

    Returns:
        Mapping of model identifier to a JSON-serializable probe verdict with an
        ``ok`` key.
    """
    # Imported lazily: the suite must still run --dry-run on a machine without
    # the full lassi_x dependency set installed.
    from lassi_x.config import RunConfig  # noqa: PLC0415
    from lassi_x.model_doctor import distinct_models, probe_model  # noqa: PLC0415

    async def probe(model: str) -> dict[str, Any]:
        config = RunConfig.load(HERE / "configs" / model / f"{kernel}.yaml")
        reports = [
            await probe_model(entry, timeout_s=timeout_s)
            for entry in distinct_models(config.models)
        ]
        failed = next((report for report in reports if not report.ok), None)
        verdict = failed or reports[0]
        return {"ok": failed is None, **verdict.model_dump(mode="json")}

    return {model: asyncio.run(probe(model)) for model in model_order}


def _run_dir(envelope: dict[str, Any] | None) -> str | None:
    """Read the run artifact path out of a result envelope.

    Args:
        envelope: Envelope from :func:`_envelope`, or ``None``.

    Returns:
        Recorded run directory, or ``None`` when absent.
    """
    value = (envelope or {}).get("run_dir")
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
        doctor_code, _ = _run(
            [python, "-m", "lassi_x.cli", "execution", "doctor", "--config", str(first_config)],
            doctor_log,
            args.run_timeout_s,
        )
        _append(journal, {"event": "doctor", "exit_code": doctor_code, "log": str(doctor_log)})
        if doctor_code:
            print(f"Execution doctor failed; see {doctor_log}", file=sys.stderr)
            return doctor_code

    # The execution doctor above covers the one shared resource topology, but each
    # model has its own endpoint and identifier. Probe them all before launching a
    # block of kernels at a model that cannot answer.
    blocked: dict[str, dict[str, Any]] = {}
    if not args.skip_model_preflight and not args.dry_run:
        verdicts = _preflight_models(model_order, kernel_order[0], args.run_timeout_s)
        for model, verdict in verdicts.items():
            _append(journal, {"event": "model_preflight", "model": model, **verdict})
            state = "OK" if verdict["ok"] else "FAIL"
            print(f"PREFLIGHT {state} {model} ({verdict['model']})", flush=True)
            if not verdict["ok"]:
                blocked[model] = verdict
                print(
                    f"  {verdict['reason']}: {verdict['detail']}\n  hint: {verdict['hint']}",
                    file=sys.stderr,
                )
        if len(blocked) == len(model_order):
            print("Every model failed preflight; nothing was launched.", file=sys.stderr)
            return 4
        model_order = [model for model in model_order if model not in blocked]

    failures = 0
    consecutive = 0
    last_signature = ""
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
                elapsed_from = time.monotonic()
                code, timed_out = _run(command, log_path, args.run_timeout_s)
                elapsed = time.monotonic() - elapsed_from
                envelope = _envelope(log_path)
                # A run that emitted a successful envelope and then stalled did
                # its work; only teardown hung. Keep the result, flag the hang.
                teardown_hang = timed_out and bool((envelope or {}).get("ok"))
                if teardown_hang:
                    code = 0
                error = "" if teardown_hang else _error(envelope)
                signature = "" if not code else _signature(error, timed_out)
                _append(
                    journal,
                    {
                        "event": "finish",
                        "model": model,
                        "kernel": kernel,
                        "repetition": repetition,
                        "exit_code": code,
                        "timed_out": timed_out,
                        "teardown_hang": teardown_hang,
                        "error": error,
                        "error_signature": signature,
                        "duration_s": round(elapsed, 1),
                        "finished_at": dt.datetime.now(dt.UTC).isoformat(),
                        "log": str(log_path),
                        "run_dir": _run_dir(envelope),
                    },
                )
                reason = ""
                if timed_out:
                    reason = (
                        "teardown hung after a successful run" if teardown_hang else "timed out"
                    )
                    print(
                        f"TIMEOUT {model} {kernel} after {args.run_timeout_s:.0f}s "
                        f"({reason}); see {log_path}",
                        file=sys.stderr,
                    )
                if not code:
                    # A success used to print nothing at all, so a passing cell was
                    # indistinguishable from a stalled one until the next RUN line
                    # appeared, and its cost was never shown.
                    print(
                        f"OK   {model} {kernel} in {elapsed:.0f}s"
                        + (" (teardown hung)" if teardown_hang else ""),
                        flush=True,
                    )
                    consecutive = 0
                    last_signature = ""
                    continue
                failures += 1
                # Name the cause on the console. Reading it out of each run
                # directory afterwards is what made these sessions expensive.
                print(
                    # A reaped run writes no envelope, so fall back to the reason
                    # it was reaped for rather than claiming nothing is known.
                    f"FAIL {model} {kernel}: "
                    f"{error or reason or 'no error recorded'}; see {log_path}",
                    file=sys.stderr,
                )
                if args.stop_on_failure:
                    return code
                consecutive = consecutive + 1 if signature == last_signature else 1
                last_signature = signature
                if args.max_consecutive_failures and consecutive >= args.max_consecutive_failures:
                    _append(
                        journal,
                        {
                            "event": "abort",
                            "reason": "consecutive_failures",
                            "error_signature": signature,
                            "count": consecutive,
                            "aborted_at": dt.datetime.now(dt.UTC).isoformat(),
                        },
                    )
                    print(
                        f"ABORT after {consecutive} consecutive failures with signature "
                        f"{signature!r}. The remaining cells would fail the same way; "
                        f"fix the cause and resume with --resume {journal}",
                        file=sys.stderr,
                    )
                    return code
    if blocked:
        # A skipped model is an incomplete matrix, so it must not exit zero.
        print(
            "Skipped by preflight: "
            + ", ".join(f"{model} ({verdict['reason']})" for model, verdict in blocked.items()),
            file=sys.stderr,
        )
    print(f"Journal: {journal}")
    return 1 if failures or blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
