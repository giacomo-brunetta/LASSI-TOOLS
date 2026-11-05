"""Static region discovery and reinsertion for the restricted Herbie bridge.

Discovery is syntactic coverage, not a tensor-type or accuracy certificate.
Only pure arithmetic over local names is extracted; opaque operations remain
in their original evaluation position. No candidate code is executed.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import cast

from lassi_x import herbie


@dataclass(frozen=True)
class Region:
    source_sha256: str
    class_name: str
    line: int
    column: int
    source: str
    precision: str

    def program(self) -> herbie.Program:
        return herbie.extract(self.source, "Region", self.precision)


def discover(source: str, class_name: str, precision: str = "binary32") -> list[Region]:
    """Find maximal supported arithmetic subexpressions in forward, in source order.

    Boundary names are provisionally tensor inputs. Generated code checks their
    dtype/device at runtime and executes the original expression otherwise.
    Calls, indexing, attributes and control flow are boundaries, never hoisted.
    """
    tree = ast.parse(source)
    if precision not in herbie.PRECISIONS:
        raise ValueError("Unknown precision")
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    if len(classes) != 1:
        raise herbie.UnsupportedExpressionError("Select exactly one named class")
    forwards = [
        n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == "forward"
    ]
    if len(forwards) != 1:
        raise herbie.UnsupportedExpressionError("Select exactly one forward")
    # Reuse the bridge's import/rebinding checks against the complete module.
    probe = "import torch\nclass Region(torch.nn.Module):\n def forward(self, x):\n  return x\n"
    probe_tree = ast.parse(probe)
    tree_without_class = ast.Module(
        body=[n for n in tree.body if n is not classes[0]] + [probe_tree.body[1]], type_ignores=[]
    )
    herbie.extract(ast.unparse(tree_without_class), "Region", precision)
    if any(
        (isinstance(n, ast.Name) and n.id == "torch" and isinstance(n.ctx, ast.Store))
        or (isinstance(n, ast.arg) and n.arg == "torch")
        for n in ast.walk(classes[0])
    ):
        raise herbie.UnsupportedExpressionError("Torch rebinding is unsupported")
    result: list[Region] = []
    digest = hashlib.sha256(source.encode()).hexdigest()

    def visit(node: ast.AST) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(node, (ast.BinOp, ast.UnaryOp)):
            allowed = (
                ast.BinOp,
                ast.UnaryOp,
                ast.Name,
                ast.Constant,
                ast.Load,
                ast.Add,
                ast.Sub,
                ast.Mult,
                ast.Div,
                ast.USub,
                ast.UAdd,
            )
            if all(isinstance(n, allowed) for n in ast.walk(node)):
                names = sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name)})
                if names:
                    wrapper = (
                        "import torch\nclass Region(torch.nn.Module):\n"
                        f" def forward(self, {', '.join(names)}):\n"
                        f"  return {ast.unparse(node)}\n"
                    )
                    try:
                        herbie.extract(wrapper, "Region", precision)
                    except herbie.UnsupportedExpressionError:
                        pass
                    else:
                        result.append(
                            Region(
                                digest, class_name, node.lineno, node.col_offset, wrapper, precision
                            )
                        )
                        return
        for child in ast.iter_child_nodes(node):
            visit(child)

    for statement in forwards[0].body:
        visit(statement)
    return result


def reinsert(source: str, region: Region, improved: str) -> str:
    """Replace one source-bound region with a guarded local helper proposal."""
    if hashlib.sha256(source.encode()).hexdigest() != region.source_sha256:
        raise ValueError("Region source hash mismatch")
    if region not in discover(source, region.class_name, region.precision):
        raise ValueError("Region does not match discovery")
    program = region.program()
    generated = ast.parse(herbie.generate(program, improved))
    cls = next(n for n in generated.body if isinstance(n, ast.ClassDef))
    helper = next(n for n in cls.body if isinstance(n, ast.FunctionDef))
    helper.args.args = helper.args.args[1:]
    tree = ast.parse(source)
    occupied = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {
        n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)
    }
    name = "_lassi_herbie_region"
    while name in occupied:
        name += "_"
    helper.name = name
    target_class = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == region.class_name
    )
    forward = next(
        n for n in target_class.body if isinstance(n, ast.FunctionDef) and n.name == "forward"
    )

    class Replace(ast.NodeTransformer):
        def visit(self, node: ast.AST) -> ast.AST:
            if isinstance(node, ast.expr) and (node.lineno, node.col_offset) == (
                region.line,
                region.column,
            ):
                return ast.Call(
                    func=ast.Name(id=name, ctx=ast.Load()),
                    args=[ast.Name(id=a, ctx=ast.Load()) for a in program.arguments],
                    keywords=[],
                )
            return cast("ast.AST", super().visit(node))

    Replace().visit(forward)
    forward.body.insert(0, helper)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n"
