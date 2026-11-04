"""Deterministically prepare a restricted C reduction subset for Tenspiler.

Uses Clang's AST, never a model or filename-specific rewrites. Unsupported
statements and dependencies are rejected before creating an output directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import re
import shlex
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from .tenspiler_affine import emit, normalize

Node = dict[str, Any]


class UnsupportedSourceError(ValueError):
    """The source cannot be transformed under the supported contract."""


def _children(node: Node) -> list[Node]:
    return list(node.get("inner", []))


def _unwrap(node: Node) -> Node:
    while node.get("kind") in {"ImplicitCastExpr", "ParenExpr"}:
        node = _children(node)[0]
    return node


def _name(node: Node) -> str:
    node = _unwrap(node)
    if node.get("kind") != "DeclRefExpr":
        raise UnsupportedSourceError("Expected a plain variable or dimension parameter")
    return str(node["referencedDecl"]["name"])


def _zero(node: Node) -> bool:
    node = _unwrap(node)
    return node.get("kind") in {"IntegerLiteral", "FloatingLiteral"} and float(node["value"]) == 0


def _offset(node: Node, edge: str) -> int:
    loc = node["range"][edge]
    loc = loc.get("expansionLoc", loc)
    return int(loc["offset"])


def _access(node: Node) -> tuple[str, tuple[str, ...]]:
    node = _unwrap(node)
    if node.get("kind") == "ArraySubscriptExpr":
        base, index = _children(node)
        name, indices = _access(base)
        return name, (*indices, _name(index))
    return _name(node), ()


@dataclass(frozen=True)
class Loop:
    index: str
    bound: str
    begin: int
    end: int


@dataclass(frozen=True)
class Assignment:
    output: str
    index: str
    loops: tuple[Loop, ...]
    position: int
    matrix: str = ""
    matrix_indices: tuple[str, ...] = ()
    vector: str = ""
    vector_index: str = ""
    matrix_first: bool = True
    accumulator_first: bool = True


@dataclass(frozen=True)
class Stage:
    output: str
    matrix: str
    vector: str
    transpose: bool
    rows: str
    columns: str
    matrix_first: bool
    accumulator_first: bool
    bias: bool = False


@dataclass(frozen=True)
class Program:
    function: str
    scalar: str
    dimensions: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    stages: tuple[Stage, ...]


def _loop(node: Node, dimensions: set[str]) -> Loop:
    init, condition_var, condition, increment, _ = _children(node)
    if condition_var:
        raise UnsupportedSourceError("Loop condition declarations are unsupported")
    if init.get("kind") == "DeclStmt":
        decls = _children(init)
        if len(decls) != 1 or decls[0]["type"]["qualType"] != "int":
            raise UnsupportedSourceError("Expected one integer loop counter")
        index = str(decls[0]["name"])
        values = _children(decls[0])
        valid_init = len(values) == 1 and _zero(values[0])
    else:
        operands = _children(init)
        valid_init = init.get("opcode") == "=" and len(operands) == 2
        index = _name(operands[0]) if valid_init else ""
        valid_init = valid_init and _zero(operands[1])
    if not valid_init or condition.get("opcode") != "<":
        raise UnsupportedSourceError("Only zero-based loops with counter < dimension are supported")
    left, right = _children(condition)
    right = _unwrap(right)
    bound = str(right["value"]) if right.get("kind") == "IntegerLiteral" else _name(right)
    if (
        index in dimensions
        or _name(left) != index
        or (
            not bound.isdigit()
            and (
                bound not in dimensions
                or right.get("referencedDecl", {}).get("kind") != "ParmVarDecl"
            )
        )
    ):
        raise UnsupportedSourceError("Loop bounds must be integer parameters or positive constants")
    if bound.isdigit() and int(bound) <= 0:
        raise UnsupportedSourceError("Loop bounds must be positive")
    if increment.get("opcode") != "++" or _name(_children(increment)[0]) != index:
        raise UnsupportedSourceError("Only unit-increment loops are supported")
    return Loop(index, bound, _offset(node, "begin"), _offset(node, "end"))


def _assign(node: Node, loops: tuple[Loop, ...]) -> Assignment:
    if node.get("opcode") not in {"=", "+="}:
        raise UnsupportedSourceError(
            "Only zero initialization and sum-of-products updates are supported"
        )
    left, right = _children(node)
    output, indices = _access(left)
    if len(indices) != 1:
        raise UnsupportedSourceError("Only vector outputs are supported")
    result = Assignment(output, indices[0], loops, _offset(node, "begin"))
    if node["opcode"] == "=" and _zero(right):
        return result
    accumulator_first = True
    if node["opcode"] == "=":
        right = _unwrap(right)
        if right.get("opcode") != "+":
            raise UnsupportedSourceError("Expected output[index] = output[index] + product")
        a, b = _children(right)
        if _access_if_possible(a) == (output, indices):
            right = b
        elif _access_if_possible(b) == (output, indices):
            right, accumulator_first = a, False
        else:
            raise UnsupportedSourceError("Assignment must accumulate into the same output element")
    right = _unwrap(right)
    if right.get("opcode") != "*":
        raise UnsupportedSourceError(
            "Only matrix-element times vector-element products are supported"
        )
    product_left, product_right = (_access(x) for x in _children(right))
    matrix_first = len(product_left[1]) == 2
    matrix, vector = (
        (product_left, product_right) if matrix_first else (product_right, product_left)
    )
    if len(matrix[1]) != 2 or len(vector[1]) != 1:
        raise UnsupportedSourceError("Expected one matrix access and one vector access")
    return Assignment(
        output,
        indices[0],
        loops,
        result.position,
        matrix[0],
        matrix[1],
        vector[0],
        vector[1][0],
        matrix_first,
        accumulator_first,
    )


def _access_if_possible(node: Node) -> tuple[str, tuple[str, ...]] | None:
    try:
        return _access(node)
    except UnsupportedSourceError:
        return None


def analyze(function: Node) -> Program:
    """Recognize zero-initialized reductions and check distribution dependencies."""
    params = [n for n in _children(function) if n.get("kind") == "ParmVarDecl"]
    types = {str(p["name"]): str(p["type"]["qualType"]) for p in params}
    if any(not re.fullmatch(r"[A-Za-z_]\w*", name, flags=re.ASCII) for name in types):
        raise UnsupportedSourceError("Parameter names must be portable ASCII identifiers")
    dimensions = {name for name, typ in types.items() if typ == "int"}
    scalars: set[str] = set()
    ranks: dict[str, int] = {}
    for name, typ in types.items():
        if name in dimensions:
            continue
        match = re.fullmatch(r"(?:const )?(double|float|int) (\*|\(\*\)\[(\d+|\w+)\])", typ)
        if not match:
            raise UnsupportedSourceError(f"Unsupported parameter {name}: {typ}")
        if match[3] and not match[3].isdigit() and match[3] not in dimensions:
            raise UnsupportedSourceError(f"Unknown array extent for {name}")
        scalars.add(match[1])
        ranks[name] = 2 if "[" in typ else 1
    if len(scalars) != 1:
        raise UnsupportedSourceError("All arrays must have the same scalar type")
    keywords = set(
        [
            "alignas",
            "alignof",
            "and",
            "asm",
            "auto",
            "bitand",
            "bitor",
            "bool",
            "catch",
            "class",
            "compl",
            "concept",
            "consteval",
            "constexpr",
            "constinit",
            "co_await",
            "co_return",
            "co_yield",
            "decltype",
            "delete",
            "dynamic_cast",
            "explicit",
            "export",
            "false",
            "friend",
            "mutable",
            "namespace",
            "new",
            "noexcept",
            "not",
            "nullptr",
            "operator",
            "or",
            "private",
            "protected",
            "public",
            "reinterpret_cast",
            "requires",
            "static_assert",
            "static_cast",
            "template",
            "this",
            "thread_local",
            "throw",
            "true",
            "try",
            "typeid",
            "typename",
            "using",
            "virtual",
            "wchar_t",
            "xor",
            "vector",
            "std",
            "size_t",
        ]
    )
    if (keywords | set(keyword.kwlist)).intersection(types):
        raise UnsupportedSourceError(
            "Parameter names conflict with C++/Python keywords or generated types"
        )
    statements: list[Assignment] = []

    def walk(node: Node, loops: tuple[Loop, ...] = ()) -> None:
        kind = node.get("kind")
        if kind == "CompoundStmt":
            for child in _children(node):
                walk(child, loops)
        elif kind == "ForStmt":
            loop = _loop(node, dimensions)
            if len(loops) >= 2 or loop.index in {p.index for p in loops}:
                raise UnsupportedSourceError("Only two distinct nested loop counters are supported")
            walk(_children(node)[-1], (*loops, loop))
        elif kind == "DeclStmt":
            if loops or any(
                n["type"]["qualType"] != "int" or _children(n) for n in _children(node)
            ):
                raise UnsupportedSourceError(
                    "Only uninitialized integer counters may precede loops"
                )
        elif kind in {"BinaryOperator", "CompoundAssignOperator"}:
            statements.append(_assign(node, loops))
        else:
            raise UnsupportedSourceError(f"Unsupported statement: {kind}")

    body = next((n for n in _children(function) if n.get("kind") == "CompoundStmt"), None)
    if body is None or not str(function["type"]["qualType"]).startswith("void ("):
        raise UnsupportedSourceError("Expected a defined void-returning C kernel")
    walk(body)
    zeros: dict[str, Assignment] = {}
    updates: dict[str, Assignment] = {}
    for stmt in statements:
        table = updates if stmt.matrix else zeros
        if stmt.output in table:
            raise UnsupportedSourceError(
                f"Multiple initializations or reductions for {stmt.output}"
            )
        table[stmt.output] = stmt
    if not updates or not zeros.keys() <= updates.keys():
        raise UnsupportedSourceError("Every initialized output must have exactly one reduction")
    if {f"stage_{name}_torch" for name in updates}.intersection(types):
        raise UnsupportedSourceError(
            "Parameter names conflict with generated Torch stage functions"
        )
    stages: dict[str, Stage] = {}
    for output, update in updates.items():
        if len(update.loops) != 2 or ranks.get(output) != 1:
            raise UnsupportedSourceError("Each reduction must have two loops and a vector output")
        outer, inner = update.loops
        if update.index not in {outer.index, inner.index}:
            raise UnsupportedSourceError("Output subscript must be a loop counter")
        output_loop = outer if update.index == outer.index else inner
        reduction_loop = inner if output_loop == outer else outer
        if (
            update.matrix_indices not in {(outer.index, inner.index), (inner.index, outer.index)}
            or update.vector_index != reduction_loop.index
        ):
            raise UnsupportedSourceError("Unsupported matrix/vector indexing relationship")
        if ranks.get(update.matrix) != 2 or ranks.get(update.vector) != 1:
            raise UnsupportedSourceError(
                "Reduction accesses must refer to declared matrix/vector parameters"
            )
        zero = zeros.get(output)
        if zero is not None and (len(zero.loops) != 1 or zero.index != zero.loops[0].index):
            raise UnsupportedSourceError(
                "Zero initialization must cover the complete output vector"
            )
        if zero is not None and zero.loops[0].bound != output_loop.bound:
            raise UnsupportedSourceError("Initialization and output dimensions differ")
        fully_before = zero is not None and zero.loops[0].end < outer.begin
        per_row = (
            zero is not None
            and output_loop == outer
            and zero.loops[0] == outer
            and zero.position < inner.begin
        )
        if zero is not None and not (fully_before or per_row):
            raise UnsupportedSourceError(
                "Output initialization does not precede its full reduction"
            )
        transpose = update.matrix_indices[1] == update.index
        stages[output] = Stage(
            output,
            update.matrix,
            update.vector,
            transpose,
            output_loop.bound,
            reduction_loop.bound,
            update.matrix_first,
            update.accumulator_first,
            zero is None,
        )
    ordered: list[Stage] = []
    pending = dict(stages)
    while pending:
        ready = [s for s in pending.values() if s.vector not in pending]
        if not ready:
            raise UnsupportedSourceError("Cyclic or in-place reduction dependency")
        for stage in ready:
            if stage.vector in updates:
                producer, consumer = updates[stage.vector], updates[stage.output]
                complete = producer.loops[0].end < consumer.position
                per_row = (
                    producer.loops[0] == consumer.loops[0]
                    and producer.index == producer.loops[0].index
                    and consumer.vector_index == producer.index
                    and producer.loops[1].end < consumer.position
                )
                if not (complete or per_row):
                    raise UnsupportedSourceError(
                        "A reduction reads an intermediate before it is complete"
                    )
            ordered.append(stage)
            del pending[stage.output]
    bias_inputs = {s.output for s in stages.values() if s.bias}
    inputs = tuple(
        name for name in types if name in ranks and (name not in stages or name in bias_inputs)
    )
    if (
        set(inputs)
        != ({name for s in stages.values() for name in [s.matrix, s.vector]} - stages.keys())
        | bias_inputs
    ):
        raise UnsupportedSourceError(
            "Unused array parameters require an explicit interface decision"
        )
    return Program(
        str(function["name"]),
        next(iter(scalars)),
        tuple(name for name in types if name in dimensions),
        inputs,
        tuple(name for name in types if name in stages),
        tuple(ordered),
    )


def stage_source(stage: Stage, scalar: str) -> str:
    access = "weight[col][row]" if stage.transpose else "weight[row][col]"
    product = f"{access} * input[col]" if stage.matrix_first else f"input[col] * {access}"
    expression = f"curr + {product}" if stage.accumulator_first else f"{product} + curr"
    rows = "weight[0].size()" if stage.transpose else "weight.size()"
    columns = "weight.size()" if stage.transpose else "input.size()"
    bias_arg = f", vector<{scalar}> bias" if stage.bias else ""
    initial = "bias[row]" if stage.bias else "0"
    return f"""#include <vector>
using namespace std;

vector<{scalar}> stage_{stage.output}(vector<vector<{scalar}>> weight,
                                    vector<{scalar}> input{bias_arg}) {{
    vector<{scalar}> output;
    int m = {rows};
    int n = {columns};
    for (int row = 0; row < m; row++) {{
        {scalar} curr = {initial};
        for (int col = 0; col < n; col++) {{
            curr = {expression};
        }}
        output.push_back(curr);
    }}
    return output;
}}
"""


def _wrapper(program: Program) -> str:
    scalar = program.scalar
    matrices = {s.matrix for s in program.stages}
    args = [f"int {name}" for name in program.dimensions]
    args += [
        f"vector<vector<{scalar}>> {name}" if name in matrices else f"vector<{scalar}> {name}"
        for name in program.inputs
    ]
    lines = ["#include <stdexcept>"]
    lines += [f'#include "stage_{s.output}.reference.cc"' for s in program.stages]
    lines += [f"\nvector<vector<{scalar}>> {program.function}_adapted({', '.join(args)}) {{"]
    for s in program.stages:
        rows, cols = (s.columns, s.rows) if s.transpose else (s.rows, s.columns)
        lines += [
            f"    if ({s.rows} <= 0 || {s.columns} <= 0 || "
            f"{s.matrix}.size() != static_cast<size_t>({rows}) || "
            f"{s.vector}.size() != static_cast<size_t>({s.columns}))",
            '        throw std::invalid_argument("logical dimensions must match vector shapes");',
            f"    for (const auto& row : {s.matrix})",
            f"        if (row.size() != static_cast<size_t>({cols}))",
            '            throw std::invalid_argument("matrix must be rectangular");',
            *(
                [
                    f"    if ({s.output}.size() != static_cast<size_t>({s.rows}))",
                    '        throw std::invalid_argument("bias shape does not match output");',
                ]
                if s.bias
                else []
            ),
            f"    {'' if s.bias else f'vector<{scalar}> '}{s.output} = "
            f"stage_{s.output}({s.matrix}, {s.vector}{', ' + s.output if s.bias else ''});",
        ]
    lines += ["    return {" + ", ".join(program.outputs) + "};", "}"]
    return "\n".join(lines) + "\n"


def prepare(
    source: Path,
    output: Path,
    *,
    function: str | None = None,
    includes: tuple[Path, ...] = (),
    defines: tuple[str, ...] = (),
    clang: str = "clang",
    integer_model: bool = False,
    extended: bool = False,
    ordered_reductions: bool = False,
    scalar_step_limit: int = 100000,
) -> dict[str, Any]:
    """Prepare files only; neither compile Tenspiler inputs nor invoke solvers."""
    if output.exists():
        raise FileExistsError(f"Output already exists: {output}")
    if scalar_step_limit < 1:
        raise UnsupportedSourceError("Scalar step limit must be positive")
    source = source.resolve(strict=True)
    command = [clang, "-x", "c", "-fsyntax-only", "-Xclang", "-ast-dump=json"]
    command += [f"-I{p.resolve()}" for p in includes]
    command += [f"-D{d}" for d in defines]
    with tempfile.TemporaryDirectory(prefix="tenspiler-prepare-") as temporary:
        depfile = Path(temporary) / "inputs.d"
        result = subprocess.run(
            [*command, "-MMD", "-MF", str(depfile), "-MT", "input", str(source)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode:
            raise UnsupportedSourceError(
                f"Clang could not parse the input:\n{result.stderr[-4000:]}"
            )
        ast: Node = json.loads(result.stdout)
        candidates = [
            n
            for n in _children(ast)
            if n.get("kind") == "FunctionDecl"
            and any(c.get("kind") == "CompoundStmt" for c in _children(n))
            and (
                n.get("name") == function
                if function
                else str(n.get("name", "")).startswith("kernel_")
            )
        ]
        if len(candidates) != 1:
            raise UnsupportedSourceError("Select exactly one kernel with --function")
        candidate = candidates[0]
        try:
            if ordered_reductions:
                raise UnsupportedSourceError(
                    "Ordered reductions require composed operator execution"
                )
            program = analyze(candidate)
        except UnsupportedSourceError as original_error:
            if not extended:
                raise
            if not integer_model:
                raise UnsupportedSourceError(
                    "Extended composition requires explicit --integer-model"
                ) from original_error
            try:
                plan = normalize(candidate)
                plan["ordered_reductions"] = ordered_reductions
                if ordered_reductions:
                    plan["operators"].remove("mv")
                plan["scalar_step_limit"] = scalar_step_limit
            except ValueError as exc:
                raise UnsupportedSourceError(str(exc)) from exc
            dependencies = shlex.split(depfile.read_text().replace("\\\n", " ").split(":", 1)[1])
            return emit(
                plan,
                source,
                output,
                {
                    "tool": "lassi_x.tenspiler_prepare",
                    "source": str(source),
                    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    "dependencies": {
                        str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest()
                        for p in sorted(set(dependencies))
                    },
                    "clang_command": [*command, str(source)],
                    "direct_path_diagnostic": str(original_error),
                    "model_calls": 0,
                },
            )
        dependencies = shlex.split(depfile.read_text().replace("\\\n", " ").split(":", 1)[1])
    generated: dict[str, str] = {"kernel.reference.cc": _wrapper(program)}
    for stage in program.stages:
        generated[f"stage_{stage.output}.reference.cc"] = stage_source(stage, program.scalar)
        if integer_model or program.scalar == "int":
            generated[f"stage_{stage.output}.cc"] = stage_source(stage, "int")
    if integer_model or program.scalar == "int":
        generated["synthesize.py"] = (
            files("lassi_x").joinpath("resources/tenspiler-driver.py.txt").read_text()
        )
    generated["README.md"] = (
        "# Prepared Tenspiler input\n\n"
        "Original source is unchanged. kernel.reference.cc preserves its scalar type; "
        "returned vectors follow manifest.json output order. Only disjoint arrays with "
        "positive logical dimensions exactly matching vector shapes are supported.\n\n"
        "The optional integer model changes arithmetic semantics. Verification of it "
        "does not prove floating-point equivalence; validate generated Torch against "
        "the original C. Preparation makes no model calls.\n\n"
        "With integer-model files present, activate the Tenspiler environment and run:\n\n"
        "```sh\npython synthesize.py --tenspiler-root /path/to/tenspiler "
        "--llvm-bin /path/to/llvm11/bin --llvm-pass /path/to/libAddEmptyBlocksPass.so\n```\n\n"
        "This separate command compiles the model, runs synthesis with verification, "
        "and emits Torch. It needs native Racket, Bitwuzla and CVC5 configured as in "
        "your Tenspiler installation. Defaults: bound 2, 30 seconds per stage. "
        "Further runs require a new --run-dir. No generated output is certified until "
        "checked against the original C.\n"
    )
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "tool": "lassi_x.tenspiler_prepare",
        "source": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "dependencies": {
            str(Path(p).resolve()): hashlib.sha256(Path(p).read_bytes()).hexdigest()
            for p in sorted(set(dependencies))
        },
        "clang_command": [*command, str(source)],
        "program": asdict(program),
        "integer_model": integer_model or program.scalar == "int",
        "floating_point_equivalence_proven": False,
        "model_calls": 0,
        "contract": "Disjoint arrays; rectangular matrices; positive exact logical shapes",
        "generated_sha256": {
            name: hashlib.sha256(text.encode()).hexdigest() for name, text in generated.items()
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, text in generated.items():
        (output / name).write_text(text)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--function")
    parser.add_argument("--include", type=Path, action="append", default=[])
    parser.add_argument("--define", action="append", default=[])
    parser.add_argument("--clang", default="clang")
    parser.add_argument(
        "--extended",
        action="store_true",
        help="Allow deterministic loop composition of Tenspiler operator models",
    )
    parser.add_argument(
        "--ordered-reductions",
        action="store_true",
        help="Preserve scalar accumulation order in composed reductions",
    )
    parser.add_argument(
        "--scalar-step-limit",
        type=int,
        default=100000,
        help="Finite residual scalar-loop budget in composed execution",
    )
    parser.add_argument(
        "--integer-model",
        action="store_true",
        help="Also emit a separate, explicitly non-equivalent integer synthesis model",
    )
    args = parser.parse_args()
    try:
        manifest = prepare(
            args.source,
            args.output,
            function=args.function,
            includes=tuple(args.include),
            defines=tuple(args.define),
            clang=args.clang,
            integer_model=args.integer_model,
            extended=args.extended,
            ordered_reductions=args.ordered_reductions,
            scalar_step_limit=args.scalar_step_limit,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, f"Preparation refused: {exc}\n")
    print(json.dumps({"output": str(args.output), "program": manifest["program"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
