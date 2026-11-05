"""Deterministic, restricted Torch/FPCore bridge; never invokes a language model.

Preparation does not import the input module or run Herbie. Generated candidates
are proposals requiring the normal C, FP32, precision and target validation gates.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import os
import re
import shutil
import signal
import struct
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

type Expr = str | list[Expr]
PRECISIONS = {
    "binary16": "float16",
    "bfloat16": "bfloat16",
    "binary32": "float32",
    "binary64": "float64",
}
UNARY = {
    "abs": "fabs",
    "sqrt": "sqrt",
    "exp": "exp",
    "expm1": "expm1",
    "log": "log",
    "log1p": "log1p",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "sinh": "sinh",
    "cosh": "cosh",
    "tanh": "tanh",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
}
NUMERIC = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")
SYMBOL = re.compile(r"[A-Za-z_][A-Za-z_0-9]*\Z")


class UnsupportedExpressionError(ValueError):
    """The requested transformation cannot preserve the supported contract."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(expr: Expr) -> str:
    return "(" + " ".join(map(_dump, expr)) + ")" if isinstance(expr, list) else expr


def parse(text: str) -> list[Expr]:
    """Read a restricted S-expression language without executing Racket or Python."""
    text = re.sub(r";[^\n]*", "", text)
    tokens = re.findall(r'"(?:\\.|[^"\\])*"|[()\[\]]|[^\s()\[\]]+', text)
    stack: list[list[Expr]] = [[]]
    brackets: list[str] = []
    for token in tokens:
        if token in {"(", "["}:
            child: list[Expr] = []
            stack[-1].append(child)
            stack.append(child)
            brackets.append(token)
        elif token in {")", "]"}:
            if len(stack) == 1 or brackets.pop() != ({")": "(", "]": "["}[token]):
                raise UnsupportedExpressionError("Unbalanced FPCore brackets")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1:
        raise UnsupportedExpressionError("Unbalanced FPCore brackets")
    return stack[0]


@dataclass
class Program:
    """One stateless, straight-line tensor forward and its scalar expression."""

    tree: ast.Module
    forward: ast.FunctionDef
    arguments: list[str]
    expression: Expr
    precision: str


def extract(source: str, class_name: str, precision: str = "binary32") -> Program:
    """Extract a named class's entire elementwise forward, refusing unknown semantics."""
    if precision not in PRECISIONS:
        raise ValueError("Unknown precision")
    tree = ast.parse(source)
    # Require the spelling we lower to actually denote the Torch import.
    torch_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.Import)
        and len(node.names) == 1
        and node.names[0].name == "torch"
        and node.names[0].asname is None
    ]
    if len(torch_imports) != 1:
        raise UnsupportedExpressionError("Require one unaliased 'import torch'")
    for node in tree.body:
        if node is torch_imports[0]:
            continue
        if any(
            isinstance(n, ast.Name) and n.id == "torch" and isinstance(n.ctx, ast.Store)
            for n in ast.walk(node)
        ):
            raise UnsupportedExpressionError("Torch rebinding is unsupported")
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == class_name]
    if len(classes) != 1:
        raise UnsupportedExpressionError("Select exactly one named class")
    cls = classes[0]
    members = [
        n
        for n in cls.body
        if not (
            isinstance(n, ast.Expr)
            and isinstance(n.value, ast.Constant)
            and isinstance(n.value.value, str)
        )
    ]
    if (
        cls.decorator_list
        or cls.keywords
        or len(cls.bases) != 1
        or ast.unparse(cls.bases[0]) != "torch.nn.Module"
        or len(members) != 1
        or not isinstance(members[0], ast.FunctionDef)
        or members[0].name != "forward"
    ):
        raise UnsupportedExpressionError(
            "Require a stateless torch.nn.Module containing only forward"
        )
    forward = members[0]
    args = forward.args
    if (
        forward.decorator_list
        or args.posonlyargs
        or args.kwonlyargs
        or args.vararg
        or args.kwarg
        or args.defaults
        or not args.args
        or args.args[0].arg != "self"
    ):
        raise UnsupportedExpressionError(
            "Require plain positional tensor arguments without defaults"
        )
    arguments = [arg.arg for arg in args.args[1:]]
    if not arguments or any(
        not SYMBOL.fullmatch(a) or a.startswith("_") or a == "torch" for a in arguments
    ):
        raise UnsupportedExpressionError("Require tensor arguments with plain nonreserved names")
    env: dict[str, tuple[Expr, str | None]] = {
        name: (f"arg{i}", precision) for i, name in enumerate(arguments)
    }

    def lower(node: ast.expr) -> tuple[Expr, str | None]:
        if isinstance(node, ast.Name) and node.id in env:
            return env[node.id]
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
            and math.isfinite(node.value)
        ):
            return repr(node.value), None
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value, dtype = lower(node.operand)
            return (["-", value] if isinstance(node.op, ast.USub) else value), dtype
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)
        ):
            left, lp = lower(node.left)
            right, rp = lower(node.right)
            if lp is None and rp is None:
                raise UnsupportedExpressionError("Constant-only arithmetic uses Python rounding")
            if lp and rp and lp != rp:
                raise UnsupportedExpressionError(
                    "Use explicit casts before combining tensor precisions"
                )
            # Torch uses an opmath scalar for half tensor/scalar arithmetic;
            # FPCore rounds literals to the operation's representation instead.
            for value, value_precision in ((left, lp), (right, rp)):
                if value_precision is None and (lp or rp) in {"binary16", "bfloat16"}:
                    atom = value
                    sign = 1
                    while isinstance(atom, list) and len(atom) == 2 and atom[0] == "-":
                        sign *= -1
                        atom = atom[1]
                    if not isinstance(atom, str):
                        raise UnsupportedExpressionError("Unsupported scalar expression")
                    number = sign * float(atom)
                    try:
                        rounded = (
                            struct.unpack("e", struct.pack("e", number))[0]
                            if (lp or rp) == "binary16"
                            else struct.unpack("f", struct.pack("f", number))[0]
                        )
                    except OverflowError as exc:
                        raise UnsupportedExpressionError("Scalar exceeds the base format") from exc
                    bits = struct.unpack("I", struct.pack("f", rounded))[0]
                    if rounded != number or ((lp or rp) == "bfloat16" and bits & 0xFFFF):
                        raise UnsupportedExpressionError(
                            "Half-precision scalars must be exactly representable"
                        )
            op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/"}[type(node.op)]
            return [op, left, right], lp or rp
        if (
            isinstance(node, ast.Call)
            and not node.keywords
            and isinstance(node.func, ast.Attribute)
        ):
            if (
                isinstance(node.func.value, ast.Name)
                and node.func.value.id == "torch"
                and node.func.attr in UNARY
                and len(node.args) == 1
            ):
                value, dtype = lower(node.args[0])
                if dtype is None:
                    raise UnsupportedExpressionError(
                        "Torch unary functions require tensor operands"
                    )
                return [UNARY[node.func.attr], value], dtype
            if node.func.attr == "to" and len(node.args) == 1:
                target = ast.unparse(node.args[0])
                dtype = next((p for p, d in PRECISIONS.items() if target == f"torch.{d}"), None)
                if dtype is not None:
                    value, old = lower(node.func.value)
                    if old is None:
                        raise UnsupportedExpressionError("Cannot cast a Python scalar as a tensor")
                    # A cast changes its result context, not the arithmetic
                    # that produced its operand.
                    return [
                        "!",
                        ":precision",
                        dtype,
                        ["cast", ["!", ":precision", old, value]],
                    ], dtype
        raise UnsupportedExpressionError(f"Unsupported Torch expression: {ast.unparse(node)}")

    returned: tuple[Expr, str | None] | None = None
    for statement in forward.body:
        if (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        ):
            continue
        if returned is not None:
            raise UnsupportedExpressionError("Statements after return are unsupported")
        if (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
        ):
            name = statement.targets[0].id
            if name in {"torch", "self"} or name in env:
                raise UnsupportedExpressionError("Reassignment is unsupported")
            env[name] = lower(statement.value)
        elif isinstance(statement, ast.Return) and statement.value is not None:
            returned = lower(statement.value)
        else:
            raise UnsupportedExpressionError(
                "Only single assignments and one tensor return are supported"
            )
    if returned is None or returned[1] != precision:
        raise UnsupportedExpressionError("Return must be a tensor in the declared base precision")

    def atoms(expr: Expr) -> set[str]:
        return set().union(*(atoms(e) for e in expr)) if isinstance(expr, list) else {expr}

    if not {f"arg{i}" for i in range(len(arguments))} <= atoms(returned[0]):
        raise UnsupportedExpressionError(
            "Unused tensor arguments have no defined output broadcast shape"
        )
    return Program(tree, forward, arguments, returned[0], precision)


def fpcore(program: Program, domains: dict[str, tuple[float, float]]) -> str:
    """Emit an expression with an explicitly supplied, finite input domain."""
    if set(domains) != set(program.arguments):
        raise ValueError("Supply exactly one domain per forward argument")
    conditions: list[Expr] = ["and"]
    for i, name in enumerate(program.arguments):
        lo, hi = domains[name]
        if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
            raise ValueError("Domains must have finite increasing bounds")
        conditions.append(["<=", repr(lo), f"arg{i}", repr(hi)])
    return (
        _dump(
            [
                "FPCore",
                [f"arg{i}" for i in range(len(program.arguments))],
                ":precision",
                program.precision,
                ":pre",
                conditions,
                program.expression,
            ]
        )
        + "\n"
    )


def _properties(items: list[Expr]) -> dict[str, Expr]:
    if len(items) % 2:
        raise UnsupportedExpressionError("Malformed FPCore properties")
    result: dict[str, Expr] = {}
    for i in range(0, len(items), 2):
        key = items[i]
        if not isinstance(key, str) or not key.startswith(":") or key in result:
            raise UnsupportedExpressionError("Malformed or duplicate FPCore property")
        result[key] = items[i + 1]
    return result


def _bounds(expr: Expr | None, arguments: list[str]) -> dict[str, tuple[Fraction, Fraction]]:
    """Normalize conjunctions of inclusive ranges, including chained comparisons."""
    lower: dict[str, Fraction] = {}
    upper: dict[str, Fraction] = {}

    def visit(term: Expr | None) -> None:
        if not isinstance(term, list) or not term:
            raise UnsupportedExpressionError("Missing or unsupported input precondition")
        if term[0] == "and":
            for condition in term[1:]:
                visit(condition)
        elif term[0] == "<=" and len(term) >= 3:
            for left, right in zip(term[1:-1], term[2:], strict=True):
                if not isinstance(left, str) or not isinstance(right, str):
                    raise UnsupportedExpressionError("Unsupported input bound")
                if left in arguments and right not in arguments:
                    number = Fraction(right)
                    upper[left] = min(upper.get(left, number), number)
                elif right in arguments and left not in arguments:
                    number = Fraction(left)
                    lower[right] = max(lower.get(right, number), number)
                else:
                    raise UnsupportedExpressionError("Unsupported input bound")
        else:
            raise UnsupportedExpressionError("Unsupported input precondition")

    visit(expr)
    if set(lower) != set(arguments) or set(upper) != set(arguments):
        raise UnsupportedExpressionError("Every input needs both domain bounds")
    return {name: (lower[name], upper[name]) for name in arguments}


def generate(program: Program, improved: str) -> str:
    """Generate dtype-explicit tensor code from one supported Herbie result.

    Other input dtypes execute the original forward. This is a proposal, not an
    equivalence proof; the external validation suite owns acceptance.
    """
    program = copy.deepcopy(program)
    forms = parse(improved)
    if len(forms) != 1 or not isinstance(forms[0], list):
        raise UnsupportedExpressionError("Expected exactly one FPCore result")
    core = forms[0]
    expected: list[Expr] = [f"arg{i}" for i in range(len(program.arguments))]
    if len(core) < 3 or core[0] != "FPCore" or core[1] != expected:
        raise UnsupportedExpressionError("Herbie changed the argument contract")
    props = _properties(core[2:-1])
    if props.get(":precision", "binary64") != program.precision:
        raise UnsupportedExpressionError("Herbie changed the result precision")
    code: list[str] = []
    counter = 0

    def bind(expression: str) -> str:
        nonlocal counter
        name = f"_herbie_{counter}"
        counter += 1
        code.append(f"{name} = {expression}")
        return name

    def lower(expr: Expr, precision: str, env: dict[str, tuple[str, str]]) -> tuple[str, str]:
        dtype = f"torch.{PRECISIONS[precision]}"
        if isinstance(expr, str):
            if expr in env:
                return env[expr]
            if not NUMERIC.fullmatch(expr) or not math.isfinite(float(expr)):
                raise UnsupportedExpressionError(f"Unsupported FPCore atom: {expr}")
            return bind(
                f"torch.tensor({expr}, dtype={dtype}, device=_herbie_template.device)"
                ".expand_as(_herbie_template)"
            ), precision
        if not expr or not isinstance(expr[0], str):
            raise UnsupportedExpressionError("Malformed expression")
        op, values = expr[0], expr[1:]
        if op == "!":
            if len(values) < 3:
                raise UnsupportedExpressionError("Malformed annotation")
            annotations = _properties(values[:-1])
            if (
                set(annotations) != {":precision"}
                or not isinstance(annotations[":precision"], str)
                or annotations[":precision"] not in PRECISIONS
            ):
                raise UnsupportedExpressionError(
                    "Only explicit precision annotations are supported"
                )
            new_precision = str(annotations[":precision"])
            return lower(values[-1], new_precision, env)
        if op in {"let", "let*"} and len(values) == 2 and isinstance(values[0], list):
            local = dict(env)
            seen: set[str] = set()
            for binding in values[0]:
                if (
                    not isinstance(binding, list)
                    or len(binding) != 2
                    or not isinstance(binding[0], str)
                    or not SYMBOL.fullmatch(binding[0])
                    or binding[0] in seen
                ):
                    raise UnsupportedExpressionError("Malformed let binding")
                seen.add(binding[0])
                local[binding[0]] = lower(binding[1], precision, local if op == "let*" else env)
            return lower(values[1], precision, local)
        if op == "cast" and len(values) == 1:
            value, _ = lower(values[0], precision, env)
            return bind(f"{value}.to(dtype={dtype})"), precision
        inverse = {v: k for k, v in UNARY.items()}
        if op in {"+", "-", "*", "/"} and (len(values) == 2 or (op == "-" and len(values) == 1)):
            operands = [lower(v, precision, env) for v in values]
            if any(p != precision for _, p in operands):
                raise UnsupportedExpressionError("FPCore operation requires explicit operand casts")
            names = [n for n, _ in operands]
            expression = f"(-{names[0]})" if len(names) == 1 else f"({names[0]} {op} {names[1]})"
        elif op in inverse and len(values) == 1:
            value, actual = lower(values[0], precision, env)
            if actual != precision:
                raise UnsupportedExpressionError("FPCore operation requires explicit operand casts")
            expression = f"torch.{inverse[op]}({value})"
        else:
            raise UnsupportedExpressionError(f"Unsupported Herbie operator: {op}")
        return bind(f"{expression}.to(dtype={dtype})"), precision

    # Broadcasting all arguments here ensures rewritten constants and eliminated
    # arguments still return the original declared elementwise output shape.
    args = ", ".join(program.arguments)
    code.append(f"_herbie_inputs = torch.broadcast_tensors({args})")
    code.append("_herbie_template = _herbie_inputs[0]")
    env = {
        f"arg{i}": (f"_herbie_inputs[{i}]", program.precision)
        for i in range(len(program.arguments))
    }
    result, result_precision = lower(core[-1], program.precision, env)
    if result_precision != program.precision:
        raise UnsupportedExpressionError("Result does not have the declared precision")
    code.append(f"return {result}")
    guard = (
        "if "
        + " and ".join(
            f"torch.is_tensor({name}) and {name}.dtype == torch.{PRECISIONS[program.precision]} "
            f"and {name}.device == {program.arguments[0]}.device"
            for name in program.arguments
        )
        + ":"
    )
    replacement = ast.parse(guard + "\n" + "\n".join("    " + line for line in code)).body[0]
    assert isinstance(replacement, ast.If)
    replacement.orelse = program.forward.body
    program.forward.body = [replacement]
    ast.fix_missing_locations(program.tree)
    return ast.unparse(program.tree) + "\n"


def prepare(
    source: Path,
    output: Path,
    *,
    class_name: str,
    domains: dict[str, tuple[float, float]],
    precision: str = "binary32",
    platform: Path | None = None,
) -> dict[str, object]:
    """Prepare content-addressed inputs only; no module import or external execution."""
    data = source.read_bytes()
    program = extract(data.decode(), class_name, precision)
    core = fpcore(program, domains)
    if precision in {"binary16", "bfloat16"} and platform is None:
        raise ValueError("FP16/BF16 search requires an explicit custom Herbie platform")
    platform_data = platform.read_bytes() if platform else None
    manifest: dict[str, object] = {
        "schema": 1,
        "tool": "lassi_x.herbie",
        "source": str(source.resolve()),
        "source_sha256": _sha(data),
        "class_name": class_name,
        "precision": precision,
        "domains": domains,
        "arguments": program.arguments,
        "input_fpcore_sha256": _sha(core.encode()),
        "adapter_sha256": _sha(Path(__file__).read_bytes()),
        "platform": str(platform.resolve()) if platform else "herbie20",
        "platform_sha256": _sha(platform_data) if platform_data else None,
        "validated": False,
        "status": "prepared",
    }
    output.mkdir(parents=True, exist_ok=False)
    (output / "original.py").write_bytes(data)
    (output / "input.fpcore").write_text(core)
    if platform_data is not None:
        (output / "platform.rkt").write_bytes(platform_data)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def optimize(
    prepared: Path,
    *,
    command: list[str],
    seed: int = 1,
    timeout_s: float = 60,
) -> Path:
    """Run one bounded Herbie process and emit an unvalidated proposal on success."""
    if not command or not 0 <= seed < 2**31 or not math.isfinite(timeout_s) or timeout_s <= 0:
        raise ValueError("Require a command, valid seed and positive finite timeout")
    manifest = json.loads((prepared / "manifest.json").read_text())
    if manifest["status"] != "prepared":
        raise ValueError("Each prepared directory supports exactly one execution attempt")
    data = (prepared / "original.py").read_bytes()
    core_data = (prepared / "input.fpcore").read_bytes()
    if (
        _sha(data) != manifest["source_sha256"]
        or _sha(core_data) != manifest["input_fpcore_sha256"]
        or _sha(Path(__file__).read_bytes()) != manifest["adapter_sha256"]
    ):
        raise ValueError("Prepared inputs or adapter changed")
    platform: str = manifest["platform"]
    if manifest["platform_sha256"]:
        platform_path = prepared / "platform.rkt"
        if _sha(platform_path.read_bytes()) != manifest["platform_sha256"]:
            raise ValueError("Prepared platform changed")
        platform = str(platform_path.resolve())
    program = extract(data.decode(), manifest["class_name"], manifest["precision"])
    destination = prepared / "improved.fpcore"
    proposal = prepared / "proposal.py"
    if destination.exists() or proposal.exists():
        raise FileExistsError("Execution outputs already exist")
    argv = [
        *command,
        "improve",
        "--seed",
        str(seed),
        "--timeout",
        str(timeout_s),
        "--platform",
        platform,
        "--disable",
        "reduce:regimes",
    ]
    if manifest["precision"] in {"binary16", "bfloat16"}:
        # The pinned Rival 3 shim only recognizes binary32/binary64. Rival 2
        # accepts a platform's representation converter and error metric.
        argv.extend(["--enable", "setup:rival2"])
    argv.extend([str((prepared / "input.fpcore").resolve()), str(destination.resolve())])
    executable = shutil.which(command[0])
    manifest["command_files_sha256"] = (
        {
            str(path.resolve()): _sha(path.read_bytes())
            for path in [Path(executable), *(Path(arg) for arg in command[1:])]
            if path.is_file()
        }
        if executable
        else {}
    )
    manifest.update(status="running", command=argv, seed=seed, timeout_s=timeout_s)

    def save() -> None:
        (prepared / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    save()
    try:
        with (
            (prepared / "stdout.log").open("wb") as stdout,
            (prepared / "stderr.log").open("wb") as stderr,
        ):
            process = subprocess.Popen(
                argv, stdout=stdout, stderr=stderr, start_new_session=os.name == "posix"
            )
            try:
                process.wait(timeout=timeout_s)
            finally:
                if os.name == "posix":
                    with suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                elif process.poll() is None:
                    process.kill()
                process.wait()
        manifest["returncode"] = process.returncode
        if process.returncode:
            raise RuntimeError(f"Herbie exited with status {process.returncode}; see stderr.log")
        improved = destination.read_text()
        # `improve` can exit zero and return the original expression after a
        # failed job. Its documented result comments must not become proposals.
        if re.search(r"(?m)^;;\s+(?:(?:Crash|Error) in\b|.* times out in\b)", improved):
            raise RuntimeError("Herbie reported an unsuccessful job; see improved.fpcore")
        original_forms, improved_forms = parse(core_data.decode()), parse(improved)
        original_form, improved_form = (
            original_forms[0],
            improved_forms[0] if improved_forms else "",
        )
        try:
            if not isinstance(original_form, list) or not isinstance(improved_form, list):
                raise UnsupportedExpressionError("Malformed FPCore")
            names = [f"arg{i}" for i in range(len(program.arguments))]
            if _bounds(_properties(original_form[2:-1]).get(":pre"), names) != _bounds(
                _properties(improved_form[2:-1]).get(":pre"), names
            ):
                raise UnsupportedExpressionError("Changed bounds")
        except ValueError as exc:
            raise UnsupportedExpressionError(
                "Herbie changed or omitted the declared input domain"
            ) from exc
        candidate = generate(program, improved)
        compile(candidate, str(proposal), "exec")
        proposal.write_text(candidate)
        manifest.update(
            status="proposal",
            proposal_sha256=_sha(candidate.encode()),
            improved_fpcore_sha256=_sha(improved.encode()),
        )
        save()
        return proposal
    except BaseException as exc:
        manifest.update(status="failed", failure_type=type(exc).__name__)
        save()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("source", type=Path)
    prep.add_argument("output", type=Path)
    prep.add_argument("--class-name", required=True)
    prep.add_argument("--domains", type=Path, required=True, help='JSON: {"x": [lower, upper]}')
    prep.add_argument("--precision", choices=PRECISIONS, default="binary32")
    prep.add_argument("--platform", type=Path)
    run = sub.add_parser("optimize")
    run.add_argument("prepared", type=Path)
    run.add_argument("--seed", type=int, default=1)
    run.add_argument("--timeout", type=float, default=60)
    run.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        required=True,
        help="Herbie executable and prefix arguments; must be the final option",
    )
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            prepare(
                args.source,
                args.output,
                class_name=args.class_name,
                domains=json.loads(args.domains.read_text()),
                precision=args.precision,
                platform=args.platform,
            )
        else:
            print(
                optimize(
                    args.prepared, command=args.command, seed=args.seed, timeout_s=args.timeout
                )
            )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"{exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
