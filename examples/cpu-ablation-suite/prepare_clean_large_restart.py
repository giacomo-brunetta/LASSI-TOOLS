"""Quarantine unconstrained campaigns and freeze a model-free restart inventory.

This does not launch agents or claim historical measurements are clean baselines.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "runs"
OUTPUT = RUNS / "a100-large-clean-restart-20261015"
ARCHIVE = RUNS / "legacy" / "unconstrained-precision-20261015"
CAMPAIGNS = (
    "a100-large-repair-20261015",
    "a100-luna-numerical-repair-20261013",
    "a100-sol-numerical-repair-20261014",
    "a100-large-validation-20261014",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main() -> None:
    if OUTPUT.exists() or ARCHIVE.exists():
        raise FileExistsError("Restart or archive already exists; refusing to overwrite")
    for name in CAMPAIGNS:
        if not (RUNS / name).is_dir():
            raise FileNotFoundError(RUNS / name)
    large = RUNS / CAMPAIGNS[0]
    campaign = json.loads((large / "campaign.json").read_text())
    original = json.loads((RUNS / CAMPAIGNS[-1] / "campaign.json").read_text())
    threshold = 0.01
    historical_cells = []
    historical_workloads = {entry["name"]: entry for entry in original["entries"]}
    for path in sorted((RUNS / CAMPAIGNS[-1] / "runs").glob("*/run.json")):
        record = json.loads(path.read_text())
        for point in record["measurements"]:
            if point["precision"] not in {"fp16", "bf16"}:
                continue
            error = point.get("relative_l2")
            failed = point["status"] != "ok"
            weak = not failed and error is not None and error > threshold
            historical_cells.append(
                {
                    "kernel": record["kernel"],
                    "precision": point["precision"],
                    "status": point["status"],
                    "relative_l2": error,
                    "needs_repair": failed or weak,
                    "reason": "execution_or_numerical_failure"
                    if failed
                    else "weak_accuracy"
                    if weak
                    else "historically_passed_unverified_precision",
                    "provisional_only": True,
                    "source_record": str(
                        ARCHIVE / CAMPAIGNS[-1] / path.relative_to(RUNS / CAMPAIGNS[-1])
                    ),
                    "historical_dimensions": historical_workloads[record["kernel"]][
                        "large_profile"
                    ],
                }
            )
    unique = {}
    for entry in campaign["entries"]:
        unique.setdefault(entry["name"], entry)
    assert len(unique) == 33
    assert len(historical_cells) == 66
    # Verify every frozen source before copying or moving anything.
    for entry in unique.values():
        assert 1 <= len(entry["seeds"]) <= 3
        for seed in entry["seeds"]:
            if digest(Path(seed["seed"])) != seed["seed_sha256"]:
                raise ValueError(f"Seed checksum mismatch: {seed['seed']}")
    OUTPUT.mkdir()
    shutil.copytree(large / "seeds", OUTPUT / "seeds")
    shutil.copytree(large / "references", OUTPUT / "references")
    inventory = []
    candidates = []
    for name, entry in unique.items():
        evidence = [cell for cell in historical_cells if cell["kernel"] == name]
        for index, seed in enumerate(entry["seeds"], 1):
            source = OUTPUT / "seeds" / name / f"c{index}.py"
            assert digest(source) == seed["seed_sha256"]
            inventory.append(
                {
                    "kernel": name,
                    "candidate_id": f"c{index}",
                    "module": str(source),
                    "sha256": digest(source),
                    "original_cpu_source": seed["source"],
                    "original_cpu_source_sha256": seed["source_sha256"],
                    "frozen_dimensions": entry["dimensions"],
                    "reference_directory": str(OUTPUT / "references" / name),
                    "specialization_error": seed.get("specialization_error"),
                    "validation_status": "pending_clean_large_baseline_measurement",
                    "precisions": ["fp64", "fp32", "fp16", "bf16"],
                }
            )
        for cell in evidence:
            if cell["needs_repair"]:
                candidates.append(
                    {
                        **cell,
                        "frozen_dimensions": entry["dimensions"],
                        "candidate_ids_to_validate": [
                            f"c{i}" for i in range(1, len(entry["seeds"]) + 1)
                        ],
                        "queue_status": "provisional_requires_clean_baseline",
                    }
                )
    created = datetime.now(UTC).isoformat()
    summary = {
        "kernels": len(unique),
        "base_implementations": len(inventory),
        "low_precision_baseline_cells_pending": len(inventory) * 2,
        "historical_failed_cells": sum(cell["status"] != "ok" for cell in historical_cells),
        "historical_weak_cells": sum(
            cell["reason"] == "weak_accuracy" for cell in historical_cells
        ),
        "provisional_repair_kernel_precision_pairs": len(candidates),
        "provisional_repair_kernels": len({cell["kernel"] for cell in candidates}),
        "confirmed_clean_repair_count": None,
    }
    save(
        OUTPUT / "baseline-inventory.json",
        {
            "schema_version": 1,
            "created_at": created,
            "status": "prepared_not_executed",
            "model_calls": False,
            "policy": {
                "target": "FP16-only accelerator portability; GPU is the evaluation platform",
                "target_arithmetic": (
                    "requested FP16/BF16 for main operations, persistent state and compensation"
                ),
                "explicit_fp32_fp64_work_in_low_precision_path": "forbidden",
                "implicit_wider_hardware_accumulation": (
                    "only if explicitly supported by the destination; "
                    "never assume explicit wider tensor operations"
                ),
                "input_contract": (
                    "Do not reconstruct or replace supplied input values inside forward"
                ),
                "allowed_interventions": [
                    "scaling",
                    "stable reformulation",
                    "centering",
                    "pairwise reduction",
                    "target-format compensated or multiword arithmetic",
                ],
                "weak_relative_l2_threshold": threshold,
                "evaluation_order": (
                    "Validate every base and classify numerical versus compatibility "
                    "failures before agent calls"
                ),
                "historical_measurements": (
                    "diagnostic only; different dimensions and repaired-source selection "
                    "prohibit treating them as clean baselines"
                ),
                "precision_enforcement": (
                    "not yet implemented; do not launch repair agents from this inventory"
                ),
            },
            "summary": summary,
            "entries": inventory,
        },
    )
    save(
        OUTPUT / "repair-candidates.json",
        {
            "status": "provisional_requires_clean_baseline",
            "summary": summary,
            "note": (
                "Historical failures and weak cells flag targets; all original bases "
                "require clean evaluation. No historical pass is trusted as "
                "target-precision compliance."
            ),
            "entries": candidates,
        },
    )
    save(
        OUTPUT / "historical-diagnostics.json",
        {
            "valid_results": False,
            "source_selection": original["candidate_selection"],
            "entries": historical_cells,
        },
    )
    grouped = {}
    for cell in candidates:
        grouped.setdefault(cell["kernel"], []).append(cell["precision"])
    listing = "\n".join(
        f"| {name} | {', '.join(sorted(precisions))} |"
        for name, precisions in sorted(grouped.items())
    )
    (OUTPUT / "README.md").write_text(
        "# Clean LARGE restart — prepared, not run\n\n"
        f"All 33 kernels and their {len(inventory)} available original Terra CPU seeds "
        "are frozen here. IIR filter bank, Durbin and Deriche have two available seeds "
        "each; the other kernels have three. "
        "No numerical/compatibility repair output has been adopted as a clean baseline. "
        "References and sizes come from the stopped LARGE campaign, not the older size sweep.\n\n"
        f"Historical diagnostics flag {summary['provisional_repair_kernels']} kernels / "
        f"{len(candidates)} kernel-precision pairs "
        f"({summary['historical_failed_cells']} failed, "
        f"{summary['historical_weak_cells']} weak at relative L2 > 0.01). "
        "These are provisional candidates, not a definitive count at the frozen workload. "
        "The old sweep selected one implementation per precision, including repaired MINI "
        "sources, at different sizes.\n\n"
        f"Before repair: independently validate all {len(inventory)} frozen bases, "
        "including high-precision semantic gates, "
        f"then measure the {len(inventory) * 2} FP16/BF16 cells and audit actual arithmetic. "
        "Separate numerical failures from timeout/OOM/compiler failures. Previously passing "
        "full-FP32 implementations are not low-precision successes.\n\n"
        "The intended policy is recorded in baseline-inventory.json. "
        "Prompts now implement this policy; runtime precision auditing is still pending. "
        "No agent campaign has been started.\n\n"
        "## Provisional targets from historical LARGE diagnostics\n\n"
        "| Kernel | Precisions |\n|---|---|\n" + listing + "\n"
    )
    # Recoverable same-filesystem moves. Internal absolute paths intentionally remain
    # unchanged as forensic evidence; these runs must not be resumed.
    ARCHIVE.mkdir(parents=True)
    save(
        ARCHIVE / "INVALID_RESULTS.json",
        {
            "status": "quarantined_unconstrained_precision",
            "archived_at": created,
            "valid_results": False,
            "publishable": False,
            "resume_allowed": False,
            "reason": (
                "Repair prompts allowed whole-computation FP32/FP64 promotion; "
                "derived size-sweep results inherit this limitation. This is a protocol "
                "limitation, not a finding of intentional misconduct."
            ),
            "campaigns": list(CAMPAIGNS),
            "fresh_inventory": str(OUTPUT),
        },
    )
    (ARCHIVE / "README.md").write_text(
        "# Quarantined — NOT VALID REPAIR RESULTS\n\n"
        "These unconstrained numerical-repair campaigns and their derived LARGE validation "
        "are retained only for provenance and diagnostics. Do not aggregate them into valid "
        "results, restart them, or seed repairs from their repaired implementations.\n\n"
        "Artifacts were moved intact. Their original absolute paths were not rewritten. "
        "No traces were deleted. To inspect an old path, replace its original runs/<campaign> "
        "prefix with this directory's <campaign> prefix.\n"
    )
    for name in CAMPAIGNS:
        shutil.move(str(RUNS / name), str(ARCHIVE / name))
    save(OUTPUT / "archive.json", {"archive": str(ARCHIVE), "campaigns": list(CAMPAIGNS)})
    print(json.dumps(summary, indent=2))
    print(f"Prepared: {OUTPUT}\nQuarantined: {ARCHIVE}")


if __name__ == "__main__":
    main()
