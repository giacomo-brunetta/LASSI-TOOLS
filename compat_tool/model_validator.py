"""Model-level validation against the compatibility database."""

from __future__ import annotations

from typing import Any

from compat_tool.compat import validate_ops


def extract_ops_from_scripted(scripted_model: Any) -> list[str]:
    """Traverse a TorchScript graph and collect unique `aten::` operations."""
    graph = scripted_model.inlined_graph if hasattr(scripted_model, "inlined_graph") else scripted_model.graph
    ops: list[str] = []
    seen: set[str] = set()

    for node in graph.nodes():
        kind = node.kind()
        if not kind.startswith("aten::"):
            continue
        op_name = kind.replace("::", ".", 1)
        if op_name not in seen:
            seen.add(op_name)
            ops.append(op_name)

    return ops


def validate_model(scripted_model: Any) -> dict[str, list[str]]:
    """Return supported and unsupported ops used by a scripted model."""
    ops = extract_ops_from_scripted(scripted_model)
    return validate_ops(ops)

