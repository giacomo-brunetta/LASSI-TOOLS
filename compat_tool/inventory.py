"""Build a pruned, fixture-validated operator probe manifest."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

import yaml

from compat_tool.fixtures import canonical_recipe, validate_recipe
from compat_tool.io import atomic_json, stable_hash
from compat_tool.parser import parse_torch_ops

GENERATED_OP_PATHS = (
    Path("include/torch-mlir/Dialect/Torch/IR/GeneratedTorchOps.td"),
    Path("include/torch-mlir/Dialect/Torch/IR/TorchOps.td"),
)
DEFAULT_PRECISIONS = ("fp64", "fp32", "fp16", "bf16")


def _git_revision(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


def resolve_ops_file(root: Path) -> Path:
    for relative in GENERATED_OP_PATHS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    expected = ", ".join(str(root / item) for item in GENERATED_OP_PATHS)
    raise FileNotFoundError(f"No generated Torch-MLIR op file found; checked {expected}")


def load_pruning(path: Path | None) -> dict[str, dict[str, str]]:
    if path is None:
        return {"include": {}, "exclude": {}}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    include = payload.get("include") or {}
    exclude = payload.get("exclude") or {}
    if not isinstance(include, dict) or not isinstance(exclude, dict):
        raise ValueError("pruning include/exclude entries must be mappings of op name to reason")
    overlap = set(include) & set(exclude)
    if overlap:
        raise ValueError(
            "operators cannot be both included and excluded: " + ", ".join(sorted(overlap))
        )
    if any(not str(reason).strip() for reason in [*include.values(), *exclude.values()]):
        raise ValueError("every pruning override requires a non-empty reason")
    return {"include": dict(include), "exclude": dict(exclude)}


def _has_tensor(entries: list[dict[str, str]]) -> bool:
    return any("tensor" in item.get("type", "").lower() for item in entries)


def eligibility(
    op_name: str,
    meta: dict[str, Any],
    pruning: dict[str, dict[str, str]],
) -> tuple[bool, str | None]:
    if op_name in pruning["exclude"]:
        return False, f"explicit exclude: {pruning['exclude'][op_name]}"
    if not op_name.startswith("aten."):
        return False, "not an ATen operator"
    if "backward" in op_name.lower():
        return False, "backward operator"
    if not _has_tensor(meta.get("args", [])):
        return False, "no tensor input"
    if not _has_tensor(meta.get("returns", [])):
        return False, "no tensor output"
    base = op_name.split(".", maxsplit=2)[1]
    overload = op_name.rsplit(".", maxsplit=1)[-1] if op_name.count(".") > 1 else ""
    mutation_or_out = base.endswith("_") or overload == "out" or overload.endswith("_out")
    if mutation_or_out and op_name not in pruning["include"]:
        return False, "in-place or explicit out overload"
    return True, None


def build_manifest(
    ops: dict[str, dict[str, Any]],
    *,
    source: dict[str, Any],
    pruning: dict[str, dict[str, str]],
    precisions: list[str],
    selected_ops: set[str] | None = None,
) -> dict[str, Any]:
    records: dict[str, Any] = {}
    for op_name, meta in sorted(ops.items()):
        if selected_ops is not None and op_name not in selected_ops:
            continue
        included, reason = eligibility(op_name, meta, pruning)
        record: dict[str, Any] = {
            "metadata": meta,
            "included": included,
            "exclusion_reason": reason,
            "cases": {},
        }
        if included:
            for precision in precisions:
                recipe = canonical_recipe(op_name, precision)
                validation = validate_recipe(op_name, meta, recipe)
                record["cases"][precision] = {
                    "canonical": {"recipe": recipe, "validation": validation}
                }
        records[op_name] = record

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "kind": "compatibility-probe-manifest",
        "source": source,
        "precisions": precisions,
        "pruning": pruning,
        "operators": records,
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    manifest["summary"] = {
        "operators": len(records),
        "included": sum(bool(record["included"]) for record in records.values()),
        "excluded": sum(not bool(record["included"]) for record in records.values()),
        "needs_fixture": sum(
            case["validation"]["status"] == "needs_fixture"
            for record in records.values()
            for cases in record["cases"].values()
            for case in cases.values()
        ),
        "not_applicable": sum(
            case["validation"]["status"] == "not_applicable"
            for record in records.values()
            for cases in record["cases"].values()
            for case in cases.values()
        ),
    }
    return manifest


def prepare_from_checkout(
    root: Path,
    revision: str,
    output: Path,
    *,
    pruning_path: Path | None = None,
    precisions: list[str] | None = None,
    selected_ops: set[str] | None = None,
) -> dict[str, Any]:
    actual = _git_revision(root)
    if actual != revision:
        raise ValueError(f"Torch-MLIR checkout is {actual}, expected exact revision {revision}")
    ops_path = resolve_ops_file(root)
    ops = parse_torch_ops(str(ops_path), output_path=None)
    source = {
        "project": "llvm/torch-mlir",
        "revision": actual,
        "ops_file": str(ops_path.relative_to(root)),
        "ops_file_hash": hashlib.sha256(ops_path.read_bytes()).hexdigest(),
    }
    manifest = build_manifest(
        ops,
        source=source,
        pruning=load_pruning(pruning_path),
        precisions=precisions or list(DEFAULT_PRECISIONS),
        selected_ops=selected_ops,
    )
    atomic_json(output, manifest)
    return manifest
