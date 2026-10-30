"""Freeze every FP16 full recovery in the paper inventory, preserving prior checks.

Reads evidence and Python ASTs only; never imports candidate modules or calls models.
The numerical evaluator and its frozen case policy are unchanged.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import shutil
from pathlib import Path

import yaml

from lassi_x.holdout import HARNESS_FILES, input_values, sha, write
from lassi_x.input_contract import compare_input_arrays, load_contract

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "docs/experiments/result-validity-audit-20261020"
CORRECTED = ROOT / "runs/input-corrected-large-20261020"


def read(path):
    return json.loads(Path(path).read_text())


def forward_arguments(path):
    tree = ast.parse(path.read_text())
    forwards = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "forward"]
    if len(forwards) != 1:
        raise ValueError(f"Review ambiguous forward signature: {path}")
    args = forwards[0].args
    if args.vararg or args.kwarg or args.kwonlyargs:
        raise ValueError(f"Review variadic forward signature: {path}")
    return [a.arg for a in (*args.posonlyargs, *args.args) if a.arg != "self"]


def validate_schema(schema):
    names = [s["argument"] for s in schema]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate input arguments")
    for s in schema:
        if s["kind"] == "tensor":
            if "stride" not in s or len(s["shape"]) != len(s["stride"]):
                raise ValueError(f"Missing or inconsistent tensor layout: {s['argument']}")
            if "integer_dtype" not in s:
                raise ValueError(f"Missing tensor dtype policy: {s['argument']}")


def prepare(paper, previous, output, reuse_completed=()):
    if output.exists():
        raise ValueError("A freeze cannot be overwritten")
    inventory_path = paper / "tables/numerical-repair.csv"
    rows = [
        r
        for r in csv.DictReader(inventory_path.open())
        if r["precision"] == "fp16" and r["outcome"] == "full_recovery"
    ]
    keys = [(r["model"], r["kernel"], r["candidate"]) for r in rows]
    if len(keys) != len(set(keys)) or not rows:
        raise ValueError("Empty or duplicate paper cohort")
    old_manifest = read(previous / "manifest.json")
    for name, digest in old_manifest["files"].items():
        if sha(previous / name) != digest:
            raise ValueError(f"Previous freeze changed: {name}")
    plan = read(CORRECTED / "plan.json")
    audit = read(AUDIT / "manifest.json")["records"]
    audited_inputs = read(AUDIT / "input-results.json")
    coverage, targets = [], []
    output.mkdir(parents=True)
    shutil.copy2(inventory_path, output / "paper-inventory.csv")
    shutil.copy2(
        paper / "tables/numerical-repair-provenance.json", output / "paper-provenance.json"
    )
    shutil.copy2(previous / "policy.json", output / "policy.json")
    for r in rows:
        source = ROOT / r["module"]
        if sha(source) != r["source_sha256"]:
            raise ValueError(f"Paper source changed: {source}")
        relative = Path(r["model"]) / r["kernel"] / f"{r['candidate']}-fp16"
        target_name = str(relative / "target.json")
        entry = {**r, "target": target_name}
        old_source = previous / relative / "repaired.py"
        if target_name in old_manifest["targets"] and sha(old_source) == r["source_sha256"]:
            entry.update(disposition="reuse_unchanged_frozen_target", prior_freeze=str(previous))
            coverage.append(entry)
            continue

        record = ROOT / r["record"]
        if r["selection"] == "retained_source_bound_remeasurement":
            arms = [
                a
                for a in plan["arms"]
                if a["model"] == r["model"]
                and a["kernel"] == r["kernel"]
                and a["candidate"] == r["candidate"]
                and a["precision"] == "fp16"
                and Path(a["corrected_module"]) == source
            ]
            if len(arms) != 1:
                raise ValueError(f"No unique corrected source binding: {relative}")
            job = plan["jobs"][arms[0]["jobs"]["cpu_guard"]]
            baseline = Path(job["base"])
            config_path = Path(job["config"])
            contract = source.parent / "contract.npz"
            schema_path = source.parent / "input-schema.json"
            for name, path in (
                ("candidate.py", source),
                ("baseline.py", baseline),
                ("contract.npz", contract),
                ("input-schema.json", schema_path),
            ):
                if sha(path) != job["files"][name]:
                    raise ValueError(f"Corrected job artifact changed: {path}")
            schema = read(schema_path)
            bindings = job["bindings"]
        elif r["selection"] == "retained_input_audited_original":
            records = [
                a
                for a in audit
                if a["kind"] == "repair"
                and a["model"] == r["model"]
                and a["kernel"] == r["kernel"]
                and a["candidate"] == r["candidate"]
                and a["precision"] == "fp16"
                and a["expected_hash"] == r["source_sha256"]
            ]
            if len(records) != 1:
                raise ValueError(f"No unique original input audit: {relative}")
            a = records[0]
            checked = audited_inputs[a["id"]]
            if checked["status"] != "pass" or checked["source_sha256"] != sha(source):
                raise ValueError(f"Original inputs not verified: {relative}")
            baseline = Path(a["input_source"])
            if sha(baseline) != a["input_expected_hash"]:
                raise ValueError(f"Original baseline changed: {baseline}")
            config_path, contract = Path(a["config"]), Path(checked["contract"])
            # The audit supplies the exact ordered tensor names/shapes; verify
            # signatures statically instead of executing either input builder.
            schema = [
                {
                    "argument": c["argument"],
                    "kind": "tensor",
                    "shape": c["shape"],
                    "integer_dtype": None,
                }
                for c in checked["report"]["checked"]
            ]
            # Construct canonical row-major tensors explicitly for the
            # evaluator's empty_strided input reconstruction.
            for s in schema:
                stride, product = [], 1
                for size in reversed(s["shape"]):
                    stride.insert(0, product)
                    product *= size
                s["stride"] = stride
            names = [s["argument"] for s in schema]
            if names != forward_arguments(source) or names != forward_arguments(baseline):
                raise ValueError(f"Input signature requires review: {relative}")
            bindings = {}
        else:
            raise ValueError(f"Missing previous result or unsupported selection: {relative}")

        validate_schema(schema)
        config = yaml.safe_load(config_path.read_text())
        arrays, metadata = load_contract(contract)
        if metadata["kernel"] != r["kernel"] or metadata["dataset"] != "large":
            raise ValueError("Contract does not match the paper workload")
        target = {
            **{k: r[k] for k in ("model", "kernel", "candidate", "precision")},
            "bindings": bindings,
            "scalar_shapes": {s["argument"]: s["shape"] for s in schema},
        }
        values = input_values(arrays, schema, target)
        parity = compare_input_arrays(
            dict(zip([s["argument"] for s in schema], values, strict=True)),
            arrays,
            metadata,
            bindings=bindings,
        )
        if not parity["ok"]:
            raise ValueError(f"Trusted input mapping failed: {parity}")
        folder = output / relative
        folder.mkdir(parents=True)
        for name, path in (
            ("baseline.py", baseline),
            ("repaired.py", source),
            ("contract.npz", contract),
        ):
            shutil.copy2(path, folder / name)
        write(folder / "schema.json", schema)
        reference = Path(config["kernel"]["reference"])
        if metadata["source_sha256"] != sha(reference):
            raise ValueError("C reference differs from the contract")
        dependencies = {reference, *reference.parent.glob("*.h")}
        dependencies.update(Path(p) for p in config["kernel"].get("context", []))
        for token in config["oracle"]["build"]:
            if Path(token).is_file():
                dependencies.add(Path(token).resolve())
            if token.startswith("-I"):
                dependencies.update(Path(token[2:]).glob("*.h"))
        files = {}
        for dep in sorted(dependencies):
            parent = hashlib.sha256(str(dep.parent).encode()).hexdigest()[:12]
            dest = folder / "references" / parent / dep.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dep, dest)
            files[str(dep.resolve())] = str(dest.relative_to(folder))
        target.update(
            record=str(record),
            record_sha256=sha(record),
            disposition="selected",
            paper_selection=r["selection"],
            source_sha256=sha(source),
            baseline_sha256=sha(baseline),
            config_sha256=sha(config_path),
            dataset="large",
            reference=str(reference),
            build=config["oracle"]["build"],
            project=str(ROOT),
            capture=config["oracle"]["capture"],
            format=config["oracle"]["format"],
            timeout_s=config["oracle"].get("timeout_s", 3600),
            dependencies={str(p.resolve()): sha(p) for p in dependencies},
            dependency_files=files,
        )
        write(folder / "target.json", target)
        targets.append(target_name)
        entry.update(disposition="new_evaluation", baseline_sha256=sha(baseline))
        coverage.append(entry)
    # Reuse both passes and failures when every frozen target artifact matches.
    # Changed historical layouts necessarily fail this equality check.
    for results in reuse_completed:
        prior = Path(read(results / "status.json")["freeze"])
        prior_manifest = read(prior / "manifest.json")
        if prior_manifest["harness_sha256"] != old_manifest["harness_sha256"]:
            raise ValueError("Cannot reuse a different evaluator")
        if sha(prior / "policy.json") != sha(output / "policy.json"):
            raise ValueError("Cannot reuse a different case policy")
        for name, digest in prior_manifest["files"].items():
            if sha(prior / name) != digest:
                raise ValueError(f"Reuse freeze changed: {name}")
        completed = read(results / "results.json")
        for entry in coverage:
            name = entry["target"]
            data = completed.get(name)
            if entry["disposition"] != "new_evaluation" or not data or "summary" not in data:
                continue
            if data["summary"]["manifest_sha256"] != sha(prior / "manifest.json"):
                raise ValueError("Cannot reuse a summary with another manifest")
            folder = output / Path(name).parent
            files = {
                str(p.relative_to(folder)): sha(p)
                for p in folder.rglob("*")
                if p.is_file() and p.name != "target.json"
            }
            old_folder = prior / Path(name).parent
            old_files = {
                str(p.relative_to(old_folder)): sha(p)
                for p in old_folder.rglob("*")
                if p.is_file() and p.name != "target.json"
            }
            if files == old_files and read(folder / "target.json") == read(
                old_folder / "target.json"
            ):
                entry.update(
                    disposition="reuse_unchanged_frozen_target",
                    prior_freeze=str(prior),
                    prior_results=str(results.resolve()),
                )
                targets.remove(name)
    hashes = {}
    for name in HARNESS_FILES:
        path = ROOT / "lassi_x" / name
        if sha(path) != old_manifest["harness_sha256"][name]:
            raise ValueError(f"Numerical evaluator changed since first cohort: {name}")
        dest = output / "harness" / name
        dest.parent.mkdir(exist_ok=True)
        shutil.copy2(path, dest)
        hashes[name] = sha(path)
    write(output / "coverage.json", coverage)
    write(
        output / "manifest.json",
        {
            "protocol": old_manifest["protocol"],
            "status": "prepared_not_evaluated",
            "scope": "All paper-eligible full FP16 recoveries; earlier exact frozen targets reused",
            "paper_inventory_sha256": sha(inventory_path),
            "harness_sha256": hashes,
            "prior_manifest_sha256": sha(previous / "manifest.json"),
            "targets": targets,
            "files": {
                str(p.relative_to(output)): sha(p) for p in sorted(output.rglob("*")) if p.is_file()
            },
        },
    )
    print(
        json.dumps(
            {
                "full_fp16_cohort": len(coverage),
                "new_targets": len(targets),
                "reused_targets": len(coverage) - len(targets),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-completed", type=Path, action="append", default=[])
    args = parser.parse_args()
    prepare(
        args.paper.resolve(),
        args.previous.resolve(),
        args.output.resolve(),
        [p.resolve() for p in args.reuse_completed],
    )
