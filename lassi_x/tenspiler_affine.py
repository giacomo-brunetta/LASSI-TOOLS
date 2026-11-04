"""Source-driven loop composition for Tenspiler operator models.

Unlike the direct reduction path, this path proves operator models only. Its
loop transformations and complete floating computations require C validation.
"""

from __future__ import annotations

import hashlib
import json
import keyword
import math
import re
from fractions import Fraction
from importlib.resources import files
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

Node = dict[str, Any]


def children(node: Node) -> list[Node]:
    return list(node.get("inner", []))


def unwrap(node: Node) -> Node:
    while node.get("kind") in {"ImplicitCastExpr", "ParenExpr"}:
        node = children(node)[0]
    return node


def variables(expr: Node) -> set[str]:
    result = {str(expr["name"])} if expr.get("kind") == "var" else set()
    for value in expr.values():
        if isinstance(value, dict):
            result |= variables(value)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, dict):
                    result |= variables(child)
    return result


def expression(node: Node) -> Node:
    kind = node.get("kind")
    if kind in {"ParenExpr", "ImplicitCastExpr", "CStyleCastExpr"}:
        value = expression(children(node)[0])
        if node.get("castKind") in {
            "FloatingCast",
            "IntegralToFloating",
            "FloatingToIntegral",
            "IntegralCast",
        }:
            return {"kind": "cast", "type": node["type"]["qualType"], "value": value}
        return value
    if kind == "DeclRefExpr":
        return {"kind": "var", "name": node["referencedDecl"]["name"]}
    if kind in {"IntegerLiteral", "FloatingLiteral", "CharacterLiteral"}:
        return {
            "kind": "literal",
            "value": float(node["value"]) if kind == "FloatingLiteral" else int(node["value"]),
        }
    if kind == "ArraySubscriptExpr":
        base, index = children(node)
        base_expr = expression(base)
        if base_expr["kind"] == "var":
            return {"kind": "array", "name": base_expr["name"], "indices": [expression(index)]}
        if base_expr["kind"] == "array":
            return {**base_expr, "indices": [*base_expr["indices"], expression(index)]}
        raise ValueError("Unsupported array base")
    if kind == "BinaryOperator":
        op = str(node["opcode"])
        if op not in {"+", "-", "*", "/", "%", "<", "<=", ">", ">=", "==", "!=", "&&", "||"}:
            raise ValueError(f"Unsupported expression operator {op}")
        a, b = children(node)
        return {"kind": "binary", "op": op, "left": expression(a), "right": expression(b)}
    if kind == "UnaryOperator" and node["opcode"] in {"+", "-", "!"}:
        return {"kind": "unary", "op": node["opcode"], "value": expression(children(node)[0])}
    if kind == "ConditionalOperator":
        cond, a, b = children(node)
        return {
            "kind": "select",
            "condition": expression(cond),
            "left": expression(a),
            "right": expression(b),
        }
    if kind == "CallExpr":
        callee, *args = children(node)
        name = str(unwrap(callee).get("referencedDecl", {}).get("name", ""))
        if name in {"pow", "powf"} and len(args) == 2:
            base = unwrap(args[0])
            if (
                base.get("kind") not in {"IntegerLiteral", "FloatingLiteral"}
                or float(base["value"]) <= 0
            ):
                raise ValueError("Power requires a positive constant base")
            return {
                "kind": "call",
                "name": "exp",
                "argument": {
                    "kind": "binary",
                    "op": "*",
                    "left": {"kind": "literal", "value": math.log(float(base["value"]))},
                    "right": expression(args[1]),
                },
                "normalization": "positive-constant-power-to-exp; floating check required",
            }
        if name not in {"sqrt", "sqrtf", "exp", "expf"} or len(args) != 1:
            raise ValueError(f"Tenspiler has no configured operator model for external call {name}")
        return {"kind": "call", "name": name.removesuffix("f"), "argument": expression(args[0])}
    raise ValueError(f"Unsupported expression {kind}")


def nodes(node: Node) -> list[Node]:
    result = [node] if "kind" in node else []
    for value in node.values():
        if isinstance(value, dict):
            result += nodes(value)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, dict):
                    result += nodes(child)
    return result


def affine(expr: Node) -> dict[str, Fraction] | None:
    kind = expr["kind"]
    if kind == "var":
        return {str(expr["name"]): Fraction(1)}
    if kind == "literal" and isinstance(expr["value"], int):
        return {"": Fraction(expr["value"])}
    if kind == "cast":
        return affine(expr["value"])
    if kind == "binary" and expr["op"] in {"+", "-"}:
        a, b = affine(expr["left"]), affine(expr["right"])
        if a is None or b is None:
            return None
        out = dict(a)
        for name, value in b.items():
            out[name] = out.get(name, Fraction()) + value * (1 if expr["op"] == "+" else -1)
        return {name: value for name, value in out.items() if value}
    return None


def same_iteration(left: Node, right: Node, index: str, nested: set[str]) -> bool:
    """Prove access equality implies equal iterations via affine row reduction."""
    if len(left["indices"]) != len(right["indices"]):
        return False
    equations: list[dict[str, Fraction]] = []
    for a, b in zip(left["indices"], right["indices"], strict=True):
        aa, bb = affine(a), affine(b)
        if aa is None or bb is None:
            return False
        row: dict[str, Fraction] = {}
        for terms, side, sign in [(aa, "L", 1), (bb, "R", -1)]:
            for name, value in terms.items():
                key = "@" + side + ":" + name if name == index or name in nested else name
                row[key] = row.get(key, Fraction()) + sign * value
        equations.append({k: v for k, v in row.items() if v})
    basis: dict[str, dict[str, Fraction]] = {}
    for row in equations:
        for pivot in sorted(basis):
            if row.get(pivot):
                scale = row[pivot]
                for name, value in basis[pivot].items():
                    row[name] = row.get(name, Fraction()) - scale * value
        row = {k: v for k, v in row.items() if v}
        if row:
            pivot = sorted(row)[0]
            basis[pivot] = {k: v / row[pivot] for k, v in row.items()}
    target = {"@L:" + index: Fraction(1), "@R:" + index: Fraction(-1)}
    for pivot in sorted(basis):
        if target.get(pivot):
            scale = target[pivot]
            for name, value in basis[pivot].items():
                target[name] = target.get(name, Fraction()) - scale * value
    return not any(target.values())


def parallel(loop: Node) -> bool:
    body = loop["body"]
    all_nodes = nodes(body)
    index = str(loop["index"])
    nested = {str(n["index"]) for n in all_nodes if n["kind"] == "for"}
    if any(
        index in variables(n[key])
        for n in all_nodes
        if n["kind"] == "for"
        for key in ["start", "stop"]
    ):
        return False
    assignments = [n for n in all_nodes if n["kind"] == "assign"]
    writes = [a["target"] for a in assignments if a["target"]["kind"] == "array"]
    if not writes or any(index not in variables(w) for w in writes):
        return False
    reads = [n for a in assignments for n in nodes(a["value"]) if n["kind"] == "array"]
    # Multiple writes must also be disjoint across iterations.
    for a in writes:
        for b in [*writes, *reads]:
            if (
                a["name"] == b["name"]
                and not same_iteration(a, b, index, nested)
                and not disjoint_from_iteration(a, b, loop)
            ):
                return False
    locals_written = {a["target"]["name"] for a in assignments if a["target"]["kind"] == "var"}
    direct = body["statements"] if body["kind"] == "block" else [body]
    for name in locals_written:
        # Local temporaries may vary by iteration only when reset in the direct body.
        reset = False
        for stmt in direct:
            if (
                stmt["kind"] == "assign"
                and stmt["target"] == {"kind": "var", "name": name}
                and name not in variables(stmt["value"])
            ):
                reset = True
                break
            if name in variables(stmt):
                break
        if not reset:
            return False
    return True


def disjoint_from_iteration(write: Node, read: Node, loop: Node) -> bool:
    """Prove a fixed pivot access lies outside a unit-stride write interval."""
    index = loop["index"]
    start, stop = affine(loop["start"]), affine(loop["stop"])
    if start is None or stop is None:
        return False
    for a, b in zip(write["indices"], read["indices"], strict=True):
        aa, bb = affine(a), affine(b)
        if aa is None or bb is None or aa.get(index) != 1 or index in bb:
            continue
        offset = {k: v for k, v in aa.items() if k != index}
        for bound, forward_low in [(start, True), (stop, False)]:
            delta = dict(bound)
            for terms, sign in [(offset, 1), (bb, -1)]:
                for name, value in terms.items():
                    delta[name] = delta.get(name, Fraction()) + sign * value
            if any(v for k, v in delta.items() if k):
                continue
            distance = delta.get("", Fraction())
            if loop["step"] > 0:
                if forward_low and distance > 0:
                    return True
                if not forward_low and (distance < 0 or distance == 0 and not loop["inclusive"]):
                    return True
            else:
                if forward_low and distance < 0:
                    return True
                if not forward_low and (distance > 0 or distance == 0 and not loop["inclusive"]):
                    return True
    return False


def pivot_schedule(loop: Node) -> Node:
    """Recognize a guarded min-plus pivot update by indices, not kernel name."""
    chain = [loop]
    current = loop["body"]
    while True:
        while current.get("kind") == "block" and len(current["statements"]) == 1:
            current = current["statements"][0]
        if current.get("kind") != "for":
            break
        chain.append(current)
        current = current["body"]
    if len(chain) != 3 or current.get("kind") != "assign":
        return loop
    if any(
        n["start"] != {"kind": "literal", "value": 0}
        or n["inclusive"]
        or n["step"] != 1
        or n["stop"] != chain[0]["stop"]
        for n in chain
    ):
        return loop
    pivot, row, column = [n["index"] for n in chain]
    target = current["target"]
    if target.get("kind") != "array" or target["indices"] != [
        {"kind": "var", "name": row},
        {"kind": "var", "name": column},
    ]:
        return loop
    name = target["name"]
    left = {
        "kind": "array",
        "name": name,
        "indices": [{"kind": "var", "name": row}, {"kind": "var", "name": pivot}],
    }
    right = {
        "kind": "array",
        "name": name,
        "indices": [{"kind": "var", "name": pivot}, {"kind": "var", "name": column}],
    }
    total = {"kind": "binary", "op": "+", "left": left, "right": right}
    value = current["value"]
    if value.get("kind") != "select" or value["left"] != target or value["right"] != total:
        return loop
    condition = value["condition"]
    if condition != {"kind": "binary", "op": "<", "left": target, "right": total}:
        return loop
    return {
        "kind": "pivot-min-plus",
        "array": name,
        "pivot": pivot,
        "bound": chain[0]["stop"],
        "original": loop,
        "guard": "nonnegative pivot diagonal; otherwise original loop order",
    }


def wavefront_schedule(loop: Node) -> Node:
    """Schedule an affine rectangular in-place point stencil by dependence order."""
    inner = loop["body"]
    while inner.get("kind") == "block" and len(inner["statements"]) == 1:
        inner = inner["statements"][0]
    if inner.get("kind") != "for" or loop["step"] != 1 or inner["step"] != 1:
        return loop
    body = inner["body"]
    while body.get("kind") == "block" and len(body["statements"]) == 1:
        body = body["statements"][0]
    if body.get("kind") != "assign" or loop["parallel"] or inner["parallel"]:
        return loop
    row, col = loop["index"], inner["index"]
    target = body["target"]
    expected = [{"kind": "var", "name": row}, {"kind": "var", "name": col}]
    if target.get("kind") != "array" or target["indices"] != expected:
        return loop
    if row in variables(inner["start"]) | variables(inner["stop"]):
        return loop
    radius = 0
    for access in (n for n in nodes(body["value"]) if n["kind"] == "array"):
        if access["name"] != target["name"] or len(access["indices"]) != 2:
            return loop
        for axis, expr in zip([row, col], access["indices"], strict=True):
            terms = affine(expr)
            if terms is None or terms.get(axis) != 1 or any(k not in {axis, ""} for k in terms):
                return loop
            if axis == col:
                offset = terms.get("", Fraction())
                if offset.denominator != 1:
                    return loop
                radius = max(radius, abs(offset.numerator))
    if not radius:
        return loop
    return {
        "kind": "wavefront-map",
        "row": row,
        "column": col,
        "weight": radius + 1,
        "rows": {k: loop[k] for k in ["start", "stop", "inclusive", "step"]},
        "columns": {k: inner[k] for k in ["start", "stop", "inclusive", "step"]},
        "body": body,
        "original": loop,
    }


def triangle_schedule(loop: Node) -> Node:
    """Prove increasing-span order for an upper-triangle interval recurrence."""
    inner = loop["body"]
    while inner.get("kind") == "block" and len(inner["statements"]) == 1:
        inner = inner["statements"][0]
    if inner.get("kind") != "for" or loop["step"] != -1 or inner["step"] != 1:
        return loop
    row, col = loop["index"], inner["index"]
    if (
        loop["stop"] != {"kind": "literal", "value": 0}
        or not loop["inclusive"]
        or inner["inclusive"]
    ):
        return loop
    n = inner["stop"]
    if loop["start"] != {
        "kind": "binary",
        "op": "-",
        "left": n,
        "right": {"kind": "literal", "value": 1},
    }:
        return loop
    if inner["start"] != {
        "kind": "binary",
        "op": "+",
        "left": {"kind": "var", "name": row},
        "right": {"kind": "literal", "value": 1},
    }:
        return loop
    assignments = [x for x in nodes(inner["body"]) if x["kind"] == "assign"]
    if not assignments:
        return loop
    target = assignments[0]["target"]
    if (
        target.get("kind") != "array"
        or target["indices"] != [{"kind": "var", "name": row}, {"kind": "var", "name": col}]
        or any(x["target"] != target for x in assignments)
    ):
        return loop
    reductions = [x for x in nodes(inner["body"]) if x["kind"] == "for"]
    if len(reductions) != 1:
        return loop
    reduction = reductions[0]
    if (
        reduction["start"] != inner["start"]
        or reduction["stop"] != {"kind": "var", "name": col}
        or reduction["step"] != 1
        or reduction["inclusive"]
    ):
        return loop
    split = reduction["index"]
    for read in (
        x for x in nodes(inner["body"]) if x["kind"] == "array" and x["name"] == target["name"]
    ):
        a, b = (affine(e) for e in read["indices"])
        if a is None or b is None:
            return loop
        point = (a == {row: 1} and b == {split: 1}) or (a == {split: 1, "": 1} and b == {col: 1})
        da, db = dict(a), dict(b)
        da[row] = da.get(row, Fraction()) - Fraction(1)
        db[col] = db.get(col, Fraction()) - Fraction(1)
        local = (
            not any(v for k, v in da.items() if k)
            and not any(v for k, v in db.items() if k)
            and da.get("", 0) in {0, 1}
            and db.get("", 0) in {0, -1}
        )
        if not (point or local):
            return loop
    return {
        "kind": "wavefront-triangle",
        "row": row,
        "column": col,
        "split": split,
        "bound": n,
        "body": inner["body"],
        "original": loop,
    }


def statement(node: Node) -> Node:
    kind = node.get("kind")
    if kind == "CompoundStmt":
        return {"kind": "block", "statements": [statement(c) for c in children(node)]}
    if kind == "DeclStmt":
        declarations = []
        for decl in children(node):
            typ = str(decl["type"]["qualType"])
            declarations.append(
                {
                    "kind": "declare",
                    "name": decl["name"],
                    "type": typ,
                    "value": expression(children(decl)[0]) if children(decl) else None,
                }
            )
        return {"kind": "block", "statements": declarations}
    if kind in {"BinaryOperator", "CompoundAssignOperator"}:
        a, b = children(node)
        rhs = unwrap(b)
        if (
            node.get("opcode") == "="
            and rhs.get("kind") == "BinaryOperator"
            and rhs.get("opcode") == "="
        ):
            return {
                "kind": "block",
                "statements": [
                    statement(rhs),
                    {
                        "kind": "assign",
                        "target": expression(a),
                        "value": expression(children(rhs)[0]),
                    },
                ],
            }
        target, value = expression(a), expression(b)
        op = str(node["opcode"])
        if op != "=":
            if op not in {"+=", "-=", "*=", "/="}:
                raise ValueError(f"Unsupported assignment {op}")
            value = {"kind": "binary", "op": op[0], "left": target, "right": value}
        elif value.get("kind") == "binary" and value.get("op") == "+" and value["right"] == target:
            value = {**value, "left": target, "right": value["left"]}
        return {"kind": "assign", "target": target, "value": value}
    if kind == "ForStmt":
        init, condition_variable, cond, increment, body = children(node)
        if condition_variable:
            raise ValueError("Unsupported condition declaration")
        if init.get("kind") == "DeclStmt":
            decl = children(init)[0]
            index, start = str(decl["name"]), expression(children(decl)[0])
        else:
            a, b = children(init)
            index, start = expression(a)["name"], expression(b)
        left, right = children(cond)
        if expression(left) != {"kind": "var", "name": index}:
            raise ValueError("Loop condition must compare its counter")
        relation = str(cond["opcode"])
        if relation not in {"<", "<=", ">", ">="}:
            raise ValueError("Unsupported loop relation")
        step = {"++": 1, "--": -1}.get(str(increment.get("opcode")))
        if step is None or expression(children(increment)[0]) != {"kind": "var", "name": index}:
            raise ValueError("Only unit increments/decrements are supported")
        if (step > 0) != (relation in {"<", "<="}):
            raise ValueError("Loop direction and relation disagree")
        result: Node = {
            "kind": "for",
            "index": index,
            "start": start,
            "stop": expression(right),
            "inclusive": relation in {"<=", ">="},
            "step": step,
            "body": statement(body),
        }
        result["parallel"] = parallel(result)
        parts = result["body"].get("statements", [])
        if len(parts) > 1 and all(p["kind"] != "declare" for p in parts):
            writes = [
                {n["target"]["name"] for n in nodes(p) if n["kind"] == "assign"} for p in parts
            ]
            reads = [
                {
                    n["name"]
                    for a in nodes(p)
                    if a["kind"] == "assign"
                    for n in nodes(a["value"])
                    if n["kind"] in {"var", "array"}
                }
                for p in parts
            ]
            independent = all(
                not (writes[i] & (writes[j] | reads[j]) or writes[j] & reads[i])
                for i in range(len(parts))
                for j in range(i)
            )
            if independent:
                loops = []
                for part in parts:
                    child = {**result, "body": part}
                    child["parallel"] = parallel(child)
                    loops.append(child)
                return {"kind": "block", "statements": loops}
        for scheduler in [pivot_schedule, wavefront_schedule, triangle_schedule]:
            scheduled = scheduler(result)
            if scheduled["kind"] != "for":
                return scheduled
        return result
    if kind == "IfStmt":
        parts = children(node)
        if len(parts) not in {2, 3}:
            raise ValueError("Unsupported conditional statement")
        return {
            "kind": "if",
            "condition": expression(parts[0]),
            "then": statement(parts[1]),
            "else": statement(parts[2]) if len(parts) == 3 else {"kind": "block", "statements": []},
        }
    if kind == "NullStmt":
        return {"kind": "block", "statements": []}
    raise ValueError(f"Unsupported statement {kind}")


def normalize(function: Node) -> Node:
    params = [n for n in children(function) if n.get("kind") == "ParmVarDecl"]
    names = [str(p["name"]) for p in params]
    if any(
        not re.fullmatch(r"[A-Za-z_]\w*", name, re.ASCII) or keyword.iskeyword(name)
        for name in names
    ):
        raise ValueError("Parameters must be portable non-keyword identifiers")
    body = next(n for n in children(function) if n.get("kind") == "CompoundStmt")
    plan = statement(body)
    mutations = {
        n["target"]["name"]
        for n in nodes(plan)
        if n["kind"] == "assign" and n["target"]["kind"] == "array"
    }
    ops = {"sum", "mv"}
    if any(n["kind"] == "wavefront-triangle" for n in nodes(plan)):
        ops.add("max")
    mapping = {"+": "add", "-": "sub", "*": "mul", "/": "div"}
    for n in nodes(plan):
        if n["kind"] == "binary" and n["op"] in mapping:
            ops.add(mapping[n["op"]])
        if n["kind"] in {"select", "if"}:
            ops.add("select")
        if n["kind"] == "call":
            ops.add(n["name"])
    return {
        "function": function["name"],
        "parameters": [
            {"name": p["name"], "type": p["type"].get("desugaredQualType", p["type"]["qualType"])}
            for p in params
        ],
        "inputs": names,
        "outputs": [name for name in names if name in mutations],
        "body": plan,
        "operators": sorted(ops),
        "proof_scope": (
            "Tenspiler operator models only; AST loop composition and floating arithmetic "
            "require independent C validation"
        ),
    }


def operator_source(op: str) -> str:
    prefix = "#include <vector>\nusing namespace std;\n"
    if op in {"add", "sub", "mul", "div"}:
        token = {"add": "+", "sub": "-", "mul": "*", "div": "/"}[op]
        return prefix + f"int op_{op}(int a, int b) {{ return a {token} b; }}\n"
    if op == "select":
        return (
            prefix + "int op_select(int cond, int a, int b) { if(cond) return a; else return b; }\n"
        )
    if op in {"sqrt", "exp"}:
        return (
            prefix + f"int integer_{op}(int);\nint op_{op}(int a) {{ return integer_{op}(a); }}\n"
        )
    if op == "sum":
        return (
            prefix + "int op_sum(vector<int> a) { int curr=0; "
            "for(int i=0;i<a.size();i++) curr+=a[i]; return curr; }\n"
        )
    if op == "max":
        return prefix + (
            "int op_max(vector<int> a) { int curr=a[0]; "
            "for(int i=1;i<a.size();i++) if(a[i]>curr) curr=a[i]; return curr; }\n"
        )
    if op == "mv":
        return (
            prefix
            + """vector<int> stage_mv(vector<vector<int>> weight, vector<int> input) {
 vector<int> output; int m=weight.size(); int n=input.size();
 for(int row=0;row<m;row++) { int curr=0;
  for(int col=0;col<n;col++) curr+=weight[row][col]*input[col];
  output.push_back(curr); } return output;
}
"""
        )
    raise ValueError(f"Unknown operator {op}")


def emit(plan: Node, source: Path, output: Path, metadata: Node) -> Node:
    generated = {
        "program.json": json.dumps(plan, indent=2) + "\n",
        "kernel.original.c": source.read_text(),
    }
    for op in plan["operators"]:
        generated[("stage_mv" if op == "mv" else "op_" + op) + ".cc"] = operator_source(op)
    resources = files("lassi_x").joinpath("resources")
    for name, resource in [
        ("synthesize.py", "tenspiler-composed-driver.py.txt"),
        ("stage_driver.py", "tenspiler-driver.py.txt"),
        ("runtime.py", "tenspiler-affine-runtime.py.txt"),
    ]:
        generated[name] = resources.joinpath(resource).read_text()
    generated["README.md"] = (
        "# Prepared composed Tenspiler input\n\n"
        "Original source is preserved in kernel.original.c. program.json describes "
        "deterministic loop scheduling around Tenspiler-generated integer operator "
        "models. This is not whole-kernel Tenspiler synthesis or a floating-point "
        "proof. All arrays must be disjoint and match the source logical shapes.\n\n"
        "Run synthesize.py in a separately configured Tenspiler environment with "
        "--tenspiler-root, --llvm-bin and --llvm-pass. It defaults to bound 2 and "
        "30 seconds per operator. --bounded-only explicitly skips unbounded "
        "verification; its output remains a candidate requiring original-C "
        "validation. Optional --operator-cache is content-addressed by source, "
        "drivers, environment and verification policy.\n\n"
        "synthesis/kernel_torch.py exposes forward in manifest input/output order. "
        "Validate every mutated array against independently compiled original C "
        "using identical typed inputs, dataset flags and precision. Nonfinite "
        "reference cases and exhausted runtime budgets cannot qualify. "
        "Preparation makes no model calls.\n"
    )
    manifest = {
        **metadata,
        "schema_version": 2,
        "mode": "composed-operators",
        "program": {**plan, "stages": [{"output": "mv", "transpose": False}]},
        "integer_model": True,
        "floating_point_equivalence_proven": False,
        "generated_sha256": {
            name: hashlib.sha256(text.encode()).hexdigest() for name, text in generated.items()
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, text in generated.items():
        (output / name).write_text(text)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
