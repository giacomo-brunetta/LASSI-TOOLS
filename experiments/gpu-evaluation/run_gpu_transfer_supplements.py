"""Collect paired timings for separately corrected Jacobi/Wavelet/Lorenz sources."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import run_gpu_transfer_timings as campaign

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs/gpu-transfer-timing-supplements-20261024"
MAIN = ROOT / "runs/gpu-transfer-timing-20261024"


def prepare():
    if (OUT / "plan.json").exists():
        return campaign.read(OUT / "plan.json")
    main = campaign.read(MAIN / "plan.json")
    assets = {digest: deepcopy(main["assets"][digest]) for digest in main["workers"].values()}
    jobs = {}
    sources = [
        ROOT / "runs/shared-baseline-supplements-20261024/jacobi-c3/a100",
        ROOT / "runs/shared-baseline-supplements-20261022/wavelet-c3/a100",
        ROOT / "runs/shared-baseline-supplements-20261022/lorenz-c1/a100",
    ]
    for source in sources:
        prior, results = campaign.read(source / "plan.json"), campaign.read(source / "results.json")
        for original in prior["jobs"].values():
            observed = results.get(original["id"], {})
            observation = observed.get("observation", {})
            if (
                original.get("kind") == "cpu_guard"
                or not observed.get("input_verified")
                or not observed.get("host_source_hash_matches")
                or not observation.get("ok")
                or not observation.get("valid")
                or not observation.get("median_s")
            ):
                continue
            # Accepted supplementary lineages have their own source-bound CPU
            # verification; the old held baseline is never reinstated.
            for digest in original["files"].values():
                item = prior["assets"][digest]
                if campaign.sha(item["source"]) != digest:
                    raise ValueError(f"Supplement asset changed: {item['source']}")
                assets[digest] = deepcopy(item)
            identity = [
                original["source_sha256"],
                original["precision"],
                original["files"]["contract.npz"],
                original["files"]["oracle.npy"],
                main["workers"]["measure_worker.py"],
            ]
            identifier = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
            if identifier in main["jobs"] or identifier in jobs:
                continue
            job = deepcopy(original)
            job.update(
                id=identifier,
                prerequisites=[],
                lineage=[
                    {
                        "kind": "corrected_supplement",
                        "source_plan": str(source / "plan.json"),
                        "original_job_id": original["id"],
                        "evidence": str(source / "observations" / (original["id"] + ".json")),
                    }
                ],
            )
            jobs[identifier] = job
    plan = {
        "endpoint": main["endpoint"],
        "workers": deepcopy(main["workers"]),
        "jobs": jobs,
        "assets": assets,
        "model_calls": 0,
        "scope": "Separately validated corrected Jacobi, Wavelet and Lorenz lineages",
        "main_plan": str(MAIN / "plan.json"),
        "main_plan_sha256": campaign.sha(MAIN / "plan.json"),
        "old_source_holds_released": False,
        "original_campaigns_modified": False,
    }
    campaign.write(OUT / "plan.json", plan)
    return plan


if __name__ == "__main__":
    plan = prepare()
    campaign.OUT = OUT
    campaign.REMOTE = "/tmp/lassi-gpu-transfer-timing-supplements-20261024"
    # Reuse already staged immutable assets, including the paired timing worker.
    campaign.driver.REMOTE = "/tmp/lassi-gpu-transfer-timing-20261024"
    campaign.run()
