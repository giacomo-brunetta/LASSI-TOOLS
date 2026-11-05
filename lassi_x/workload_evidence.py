"""Audit explicit preparation/preflight partitions against frozen reference arrays."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .config import RunConfig
from .input_contract import load_contract
from .workload_checks import digest, random_inputs
from .workload_inputs import random_inputs as native_random_inputs
from .workload_invariants import check_native
from .workload_native import KINDS


def audit(root: Path, plan: Path, destination: Path) -> dict[str, Any]:
    """Require one predeclared owner for every workload, including failures."""
    manifest_path = root / "benchmarks/provenance/workloads-39.json"
    manifest = json.loads(manifest_path.read_text())
    partitions = json.loads(plan.read_text())["partitions"]
    declared = [wid for partition in partitions for wid in partition["workload_ids"]]
    wanted = [w["id"] for w in manifest["workloads"]]
    if len(declared) != len(set(declared)) or set(declared) != set(wanted):
        raise ValueError("Evidence partitions must own each active workload exactly once")
    sources: dict[str, Any] = {}
    records = []
    for partition in partitions:
        prepare_path, gate_path = Path(partition["preparation"]), Path(partition["preflight"])
        prepared, checked = json.loads(prepare_path.read_text()), json.loads(gate_path.read_text())
        if prepared["dataset"] != "large" or checked["dataset"] != "large":
            raise ValueError("Final evidence must use LARGE in every partition")
        records.append(
            {
                "preparation": str(prepare_path),
                "preparation_sha256": digest(prepare_path),
                "preflight": str(gate_path),
                "preflight_sha256": digest(gate_path),
                "workload_ids": partition["workload_ids"],
            }
        )
        for wid in partition["workload_ids"]:
            sources[wid] = (
                next(w for w in prepared["workloads"] if w["id"] == wid),
                next(w for w in checked["workloads"] if w["id"] == wid),
            )
    result: dict[str, Any] = {
        "manifest_sha256": digest(manifest_path),
        "partition_plan_sha256": digest(plan),
        "partitions": records,
        "dataset": "large",
        "model_calls": 0,
        "generator_sha256": {
            name: digest(Path(__file__).with_name(name + ".py"))
            for name in ("workload_checks", "workload_inputs", "workload_invariants")
        },
        "scope": "Native random-input references and executed same-source C preflight; "
        "not model-candidate or accelerator certification",
        "workloads": [],
    }
    for workload in manifest["workloads"]:
        prepared, checked = sources[workload["id"]]
        row: dict[str, Any] = {"id": workload["id"], "status": "incomplete", "cases": []}
        result["workloads"].append(row)
        try:
            if prepared["status"] != "reference_checked" or checked["status"] != "passed":
                raise ValueError("Preparation or C preflight is incomplete/failed")
            if len(prepared["cases"]) < 2 or len(prepared["cases"]) != len(checked["cases"]):
                raise ValueError("Missing random cases in C preflight")
            expected_seeds = workload["correctness"]["seeds"]
            if [c["seed"] for c in prepared["cases"]] != expected_seeds:
                raise ValueError("Random seeds differ from declared cohort")
            if len({c["output_sha256"] for c in prepared["cases"]}) != len(expected_seeds):
                raise ValueError("Random inputs do not produce distinct observable outputs")
            config = Path(prepared["config"])
            if digest(config) != prepared["config_sha256"]:
                raise ValueError("Prepared config changed")
            tolerance = RunConfig.load(config).arena.equivalence
            previous_outputs: list[Path] = []
            row["config"] = str(config)
            row["config_sha256"] = prepared["config_sha256"]
            for source in workload["sources"]:
                if digest(root / source["path"]) != source["sha256"]:
                    raise ValueError("Pinned source hash mismatch")
            initial, _ = load_contract(config.parent / "native/oracle/c-fixture/inputs.npz")
            for case, check in zip(prepared["cases"], checked["cases"], strict=True):
                if (
                    case["id"] != check["id"]
                    or case["seed"] != check["seed"]
                    or check["status"] != "passed"
                ):
                    raise ValueError(
                        "Case identities or outcomes differ between preparation and preflight"
                    )
                inputs = config.parent / (case["id"] + "-inputs.npz")
                oracle = config.parent / case["id"] / "oracle/c-fixture"
                if (
                    digest(inputs) != case["input_sha256"]
                    or digest(oracle / "expected.npy") != case["output_sha256"]
                ):
                    raise ValueError("Canonical fixture artifacts changed")
                supplied, _ = load_contract(inputs)
                regenerated = (
                    random_inputs(workload["name"], initial, case["seed"])
                    if workload["suite"] == "polybench"
                    else native_random_inputs(KINDS[workload["id"]], initial, case["seed"])
                )
                if set(regenerated) != set(supplied) or any(
                    supplied[name].dtype != value.dtype
                    or supplied[name].shape != value.shape
                    or not np.array_equal(supplied[name], value)
                    for name, value in regenerated.items()
                ):
                    raise ValueError("Current generator does not reproduce the frozen random input")
                arrays, metadata = load_contract(oracle / "outputs.npz")
                independent = (
                    check_native(KINDS[workload["id"]], supplied, arrays)
                    if workload["suite"] != "polybench"
                    else {}
                )
                flattened = np.load(oracle / "expected.npy", mmap_mode="r")
                for previous in previous_outputs:
                    if np.allclose(
                        flattened,
                        np.load(previous, mmap_mode="r"),
                        rtol=tolerance.rtol,
                        atol=tolerance.atol,
                    ):
                        raise ValueError("Random outputs are equivalent at acceptance tolerances")
                previous_outputs.append(oracle / "expected.npy")
                gate_path = Path(check["gate"])
                gate = json.loads(gate_path.read_text())
                if not gate["passed"] or not all(c["passed"] for c in gate["checks"]):
                    raise ValueError("C gate report contains a failure")
                by_name = {c["output"]: c for c in gate["checks"]}
                offset = 0
                comparisons = []
                for name in metadata["outputs"]:
                    value = arrays[name]
                    golden = flattened[offset : offset + value.size]
                    if not np.array_equal(golden, value.reshape(-1)):
                        raise ValueError("Typed outputs differ from canonical expected.npy")
                    offset += value.size
                    field = by_name[name]
                    checksum = hashlib.sha256(memoryview(value)).hexdigest()
                    if (
                        field["expected_sha256"] != checksum
                        or field["dtype"] != value.dtype.str
                        or field["shape"] != list(value.shape)
                    ):
                        raise ValueError(
                            f"Fresh C preflight changed frozen reference output {name}"
                        )
                    comparisons.append(
                        {
                            "output": name,
                            "sha256": checksum,
                            "dtype": value.dtype.str,
                            "shape": list(value.shape),
                        }
                    )
                if offset != flattened.size:
                    raise ValueError("Canonical output length mismatch")
                row["cases"].append(
                    {
                        "id": case["id"],
                        "seed": case["seed"],
                        "status": "passed",
                        "input_sha256": case["input_sha256"],
                        "output_sha256": case["output_sha256"],
                        "independent_checks": independent,
                        "current_generator_reproduced_input": True,
                        "numerically_distinct_from_previous": True,
                        "gate": str(gate_path),
                        "gate_sha256": digest(gate_path),
                        "frozen_reference_outputs": comparisons,
                    }
                )
            row["status"] = "passed"
        except (ValueError, KeyError, OSError) as error:
            row.update(status="failed", reason=str(error))
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2) + "\n")
        print(f"{row['id']}: {row['status']}", flush=True)
    result["workloads_passed"] = sum(w["status"] == "passed" for w in result["workloads"])
    result["cases_passed"] = sum(
        c["status"] == "passed" for w in result["workloads"] for c in w["cases"]
    )
    destination.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = audit(args.root, args.plan, args.destination)
    return int(result["workloads_passed"] != len(result["workloads"]))


if __name__ == "__main__":
    raise SystemExit(main())
