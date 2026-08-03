from __future__ import annotations

import argparse
import asyncio
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np

from . import __version__
from .artifacts import atomic_write, write_json
from .compensation import TECHNIQUE_SUMMARY
from .config import RunConfig
from .measurement import build_backends
from .pareto import frontier_indices
from .pipeline import run_pipeline
from .skills import (
    SKILL_NAMES,
    doctor_skills,
    install_skills,
    uninstall_skills,
)
from .types import Measurement, Status
from .validation import (
    build_oracle,
    compare_outputs,
    load_reference_output,
    validate_candidate,
)


def emit(tool: str, payload: dict[str, Any], *, json_output: bool = True) -> None:
    envelope = {
        "schema_version": 1,
        "tool": tool,
        "tool_version": __version__,
        **payload,
    }
    if json_output:
        print(json.dumps(envelope, indent=2, default=str))
    else:
        for key, value in envelope.items():
            print(f"{key}: {value}")


def _load_any(path: Path) -> np.ndarray:
    return load_reference_output(path)


def command_output(args: argparse.Namespace) -> int:
    if args.output_command == "summarize":
        values = _load_any(args.path)
        finite = np.isfinite(values)
        payload = {
            "ok": True,
            "path": str(args.path),
            "shape": list(values.shape),
            "count": int(values.size),
            "finite": bool(finite.all()),
            "nan_count": int(np.isnan(values).sum()),
            "inf_count": int(np.isinf(values).sum()),
            "min": float(values[finite].min()) if finite.any() else None,
            "max": float(values[finite].max()) if finite.any() else None,
            "mean": float(values[finite].mean()) if finite.any() else None,
            "std": float(values[finite].std()) if finite.any() else None,
            "l2_norm": float(np.linalg.norm(values[finite])) if finite.any() else None,
        }
        emit("output.summarize", payload, json_output=args.json)
        return 0
    reference = _load_any(args.reference)
    candidate = _load_any(args.candidate)
    ok, diagnostic, metrics = compare_outputs(
        candidate,
        reference,
        rtol=args.rtol,
        atol=args.atol,
        max_mismatches=args.max_mismatches,
    )
    emit(
        "output.compare",
        {
            "ok": ok,
            "metrics": metrics,
            "diagnostic": diagnostic.to_dict() if diagnostic else None,
        },
        json_output=args.json,
    )
    return 0 if ok else 1


def _run_capture(command: list[str]) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {"available": False}
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, check=False)
        return {
            "available": True,
            "exit_code": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-2000:],
        }
    except Exception as exc:
        return {"available": True, "error": f"{type(exc).__name__}: {exc}"}


def command_inspect(args: argparse.Namespace) -> int:
    if args.inspect_command == "machine":
        payload = {
            "ok": True,
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "memory_bytes": (
                os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
                if hasattr(os, "sysconf")
                else None
            ),
            "executables": {
                name: shutil.which(name)
                for name in ("gcc", "clang", "perf", "nvidia-smi", "rocm-smi")
            },
        }
        emit("inspect.machine", payload, json_output=args.json)
        return 0
    if args.inspect_command == "gpu":
        probes = {
            "nvidia": [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version",
                "--format=csv",
            ],
            "amd": ["rocm-smi", "--showproductname", "--showmeminfo", "vram"],
            "intel": ["xpu-smi", "discovery", "-j"],
        }
        results = {name: _run_capture(command) for name, command in probes.items()}
        available = any(result.get("available") for result in results.values())
        emit(
            "inspect.gpu",
            {"ok": available, "probes": results},
            json_output=args.json,
        )
        return 0 if available else 3
    packages: dict[str, str | None] = {}
    for package in ("lassi-x", "hermes-agent", "torch", "numpy", "pydantic"):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = None
    payload = {
        "ok": True,
        "python": sys.version,
        "packages": packages,
        "gcc": _run_capture(["gcc", "--version"]),
        "clang": _run_capture(["clang", "--version"]),
        "cuda": _run_capture(["nvcc", "--version"]),
    }
    emit("inspect.toolchain", payload, json_output=args.json)
    return 0


async def _validate_command(args: argparse.Namespace) -> int:
    config = RunConfig.load(args.config)
    artifact_dir = args.artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    oracle = await build_oracle(config, artifact_dir)
    result = await validate_candidate(config, args.module.resolve(), oracle, artifact_dir)
    emit(
        "validate.candidate",
        {
            "ok": result.ok,
            "oracle_kind": "c_reference_fp64",
            "oracle_path": str(oracle.output_path),
            "metrics": result.metrics,
            "diagnostic": result.diagnostic.to_dict() if result.diagnostic else None,
        },
        json_output=args.json,
    )
    return 0 if result.ok else 1


async def _benchmark_command(args: argparse.Namespace) -> int:
    config = RunConfig.load(args.config)
    with tempfile.TemporaryDirectory(prefix="lassi-x-bench-") as temporary:
        root = Path(temporary)
        oracle = await build_oracle(config, root)
        backend = next(
            (item for item in build_backends(config) if item.spec.name == args.backend),
            None,
        )
        if backend is None:
            emit(
                "benchmark.run",
                {"ok": False, "error": f"unknown backend {args.backend!r}"},
                json_output=args.json,
            )
            return 2
        result = await backend.measure(
            config,
            oracle,
            args.module.resolve(),
            candidate_id="manual",
            variant_id="manual",
            precision=args.precision,
            compensation=args.compensation,
        )
        emit(
            "benchmark.run",
            {"ok": result.status == Status.OK, "measurement": result.to_dict()},
            json_output=args.json,
        )
        return 0 if result.status == Status.OK else 1


def command_pareto(args: argparse.Namespace) -> int:
    points: list[Measurement] = []
    for line in args.measurements.read_text().splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        raw.pop("y_error", None)
        raw["status"] = Status(raw["status"])
        points.append(Measurement(**raw))
    frontier = [points[index].to_dict() for index in frontier_indices(points)]
    write_json(args.output, frontier)
    emit(
        "pareto.build",
        {"ok": bool(frontier), "output": str(args.output), "frontier": frontier},
        json_output=args.json,
    )
    return 0 if frontier else 1


def command_report(args: argparse.Namespace) -> int:
    record_path = args.run / "run.json"
    if not record_path.is_file():
        emit(
            "report.verification",
            {"ok": False, "error": f"missing {record_path}"},
            json_output=args.json,
        )
        return 2
    record = json.loads(record_path.read_text())
    payload = {
        "ok": record.get("status") == "ok",
        "status": record.get("status"),
        "oracle": record.get("oracle"),
        "candidates": record.get("candidates", []),
        "compensation_variants": record.get("compensation_variants", []),
        "frontier": record.get("frontier", []),
    }
    emit("report.verification", payload, json_output=args.json)
    return 0 if payload["ok"] else 1


def command_skills(args: argparse.Namespace) -> int:
    home = args.hermes_home
    if args.skills_command == "install":
        payload = install_skills(home, sync=False)
    elif args.skills_command == "sync":
        payload = install_skills(home, sync=True)
    elif args.skills_command == "doctor":
        payload = doctor_skills(home)
    elif args.skills_command == "uninstall":
        payload = uninstall_skills(home)
    else:
        payload = {"ok": True, "skills": list(SKILL_NAMES)}
    emit(f"skills.{args.skills_command}", payload, json_output=args.json)
    return 0 if payload.get("ok") else 1


def _groq_claim(queue: Path) -> Path | None:
    pending = queue / "pending"
    running = queue / "running"
    completed = queue / "completed"
    for directory in (pending, running, completed):
        directory.mkdir(parents=True, exist_ok=True)
    for request in sorted(pending.glob("*.json")):
        claimed = running / request.name
        try:
            os.replace(request, claimed)
            return claimed
        except FileNotFoundError:
            continue
    return None


def _groq_execute(request_path: Path, queue: Path, executor: list[str]) -> None:
    request = json.loads(request_path.read_text())
    result_path = queue / "completed" / request_path.name
    values = {key: str(value) for key, value in request.items()}
    payload: dict[str, Any]
    try:
        if not executor:
            raise RuntimeError("Groq worker requires an executor command")
        command = [part.format_map(values) for part in executor]
        result = subprocess.run(command, capture_output=True, text=True, timeout=None, check=False)
        if result.returncode:
            payload = {
                "status": "crashed",
                "notes": (result.stderr or result.stdout)[-4000:],
            }
        else:
            payload = json.loads(result.stdout.strip().splitlines()[-1])
            payload.setdefault("status", "ok")
    except Exception as exc:
        payload = {"status": "crashed", "notes": f"{type(exc).__name__}: {exc}"}
    payload.update({"schema_version": 1, "request_id": request["request_id"]})
    atomic_write(result_path, json.dumps(payload, indent=2) + "\n")
    request_path.unlink(missing_ok=True)


def _groq_heartbeat(queue: Path, stop: threading.Event, interval_s: float) -> None:
    """Publish worker liveness until the owning command exits.

    Args:
        queue: Root directory of the filesystem queue.
        stop: Event set by the worker's shutdown path.
        interval_s: Maximum delay between heartbeat updates.

    """
    heartbeat = queue / "worker-heartbeat.json"
    while not stop.is_set():
        atomic_write(
            heartbeat,
            json.dumps(
                {
                    "schema_version": 1,
                    "pid": os.getpid(),
                    "updated_at": time.time(),
                },
                indent=2,
            )
            + "\n",
        )
        stop.wait(interval_s)


def command_groq(args: argparse.Namespace) -> int:
    queue = args.queue_dir.resolve()
    if args.groq_command == "submit":
        request = json.loads(args.request.read_text())
        request.setdefault("request_id", uuid.uuid4().hex)
        request.setdefault("schema_version", 1)
        destination = queue / "pending" / f"{request['request_id']}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(destination, json.dumps(request, indent=2) + "\n")
        emit("groq.submit", {"ok": True, "request": str(destination)}, json_output=args.json)
        return 0
    if args.groq_command == "status":
        states = {}
        for state in ("pending", "running", "completed"):
            path = queue / state / f"{args.request_id}.json"
            if path.is_file():
                states = {"state": state, "path": str(path)}
                if state == "completed":
                    states["result"] = json.loads(path.read_text())
                break
        emit("groq.status", {"ok": bool(states), **states}, json_output=args.json)
        return 0 if states else 1
    heartbeat_stop = threading.Event()
    heartbeat = threading.Thread(
        target=_groq_heartbeat,
        args=(queue, heartbeat_stop, max(0.1, min(float(args.poll_s), 1.0))),
        daemon=True,
    )
    heartbeat.start()
    try:
        while True:
            claimed = _groq_claim(queue)
            if claimed is None:
                if args.once:
                    break
                time.sleep(args.poll_s)
                continue
            _groq_execute(claimed, queue, args.executor)
            if args.once:
                break
    finally:
        heartbeat_stop.set()
        heartbeat.join(timeout=2)
        heartbeat_path = queue / "worker-heartbeat.json"
        try:
            heartbeat_record = json.loads(heartbeat_path.read_text())
            if int(heartbeat_record.get("pid", -1)) == os.getpid():
                heartbeat_path.unlink(missing_ok=True)
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
    emit("groq.worker", {"ok": True, "queue_dir": str(queue)}, json_output=args.json)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lassi-x")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("config", type=Path)

    skills = sub.add_parser("skills")
    skills_sub = skills.add_subparsers(dest="skills_command", required=True)
    for name in ("install", "sync", "list", "doctor", "uninstall"):
        item = skills_sub.add_parser(name)
        item.add_argument("--hermes-home", type=Path)
        item.add_argument("--json", action="store_true", default=True)

    output = sub.add_parser("output")
    output_sub = output.add_subparsers(dest="output_command", required=True)
    summarize = output_sub.add_parser("summarize")
    summarize.add_argument("--path", type=Path, required=True)
    summarize.add_argument("--json", action="store_true", default=True)
    compare = output_sub.add_parser("compare")
    compare.add_argument("--reference", type=Path, required=True)
    compare.add_argument("--candidate", type=Path, required=True)
    compare.add_argument("--rtol", type=float, default=1e-3)
    compare.add_argument("--atol", type=float, default=1e-6)
    compare.add_argument("--max-mismatches", type=int, default=20)
    compare.add_argument("--json", action="store_true", default=True)

    inspect = sub.add_parser("inspect")
    inspect_sub = inspect.add_subparsers(dest="inspect_command", required=True)
    for name in ("machine", "gpu", "toolchain"):
        item = inspect_sub.add_parser(name)
        item.add_argument("--json", action="store_true", default=True)

    validate = sub.add_parser("validate")
    validate_sub = validate.add_subparsers(dest="validate_command", required=True)
    candidate = validate_sub.add_parser("candidate")
    candidate.add_argument("--config", type=Path, required=True)
    candidate.add_argument("--module", type=Path, required=True)
    candidate.add_argument("--artifact-dir", type=Path, required=True)
    candidate.add_argument("--json", action="store_true", default=True)

    benchmark = sub.add_parser("benchmark")
    benchmark_sub = benchmark.add_subparsers(dest="benchmark_command", required=True)
    bench_run = benchmark_sub.add_parser("run")
    bench_run.add_argument("--config", type=Path, required=True)
    bench_run.add_argument("--module", type=Path, required=True)
    bench_run.add_argument("--backend", required=True)
    bench_run.add_argument("--precision", choices=["fp64", "fp32", "fp16", "bf16"], required=True)
    bench_run.add_argument("--compensation", default="none")
    bench_run.add_argument("--json", action="store_true", default=True)

    precision = sub.add_parser("precision")
    precision_sub = precision.add_subparsers(dest="precision_command", required=True)
    precision_measure = precision_sub.add_parser("measure")
    precision_measure.add_argument("--config", type=Path, required=True)
    precision_measure.add_argument("--module", type=Path, required=True)
    precision_measure.add_argument("--backend", required=True)
    precision_measure.add_argument("--precision", choices=["fp16", "bf16"], required=True)
    precision_measure.add_argument("--compensation", default="none")
    precision_measure.add_argument("--json", action="store_true", default=True)
    precision_methods = precision_sub.add_parser("methods")
    precision_methods.add_argument("--json", action="store_true", default=True)

    pareto = sub.add_parser("pareto")
    pareto_sub = pareto.add_subparsers(dest="pareto_command", required=True)
    pareto_build = pareto_sub.add_parser("build")
    pareto_build.add_argument("--measurements", type=Path, required=True)
    pareto_build.add_argument("--output", type=Path, required=True)
    pareto_build.add_argument("--json", action="store_true", default=True)

    report = sub.add_parser("report")
    report_sub = report.add_subparsers(dest="report_command", required=True)
    verification = report_sub.add_parser("verification")
    verification.add_argument("--run", type=Path, required=True)
    verification.add_argument("--json", action="store_true", default=True)

    groq = sub.add_parser("groq")
    groq_sub = groq.add_subparsers(dest="groq_command", required=True)
    submit = groq_sub.add_parser("submit")
    submit.add_argument("--queue-dir", type=Path, required=True)
    submit.add_argument("--request", type=Path, required=True)
    submit.add_argument("--json", action="store_true", default=True)
    status = groq_sub.add_parser("status")
    status.add_argument("--queue-dir", type=Path, required=True)
    status.add_argument("--request-id", required=True)
    status.add_argument("--json", action="store_true", default=True)
    worker = groq_sub.add_parser("worker")
    worker.add_argument("--queue-dir", type=Path, required=True)
    worker.add_argument("--poll-s", type=float, default=0.5)
    worker.add_argument("--once", action="store_true")
    worker.add_argument("--executor", nargs=argparse.REMAINDER, default=[])
    worker.add_argument("--json", action="store_true", default=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "run":
        try:
            code, run_dir = asyncio.run(run_pipeline(args.config))
        except Exception as exc:
            emit(
                "run",
                {
                    "ok": False,
                    "error": type(exc).__name__,
                    "message": str(exc),
                },
            )
            return 3
        emit("run", {"ok": code == 0, "run_dir": str(run_dir)})
        return code
    if args.command == "skills":
        return command_skills(args)
    if args.command == "output":
        return command_output(args)
    if args.command == "inspect":
        return command_inspect(args)
    if args.command == "validate":
        return asyncio.run(_validate_command(args))
    if args.command == "benchmark":
        return asyncio.run(_benchmark_command(args))
    if args.command == "precision":
        if args.precision_command == "methods":
            emit(
                "precision.methods",
                {"ok": True, "techniques": TECHNIQUE_SUMMARY},
                json_output=args.json,
            )
            return 0
        return asyncio.run(_benchmark_command(args))
    if args.command == "pareto":
        return command_pareto(args)
    if args.command == "report":
        return command_report(args)
    if args.command == "groq":
        return command_groq(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
