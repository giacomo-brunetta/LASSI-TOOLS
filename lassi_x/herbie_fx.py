"""Deterministic Herbie regions in an explicitly captured, trusted Torch FX graph.

Tracing is the caller's responsibility and can execute Python. Graph rewrites
are proposals; numerical domains, validation and precision audits remain external.
"""

from __future__ import annotations

import copy
import operator
from dataclasses import dataclass
from typing import Any

import torch
from torch import fx

from lassi_x import herbie

_BINARY = {operator.add: "+", operator.sub: "-", operator.mul: "*", operator.truediv: "/"}
_UNARY = {getattr(torch, name): name for name in herbie.UNARY}


@dataclass(frozen=True)
class FXRegion:
    root: str
    boundaries: tuple[str, ...]
    source: str
    precision: str
    graph_code: str

    def program(self) -> herbie.Program:
        return herbie.extract(self.source, "Region", self.precision)


def discover(module: fx.GraphModule, precision: str = "binary32") -> list[FXRegion]:
    """Find supported roots, expanding dependencies since the last opaque operation.

    Opaque calls are barriers because they may mutate earlier tensors. Boundary
    values are passed directly from the graph, so opaque operations execute once.
    Uniform boundary precision is guarded at runtime, not inferred from syntax.
    """
    if precision not in herbie.PRECISIONS:
        raise ValueError("Unknown precision")
    nodes = list(module.graph.nodes)
    positions = {n: i for i, n in enumerate(nodes)}
    expressions: dict[fx.Node, str] = {}
    results: list[FXRegion] = []
    barrier = -1
    for node in nodes:
        boundaries: list[fx.Node] = []

        def atom(value: Any, boundaries: list[fx.Node] = boundaries, barrier: int = barrier) -> str:
            if isinstance(value, fx.Node):
                if value in expressions and positions[value] > barrier:
                    # Expand recursively with this region's boundary numbering.
                    return expression(value)
                if value not in boundaries:
                    boundaries.append(value)
                return f"v{boundaries.index(value)}"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return repr(value)
            raise herbie.UnsupportedExpressionError("Unsupported FX operand")

        def expression(current: fx.Node) -> str:
            args = current.args
            if current.kwargs:
                raise herbie.UnsupportedExpressionError("Keyword operations are boundaries")
            if current.op == "call_function":
                target = current.target
                if target in _BINARY and len(args) == 2:
                    return f"({atom(args[0])} {_BINARY[target]} {atom(args[1])})"
                if target is operator.neg and len(args) == 1:
                    return f"(-{atom(args[0])})"
                if target in _UNARY and len(args) == 1:
                    return f"torch.{_UNARY[target]}({atom(args[0])})"
            if current.op == "call_method" and current.target == "to" and len(args) == 2:
                dtype = next(
                    (
                        name
                        for name in herbie.PRECISIONS.values()
                        if args[1] == getattr(torch, name)
                    ),
                    None,
                )
                if dtype:
                    return f"{atom(args[0])}.to(torch.{dtype})"
            raise herbie.UnsupportedExpressionError("Opaque FX operation")

        if node.op in {"placeholder", "get_attr", "output"}:
            continue
        try:
            text = expression(node)
            if not boundaries:
                raise herbie.UnsupportedExpressionError("No tensor boundaries")
            arguments = ", ".join(f"v{i}" for i in range(len(boundaries)))
            source = (
                "import torch\nclass Region(torch.nn.Module):\n"
                f" def forward(self, {arguments}):\n  return {text}\n"
            )
            herbie.extract(source, "Region", precision)
        except herbie.UnsupportedExpressionError:
            barrier = positions[node]
            continue
        expressions[node] = text
        results.append(
            FXRegion(node.name, tuple(n.name for n in boundaries), source, precision, module.code)
        )
    return results


def reinsert(module: fx.GraphModule, region: FXRegion, improved: str) -> fx.GraphModule:
    """Copy a graph and replace one supported root with a guarded proposal module."""
    if module.code != region.graph_code or region not in discover(module, region.precision):
        raise ValueError("Region graph mismatch")
    source = herbie.generate(region.program(), improved)
    namespace: dict[str, Any] = {}
    # Only our generated restricted wrapper is executed, never candidate source.
    exec(compile(source, "<herbie-fx>", "exec"), namespace)
    result = copy.deepcopy(module)
    nodes = {n.name: n for n in result.graph.nodes}
    root = nodes[region.root]
    name = "_lassi_herbie_region"
    while hasattr(result, name):
        name += "_"
    result.add_module(name, namespace["Region"]())
    with result.graph.inserting_before(root):
        replacement = result.graph.call_module(name, tuple(nodes[n] for n in region.boundaries))
    root.replace_all_uses_with(replacement)
    result.graph.erase_node(root)
    # Do not eliminate unrelated nodes: arbitrary opaque calls may have effects.
    result.graph.lint()
    result.recompile()
    return result


def _matmul_fp32(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    if left.dtype == right.dtype and left.dtype in (torch.float16, torch.bfloat16):
        return torch.matmul(left.float(), right.float()).to(left.dtype)
    return torch.matmul(left, right)


def promote_matmul(module: fx.GraphModule, node_name: str) -> fx.GraphModule:
    """Propose FP32 matmul computation with original output storage for FP16/BF16.

    This is an explicit precision transformation, not a Herbie rewrite or a
    hardware accumulation guarantee. Other dtypes retain the original operation.
    """
    result = copy.deepcopy(module)
    node = next((n for n in result.graph.nodes if n.name == node_name), None)
    if (
        node is None
        or node.op != "call_function"
        or node.target not in (torch.matmul, operator.matmul)
        or len(node.args) != 2
        or node.kwargs
    ):
        raise ValueError("Select a positional torch.matmul or operator.matmul node")
    node.target = _matmul_fp32
    result.graph.lint()
    result.recompile()
    return result


class _MethodBoundary(torch.nn.Module):
    def __init__(self, owner: torch.nn.Module, method: str) -> None:
        super().__init__()
        self.owner = owner
        self.method = method

    def forward(self, *args: Any, **kwargs: Any) -> Any:
        return getattr(self.owner, self.method)(*args, **kwargs)


def capture_with_leaf_methods(model: torch.nn.Module, methods: tuple[str, ...]) -> fx.GraphModule:
    """Capture a trusted model while preserving selected helpers as runtime calls.

    Uses isolated copies, never patches the original class. Intended for stateless
    numerical helpers: stateful helpers sharing mutable state with forward are
    outside this contract. Tracing still executes surrounding Python.
    """
    if not methods or len(set(methods)) != len(methods):
        raise ValueError("Supply distinct helper method names")
    owner = copy.deepcopy(model)
    captured = copy.deepcopy(model)
    overrides: dict[str, Any] = {}
    for index, method in enumerate(methods):
        if method == "forward" or not callable(getattr(owner, method, None)):
            raise ValueError(f"Not a helper method: {method}")
        name = f"_lassi_boundary_{index}"
        if hasattr(captured, name):
            raise ValueError(f"Boundary name collision: {name}")
        captured.add_module(name, _MethodBoundary(owner, method))

        def dispatch(self: torch.nn.Module, *args: Any, _name: str = name, **kwargs: Any) -> Any:
            return getattr(self, _name)(*args, **kwargs)

        overrides[method] = dispatch
    captured.__class__ = type(f"{type(model).__name__}Boundaries", (type(model),), overrides)

    class Tracer(fx.Tracer):
        def is_leaf_module(self, m: torch.nn.Module, module_qualified_name: str) -> bool:
            return isinstance(m, _MethodBoundary) or super().is_leaf_module(
                m, module_qualified_name
            )

    return fx.GraphModule(captured, Tracer().trace(captured))
