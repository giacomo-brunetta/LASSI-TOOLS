"""Classify unsupported ops in the generated compatibility database."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from compat_tool.utils import DEFAULT_ALL_OPS_PATH, DEFAULT_DB_PATH, DATA_DIR, save_json


OUTPUT_JSON_PATH = DATA_DIR / "unsupported_analysis.json"
OUTPUT_MARKDOWN_PATH = DATA_DIR / "unsupported_summary.md"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _base_name(op_name: str) -> str:
    parts = op_name.split(".")
    return ".".join(parts[:2]) if len(parts) > 2 else op_name


def _supported_siblings(op_name: str, supported_ops: set[str]) -> list[str]:
    base_name = _base_name(op_name)
    return sorted(op for op in supported_ops if op != op_name and _base_name(op) == base_name)


def _has_tensor(entries: list[dict[str, str]]) -> bool:
    return any("Tensor" in entry["type"] for entry in entries)


def classify_op(
    op_name: str,
    info: dict[str, Any],
    op_meta: dict[str, Any],
    supported_ops: set[str],
) -> dict[str, Any]:
    """Classify one unsupported op into a likely failure cause."""
    error = info.get("error") or ""
    error_lower = error.lower()
    siblings = _supported_siblings(op_name, supported_ops)
    args = op_meta.get("args", [])
    returns = op_meta.get("returns", [])

    category = "manual_review"
    summary = "Needs manual inspection."
    suggestion = "Inspect the error and run a targeted reproducer for this op."

    if (
        "failed to legalize operation" in error_lower
        or "unsupported by backend lowering" in error_lower
        or "lowering torch backend ir -> tosa backend ir failed" in error_lower
        or "tosa." in error_lower
    ):
        category = "backend_lowering_missing"
        if siblings:
            summary = "The op traced successfully, but this overload or variant does not lower to TOSA."
        else:
            summary = "The op traced successfully, but torch-mlir/TOSA lowering is missing."
        suggestion = "Treat this as a real lowering gap, not a float32/harness issue."
    elif "missing value for argument" in error_lower:
        category = "harness_missing_arguments"
        if siblings:
            summary = "The generated test omitted required arguments for this overload."
        else:
            summary = "The generated test omitted required arguments."
        suggestion = "Add overload-specific example inputs rather than marking this op unsupported."
    elif "cannot be traced" in error_lower or "can be output from traced functions" in error_lower:
        category = "harness_tracing_limitation"
        summary = "The test hit a tracing limitation due to non-tensor inputs or outputs."
        suggestion = "Use scripting, wrapper modules, or structured tensor-only adapters for this op."
    elif (
        "expected a value of type" in error_lower
        or "cannot be converted to scalar" in error_lower
        or "boolean value of tensor" in error_lower
        or "not implemented for '" in error_lower
        or "must be a 3d tensor" in error_lower
        or "must be batches of square matrices" in error_lower
        or "last dimension of size 2" in error_lower
        or "only supported for complex tensors" in error_lower
        or "imag is not implemented for tensors with non-complex dtypes" in error_lower
        or "one_hot is only applicable to index tensor" in error_lower
        or "expected p_in >=" in error_lower
        or "halving dimension must be even" in error_lower
        or "weight should have at least three dimensions" in error_lower
        or "expected 3d (unbatched) or 4d (batched) input to conv2d" in error_lower
        or "expected 4d (unbatched) or 5d (batched) input to conv3d" in error_lower
        or "not linked with support for cuda devices" in error_lower
    ):
        category = "harness_wrong_inputs_or_dtype"
        if siblings:
            summary = "The harness chose the wrong input kind, shape, device, or dtype for this overload, and a sibling overload is supported."
        else:
            summary = "The harness chose the wrong input kind, shape, device, or dtype for this op."
        suggestion = "Do not treat this as a real TOSA gap until the op is retried with schema-appropriate inputs."
    elif (
        "backend illegal" in error_lower
        or "unsupported by backend contract" in error_lower
        or "decomposecomplexops" in error_lower
        or "maximizevaluesemantics" in error_lower
        or "unknown rank" in error_lower
        or "non-value tensor type" in error_lower
    ):
        category = "torch_mlir_frontend_or_value_semantics_limit"
        summary = "The failure happened before TOSA lowering in TorchScript/Torch backend conversion or value-semantics legalization."
        suggestion = "Treat this as a torch-mlir frontend/backend-contract limitation, not as a confirmed TOSA lowering result."
    elif op_name.startswith(("aten.__", "aten.Bool", "aten.Int", "aten.Float", "aten.ScalarImplicit", "aten.Delete", "aten.format", "aten.get.")):
        category = "language_or_runtime_helper"
        summary = "This is a language/runtime helper op rather than a natural tensor compute op for TOSA."
        suggestion = "Track separately from tensor compute coverage."
    elif returns and not _has_tensor(returns):
        category = "non_tensor_return"
        summary = "The op returns a scalar or container rather than a tensor."
        suggestion = "Track separately from tensor-to-TOSA lowering coverage."
    elif args and not _has_tensor(args):
        category = "constructor_or_non_tensor_input"
        summary = "The op primarily consumes non-tensor arguments, which the current tensor-only harness does not model."
        suggestion = "Use a constructor/scalar-specific harness for this family."
    elif "invalid syntax" in error_lower:
        category = "test_generation_bug"
        summary = "The generated Python source for the test function was invalid."
        suggestion = "Fix the code generator for this op name/signature before classifying support."

    return {
        "category": category,
        "summary": summary,
        "suggestion": suggestion,
        "supported_siblings": siblings,
        "error": error,
        "args": args,
        "returns": returns,
    }


def build_analysis() -> dict[str, Any]:
    """Build a classification report for every unsupported op."""
    all_ops = _load_json(DEFAULT_ALL_OPS_PATH)
    database = _load_json(DEFAULT_DB_PATH)
    supported_ops = {op_name for op_name, info in database.items() if info.get("supported")}

    unsupported: dict[str, Any] = {}
    category_counts: Counter[str] = Counter()
    for op_name, info in sorted(database.items()):
        if info.get("supported"):
            continue
        op_meta = all_ops.get(op_name, {})
        classification = classify_op(op_name, info, op_meta, supported_ops)
        unsupported[op_name] = classification
        category_counts[classification["category"]] += 1

    return {
        "summary": {
            "supported_count": len(supported_ops),
            "unsupported_count": len(unsupported),
            "category_counts": dict(sorted(category_counts.items())),
        },
        "unsupported_ops": unsupported,
    }


def write_markdown_report(analysis: dict[str, Any], output_path: Path = OUTPUT_MARKDOWN_PATH) -> None:
    """Write a compact markdown summary for human inspection."""
    lines = [
        "# Unsupported Op Analysis",
        "",
        f"- Supported ops: {analysis['summary']['supported_count']}",
        f"- Unsupported ops: {analysis['summary']['unsupported_count']}",
        "",
        "## Category Counts",
        "",
    ]

    for category, count in analysis["summary"]["category_counts"].items():
        lines.append(f"- `{category}`: {count}")

    lines.extend(["", "## Sample Ops", ""])

    grouped: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for op_name, op_info in analysis["unsupported_ops"].items():
        grouped.setdefault(op_info["category"], []).append((op_name, op_info))

    for category in sorted(grouped):
        lines.append(f"### {category}")
        lines.append("")
        for op_name, op_info in grouped[category][:10]:
            sibling_text = f" | supported siblings: {', '.join(op_info['supported_siblings'])}" if op_info["supported_siblings"] else ""
            lines.append(f"- `{op_name}`: {op_info['summary']}{sibling_text}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    """Generate JSON and markdown unsupported-op analysis artifacts."""
    analysis = build_analysis()
    save_json(OUTPUT_JSON_PATH, analysis)
    write_markdown_report(analysis)
    print(f"Wrote {OUTPUT_JSON_PATH}")
    print(f"Wrote {OUTPUT_MARKDOWN_PATH}")


if __name__ == "__main__":
    main()
