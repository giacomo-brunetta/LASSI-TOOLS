"""Frozen five-model FX capture and region capability gate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import torch

from lassi_x import herbie, herbie_fx, herbie_regions
from lassi_x.campaign import Check, StageContext, Verdict


def main() -> None:
    context = StageContext.load()
    for name, module in [
        ("herbie_adapter", herbie),
        ("fx_adapter", herbie_fx),
        ("static_adapter", herbie_regions),
    ]:
        if context.input_path(name).read_bytes() != Path(module.__file__).read_bytes():
            raise ValueError("Adapter hash mismatch")
    data = context.input_path("candidate").read_bytes()
    spec = json.loads(context.input_path("specification").read_text())
    if hashlib.sha256(data).hexdigest() != spec["source_sha256"]:
        raise ValueError("Source hash mismatch")
    evidence: dict[str, Any] = dict(spec)
    evidence.update(
        herbie_invocations=0,
        numerical_forward_invocations=0,
        numerically_validated=False,
        repaired=False,
    )
    evidence["static_regions"] = [
        asdict(r)
        for r in herbie_regions.discover(data.decode(), spec["class_name"], spec["precision"])
    ]
    namespace: dict[str, Any] = {"__name__": "frozen_candidate"}
    try:
        exec(compile(data, str(context.input_path("candidate")), "exec"), namespace)
        model = namespace[spec["class_name"]]()
        graph = herbie_fx.capture_with_leaf_methods(model, ("_scan",))
        comparisons = []
        for shape in ((4, 4), (16, 17)):
            image = torch.arange(shape[0] * shape[1], dtype=torch.float64).reshape(shape) / (
                shape[0] * shape[1]
            )
            alpha = torch.tensor(0.25, dtype=torch.float64)
            expected = model(image, alpha)
            actual = graph(image, alpha)
            comparisons.append(
                {
                    "shape": shape,
                    "equal": torch.equal(actual, expected),
                    "finite": bool(torch.isfinite(actual).all()),
                    "dtype": str(actual.dtype),
                }
            )
        evidence["runtime_comparisons"] = comparisons
        evidence["numerical_forward_invocations"] = 4
        if not all(c["equal"] and c["finite"] for c in comparisons):
            raise ValueError("Captured graph differs from original")
        evidence["trace_status"] = "passed"
        evidence["graph"] = graph.code
        regions = herbie_fx.discover(graph, spec["precision"])
        evidence["fx_regions"] = [asdict(r) for r in regions]
        proposals = []
        for node in graph.graph.nodes:
            try:
                proposal = herbie_fx.promote_matmul(graph, node.name)
            except ValueError:
                continue
            proposals.append({"node": node.name, "graph": proposal.code})
        evidence["matmul_proposals"] = proposals
        supported = bool(regions)
        reason = (
            f"FX captured; {len(regions)} Herbie regions; "
            f"{len(proposals)} matmul precision proposals"
        )
    except Exception as exc:
        evidence["trace_status"] = "failed"
        evidence["trace_error"] = f"{type(exc).__name__}: {exc}"
        evidence["fx_regions"] = []
        evidence["matmul_proposals"] = []
        supported = False
        reason = evidence["trace_error"]
    (Path(context.work_dir) / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
    status = "passed" if supported else "failed"
    context.finish(
        Verdict(
            status=status,
            reason=reason,
            checks=[
                Check(id="frozen-inputs", status="passed", reason="Source and adapters verified"),
                Check(id="extraction-support", status=status, reason=reason),
            ],
        )
    )


if __name__ == "__main__":
    main()
