"""Frozen, common-seed LARGE repair comparison; preflight must pass before model calls."""

from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from lassi_x.artifacts import write_json
from lassi_x.config import RunConfig
from lassi_x.dataset_specialization import read_profile, specialize_source
from lassi_x.execution.context import ExecutionContext
from lassi_x.interruptions import model_service_interrupted
from lassi_x.validation import build_oracle

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "runs/a100-terra-medium-20261010"
DEFAULT_OUTPUT = REPO / "runs/a100-large-repair-20261015"
SCIENCE = {
    "direct-dft": {"SIZE": 4096},
    "softened-nbody": {"SIZE": 2048},
    "lorenz-rk4": {"SIZE": 1024, "STEPS": 200},
    "poisson-cg": {"SIZE": 16384},
    "jpeg-dct": {"SIZE": 1024},
    "wavelet-compression": {"SIZE": 1024},
    "low-rank-compression": {"SIZE": 1024},
    "iir-filter-bank": {"SIZE": 16384},
    "mutual-information": {"N": 256},
}
POLICY = """
This is a scored LARGE port-and-repair experiment from a frozen, unverified seed.
Read the supplied reference and headers: those are the exact frozen workload.
Use LARGE, never silently reduce sizes, iterations, output coverage, or tolerances.
Repair input construction as well as execution if the size-only seed adaptation is incomplete.
Preserve FP64 C semantics. Do not read, embed, or precompute oracle outputs.
Previous unscored LARGE diagnostics exposed these implementation hazards:
Seidel: dense dependency matrices over grid cells need O(N^4) memory and are forbidden;
use bounded-memory dependency-preserving sweeps/wavefronts/tiles instead.
SYR2K: avoid giant broadcast/reduction intermediates; use contractions or bounded tiles.
Floyd-Warshall: fixed MINI-only stage counts are invalid; support the full configured N.
ADI/Durbin: avoid scalar-per-element CUDA launches and materialized unrolled graphs.
FP16 overflow and long-recurrence errors require substantive numerical interventions.
All models receive the same hints. There is no access to earlier repaired implementations.
Budget: one initial seed-adaptation turn plus two externally checked correction rounds;
compatibility and numerical repair each retain two correction rounds. All calls count.
Measurement has an 8192 MiB PyTorch CUDA allocator ceiling (not a Groq-fit certificate),
900-second worker timeout, 3 warmups, and 20 timed single invocations.
Plan memory before execution; do not allocate an operator proportional to N^4.
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(output: Path) -> None:
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite {output}")
    source = json.loads((SOURCE / "campaign.json").read_text())
    entries, inventory = [], {}
    # Interleave models within kernels, rather than finishing one model first.
    items = sorted(source["entries"], key=lambda e: e["name"].startswith("polybench-"))
    for item in items:
        name = item["name"]
        original = yaml.safe_load((SOURCE / item["config"]).read_text())
        reference = Path(original["kernel"]["reference"])
        header = reference.with_suffix(".h")
        if not header.exists():
            header = reference.parent / "common.h"
        mini, large = read_profile(header, "mini"), read_profile(header, "large")
        large.update(SCIENCE.get(name, {}))
        # Freeze every source/context file, including high precision dump headers.
        refdir = output / "references" / name
        refdir.mkdir(parents=True)
        replacements = {}
        for source_path in [reference, *map(Path, original["kernel"]["context"])]:
            target = refdir / source_path.name
            if target.exists() and target.read_bytes() != source_path.read_bytes():
                target = refdir / ("dump-" + source_path.name)
            target.write_bytes(source_path.read_bytes())
            replacements[str(source_path)] = str(target)
        for target in map(Path, replacements.values()):
            text = target.read_text()
            for src, dest in replacements.items():
                text = text.replace(f'"{src}"', f'"{Path(dest).name}"')
            target.write_text(text)
        if name in SCIENCE and header.name == "common.h":
            common = refdir / "common.h"
            common.write_text(
                common.read_text().replace("#define SIZE 256", f"#define SIZE {large['SIZE']}")
            )
        config = copy.deepcopy(original)
        config["kernel"]["name"] = name + "-large"
        config["kernel"]["reference"] = replacements[str(reference)]
        config["kernel"]["context"] = [replacements[str(p)] for p in original["kernel"]["context"]]
        config["kernel"]["validation_dataset"] = "large"
        config["kernel"]["task"] = (
            original["kernel"]["task"].replace("MINI_DATASET", "LARGE_DATASET")
            + "\n"
            + POLICY
            + "\nFrozen dimensions: "
            + json.dumps(large)
        )
        config["oracle"]["build"] = [
            "-DLARGE_DATASET"
            if value == "-DMINI_DATASET"
            else "-O2"
            if value == "-O0"
            else replacements.get(value, value)
            for value in config["oracle"]["build"]
        ]
        config["oracle"]["timeout_s"] = 3600
        config["arena"].update(correction_rounds=2, timeout_s=900)
        config["scheduler"].update(max_candidate_flows=1, max_model_sessions=1)
        config["measure"].update(evaluation_dataset="large", warmup=3, iterations=20)
        for backend in config["measure"]["backends"]:
            backend.update(timeout_s=900, cuda_memory_limit_mb=8192)
        config["compensation"].update(enabled=True, repair_catastrophic=True)
        config.setdefault("compatibility", {}).update(
            enabled=True, correction_rounds=2, repair_statuses=["crashed", "no_fit", "timeout"]
        )
        config.setdefault("screening", {})["enabled"] = True
        baseline = Path(item["baseline"])
        baseline_manifest = json.loads((baseline / "manifest.json").read_text())
        seeds, provenance = [], []
        for index, candidate in enumerate(baseline_manifest["candidates"], 1):
            src = baseline / candidate["module_path"]
            if digest(src) != baseline_manifest["files"][candidate["module_path"]]:
                raise ValueError(f"Baseline checksum mismatch: {src}")
            seed = output / "seeds" / name / f"c{index}.py"
            seed.parent.mkdir(parents=True, exist_ok=True)
            try:
                text, changes = specialize_source(src.read_text(), name, mini, large)
                error = None
            except (ValueError, SyntaxError) as exc:
                # A failed size-only adapter is not silently dropped or passed.
                text, changes, error = src.read_text(), [], str(exc)
            compile(text, str(seed), "exec")
            seed.write_text(text)
            seeds.append(str(seed))
            provenance.append(
                {
                    "source": str(src),
                    "source_sha256": digest(src),
                    "seed": str(seed),
                    "seed_sha256": digest(seed),
                    "changes": changes,
                    "specialization_error": error,
                    "target_verified": False,
                }
            )
        if not seeds:
            raise ValueError(f"No common CPU-verified candidates for {name}")
        config["arena"].update(candidates=len(seeds), seed_sources=seeds)
        write_json(output / "seeds" / name / "provenance.json", {"candidates": provenance})
        for model in ("luna", "terra", "sol"):
            cfg = copy.deepcopy(config)
            model_set = yaml.safe_load(
                (REPO / f"examples/cpu-ablation-suite/models/{model}.yaml").read_text()
            )["models"]
            cfg["models"] = {**model_set, "compatibility": model_set["planner"]}
            cfg["models"]["candidates"] = model_set["candidates"][: len(seeds)]
            for resource in cfg["execution"]["resources"].values():
                resource["workspace_root"] += f"/{output.name}/{model}/{name}"
            cfg["runs_dir"] = str(output / model / "runs" / name)
            path = output / model / "configs" / f"{name}.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.safe_dump(cfg, sort_keys=False))
            RunConfig.load(path)
            entries.append(
                {
                    "name": name,
                    "model": model,
                    "config": str(path),
                    "dimensions": large,
                    "seeds": provenance,
                }
            )
        for path in [*refdir.iterdir(), *(Path(s) for s in seeds)]:
            inventory[str(path)] = digest(path)
    for entry in entries:
        inventory[entry["config"]] = digest(Path(entry["config"]))
    write_json(
        output / "campaign.json",
        {
            "schema_version": 1,
            "dataset": "large",
            "created_at": datetime.now(UTC).isoformat(),
            "models": ["luna", "terra", "sol"],
            "scientific_profiles": SCIENCE,
            "policy": POLICY,
            "entries": entries,
            "inventory": inventory,
        },
    )


async def preflight(output: Path, plan: dict) -> dict:
    report = {"status": "running", "references": [], "handshakes": {}}
    path = output / "preflight.json"
    if path.exists():
        report = json.loads(path.read_text())
    cached = {item["name"]: item for item in report["references"]}
    write_json(path, report)
    seen = set()
    for entry in plan["entries"]:
        if entry["name"] in seen:
            continue
        seen.add(entry["name"])
        config = RunConfig.load(Path(entry["config"]))
        run_dir = output / "preflight" / entry["name"]
        if entry["name"] in cached:
            oracle_path = run_dir / "oracle" / config.oracle.output
            if digest(oracle_path) != cached[entry["name"]]["sha256"]:
                raise ValueError(f"Cached preflight oracle changed: {oracle_path}")
            continue
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"Preflight C oracle {entry['name']}", flush=True)
        oracle = await build_oracle(config, run_dir)
        report["references"].append(
            {
                "name": entry["name"],
                "numel": int(oracle.values.size),
                "sha256": oracle.output_sha256,
                "determinism_runs": oracle.determinism_runs,
            }
        )
        write_json(path, report)
    # Fresh A100-only handshake: do not route through the Groq/Cerebras endpoint.
    config = RunConfig.load(Path(plan["entries"][0]["config"]))
    async with await ExecutionContext.start(config, output / "preflight-endpoint") as ctx:
        reports = await asyncio.wait_for(ctx.handshakes(), 120)
        report["handshakes"] = {
            name: value.model_dump(mode="json") for name, value in reports.items()
        }
        if not any(a.kind == "cuda" for h in reports.values() for a in h.accelerators):
            raise RuntimeError("A100 preflight found no CUDA accelerator")
    report["status"] = "passed"
    write_json(path, report)
    return report


def execute(output: Path) -> int:
    plan = json.loads((output / "campaign.json").read_text())
    state = {
        "pid": os.getpid(),
        "status": "preflight",
        "started_at": datetime.now(UTC).isoformat(),
        "total": len(plan["entries"]),
        "completed": [],
    }
    status = output / "status.json"
    write_json(status, state)
    try:
        for path, expected in plan["inventory"].items():
            if digest(Path(path)) != expected:
                raise ValueError(f"Frozen input changed: {path}")
        asyncio.run(preflight(output, plan))
        state["status"] = "running"
        write_json(status, state)
        for entry in plan["entries"]:
            state["current"] = {k: entry[k] for k in ("model", "name", "config")}
            write_json(status, state)
            print(f"Starting {entry['model']} {entry['name']}", flush=True)
            result = subprocess.run(
                [str(REPO / ".venv/bin/lassi-x"), "--log-level", "INFO", "run", entry["config"]],
                cwd=REPO,
                check=False,
            )
            records = sorted((output / entry["model"] / "runs" / entry["name"]).glob("*/run.json"))
            record = json.loads(records[-1].read_text()) if records else {}
            # Infrastructure/model service interruptions are not scored scientific failures.
            text = json.dumps(record).lower()
            infrastructure = any(
                word in text
                for word in (
                    "quota",
                    "insufficient_quota",
                    "rate_limit_exceeded",
                    "resourceunavailableerror",
                    "forbiddenerror",
                )
            )
            crashed_turn = any(
                not turn.get("completed", True)
                for field in ("candidates", "compatibility_candidates", "compensation_variants")
                for candidate in record.get(field, [])
                for turn in candidate.get("turn_outcomes", [])
            )
            if (
                record.get("error")
                or infrastructure
                or crashed_turn
                or not record
                or model_service_interrupted(record)
            ):
                raise RuntimeError(
                    f"Interrupted {entry['model']} {entry['name']}; "
                    f"saved at {records[-1] if records else 'no record'}; inspect before resume"
                )
            state["completed"].append(
                {
                    **state["current"],
                    "returncode": result.returncode,
                    "status": record.get("status"),
                    "run": str(records[-1]),
                }
            )
            write_json(status, state)
        state.update(status="finished", current=None, finished_at=datetime.now(UTC).isoformat())
        write_json(status, state)
        return 0
    except Exception as exc:
        state.update(status="interrupted", error=f"{type(exc).__name__}: {exc}")
        write_json(status, state)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--launch-prepared", action="store_true")
    parser.add_argument("--resume-preflight", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.execute:
        return execute(output)
    if args.resume_preflight:
        state = json.loads((output / "status.json").read_text())
        if state["status"] != "interrupted" or state["completed"]:
            raise ValueError("Only an interrupted, unscored preflight can be resumed here")
    elif not args.launch_prepared:
        prepare(output)
    elif not (output / "campaign.json").is_file() or (output / "status.json").exists():
        raise ValueError("Expected a prepared campaign that has not been launched")
    if args.detach:
        with (output / "launcher.log").open("a" if args.resume_preflight else "x") as log:
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--output",
                    str(output),
                    "--execute",
                ],
                cwd=REPO,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        print(f"Preflight-gated campaign PID {process.pid}; status {output / 'status.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
