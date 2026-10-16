"""Explicit size-only specializations of fixed-profile scientific translations.

The source algorithm is retained. Only named dimensions, dataset labels, and
known timestep bounds are changed; scalar arithmetic coefficients are untouched.
Each specialization must still be evaluated against an independent C oracle.
"""

from __future__ import annotations

import ast
import subprocess
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pathlib import Path

DIMENSIONS = {
    "N",
    "M",
    "NI",
    "NJ",
    "NK",
    "NL",
    "NM",
    "NR",
    "NQ",
    "NP",
    "NX",
    "NY",
    "W",
    "H",
    "TSTEPS",
    "TMAX",
    "SIZE",
    "STEPS",
}


def read_profile(header: Path, dataset: str, cc: str = "gcc") -> dict[str, int]:
    result = subprocess.run(
        [cc, "-E", "-dM", f"-D{dataset.upper()}_DATASET", "-include", str(header), "-"],
        input="",
        text=True,
        capture_output=True,
        check=True,
    )
    values = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] in DIMENSIONS and parts[2].isdigit():
            values[parts[1]] = int(parts[2])
    if not values:
        raise ValueError(f"No dataset dimensions found in {header}")
    return values


def specialize_source(
    source: str,
    kernel: str,
    original: dict[str, int],
    target: dict[str, int],
    dataset: str = "large",
) -> tuple[str, list[dict[str, object]]]:
    changes: list[dict[str, object]] = []
    time_key = (
        "STEPS"
        if kernel == "lorenz-rk4"
        else "TSTEPS"
        if "TSTEPS" in original
        else "TMAX"
        if "TMAX" in original
        else None
    )

    def key_for(name: str) -> str | None:
        key = name.upper().strip("_").removeprefix("MINI_")
        key = {"WIDTH": "W", "HEIGHT": "H", "TMAX": "TMAX"}.get(key, key)
        if key in original:
            return key
        if key in {"N", "SIZE"} and "SIZE" in original:
            return "SIZE"
        if key in {"STEPS", "TSTEPS", "TIME_STEPS", "TIMESTEPS"}:
            return time_key
        return None

    def sized(node: ast.expr, key: str | None) -> ast.expr:
        if (
            key
            and isinstance(node, ast.Constant)
            and type(node.value) is int
            and node.value == original[key]
        ):
            changes.append(
                {"line": node.lineno, "dimension": key, "before": node.value, "after": target[key]}
            )
            return ast.copy_location(ast.Constant(target[key]), node)
        return node

    def assignment(value: ast.expr, dest: ast.AST) -> ast.expr:
        if isinstance(dest, ast.Name):
            key = key_for(dest.id)
            if (
                dest.id.upper().strip("_") in {"MINI_DIMS", "DIMS", "MINI_SHAPE"}
                and isinstance(value, (ast.Tuple, ast.List))
                and len(value.elts) == 5
            ):
                value.elts = [
                    sized(v, k)
                    for v, k in zip(value.elts, ("NI", "NJ", "NK", "NL", "NM"), strict=True)
                ]
                return value
            return sized(value, key)
        if (
            isinstance(dest, (ast.Tuple, ast.List))
            and isinstance(value, (ast.Tuple, ast.List))
            and len(dest.elts) == len(value.elts)
        ):
            value.elts = [assignment(v, d) for v, d in zip(value.elts, dest.elts, strict=True)]
        return value

    class Specializer(ast.NodeTransformer):
        in_size_function = False

        def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
            previous = self.in_size_function
            self.in_size_function = node.name in {"_dataset_size", "dataset_size"}
            node = cast("ast.FunctionDef", self.generic_visit(node))
            self.in_size_function = previous
            return node

        def visit_Return(self, node: ast.Return) -> ast.AST:
            if self.in_size_function and node.value is not None:
                node.value = sized(node.value, key_for("n"))
            return self.generic_visit(node)

        def visit_Constant(self, node: ast.Constant) -> ast.AST:
            if node.value == "mini":
                return ast.copy_location(ast.Constant(dataset), node)
            return node

        def visit_Assign(self, node: ast.Assign) -> ast.AST:
            node.value = assignment(node.value, node.targets[0])
            return self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AST:
            if node.value is not None:
                node.value = assignment(node.value, node.target)
            return self.generic_visit(node)

        def visit_Dict(self, node: ast.Dict) -> ast.AST:
            # Some input builders select their single supported size by name.
            for key, value in zip(node.keys, node.values, strict=True):
                if isinstance(key, ast.Constant) and key.value in {"mini", "default"}:
                    index = node.values.index(value)
                    order = (
                        ("NI", "NJ", "NK", "NL", "NM")
                        if kernel == "polybench-3mm"
                        else (("NI", "NJ", "NK") if kernel == "polybench-gemm" else ())
                    )
                    if isinstance(value, (ast.Tuple, ast.List)) and len(value.elts) == len(order):
                        value.elts = [sized(v, k) for v, k in zip(value.elts, order, strict=True)]
                    else:
                        node.values[index] = sized(value, key_for("n"))
            return self.generic_visit(node)

        def visit_arguments(self, node: ast.arguments) -> ast.AST:
            positional = node.posonlyargs + node.args
            if node.defaults:
                node.defaults = [
                    sized(default, key_for(arg.arg))
                    for arg, default in zip(
                        positional[-len(node.defaults) :], node.defaults, strict=True
                    )
                ]
            return self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> ast.AST:
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else (node.func.attr if isinstance(node.func, ast.Attribute) else "")
            )
            if name == "range" and time_key:
                node.args = [sized(arg, time_key) for arg in node.args]
            elif name == "range":
                for index, arg in enumerate(node.args):
                    if isinstance(arg, ast.Constant) and type(arg.value) is int:
                        matches = [
                            key
                            for key, value in original.items()
                            if value == arg.value and key not in {"STEPS", "TSTEPS", "TMAX"}
                        ]
                        if len(matches) == 1:
                            node.args[index] = sized(arg, matches[0])
            if name == "arange" and "SIZE" in original:
                for index, arg in enumerate(node.args[:2]):
                    if isinstance(arg, ast.Constant) and type(arg.value) is int:
                        if arg.value == original["SIZE"]:
                            node.args[index] = sized(arg, "SIZE")
                        elif arg.value == original["SIZE"] + 1:
                            changes.append(
                                {
                                    "line": arg.lineno,
                                    "dimension": "SIZE+1",
                                    "before": arg.value,
                                    "after": target["SIZE"] + 1,
                                }
                            )
                            node.args[index] = ast.copy_location(
                                ast.Constant(target["SIZE"] + 1), arg
                            )
            if kernel == "polybench-adi" and name in {"new_tensor", "tensor"}:
                node.args = [sized(arg, time_key) for arg in node.args]
            return self.generic_visit(node)

        def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
            if kernel == "polybench-atax" and isinstance(node.op, ast.Div):
                if isinstance(node.right, ast.Constant) and node.right.value == 5 * original["M"]:
                    changes.append(
                        {
                            "line": node.lineno,
                            "dimension": "5*M",
                            "before": node.right.value,
                            "after": 5 * target["M"],
                        }
                    )
                    node.right = ast.copy_location(ast.Constant(5 * target["M"]), node.right)
                else:
                    node.right = sized(node.right, "N")
            if kernel == "polybench-adi" and isinstance(node.op, ast.Div):
                node.right = sized(node.right, time_key)
            return self.generic_visit(node)

        def visit_Compare(self, node: ast.Compare) -> ast.AST:
            if isinstance(node.left, ast.Name):
                node.comparators = [sized(c, key_for(node.left.id)) for c in node.comparators]
            return self.generic_visit(node)

    tree = Specializer().visit(ast.parse(source))
    if not changes:
        raise ValueError(f"No explicit dimension specialization found for {kernel}")
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + "\n", changes
