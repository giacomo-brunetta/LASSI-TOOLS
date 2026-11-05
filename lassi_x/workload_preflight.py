"""Execute the real C gate for every random case in explicit preparation reports."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

import yaml

from .c_to_torch import c_gate
from .config import RunConfig
from .workload_checks import digest


def compact_gate(directory: Path) -> None:
    """Retain gate hashes, sources, commands and logs; remove duplicate raw arrays."""
    removed = []
    for variant in ("original", "adapted"):
        fixture = directory / variant / "oracle/c-fixture"
        if not fixture.exists():
            continue
        for path in fixture.iterdir():
            if path.suffix in {".bin", ".npz", ".npy"}:
                removed.append(
                    {"path": str(path.relative_to(directory)), "bytes": path.stat().st_size}
                )
                path.unlink()
    (directory / "retention.json").write_text(
        json.dumps(
            {
                "policy": "Canonical inputs and expected results remain in preparation artifacts; "
                "gate.json retains per-array hashes, shape, dtype and comparison outcome.",
                "removed_duplicates": removed,
            },
            indent=2,
        )
        + "\n"
    )


async def preflight(
    root: Path,
    reports: list[Path],
    destination: Path,
    *,
    dataset: str = "large",
    retain_raw: bool = False,
    workload_ids: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Check the complete cohort; never select between competing passed/failed rows."""
    destination.mkdir(parents=True, exist_ok=False)
    manifest_path = root / "benchmarks/provenance/workloads-40.json"
    manifest = json.loads(manifest_path.read_text())
    selected: dict[str, Any] = {}
    evidence = []
    for path in reports:
        data = json.loads(path.read_text())
        evidence.append({"path": str(path.resolve()), "sha256": digest(path)})
        if data["dataset"] != dataset:
            raise ValueError("Preparation report dataset differs from preflight dataset")
        for row in data["workloads"]:
            if row["status"] in {"not_run", "unsupported"}:
                continue
            if row["id"] in selected:
                raise ValueError(f"Conflicting explicit preparation rows for {row['id']}")
            selected[row["id"]] = row
    result: dict[str, Any] = {
        "dataset": dataset,
        "preparation_reports": evidence,
        "manifest_sha256": digest(manifest_path),
        "model_calls": 0,
        "scope": "Executed original-versus-same-source C preflight; not candidate certification",
        "workloads": [
            {"id": w["id"], "status": "not_run", "cases": []} for w in manifest["workloads"]
        ],
    }
    for workload, row in zip(manifest["workloads"], result["workloads"], strict=True):
        if workload_ids is not None and workload["id"] not in workload_ids:
            continue
        prepared = selected.get(workload["id"])
        if prepared is None or prepared["status"] != "reference_checked":
            row.update(
                status="incomplete", reason="Missing successful explicit reference preparation"
            )
        else:
            try:
                for source in workload["sources"]:
                    if digest(root / source["path"]) != source["sha256"]:
                        raise ValueError("Pinned source changed since preparation")
                config_path = Path(prepared["config"])
                if digest(config_path) != prepared["config_sha256"]:
                    raise ValueError("Prepared configuration hash mismatch")
                config = RunConfig.model_validate(yaml.safe_load(config_path.read_text()))
                reference = config.resolve_project_path(config.kernel.reference)
                expected_source = prepared.get("reference_sha256", workload["sources"][0]["sha256"])
                if digest(reference) != expected_source:
                    raise ValueError("Fixture reference changed since preparation")
                assert config.oracle.fixture_spec is not None
                if (
                    digest(config.resolve_project_path(config.oracle.fixture_spec))
                    != prepared["fixture_spec_sha256"]
                ):
                    raise ValueError("Fixture specification changed since preparation")
                for context, checksum in prepared.get("context_sha256", {}).items():
                    if digest(config.resolve_project_path(Path(context))) != checksum:
                        raise ValueError("Native dependency context changed since preparation")
                cases = [
                    config.validated_update(
                        arena=config.arena.validated_update(correctness_tests=[])
                    )
                ]
                cases += [
                    config.validated_update(
                        kernel=config.kernel.validated_update(validation_dataset=c.dataset),
                        oracle=c.oracle,
                        arena=config.arena.validated_update(correctness_tests=[]),
                    )
                    for c in config.arena.correctness_tests
                ]
                if len(cases) < 2 or len(cases) != len(prepared["cases"]):
                    raise ValueError("Preflight requires every declared random case")
                directory = destination / workload["id"].replace("/", "-")
                directory.mkdir()
                candidate = directory / "same-source.c"
                candidate.write_bytes(reference.read_bytes())
                for case_config, case in zip(cases, prepared["cases"], strict=True):
                    case_row: dict[str, Any] = {
                        "id": case["id"],
                        "seed": case["seed"],
                        "status": "not_run",
                    }
                    row["cases"].append(case_row)
                    if case_config.kernel.validation_dataset != dataset:
                        raise ValueError("Case changes workload dimensions")
                    inputs = case_config.oracle.input_fixture
                    if (
                        inputs is None
                        or digest(case_config.resolve_project_path(inputs)) != case["input_sha256"]
                    ):
                        raise ValueError("Seeded input artifact hash mismatch")
                    case_directory = directory / case["id"]
                    gate = await c_gate(case_config, candidate, case_directory)
                    case_row.update(
                        status="passed" if gate["passed"] else "failed",
                        gate=str(case_directory / "gate.json"),
                    )
                    if gate["passed"] and not retain_raw:
                        compact_gate(case_directory)
                    (destination / "report.json").write_text(json.dumps(result, indent=2) + "\n")
                row["status"] = (
                    "passed" if all(c["status"] == "passed" for c in row["cases"]) else "failed"
                )
            except (ValueError, RuntimeError, OSError, TimeoutError) as error:
                row.update(status="failed", reason=str(error))
        (destination / "report.json").write_text(json.dumps(result, indent=2) + "\n")
        print(f"{row['id']}: {row['status']}", flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--reports", type=Path, nargs="+", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--retain-raw", action="store_true")
    parser.add_argument("--workload-ids", nargs="+")
    args = parser.parse_args()
    result = asyncio.run(
        preflight(args.root, args.reports, args.destination, retain_raw=args.retain_raw)
    )
    return int(any(w["status"] != "passed" for w in result["workloads"]))


if __name__ == "__main__":
    raise SystemExit(main())
