"""Serial Terra/Luna/GPT-OSS rerun of the five explicitly promoted kernels.

Fresh CPU translations -> strict MINI GPU compatibility -> frozen LARGE evaluation.
Only model-based compatibility edits are allowed; numerical repair is not part of this rerun.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml
from dotenv import dotenv_values

from lassi_x.artifacts import write_json
from lassi_x.config import RunConfig
from lassi_x.dataset_specialization import read_profile, specialize_source
from lassi_x.interruptions import model_service_interrupted
from lassi_x.pipeline import _baseline_contract

REPO = Path(__file__).resolve().parents[2]
OUTPUT = REPO / "runs/three-model-strict-rerun-20261016"
OLD = REPO / "runs/a100-terra-medium-20261010"
FROZEN = REPO / "runs/a100-clean-gpu-repairs-20261016"
DERICHE = REPO / "runs/terra-deriche-strict-rerun-20261016"
MODELS = ("terra", "luna", "oss")
KERNELS = (
    "polybench-deriche",
    "polybench-correlation",
    "polybench-adi",
    "direct-dft",
    "polybench-durbin",
)


def prepare() -> None:
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    entries = []
    for model in MODELS:
        filename = "gpt-oss-120b-openrouter.yaml" if model == "oss" else f"{model}.yaml"
        models = yaml.safe_load(
            (REPO / "experiments/cpu-generation/models" / filename).read_text()
        )["models"]
        for kernel in KERNELS:
            root = OUTPUT / model / kernel
            base = yaml.safe_load((OLD / "configs" / f"{kernel}.yaml").read_text())
            base["models"] = {**models, "compatibility": models["planner"]}
            base["arena"]["candidates"] = 3
            base["scheduler"] = {"max_candidate_flows": 1, "max_model_sessions": 1}
            base["compensation"] = {"enabled": False, "arithmetic_policy": "target_format_only"}
            base["kernel"]["task"] += (
                " This source will be evaluated separately at FP64, FP32, FP16 and BF16. "
                "Each forward must honor its requested tensor arithmetic format. "
                "Failure in a format is acceptable: never replace it with FP32/FP64 "
                "or cast a wider answer back. Precomputed constants may be cast before use, "
                "and unused wider buffers are allowed. No earlier translations or repairs "
                "are provided as seeds. Preserve the full workload."
            )
            if model == "terra" and kernel == "polybench-deriche":
                # Reused CPU exports bind the original prompt as well as the workload.
                base["kernel"]["task"] = yaml.safe_load((DERICHE / "configs/cpu.yaml").read_text())[
                    "kernel"
                ]["task"]
            cpu = copy.deepcopy(base)
            cpu["execution"] = {"mode": "local"}
            cpu["compatibility"] = {"enabled": False}
            cpu["screening"] = {"enabled": False}
            cpu["measure"]["backends"] = [
                {
                    "type": "torch",
                    "name": "cpu",
                    "device": "cpu",
                    "precisions": ["fp64", "fp32", "fp16", "bf16"],
                    "precision_audit": "enforce",
                }
            ]
            cpu["success"] = {"required_backends": [], "required_precisions": {}}
            cpu["runs_dir"] = str(root / "cpu/runs" / kernel)
            gpu = copy.deepcopy(base)
            gpu["execution"].update(call_timeout_s=120, pause_max_s=120)
            gpu["execution"]["resources"]["a100"]["workspace_root"] = (
                f"/home/gbrun/lassi-x-work/three-model-strict-rerun-20261016/{model}/{kernel}/mini"
            )
            gpu["compatibility"] = {"enabled": True, "correction_rounds": 2}
            gpu["screening"] = {"enabled": False}
            gpu["measure"]["backends"][0].update(
                precision_audit="enforce", timeout_s=900, cuda_memory_limit_mb=8192
            )
            gpu["runs_dir"] = str(root / "gpu/runs" / kernel)
            configs = {}
            for stage, config in (("cpu", cpu), ("gpu", gpu)):
                RunConfig.model_validate(config)
                path = root / "configs" / f"{stage}.yaml"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(yaml.safe_dump(config, sort_keys=False))
                configs[stage] = str(path)
            entries.append(
                {
                    "model": model,
                    "kernel": kernel,
                    "root": str(root),
                    "configs": configs,
                    "reuse_cpu_root": str(DERICHE / "cpu/runs/polybench-deriche")
                    if model == "terra" and kernel == "polybench-deriche"
                    else None,
                }
            )
    write_json(
        OUTPUT / "campaign.json",
        {
            "created_at": datetime.now(UTC).isoformat(),
            "models": list(MODELS),
            "reasoning_effort": "medium",
            "kernels": list(KERNELS),
            "entries": entries,
            "policy": "executed-dtype-v3",
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "datasets": ["mini", "frozen_large"],
            "new_cpu_generations": 14,
            "reused_in_progress_cpu_generations": 1,
            "numerical_repair": False,
            "comparison": "Fresh translations per model; identical C workloads and gates",
        },
    )


def latest(folder: Path) -> Path | None:
    paths = sorted(folder.glob("*/run.json"))
    return paths[-1] if paths else None


def large_config(entry: dict) -> tuple[dict, dict]:
    """Validate the entire next-stage config before writing or launching anything."""
    kernel, model = entry["kernel"], entry["model"]
    root = Path(entry["root"]) / "large"
    plan = json.loads((FROZEN / "campaign.json").read_text())
    template = next(e for e in plan["entries"] if e["name"] == kernel)
    config = yaml.safe_load(Path(template["config"]).read_text())
    mini_config = yaml.safe_load(Path(entry["configs"]["gpu"]).read_text())
    config["models"] = mini_config["models"]
    config["arena"]["candidates"] = len(config["models"]["candidates"])
    config["compensation"] = {"enabled": False, "arithmetic_policy": "target_format_only"}
    config["compatibility"] = {"enabled": False}
    config["screening"] = {"enabled": False}
    config["runs_dir"] = str(root / "unused-model-runs")
    config["execution"]["resources"]["a100"]["workspace_root"] = (
        f"/home/gbrun/lassi-x-work/three-model-strict-rerun-20261016/{model}/{kernel}/large"
    )
    config["measure"]["backends"][0]["precision_audit"] = "enforce"
    RunConfig.model_validate(config)
    for filename, expected in template["references"].items():
        if hashlib.sha256(Path(filename).read_bytes()).hexdigest() != expected:
            raise RuntimeError(f"Frozen LARGE reference changed: {filename}")
    return config, template


def large_plan(entry: dict, gpu_path: Path) -> Path:
    kernel = entry["kernel"]
    root = Path(entry["root"]) / "large"
    config, template = large_config(entry)
    if (root / "campaign.json").exists():
        # A resumed evaluator owns these immutable seeds and completed measurements.
        saved = json.loads((root / "campaign.json").read_text())
        if RunConfig.load(Path(saved["entries"][0]["config"])) != RunConfig.model_validate(config):
            raise RuntimeError(f"Existing LARGE configuration changed: {kernel}")
        for cell in saved["entries"][0]["cells"]:
            if hashlib.sha256(Path(cell["module"]).read_bytes()).hexdigest() != cell["sha256"]:
                raise RuntimeError(f"Existing LARGE seed changed: {cell['module']}")
            if (
                hashlib.sha256(Path(cell["source"]).read_bytes()).hexdigest()
                != cell["source_sha256"]
            ):
                raise RuntimeError(f"Existing MINI source changed: {cell['source']}")
        return root / "campaign.json"
    mini_config = yaml.safe_load(Path(entry["configs"]["gpu"]).read_text())
    path = root / "configs" / f"{kernel}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False))
    RunConfig.load(path)
    reference = Path(mini_config["kernel"]["reference"])
    header = reference.with_suffix(".h")
    if not header.exists():
        header = reference.parent / "common.h"
    mini = read_profile(header, "mini")
    # Frozen specialized seed inventory records the approved non-PolyBench profiles.
    inventory = json.loads(
        (REPO / "runs/a100-large-clean-restart-20261015/baseline-inventory.json").read_text()
    )
    target = next(e["frozen_dimensions"] for e in inventory["entries"] if e["kernel"] == kernel)
    record = json.loads(gpu_path.read_text())
    cells = []
    for base in record["candidates"]:
        if base["status"] != "ok":
            continue
        for precision in ("fp16", "bf16"):
            cid = base["candidate_id"]
            ports = [
                c
                for c in record.get("compatibility_candidates", [])
                if c.get("parent_candidate_id") == cid
                and c["status"] == "ok"
                and c.get("target_precision") == precision
            ]
            source = Path((ports[-1] if ports else base)["module_path"])
            module = root / "seeds" / kernel / f"{cid}-{precision}.py"
            module.parent.mkdir(parents=True, exist_ok=True)
            try:
                text, changes = specialize_source(source.read_text(), kernel, mini, target)
                error = None
            except (ValueError, SyntaxError) as exc:
                text, changes, error = source.read_text(), [], str(exc)
            module.write_text(text)
            cells.append(
                {
                    "candidate_id": cid,
                    "precision": precision,
                    "module": str(module),
                    "source": str(source),
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "sha256": hashlib.sha256(module.read_bytes()).hexdigest(),
                    "changes": changes,
                    "specialization_error": error,
                }
            )
    path = root / "campaign.json"
    write_json(
        path,
        {
            "models": [],
            "dataset": "large",
            "policy": "executed-dtype-v3",
            "entries": [
                {
                    "name": kernel,
                    "config": str(root / "configs" / f"{kernel}.yaml"),
                    "cells": cells,
                    "references": template["references"],
                }
            ],
        },
    )
    return path


def gpu_resume_state(plan: dict) -> dict:
    """Reuse CPU work and finalized MINI stages; reject ambiguous partial GPU work."""
    state = json.loads((OUTPUT / "status.json").read_text())
    import_failed = (
        state["status"] == "interrupted"
        and state.get("phase") == "mini_gpu_compatibility"
        and state.get("error", "").startswith(
            "RuntimeError: GPU invocation produced no terminal record: "
        )
    )
    large_interrupted = (
        state["status"] == "interrupted" and state.get("phase") == "large_evaluation_only"
    )
    if state["status"] != "gpu_blocked" and not import_failed and not large_interrupted:
        raise RuntimeError("GPU-only restart requires the untouched GPU preflight checkpoint")
    for entry in plan["entries"]:
        name = f"{entry['model']}/{entry['kernel']}"
        path = Path(state["cpu_runs"][name])
        record = json.loads(path.read_text())
        if record["status"] not in {"cpu_verified", "failed"} or record.get("error"):
            raise RuntimeError(f"CPU result is not terminal: {path}")
        if model_service_interrupted(record):
            raise RuntimeError(f"CPU result contains a service interruption: {path}")
        saved_gpu = state.get("gpu_runs", {}).get(name)
        gpu_dir = Path(saved_gpu).parent.resolve() if saved_gpu else None
        if saved_gpu:
            gpu_record = json.loads(Path(saved_gpu).read_text())
            if (
                gpu_record.get("error")
                or model_service_interrupted(gpu_record)
                or "finalize" not in gpu_record.get("checkpoint", {}).get("completed_stages", [])
            ):
                raise RuntimeError(f"Existing GPU work requires stage-specific recovery: {name}")
            provenance = json.loads((gpu_dir / "cpu-baseline-provenance.json").read_text())
            manifest_path = path.parent / "cpu-baseline/manifest.json"
            if (
                hashlib.sha256(manifest_path.read_bytes()).hexdigest()
                != provenance["manifest_sha256"]
            ):
                raise RuntimeError(f"GPU baseline provenance mismatch: {name}")
        for artifact in (Path(entry["root"]) / "gpu/runs").rglob("*"):
            if (
                artifact.is_file()
                and artifact.name != "resolved-config.yaml"
                and (gpu_dir is None or not artifact.resolve().is_relative_to(gpu_dir))
            ):
                raise RuntimeError(f"Existing GPU work requires stage-specific recovery: {name}")
        if record["status"] == "cpu_verified" and not (path.parent / "cpu-baseline").is_dir():
            raise RuntimeError(f"Missing exported CPU baseline: {path}")
        if record["status"] == "cpu_verified":
            baseline = path.parent / "cpu-baseline"
            manifest = json.loads((baseline / "manifest.json").read_text())
            config = RunConfig.load(Path(entry["configs"]["gpu"]))
            if manifest["contract"] != _baseline_contract(config):
                raise RuntimeError(f"CPU/GPU baseline contract mismatch: {name}")
            for filename, expected in manifest["files"].items():
                if Path(filename).name != filename:
                    raise RuntimeError(f"Unsafe CPU baseline filename: {filename}")
                if hashlib.sha256((baseline / filename).read_bytes()).hexdigest() != expected:
                    raise RuntimeError(f"CPU baseline checksum mismatch: {baseline / filename}")
            large_config(entry)
    return state


def run(*, resume_gpu: bool = False) -> int:
    plan = json.loads((OUTPUT / "campaign.json").read_text())
    state = {
        "pid": os.getpid(),
        "status": "running",
        "phase": "cpu_translations",
        "completed": [],
        "started_at": datetime.now(UTC).isoformat(),
        "cpu_runs": {},
        "gpu_runs": {},
    }

    if resume_gpu:
        state = gpu_resume_state(plan)
        state.update(pid=os.getpid(), status="running", error=None)
        state["gpu_resumed_at"] = datetime.now(UTC).isoformat()

    def update(**values):
        state.update(values)
        write_json(OUTPUT / "status.json", state)

    def command(argv: list[str], *, timeout=None) -> int:
        print(subprocess.list2cmdline(argv), flush=True)
        return subprocess.run(argv, cwd=REPO, timeout=timeout, check=False).returncode

    def inspect(path: Path) -> dict:
        record = json.loads(path.read_text())
        if model_service_interrupted(record):
            raise RuntimeError(f"Model service interruption; queue stopped at {path}")
        return record

    # The same OpenRouter/Groq route and existing credential as the original OSS run.
    key = os.environ.get("OPENROUTER_API_KEY") or dotenv_values(Path.home() / ".hermes/.env").get(
        "OPENROUTER_API_KEY"
    )
    if key:
        os.environ["OPENROUTER_API_KEY"] = key
    os.environ["PATH"] = str(REPO / ".venv/bin") + os.pathsep + os.environ.get("PATH", "")
    cli = str(REPO / ".venv/bin/lassi-x")
    try:
        for entry in plan["entries"]:
            if resume_gpu:
                continue
            name = f"{entry['model']}/{entry['kernel']}"
            update(current=name, phase="cpu_translations")
            if entry["reuse_cpu_root"]:
                update(phase="waiting_existing_terra_deriche_cpu")
                while (path := latest(Path(entry["reuse_cpu_root"]))) is None:
                    # This is a local background wait, not model/token monitoring.
                    handoff = json.loads((OUTPUT / "handoff.json").read_text())
                    try:
                        os.kill(handoff["cpu_pid"], 0)
                    except ProcessLookupError as exc:
                        raise RuntimeError(
                            "Existing Deriche CPU process stopped without a result"
                        ) from exc
                    time.sleep(600)
                record = inspect(path)
            else:
                if entry["model"] == "oss" and not key:
                    raise RuntimeError("OpenRouter credential unavailable; no OSS calls attempted")
                command([cli, "run", entry["configs"]["cpu"], "--until", "cpu-verified"])
                path = latest(Path(entry["root"]) / "cpu/runs" / entry["kernel"])
                if path is None:
                    raise RuntimeError(f"CPU invocation produced no terminal record: {name}")
                record = inspect(path)
            if record.get("error"):
                raise RuntimeError(f"CPU infrastructure/model error saved at {path}")
            state["cpu_runs"][name] = str(path)
            state["completed"].append({"case": name, "stage": "cpu", "status": record["status"]})
            update(phase="cpu_translations")
        # Do not burn model-based porting attempts while the execution endpoint is down.
        update(phase="gpu_preflight", current=None)
        if command(
            [cli, "execution", "doctor", "--config", plan["entries"][0]["configs"]["gpu"]],
            timeout=180,
        ):
            update(
                status="gpu_blocked",
                error="A100 execution preflight failed; all CPU results retained",
            )
            return 1
        for entry in plan["entries"]:
            name = f"{entry['model']}/{entry['kernel']}"
            cpu = Path(state["cpu_runs"][name])
            if json.loads(cpu.read_text())["status"] != "cpu_verified":
                state["completed"].append(
                    {"case": name, "stage": "gpu", "status": "no_valid_cpu_candidate"}
                )
                update()
                continue
            gpu = Path(state["gpu_runs"][name]) if name in state["gpu_runs"] else None
            if gpu is None:
                update(phase="mini_gpu_compatibility", current=name)
                command(
                    [
                        cli,
                        "run",
                        entry["configs"]["gpu"],
                        "--from-cpu-baseline",
                        str(cpu.parent / "cpu-baseline"),
                        "--allow-adaptations",
                    ]
                )
                gpu = latest(Path(entry["root"]) / "gpu/runs" / entry["kernel"])
            if gpu is None:
                raise RuntimeError(f"GPU invocation produced no terminal record: {name}")
            record = inspect(gpu)
            if record.get("error"):
                raise RuntimeError(f"GPU stage interrupted: {gpu}")
            state["gpu_runs"][name] = str(gpu)
            if not any(c["case"] == name and c["stage"] == "mini_gpu" for c in state["completed"]):
                state["completed"].append(
                    {"case": name, "stage": "mini_gpu", "status": record["status"]}
                )
            if any(c["case"] == name and c["stage"] == "large" for c in state["completed"]):
                continue
            update(phase="large_evaluation_only", current=name)
            large = large_plan(entry, gpu)
            code = command(
                [
                    str(REPO / ".venv/bin/python"),
                    str(REPO / "experiments/repair-campaigns/run_gpu_repair_comparison.py"),
                    "--output",
                    str(large.parent),
                    "--resume",
                    "--execute",
                    "--baseline-only",
                ]
            )
            if code:
                raise RuntimeError(
                    f"LARGE execution interrupted: {name}; all earlier results retained"
                )
            state["completed"].append({"case": name, "stage": "large", "status": "evaluated"})
            update()
        update(status="completed", current=None, finished_at=datetime.now(UTC).isoformat())
        return 0
    except Exception as exc:
        update(status="interrupted", error=f"{type(exc).__name__}: {exc}")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--resume-gpu", action="store_true", help="Reuse all terminal CPU results")
    parser.add_argument(
        "--check-ready", action="store_true", help="Offline preflight; no jobs or models"
    )
    args = parser.parse_args()
    if args.check_ready:
        plan = json.loads((OUTPUT / "campaign.json").read_text())
        state = gpu_resume_state(plan)
        for entry in plan["entries"]:
            large_config(entry)
        print(
            f"Ready: {len(state['cpu_runs'])} CPU results preserved; "
            f"{len(state['gpu_runs'])} completed MINI GPU stages reusable; "
            f"all {len(plan['entries'])} LARGE configurations valid."
        )
        return 0
    if args.prepare:
        prepare()
        return 0
    if args.detach:
        if (OUTPUT / "launcher.json").exists():
            if not args.resume_gpu:
                raise RuntimeError("Queue already launched; inspect its status before any resume")
            pid = json.loads((OUTPUT / "launcher.json").read_text())["pid"]
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError(f"Previous launcher PID {pid} is still alive")
            gpu_resume_state(json.loads((OUTPUT / "campaign.json").read_text()))
        with (OUTPUT / "launcher.log").open("a") as log:
            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    *(["--resume-gpu"] if args.resume_gpu else []),
                ],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        write_json(OUTPUT / "launcher.json", {"pid": proc.pid})
        print(f"Started serial three-model queue PID {proc.pid}")
        return 0
    return run(resume_gpu=args.resume_gpu)


if __name__ == "__main__":
    raise SystemExit(main())
