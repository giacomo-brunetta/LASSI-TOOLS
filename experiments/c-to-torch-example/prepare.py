"""Prepare an explicit two-workload ATAX development smoke, without model calls."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import yaml

from lassi_x.config import RunConfig


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--native-root", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    native = args.native_root.resolve()
    source = root / "benchmarks/polybench/linear-algebra/kernels/atax/atax.c"
    compiler = shutil.which("clang")
    if compiler is None:
        raise RuntimeError("Clang required")
    utilities = root / "benchmarks/polybench/utilities"
    spec = {
        "inputs": {
            "m": {"argument": "m", "access": "read_only", "scalar": True},
            "n": {"argument": "n", "access": "read_only", "scalar": True},
            "A": {"argument": "A", "access": "read_only"},
            "x": {"argument": "x", "access": "read_only"},
        },
        "outputs": ["tmp", "y"],
    }
    (output / "fixture.yaml").write_text(yaml.safe_dump(spec))
    for dataset in ("MINI", "SMALL"):
        config = {
            "version": 1,
            "project": {"root": str(root)},
            "kernel": {
                "name": "atax",
                "reference": str(source),
                "task": "Minimally adapt ATAX C for direct Tenspiler synthesis.",
                "validation_dataset": dataset.lower(),
            },
            "oracle": {
                "fixture_spec": str(output / "fixture.yaml"),
                "build": [
                    compiler,
                    "-O3",
                    "-ffp-contract=off",
                    f"-D{dataset}_DATASET",
                    f"-I{utilities}",
                    "{reference}",
                    str(utilities / "polybench.c"),
                    "-lm",
                    "-o",
                    "{oracle_dir}/reference",
                ],
                "run": ["{oracle_dir}/reference"],
                "timeout_s": 30,
            },
            "models": {
                "planner": {"model": "configure-before-live-use"},
                "compensation": {"model": "configure-before-live-use"},
                "candidates": [{"model": "configure-before-live-use"}],
            },
            "arena": {"candidates": 1, "equivalence": {"rtol": 1e-10, "atol": 1e-12}},
            "measure": {
                "evaluation_dataset": dataset.lower(),
                "precisions": ["fp64"],
                "backends": [
                    {"type": "torch", "name": "cpu", "device": "cpu", "precisions": ["fp64"]}
                ],
            },
        }
        RunConfig.model_validate(config)
        (output / f"{dataset.lower()}.yaml").write_text(yaml.safe_dump(config))
    plan = {
        "clang": compiler,
        "cases": ["mini.yaml", "small.yaml"],
        "function": "kernel_atax",
        "model": {
            "model": "configure-before-live-use",
            "turn_retries": 0,
            "max_iterations": 1,
            "max_tokens": 8192,
        },
        "includes": [str(source.parent), str(utilities)],
        "defines": ["MINI_DATASET"],
        "native_python": str(native / "venv/bin/python"),
        "tenspiler_root": str(native / "source"),
        "llvm_bin": str(native / "llvm11/bin"),
        "llvm_pass": str(native / "llvm-pass-build/addEmptyBlocks/libAddEmptyBlocksPass.so"),
        "proposals": 1,
        "synthesis_timeout_s": 120,
        "bound": 2,
    }
    (output / "plan.yaml").write_text(yaml.safe_dump(plan))
    original = source.read_text()
    start = original.index("{", original.index("void kernel_atax"))
    end = original.index("\n}", start) + 2
    body = """{
  int i, j;
  for (i = 0; i < _PB_M; i++) {
    tmp[i] = SCALAR_VAL(0.0);
    for (j = 0; j < _PB_N; j++)
      tmp[i] = tmp[i] + A[i][j] * x[j];
  }
  for (j = 0; j < _PB_N; j++) {
    y[j] = SCALAR_VAL(0.0);
    for (i = 0; i < _PB_M; i++)
      y[j] = y[j] + A[i][j] * tmp[i];
  }
}"""
    (output / "replay-proposal.json").write_text(
        json.dumps(
            {
                "source": original[:start] + body + original[end:],
                "changes": [
                    "Hand-authored integration fixture, not a model result: distribute complete "
                    "tmp reduction from y reduction, preserving per-output accumulation order."
                ],
            },
            indent=2,
        )
    )
    (output / "inputs.json").write_text(
        json.dumps(
            {
                "source": str(source),
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "datasets": ["MINI", "SMALL"],
                "model_calls": 0,
                "scope": "development integration smoke; replay proposal is hand-authored",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
