"""Remeasure saved LARGE GPU sources with explicit H2D and D2H transfers.

No model calls or changes to candidate algorithms. Existing measurements remain
immutable. The campaign freezes worker code and uses the shared A100 lease.
"""

# Standalone campaign scripts import endpoint SDKs only when running.
# ruff: noqa: PLC0415, E402
from __future__ import annotations

import argparse
import csv
import hashlib
import inspect
import json
import math
import os
import sys
from collections import Counter
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import torch
import yaml

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/experiments/result-validity-audit-20261020"
sys.path.insert(0, str(AUDIT))
import revalidate_corrected_inputs as driver
from baseline_validity import baseline_hold

OUT = ROOT / "runs/gpu-transfer-timing-20261024"
REMOTE = "/tmp/lassi-gpu-transfer-timing-20261024"
ORIGINAL_VERIFY = driver.verify_result


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    driver.write(path, value)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(name):
    path = ROOT / "docs/experiments/input-corrected-agent-repairs-20261021" / name
    return list(csv.DictReader(path.open()))


def prepare():
    if (OUT / "plan.json").exists():
        return read(OUT / "plan.json")
    prior = read(ROOT / "runs/input-corrected-large-20261020/plan.json")
    old_results = read(ROOT / "runs/input-corrected-large-20261020/results.json")
    assets, jobs, exclusions = {}, {}, []
    source_files = {}

    def asset(path):
        path = Path(path)
        digest = sha(path)
        assets[digest] = {"source": str(path), "sha256": digest, "bytes": path.stat().st_size}
        return digest

    def freeze(path, destination):
        path = Path(path)
        digest = sha(path)
        stored = OUT / "assets" / digest
        stored.parent.mkdir(parents=True, exist_ok=True)
        if not stored.exists():
            stored.write_bytes(path.read_bytes())
        if not destination.exists():
            os.link(stored, destination)
        if sha(destination) != digest:
            raise ValueError(f"Frozen asset changed: {destination}")
        return asset(stored)

    # Pin the existing checks, changing only the timing worker in this campaign.
    workers = {}
    for name, digest in prior["workers"].items():
        destination = OUT / "workers" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        content = Path(prior["assets"][digest]["source"]).read_bytes()
        if name == "measure_worker.py":
            source = ROOT / "lassi_x/measure_worker.py"
            source_files[str(source)] = sha(source)
            text = source.read_text()
            needle = 'parser.add_argument("--include-transfers", action="store_true")'
            if text.count(needle) != 1:
                raise ValueError("Cannot configure the frozen transfer worker")
            content = text.replace(needle, needle[:-1] + ", default=True)").encode()
        destination.write_bytes(content)
        workers[name] = asset(destination)

    def add(template, lineage, *, source=None, fixture=None, evidence=None):
        job = deepcopy(template)
        old = old_results.get(template["id"])
        source = Path(source or job["module"])
        expected = lineage.get("source_hash") or job["source_sha256"]
        if sha(source) != expected:
            raise ValueError(f"Accepted source changed: {source}")
        identity = [
            expected,
            job["precision"],
            job["files"]["contract.npz"],
            job["files"]["oracle.npy"],
            workers["measure_worker.py"],
        ]
        identifier = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
        alias = {**lineage, "evidence": str(evidence or ""), "original_job_id": template["id"]}
        if identifier in jobs:
            jobs[identifier]["lineage"].append(alias)
            return
        folder = OUT / "sources" / identifier
        folder.mkdir(parents=True, exist_ok=True)
        files = {}
        for name, digest in job["files"].items():
            path = Path(prior["assets"][digest]["source"])
            if name == "candidate.py":
                path = source
            destination = folder / name
            # A byte copy isolates the new campaign from later workspace edits.
            files[name] = freeze(path, destination)
        if fixture:
            destination = folder / "c-inputs.npz"
            files["c-inputs.npz"] = freeze(fixture, destination)
        job.update(
            id=identifier,
            module=str(folder / "candidate.py"),
            source_sha256=expected,
            files=files,
            lineage=[alias],
            prerequisites=[],
            original_resident_s=(old or {}).get("observation", {}).get("median_s"),
        )
        jobs[identifier] = job

    # Current source/ancestor holds are applied again before selecting old jobs.
    by_record = {b["baseline_record"]: b for b in prior["baselines"]}
    base_rows = rows("shared-baseline-validity.csv")
    valid_bases = {}
    for row in base_rows:
        hold = baseline_hold(row)
        if hold or row["classification"] == "semantic_or_resource_failure":
            exclusions.append({"row": row, "reason": hold or row["classification"]})
            continue
        baseline = by_record[row["old_record"]]
        valid_bases[row["old_record"]] = baseline
        for job_id in baseline["jobs"].values():
            job, result = prior["jobs"][job_id], old_results[job_id]
            observation = result.get("observation", {})
            if (
                job.get("kind") == "cpu_guard"
                or not result.get("input_verified")
                or not result.get("host_source_hash_matches")
                or not observation.get("valid")
                or not observation.get("median_s")
            ):
                continue
            add(
                job,
                {
                    "kind": "baseline_or_control",
                    "model": "terra",
                    "kernel": row["kernel"],
                    "candidate": row["candidate"],
                    "baseline_record": row["old_record"],
                },
                evidence=ROOT
                / "runs/input-corrected-large-20261020/observations"
                / (job_id + ".json"),
            )
    for row in rows("inherited-repair-validity.csv"):
        if row["validity_disposition"] != "keep_new_measurement" or baseline_hold(row):
            continue
        job = prior["jobs"][row["target_job"]]
        result = old_results[job["id"]]
        if (
            result.get("input_verified")
            and result.get("host_source_hash_matches")
            and result["observation"].get("valid")
        ):
            add(
                job,
                {**row, "kind": "retained_repair"},
                evidence=ROOT
                / "runs/input-corrected-large-20261020/observations"
                / (job["id"] + ".json"),
            )

    arms = {a["record"]: a["baseline_record"] for a in prior["arms"]}
    for row in rows("agent-results.csv"):
        if row["disposition"] not in {"full_recovery", "partial_improvement"} or baseline_hold(row):
            continue
        if row["target_input_verified"] != "True" or row["target_precision_eligible"] != "True":
            continue
        baseline_record = arms.get(row["original_record"], row["original_record"])
        baseline = valid_bases.get(baseline_record)
        if baseline is None:
            exclusions.append({"row": row, "reason": "baseline_not_eligible"})
            continue
        job = prior["jobs"][baseline["jobs"][row["precision"]]]
        cfg = yaml.safe_load((Path(row["record"]).parent / "config.yaml").read_text())
        add(
            job,
            {**row, "kind": "current_agent_repair"},
            source=row["effective_measured_source"],
            fixture=cfg["oracle"]["input_fixture"],
            evidence=row["record"],
        )

    # Tag matching FP16 accelerator sources so the comparison set runs first.
    ports = read(ROOT / "runs/graphcore-sol-porting-20261023/plan.json")["entries"]
    for entry in ports:
        matches = [
            j
            for j in jobs.values()
            if j["source_sha256"] == entry["source_sha256"] and j["precision"] == "fp16"
        ]
        for job in matches:
            job.setdefault("accelerator_case_ids", []).append(entry["id"])
        if not matches:
            exclusions.append(
                {
                    "accelerator_case_id": entry["id"],
                    "source": entry["source"],
                    "reason": "requires_supplement_source_intake",
                }
            )
    six = {
        e["id"]
        for e in read(ROOT / "runs/cerebras-latency-audit-20261024/manifest.json")["entries"]
    }
    jobs = dict(
        sorted(
            jobs.items(),
            key=lambda item: (
                not bool(six.intersection(item[1].get("accelerator_case_ids", []))),
                not bool(item[1].get("accelerator_case_ids")),
                item[1]["precision"] != "fp16",
                item[1]["kernel"],
                item[0],
            ),
        )
    )
    plan = {
        "created_at": datetime.now(UTC).isoformat(),
        "endpoint": prior["endpoint"],
        "scope": (
            "Eligible saved LARGE baselines/controls and retained/current repairs; "
            "source holds applied"
        ),
        "model_calls": 0,
        "dataset": "large",
        "assets": assets,
        "workers": workers,
        "jobs": jobs,
        "exclusions": exclusions,
        "source_files": source_files,
        "worker_configuration": "Frozen measure_worker.py defaults --include-transfers to true",
        "protocol": (
            "Paired resident CUDA graph events and pinned-host "
            "H2D/replay/D2H synchronized wall time"
        ),
        "original_campaigns_modified": False,
    }
    write(OUT / "plan.json", plan)
    return plan


def validate_transfer_result(job, result):
    result = ORIGINAL_VERIFY(job, result)
    observation = result["observation"]
    result["transfer_timing_verified"] = False
    if not observation.get("ok"):
        return result
    metrics = observation.get("timings", {})
    resident, host = metrics.get("resident_execution", {}), metrics.get("host_to_host", {})
    samples = host.get("samples_s", [])
    valid = (
        host.get("kind") == "measured"
        and host.get("scope") == "host_to_host"
        and host.get("invocations_per_sample") == 1
        and host.get("host_memory") == "pinned"
        and host.get("input_residency") == host.get("output_residency_at_stop") == "host"
        and len(samples) == host.get("sample_count") == job["iterations"]
        and all(math.isfinite(v) and v > 0 for v in samples)
        and host.get("output_matches_resident") is True
        and host.get("output_sha256")
        == resident.get("output_sha256")
        == observation.get("evaluation_output", {}).get("sha256")
        and result["input_verified"]
        and result["host_source_hash_matches"]
    )
    if not valid:
        raise ValueError(f"Transfer timing evidence failed: {job['id']}")
    result["transfer_timing_verified"] = True
    return result


def extend_plan():
    """Add independently validated sources outside the corrected-input batch."""
    plan = prepare()
    if plan.get("supplement_intake_completed"):
        return plan
    original_plan_hash = sha(OUT / "plan.json")
    additions, skipped = [], []

    def asset(path):
        path = Path(path)
        digest = sha(path)
        stored = OUT / "assets" / digest
        if not stored.exists():
            stored.write_bytes(path.read_bytes())
        plan["assets"][digest] = {
            "source": str(stored),
            "sha256": digest,
            "bytes": stored.stat().st_size,
        }
        return digest

    def add(
        source,
        expected,
        precision,
        kernel,
        candidate,
        config,
        contract,
        oracle,
        evidence,
        lineage,
        fixture=None,
        case_id=None,
    ):
        source = Path(source)
        if sha(source) != expected:
            raise ValueError(f"Supplement source changed: {source}")
        identity = [
            expected,
            precision,
            sha(contract),
            sha(oracle),
            plan["workers"]["measure_worker.py"],
        ]
        identifier = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
        if identifier in plan["jobs"]:
            if case_id:
                plan["jobs"][identifier].setdefault("accelerator_case_ids", []).append(case_id)
            return
        folder = OUT / "sources" / identifier
        folder.mkdir(parents=True, exist_ok=True)
        module = driver.load(source)
        torch.manual_seed(0)
        keywords = {"device": "cpu", "dtype": torch.float64}
        parameters = inspect.signature(module.build_inputs).parameters
        if "dataset" in parameters:
            keywords["dataset"] = "large"
        if fixture and "fixture" in parameters:
            keywords["fixture"] = Path(fixture)
        inputs = module.build_inputs(**keywords)
        model = module.make_model()
        names = list(inspect.signature(model.forward).parameters)
        schema, arrays = [], {}
        for index, value in enumerate(inputs):
            name = names[index] if index < len(names) else f"#{index}"
            if not isinstance(value, torch.Tensor):
                raise ValueError("Supplement requires a tensor-only CUDA graph interface")
            arrays[name] = value.detach().double().cpu().numpy()
            schema.append(
                {
                    "argument": name,
                    "kind": "tensor",
                    "shape": list(value.shape),
                    "stride": list(value.stride()),
                    "integer_dtype": str(value.dtype).removeprefix("torch.")
                    if not value.is_floating_point()
                    else None,
                }
            )
        np.savez(folder / "inputs.npz", **arrays)
        write(folder / "input-schema.json", schema)
        files = {
            "input-schema.json": asset(folder / "input-schema.json"),
            "inputs.npz": asset(folder / "inputs.npz"),
        }
        for name, path in {
            "candidate.py": source,
            "contract.npz": contract,
            "oracle.npy": oracle,
            **({"c-inputs.npz": fixture} if fixture else {}),
        }.items():
            files[name] = asset(path)
            destination = folder / name
            if not destination.exists():
                os.link(plan["assets"][files[name]]["source"], destination)
        cfg = yaml.safe_load(Path(config).read_text())
        bindings = cfg.get("arena", {}).get("input_check", {}).get(
            "bindings", {}
        ) or driver.bindings(kernel)
        job = {
            "id": identifier,
            "kernel": kernel,
            "precision": precision,
            "source_sha256": expected,
            "module": str(folder / "candidate.py"),
            "config": str(config),
            "oracle": str(oracle),
            "files": files,
            "bindings": bindings,
            "base": None,
            "timeout_s": 900,
            "memory_limit_mb": 8192,
            "warmup": 3,
            "iterations": 20,
            "rtol": 1e-10,
            "atol": 1e-12,
            "invariant": None,
            "invariant_threshold": None,
            "prerequisites": [],
            "lineage": [
                {**lineage, "kernel": kernel, "candidate": candidate, "evidence": str(evidence)}
            ],
        }
        if case_id:
            job["accelerator_case_ids"] = [case_id]
        plan["jobs"][identifier] = job
        additions.append(identifier)

    manifest = read(AUDIT / "manifest.json")["records"]
    claims = list(
        csv.DictReader(
            (
                ROOT
                / "docs/experiments/input-corrected-large-20261020/previously-correct-claims.csv"
            ).open()
        )
    )
    for row in claims:
        if row["disposition"] != "keep_cuda_input_verified":
            continue
        lineage = {**row, "old_record": row["record"], "source": row["input_source"]}
        if baseline_hold(lineage):
            skipped.append({"source": row["source"], "reason": "current_source_or_ancestor_hold"})
            continue
        entry = next(x for x in manifest if x["record"] == row["record"])
        record = read(row["record"])
        points = record.get(
            "measurements", record.get("variant", {}).get("target_measurements", [])
        )
        cfg = yaml.safe_load(Path(entry["config"]).read_text())
        oracle = cfg["oracle"].get("output")
        if not oracle or not Path(oracle).is_file():
            # The baseline record lives beside its authoritative C output.
            baseline_record = Path(record.get("baseline_record", row["record"]))
            oracle = baseline_record.parent / "oracle/reference.npy"
        if not Path(oracle).is_file():
            raise ValueError(f"Missing C oracle for {row['record']}")
        for point in points:
            if (
                point.get("status") != "ok"
                or not point.get("latency_s")
                or point.get("source_hash") != row["source_sha256"]
                or not point.get("evaluation_output_finite")
                or point["precision"]
                not in (
                    {row["precision"]}
                    if row["kind"] == "repair"
                    else {"fp64", "fp32", row["precision"]}
                )
            ):
                continue
            add(
                row["source"],
                row["source_sha256"],
                point["precision"],
                row["kernel"],
                row["candidate"],
                entry["config"],
                row["contract"],
                oracle,
                row["record"],
                {**row, "kind": "previously_input_verified"},
                fixture=cfg["oracle"].get("input_fixture"),
            )

    for entry in read(ROOT / "runs/graphcore-sol-porting-20261023/plan.json")["entries"]:
        if entry["origin"] != "SOL_diversity_baseline":
            continue
        record = read(entry["evidence"])
        for point in record.get("measurements", []):
            if point.get("status") != "ok" or not point.get("latency_s"):
                continue
            add(
                entry["source"],
                entry["source_sha256"],
                point["precision"],
                entry["kernel"],
                entry["candidate"],
                entry["config"],
                entry["contract"],
                entry["oracle"],
                entry["evidence"],
                {
                    "kind": "validated_SOL_diversity",
                    "model": "sol",
                    "lineage_row": entry["lineage_row"],
                },
                fixture=entry["fixture"],
                case_id=entry["id"] if point["precision"] == "fp16" else None,
            )
    plan["supplement_intake_completed"] = True
    plan["supplement_intake"] = {
        "previous_plan_sha256": original_plan_hash,
        "added_jobs": additions,
        "skipped": skipped,
        "updated_at": datetime.now(UTC).isoformat(),
    }
    covered = {c for j in plan["jobs"].values() for c in j.get("accelerator_case_ids", [])}
    plan["exclusions"] = [
        e for e in plan["exclusions"] if e.get("accelerator_case_id") not in covered
    ]
    write(OUT / "plan-before-supplements.json", read(OUT / "plan.json"))
    write(OUT / "plan.json", plan)
    return plan


def report(output, results, final=False):
    plan = read(output / "plan.json")
    table = []
    for identifier, result in results.items():
        job = plan["jobs"][identifier]
        obs = result.get("observation", {})
        host = obs.get("timings", {}).get("host_to_host", {})
        table.append(
            {
                "job_id": identifier,
                "kernel": job["kernel"],
                "precision": job["precision"],
                "source_sha256": job["source_sha256"],
                "accelerator_case_ids": ";".join(job.get("accelerator_case_ids", [])),
                "verified": result.get("transfer_timing_verified", False),
                "valid": obs.get("valid", False),
                "relative_l2": obs.get("metrics", {}).get("relative_l2"),
                "resident_s": obs.get("median_s"),
                "host_to_host_s": host.get("median_s"),
                "input_bytes": host.get("input_bytes"),
                "output_bytes": host.get("output_bytes"),
                "phase": obs.get("phase", "completed"),
            }
        )
    if table:
        with (output / "timings.csv").open("w") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(table[0]))
            writer.writeheader()
            writer.writerows(table)
    write(
        output / "summary.json",
        {
            "updated_at": datetime.now(UTC).isoformat(),
            "completed": len(results),
            "total": len(plan["jobs"]),
            "final": final,
            "transfer_timing_verified": sum(
                r.get("transfer_timing_verified", False) for r in results.values()
            ),
            "precisions": dict(Counter(j["precision"] for j in plan["jobs"].values())),
            "applications": len({j["kernel"] for j in plan["jobs"].values()}),
            "model_calls": 0,
        },
    )


def reuse_assets(payload):
    import hashlib
    import os
    from pathlib import Path

    root, cache = Path(payload["root"]), Path(payload["cache"])
    root.mkdir(parents=True, exist_ok=True)
    reused = 0
    for digest in payload["assets"]:
        source, destination = cache / digest, root / digest
        if destination.exists() or not source.is_file():
            continue
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError("Cached asset hash mismatch")
        os.link(source, destination)
        reused += 1
    return {"reused_assets": reused}


def run(limit=None):
    from globus_compute_sdk import Client, Executor
    from globus_compute_sdk.serialize import ComputeSerializer, DillCodeSource

    plan = prepare()
    # Host-side controller ownership prevents two accidental launches.
    import fcntl

    lock = (OUT / "controller.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    client = Client()
    executor = Executor(
        endpoint_id=plan["endpoint"],
        client=client,
        serializer=ComputeSerializer(strategy_code=DillCodeSource()),
    )
    try:
        future = executor.submit(
            reuse_assets, {"root": REMOTE, "cache": driver.REMOTE, "assets": list(plan["assets"])}
        )
        write(OUT / "asset-reuse-task.json", {"task_id": str(future.task_id)})
        write(OUT / "asset-reuse.json", future.result(timeout=120))
    finally:
        executor.shutdown(wait=False)
    driver.OUT, driver.REMOTE = OUT, REMOTE
    driver.verify_result = validate_transfer_result
    try:
        return driver.run(limit=limit, report_callback=report)
    finally:
        driver.verify_result = ORIGINAL_VERIFY
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--extend", action="store_true")
    args = parser.parse_args()
    if args.prepare or args.extend:
        plan = extend_plan() if args.extend else prepare()
        print(
            json.dumps(
                {
                    "jobs": len(plan["jobs"]),
                    "assets": len(plan["assets"]),
                    "applications": len({j["kernel"] for j in plan["jobs"].values()}),
                    "exclusions": len(plan["exclusions"]),
                }
            )
        )
    else:
        run(args.limit)
