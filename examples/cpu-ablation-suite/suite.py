"""Prepare reproducible CPU-only benchmark campaigns; no model calls by default."""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

import yaml

from lassi_x.config import RunConfig
from lassi_x.validation import build_oracle

REPO = Path(__file__).resolve().parents[2]
SCIENTIFIC = Path(__file__).resolve().parent / "scientific"
# Six additional kernels complete PolyBench/C's 30-kernel collection.
CORE = {
    "datamining": ["correlation", "covariance"],
    "linear-algebra/blas": ["gemm", "gemver", "gesummv", "syr2k", "trmm"],
    "linear-algebra/kernels": ["3mm", "atax", "bicg", "doitgen", "mvt"],
    "linear-algebra/solvers": ["cholesky", "durbin", "gramschmidt", "lu"],
    "medley": ["deriche", "floyd-warshall", "nussinov"],
    "stencils": ["adi", "fdtd-2d", "heat-3d", "jacobi-2d", "seidel-2d"],
}
EXTRA = {
    "linear-algebra/blas": ["symm", "syrk"],
    "linear-algebra/kernels": ["2mm"],
    "linear-algebra/solvers": ["ludcmp", "trisolv"],
    "stencils": ["jacobi-1d"],
}
SCIENCE = {
    "direct-dft": "spectral analysis: real/imaginary DFT, trigonometry and reductions",
    "softened-nbody": "particle physics: all-pairs gravitational acceleration",
    "lorenz-rk4": "ODE integration: fixed-step fourth-order Runge-Kutta",
    "poisson-cg": "iterative sparse solve: fixed-iteration conjugate gradient",
    "jpeg-dct": "lossy image compression: block DCT, quantization and reconstruction",
    "wavelet-compression": "lossy image compression: multilevel Haar thresholding",
    "low-rank-compression": "lossy image compression: fixed-iteration power deflation",
    "iir-filter-bank": "signal processing: recurrent biquad filter bank",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(args: argparse.Namespace) -> Path:
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError(f"Refusing to overwrite an existing campaign: {output}")
    polybench = args.polybench.resolve()
    template = yaml.safe_load(args.models_config.read_text())
    models = template.get("models", template)
    # Validate models before creating files; do not copy remote execution or memory.
    sources = []
    groups = {key: list(value) for key, value in CORE.items()}
    if args.full_polybench:
        for key, names in EXTRA.items():
            groups.setdefault(key, []).extend(names)
    for family, names in groups.items():
        for name in names:
            base = polybench / family / name
            sources.append((f"polybench-{name}", family, base / f"{name}.c", base / f"{name}.h"))
    if not args.polybench_only:
        for name, family in SCIENCE.items():
            sources.append((name, family, SCIENTIFIC / f"{name}.c", None))
        mutual = REPO / "examples/PolyBenchC-4.2.1/scientific/mutual-information"
        sources.append(
            (
                "mutual-information",
                "information theory",
                mutual / "mutual-information.c",
                mutual / "mutual-information.h",
            )
        )
    required = [polybench / "utilities/polybench.c", polybench / "utilities/polybench.h"]
    for _, _, source, header in sources:
        required.append(source)
        if header:
            required.append(header)
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(path)
    entries = []
    configurations = []
    for name, family, source, header in sources:
        precision = output / "headers" / f"{name}.h"
        context = [source.parent / "common.h"] if header is None else [header, precision]
        task = (
            f"Translate {name} into a semantically equivalent, export-friendly PyTorch module. "
            f"Use the {args.dataset.upper()}_DATASET profile selected by the oracle build. "
            "Read the reference, initialization, headers and live-out printing carefully. "
            "Expose build_inputs(device, dtype), make_model(), and forward with tensor inputs. "
            "Reproduce the deterministic C inputs exactly; compute from supplied inputs, never "
            "hard-code the oracle or precompute final outputs in build_inputs. Do not mutate "
            "caller inputs. Return every printed live-out in print order, each flattened in "
            "row-major order (a tensor or tuple of tensors). Preserve integer semantics for "
            "integer kernels, boundaries, triangular regions, recurrence dependencies and "
            "iteration counts. Use FP64 for floating-point CPU verification."
        )
        build = [
            args.cc,
            "-std=c99",
            "-O0",
            "-ffp-contract=off",
            f"-D{args.dataset.upper()}_DATASET",
        ]
        if header:
            build += ["-DPOLYBENCH_DUMP_ARRAYS", "-include", str(precision)]
        build += ["{reference}"]
        if header:
            build += [
                str(polybench / "utilities/polybench.c"),
                f"-I{polybench / 'utilities'}",
                f"-I{source.parent}",
            ]
            context += [polybench / "utilities/polybench.c", polybench / "utilities/polybench.h"]
        build += ["-lm", "-o", "{oracle_dir}/reference"]
        data = {
            "version": 1,
            "project": {"root": str(REPO)},
            "kernel": {
                "name": f"{name}-{args.dataset}",
                "reference": str(source),
                "context": [str(p) for p in context],
                "task": task,
                "validation_dataset": args.dataset,
            },
            "oracle": {
                "build": build,
                "run": ["{oracle_dir}/reference"],
                "capture": "stderr" if header else "stdout",
                "format": "polybench" if header else "numeric",
                "determinism_runs": 2,
                "timeout_s": 120,
            },
            "arena": {
                "candidates": args.candidates,
                "correction_rounds": args.correction_rounds,
                "timeout_s": 900,
                "equivalence": {"rtol": 1e-10, "atol": 1e-12},
            },
            "scheduler": {
                "max_candidate_flows": args.max_candidate_flows,
                "max_model_sessions": args.max_model_sessions,
            },
            "models": models,
            "memory": {"enabled": False},
            "execution": {"mode": args.execution},
            "measure": {
                "precisions": ["fp64"],
                "evaluation_dataset": args.dataset,
                "backends": [
                    {"type": "torch", "name": "cpu", "device": "cpu", "precisions": ["fp64"]}
                ],
            },
            "compensation": {"enabled": False},
            "runs_dir": str(output / "runs" / name),
        }
        RunConfig.model_validate(data)
        configurations.append((name, data, header, precision))
        entries.append({"name": name, "family": family, "config": f"configs/{name}.yaml"})
    (output / "configs").mkdir(parents=True)
    (output / "headers").mkdir()
    for name, data, header, precision in configurations:
        if header:
            # Include the actual benchmark header first: preserve profile/type, only fix printing.
            precision.write_text(
                f'#include "{header}"\n#undef DATA_PRINTF_MODIFIER\n'
                '#ifdef DATA_TYPE_IS_INT\n#define DATA_PRINTF_MODIFIER "%d "\n'
                '#else\n#define DATA_PRINTF_MODIFIER "%.17g "\n#endif\n'
            )
        (output / "configs" / f"{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False))
    tracked = set(required) | set((output / "configs").glob("*.yaml"))
    tracked |= set((output / "headers").glob("*.h"))
    if not args.polybench_only:
        tracked.add(SCIENTIFIC / "common.h")
    manifest = {
        "schema_version": 1,
        "dataset": args.dataset,
        "entries": entries,
        "files": {str(path): digest(path) for path in sorted(tracked)},
    }
    path = output / "suite.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return path


def run_suite(args: argparse.Namespace) -> int:
    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text())
    for filename, expected in manifest["files"].items():
        if digest(Path(filename)) != expected:
            raise ValueError(f"Campaign input changed: {filename}; prepare a new campaign")
    selected = set(args.only or [])
    known = {entry["name"] for entry in manifest["entries"]}
    if selected - known:
        raise ValueError(f"Unknown kernels: {sorted(selected - known)}")
    entries = [entry for entry in manifest["entries"] if not selected or entry["name"] in selected]
    failures = 0
    for index, entry in enumerate(entries):
        config = manifest_path.parent / entry["config"]
        command = [args.lassi_x, "run", str(config), "--until", "cpu-verified"]
        if args.check_oracles:
            # Use the production oracle path, including parsing and determinism checks.
            cfg = RunConfig.load(config)
            target = manifest_path.parent / "oracle-checks" / entry["name"]
            target.mkdir(parents=True, exist_ok=True)
            try:
                result = asyncio.run(build_oracle(cfg, target))
                print(f"{entry['name']}: oracle OK ({result.output_path})", flush=True)
            except Exception as exc:
                failures += 1
                print(f"{entry['name']}: oracle FAILED: {exc}", file=sys.stderr)
        elif args.execute:
            run_root = manifest_path.parent / "runs" / entry["name"]
            previous_records = set(run_root.glob("*/run.json"))
            print(shlex.join(command), flush=True)
            result = subprocess.run(command, check=False)
            failures += result.returncode != 0
            # Quota exhaustion is not a kernel failure. Do not consume the rest
            # of the campaign with attempts that cannot reach the model.
            for record in set(run_root.glob("*/run.json")) - previous_records:
                diagnostic = record.read_text().lower()
                if "http 429" in diagnostic and "usage limit has been reached" in diagnostic:
                    print(
                        "Stopping campaign: model usage limit exhausted",
                        file=sys.stderr,
                        flush=True,
                    )
                    return 2
                if "connection error." in diagnostic or "apiconnectionerror" in diagnostic:
                    print(
                        "Stopping campaign: model endpoint connection failed",
                        file=sys.stderr,
                        flush=True,
                    )
                    return 3
        else:
            print(shlex.join(command))
        if args.cooldown_s and index + 1 < len(entries):
            print(f"Cooling down for {args.cooldown_s:g}s before the next kernel", flush=True)
            time.sleep(args.cooldown_s)
    return 1 if failures else 0


def summarize(manifest_path: Path) -> None:
    """Include every attempt, including failed/interrupted runs, rather than best-of selection."""
    root = manifest_path.resolve().parent
    manifest = json.loads(manifest_path.read_text())
    fields = [
        "benchmark",
        "family",
        "run",
        "run_status",
        "candidate",
        "provider",
        "model",
        "candidate_status",
        "wall_seconds",
        "cpu_baseline",
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields)
    writer.writeheader()
    for entry in manifest["entries"]:
        records = sorted((root / "runs" / entry["name"]).glob("*/run.json"))
        if not records:
            writer.writerow(
                {"benchmark": entry["name"], "family": entry["family"], "run_status": "not_run"}
            )
        for path in records:
            run = json.loads(path.read_text())
            base = {
                "benchmark": entry["name"],
                "family": entry["family"],
                "run": str(path.parent),
                "run_status": run.get("status"),
                "wall_seconds": run.get("wall_seconds"),
                "cpu_baseline": str(path.parent / "cpu-baseline")
                if (path.parent / "cpu-baseline/manifest.json").exists()
                else "",
            }
            for candidate in run.get("candidates", []) or [{}]:
                writer.writerow(
                    {
                        **base,
                        "candidate": candidate.get("candidate_id"),
                        "provider": candidate.get("provider"),
                        "model": candidate.get("model"),
                        "candidate_status": candidate.get("status"),
                    }
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument(
        "--models-config",
        type=Path,
        required=True,
        help="Run YAML or YAML containing planner/candidates/compensation",
    )
    prepare_parser.add_argument("--polybench", type=Path, default=REPO.parent / "PolyBenchC-4.2.1")
    prepare_parser.add_argument("--output", type=Path, required=True)
    prepare_parser.add_argument("--dataset", choices=["mini", "small", "medium"], default="mini")
    prepare_parser.add_argument("--candidates", type=int, choices=range(1, 11), default=3)
    prepare_parser.add_argument("--correction-rounds", type=int, choices=range(11), default=2)
    prepare_parser.add_argument("--max-candidate-flows", type=int, choices=range(1, 65), default=3)
    prepare_parser.add_argument("--max-model-sessions", type=int, choices=range(1, 65), default=4)
    prepare_parser.add_argument("--full-polybench", action="store_true")
    prepare_parser.add_argument("--polybench-only", action="store_true")
    prepare_parser.add_argument("--cc", default="gcc")
    prepare_parser.add_argument("--execution", choices=["local", "docker"], default="local")
    run_parser = sub.add_parser("run")
    run_parser.add_argument("manifest", type=Path)
    mode = run_parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Explicitly authorize model runs")
    mode.add_argument("--check-oracles", action="store_true", help="Compile/run C only; no models")
    run_parser.add_argument("--only", nargs="+")
    run_parser.add_argument(
        "--cooldown-s",
        type=float,
        default=0.0,
        help="Wait this many seconds after each selected kernel before starting the next",
    )
    run_parser.add_argument("--lassi-x", default="lassi-x")
    summary_parser = sub.add_parser("summary", help="CSV of all attempts and candidate outcomes")
    summary_parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    if args.action == "prepare":
        print(prepare(args))
        return 0
    if args.action == "summary":
        summarize(args.manifest)
        return 0
    return run_suite(args)


if __name__ == "__main__":
    raise SystemExit(main())
