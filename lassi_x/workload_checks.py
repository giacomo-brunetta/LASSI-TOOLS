"""Prepare trusted, multi-case development checks for the pinned workload cohort.

No model calls or accelerator execution. Use generated configs only with
``lassi-x run --until cpu-verified`` while fixture measurement is unsupported.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .config import CorrectnessTestConfig, RunConfig
from .input_contract import load_contract, save_contract
from .validation import build_oracle
from .workload_inputs import FIELDS as NATIVE_FIELDS
from .workload_inputs import random_inputs as native_random_inputs
from .workload_invariants import check_native
from .workload_native import KINDS
from .workload_native import configuration as native_configuration

# Randomize a consumed tensor, preserving dimensions and structural state.
RANDOM_FIELDS = dict(
    correlation="data",
    covariance="data",
    gemm="A",
    gemver="u1",
    gesummv="x",
    symm="B",
    syr2k="A",
    syrk="A",
    trmm="B",
    atax="x",
    bicg="r",
    doitgen="C4",
    mvt="y_1",
    cholesky="A",
    durbin="r",
    gramschmidt="A",
    lu="A",
    ludcmp="b",
    trisolv="b",
    deriche="imgIn",
    nussinov="seq",
    adi="u",
    **{
        "2mm": "A",
        "3mm": "A",
        "floyd-warshall": "path",
        "fdtd-2d": "hz",
        "heat-3d": "A",
        "jacobi-1d": "A",
        "jacobi-2d": "A",
        "seidel-2d": "A",
    },
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def configuration(root: Path, workload: dict[str, Any], spec: Path, dataset: str) -> RunConfig:
    """Construct a direct-input correctness run from an explicit manifest entry."""
    source = root / workload["sources"][0]["path"]
    if digest(source) != workload["sources"][0]["sha256"]:
        raise ValueError(f"Source hash mismatch: {source}")
    compiler = shutil.which("cc")
    if compiler is None:
        raise RuntimeError("A C11 compiler is required")
    utilities = root / "benchmarks/polybench/utilities"
    model = {"model": "configure-before-live-use"}
    return RunConfig.model_validate(
        {
            "version": 1,
            "project": {"root": str(root)},
            "kernel": {
                "name": workload["name"],
                "reference": str(source),
                "context": [str(source.with_suffix(".h")), str(utilities / "polybench.h")],
                "task": "Implement forward with the exact named fixture inputs and output order. "
                "All development correctness cases must pass on the same source revision.",
                "validation_dataset": dataset,
            },
            "oracle": {
                "fixture_spec": str(spec),
                "build": [
                    compiler,
                    "-std=c11",
                    "-O2",
                    "-ffp-contract=off",
                    f"-D{dataset.upper()}_DATASET",
                    f"-I{utilities}",
                    "{reference}",
                    str(root / "benchmarks/checks/zero-alloc.c"),
                    "-lm",
                    "-o",
                    "{oracle_dir}/reference",
                ],
                "run": ["{oracle_dir}/reference"],
                "timeout_s": 1800,
                "determinism_runs": 2,
            },
            "models": {"planner": model, "compensation": model, "candidates": [model]},
            "arena": {"candidates": 1, "equivalence": {"rtol": 1e-10, "atol": 1e-12}},
            "measure": {
                "evaluation_dataset": dataset,
                "precisions": ["fp64"],
                "backends": [
                    {"type": "torch", "name": "cpu", "device": "cpu", "precisions": ["fp64"]}
                ],
            },
        }
    )


DEFAULT_SEEDS = (0, 1, 2, 3, 4)


def random_inputs(name: str, arrays: dict[str, Any], seed: int) -> dict[str, Any]:
    """Generate independent values without changing the native tensor interface.

    Only the named consumed tensor varies; remaining initial state and parameters
    stay native. This avoids randomizing scratch buffers or violating boundaries.
    """
    result = dict(arrays)
    field = RANDOM_FIELDS[name]
    value = arrays[field]
    # A per-workload stream avoids giving equally shaped kernels identical data.
    stream = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "little")
    rng = np.random.default_rng(np.random.SeedSequence([seed, stream]))
    if name == "nussinov":
        generated = rng.integers(0, 4, size=value.shape, dtype=value.dtype)
    elif name == "floyd-warshall":
        generated = rng.integers(1, 20, size=value.shape, dtype=value.dtype)
        generated[value == 999] = 999  # Preserve absent edges.
    elif name in {"cholesky", "lu"}:
        # Symmetric strict diagonal dominance with positive diagonal implies SPD.
        generated = rng.uniform(-0.5, 0.5, size=value.shape)
        generated = (generated + generated.T) * 0.5
        np.fill_diagonal(generated, 0)
        np.fill_diagonal(generated, np.abs(generated).sum(axis=1) + 1)
    elif name == "durbin":
        # Strictly diagonally dominant unit-diagonal Toeplitz correlation matrix.
        generated = rng.uniform(-0.25 / value.size, 0.25 / value.size, size=value.shape)
    else:
        generated = rng.uniform(0.1, 1.0, size=value.shape)
    result[field] = generated.astype(value.dtype)
    if np.array_equal(value, result[field]):
        raise ValueError(f"Random input did not change {field}")
    return result


async def prepare(
    root: Path,
    destination: Path,
    *,
    seeds: tuple[int, ...] = DEFAULT_SEEDS,
    dataset: str = "large",
    native_root: Path | None = None,
    workload_ids: tuple[str, ...] | None = None,
    retain_raw: bool = False,
) -> dict[str, Any]:
    """Freeze multiple seeded random cases, all at the same LARGE dimensions.

    The dataset override exists for bounded adapter regression tests only.
    The production CLI always uses LARGE.
    """
    if len(seeds) < 2 or len(set(seeds)) != len(seeds) or any(s < 0 for s in seeds):
        raise ValueError("Supply at least two distinct nonnegative seeds")
    root, destination = root.resolve(), destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "benchmarks/provenance/workloads-40.json"
    manifest = json.loads(manifest_path.read_text())
    report: dict[str, Any] = {
        "manifest_sha256": digest(manifest_path),
        "model_calls": 0,
        "dataset": dataset,
        "seeds": list(seeds),
        "rng": "numpy.default_rng/PCG64; SeedSequence(seed, workload SHA256 prefix)",
        "scope": "CPU development correctness; no candidate or accelerator certification",
        "dependencies": {
            str(p.relative_to(root)): digest(p)
            for p in (
                root / "benchmarks/checks/zero-alloc.c",
                root / "benchmarks/polybench/utilities/polybench.c",
                root / "benchmarks/polybench/utilities/polybench.h",
            )
        },
        "workloads": [
            {"id": w["id"], "status": "not_run", "cases": []} for w in manifest["workloads"]
        ],
    }
    for workload, entry in zip(manifest["workloads"], report["workloads"], strict=True):
        if workload_ids is not None and workload["id"] not in workload_ids:
            continue
        if workload["suite"] != "polybench" and native_root is None:
            entry["status"] = "unsupported"
            entry["reason"] = "Explicit native dependency root required for this suite"
            continue
        directory = destination / workload["name"]
        directory.mkdir()
        try:
            profile = (
                workload["name"] if workload["suite"] == "polybench" else KINDS[workload["id"]]
            )
            spec = root / "benchmarks/checks" / (profile + ".json")
            if workload["suite"] == "polybench":
                config = configuration(root, workload, spec, dataset)
            else:
                assert native_root is not None
                config = native_configuration(root, workload, dataset, native_root)

            # Bootstrap exports the native interface; it is not a candidate test.
            native = await build_oracle(config, directory / "native")
            assert native.input_contract_path is not None
            arrays, metadata = load_contract(native.input_contract_path)
            if not retain_raw:
                discard_transfers(native.input_contract_path.parent)
            cases: list[RunConfig] = []
            checks: list[CorrectnessTestConfig] = []
            for seed in seeds:
                case_id = f"random-{seed}"
                inputs = directory / f"{case_id}-inputs.npz"
                randomized = (
                    random_inputs(profile, arrays, seed)
                    if workload["suite"] == "polybench"
                    else native_random_inputs(profile, arrays, seed)
                )
                save_contract(inputs, randomized, metadata)
                case = config.validated_update(
                    oracle=config.oracle.validated_update(input_fixture=inputs)
                )
                oracle = await build_oracle(case, directory / case_id)
                invariants = {}
                if workload["suite"] != "polybench":
                    outputs, _ = load_contract(oracle.output_path.parent / "outputs.npz")
                    invariants = check_native(profile, randomized, outputs)
                if not retain_raw:
                    discard_transfers(oracle.output_path.parent)
                cases.append(case)
                entry["cases"].append(
                    {
                        "id": case_id,
                        "seed": seed,
                        "randomized_fields": [RANDOM_FIELDS[profile]]
                        if workload["suite"] == "polybench"
                        else NATIVE_FIELDS[profile],
                        "dataset": dataset,
                        "input_sha256": digest(inputs),
                        "output_sha256": digest(oracle.output_path),
                        "independent_checks": invariants,
                    }
                )
                if len(cases) > 1:
                    checks.append(
                        CorrectnessTestConfig.model_validate(
                            {
                                "id": case_id,
                                "dataset": dataset,
                                "oracle": case.oracle.model_dump(mode="json"),
                                "timeout_s": 1800,
                            }
                        )
                    )
            if len({c["output_sha256"] for c in entry["cases"]}) != len(seeds):
                raise ValueError("Random cases must produce distinct observable outputs")
            config = cases[0].validated_update(
                arena=config.arena.validated_update(
                    correctness_tests=checks,
                    suite_timeout_s=1800 * len(seeds),
                )
            )
            config_path = directory / "run.yaml"
            config_path.write_text(yaml.safe_dump(config.model_dump(mode="json")))
            case_files = explicit_case_configs(
                config, [c["id"] for c in entry["cases"]], directory / "cases"
            )
            entry.update(
                status="reference_checked",
                case_configs=case_files,
                config=str(config_path),
                config_sha256=digest(config_path),
                fixture_spec_sha256=digest(spec),
                reference_sha256=digest(config.resolve_project_path(config.kernel.reference)),
                context_sha256={
                    str(p): digest(config.resolve_project_path(p)) for p in config.kernel.context
                },
            )
        except (ValueError, RuntimeError) as error:
            entry.update(status="failed", reason=str(error))
        (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (destination / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def explicit_case_configs(
    config: RunConfig,
    case_ids: list[str],
    directory: Path,
) -> list[dict[str, str]]:
    """Export flat cases accepted by the C-adaptation pipeline's case loader."""
    cases = [config] + [
        config.validated_update(
            kernel=config.kernel.validated_update(validation_dataset=case.dataset),
            oracle=case.oracle,
        )
        for case in config.arena.correctness_tests
    ]
    if len(cases) != len(case_ids):
        raise ValueError("Every explicit case requires its own identity")
    directory.mkdir(parents=True, exist_ok=False)
    result = []
    for case_id, case in zip(case_ids, cases, strict=True):
        if not case_id.startswith("random-") or not case_id.removeprefix("random-").isdigit():
            raise ValueError("Explicit random case IDs must contain a nonnegative seed")
        case = case.validated_update(arena=case.arena.validated_update(correctness_tests=[]))
        path = directory / (case_id + ".yaml")
        path.write_text(yaml.safe_dump(case.model_dump(mode="json")))
        result.append({"id": case_id, "path": str(path), "sha256": digest(path)})
    return result


def discard_transfers(directory: Path) -> None:
    """Drop duplicate binary transfers after canonical contracts are saved."""
    removed = []
    for path in directory.iterdir():
        if path.suffix == ".bin":
            removed.append({"path": path.name, "bytes": path.stat().st_size})
            path.unlink()
    (directory / "retention.json").write_text(
        json.dumps(
            {
                "policy": "Canonical inputs.npz, outputs.npz and expected.npy retained",
                "removed_duplicate_transfers": removed,
            },
            indent=2,
        )
        + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--seeds", nargs="+", type=int, default=list(DEFAULT_SEEDS))
    parser.add_argument("--native-root", type=Path)
    parser.add_argument("--workload-ids", nargs="+")
    parser.add_argument("--retain-raw", action="store_true")
    args = parser.parse_args()
    report = asyncio.run(
        prepare(
            args.root,
            args.destination,
            seeds=tuple(args.seeds),
            native_root=args.native_root or args.root / "build/workload-native",
            retain_raw=args.retain_raw,
            workload_ids=tuple(args.workload_ids) if args.workload_ids else None,
        )
    )
    counts = {
        status: sum(w["status"] == status for w in report["workloads"])
        for status in ("reference_checked", "failed", "unsupported")
    }
    print(json.dumps(counts))
    return int(any(w["status"] != "reference_checked" for w in report["workloads"]))


if __name__ == "__main__":
    raise SystemExit(main())
