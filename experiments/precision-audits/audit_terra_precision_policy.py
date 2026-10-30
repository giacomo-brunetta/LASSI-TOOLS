"""Source review inventory plus small-input confirmation of explicit promotions.

Does not run LARGE validation, collect timings, or certify accelerator internals.
Original campaign seeds and measurements are never modified.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path

import torch

from lassi_x.precision_audit_worker import audit_forward

ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN = ROOT / "runs/a100-clean-gpu-repairs-20261016"


def main() -> None:
    plan = json.loads((CAMPAIGN / "campaign.json").read_text())
    entries = []
    torch.set_num_threads(1)
    for entry in plan["entries"]:
        kernel = entry["name"]
        for cell in entry["cells"]:
            path = Path(cell["module"])
            source = path.read_text()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != cell["sha256"]:
                raise ValueError(f"Seed hash mismatch: {path}")
            tree = ast.parse(source)
            review = []
            for fn in ast.walk(tree):
                if not isinstance(fn, ast.FunctionDef):
                    continue
                # Defaults and setup are not target-format forward arithmetic.
                if fn.name in {"build_inputs", "__init__"}:
                    continue
                for statement in fn.body:
                    for node in ast.walk(statement):
                        if not isinstance(node, ast.Call):
                            continue
                        text = ast.unparse(node)
                        attr = node.func.attr if isinstance(node.func, ast.Attribute) else ""
                        if (
                            attr in {"float", "double", "item", "tolist", "numpy", "type"}
                            or any(x in text for x in ("torch.float32", "torch.float64"))
                        ) and attr in {"float", "double", "item", "tolist", "numpy", "type", "to"}:
                            # Keep the innermost relevant call as review evidence.
                            review.append(
                                {"function": fn.name, "line": node.lineno, "expression": text}
                            )
            cid, precision = cell["candidate_id"], cell["precision"]
            invalid = (
                (kernel == "direct-dft" and cid == "c3" and precision == "bf16")
                or (kernel == "polybench-adi" and cid == "c1" and precision == "bf16")
                or kernel == "polybench-deriche"
                or (kernel == "polybench-durbin" and cid == "c1")
            )
            report = None
            if invalid:
                spec = importlib.util.spec_from_file_location("reviewed_seed", path)
                assert spec is not None and spec.loader is not None
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                dtype = torch.float16 if precision == "fp16" else torch.bfloat16
                if kernel == "direct-dft":
                    inputs = (torch.ones(8, dtype=dtype),)
                elif kernel == "polybench-deriche":
                    inputs = (torch.ones(4, 4, dtype=dtype), torch.tensor(0.25, dtype=dtype))
                elif kernel == "polybench-adi":
                    inputs = (torch.ones(3, 3, dtype=dtype),)
                else:
                    inputs = (torch.ones(4, dtype=dtype),)
                report = audit_forward(module.make_model().eval(), inputs, dtype)
                if report["passed"]:
                    raise AssertionError(f"Expected promotion not observed: {path}")
            entries.append(
                {
                    "kernel": kernel,
                    "candidate": cid,
                    "precision": precision,
                    "module": str(path),
                    "sha256": digest,
                    "classification": "invalid_precision_promotion"
                    if invalid
                    else "no_explicit_violation_found_in_source_review",
                    "source_review_findings": review,
                    "small_cpu_runtime_confirmation": report,
                }
            )
    print(
        json.dumps(
            {
                "policy": (
                    "observed-eager-dtype-v2; wide setup constants and unused buffers allowed; "
                    "target-format forward arithmetic required"
                ),
                "scope": (
                    "All 192 frozen Terra baseline precision cells, 33 kernels; source inspection "
                    "plus small CPU forward confirmation of eight promotions. Not a full runtime "
                    "audit of the other 184 cases, nor LARGE accuracy/performance validation."
                ),
                "source_review_notes": (
                    "ADI CPU-FP64-only fallback is outside low-precision GPU path. Wider input "
                    "initialization and setup constants are allowed. Unused dtype-specific "
                    "buffers are allowed."
                ),
                "total_cells": len(entries),
                "invalid_precision_cells": sum(
                    e["classification"] == "invalid_precision_promotion" for e in entries
                ),
                "entries": entries,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
