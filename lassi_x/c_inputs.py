"""Capture trusted initialized inputs by executing the original C initialization.

The reference is instrumented at the initialization/computation boundary. The
configured compiler, type/profile flags, and headers are retained. C algorithms
are never called to produce these fixtures and Torch is not used to generate them.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from .input_contract import load_contract, save_contract

if TYPE_CHECKING:
    from .config import RunConfig
    from .validation import OracleResult


# Explicit computation boundaries for scientific references with inline main
# bodies. Shapes refer to C macros, not independently copied size tables.
SCIENCE: dict[str, tuple[str, dict[str, tuple[str, ...]], list[str]]] = {
    "direct-dft": (
        "  for (int k = 0; k < SIZE; ++k) {\n    real",
        {"signal": ("SIZE",)},
        ["signal"],
    ),
    "softened-nbody": (
        "  for (int i = 0; i < SIZE; ++i) {\n    for (int d = 0; d < 3; ++d) acceleration",
        {"position": ("SIZE", "3"), "mass": ("SIZE",)},
        ["position", "mass"],
    ),
    "lorenz-rk4": ("  for (int step =", {"state": ("SIZE", "3"), "dt": ()}, ["state"]),
    "poisson-cg": (
        "  for (int step =",
        {"x": ("SIZE",), "r": ("SIZE",), "p": ("SIZE",), "ap": ("SIZE",), "rr": ()},
        ["r"],
    ),
    "jpeg-dct": ("  for (int block_row =", {"image": ("SIZE", "SIZE")}, ["image"]),
    "wavelet-compression": (
        "  int width =",
        {"image": ("SIZE", "SIZE"), "coefficients": ("SIZE", "SIZE")},
        ["image"],
    ),
    "low-rank-compression": (
        "  for (int component =",
        {
            "image": ("SIZE", "SIZE"),
            "residual": ("SIZE", "SIZE"),
            "approximation": ("SIZE", "SIZE"),
        },
        ["image"],
    ),
    "iir-filter-bank": (
        "  for (int filter = 0; filter < FILTERS; ++filter) {\n    double state_one",
        {"signal": ("SIZE",), **{k: ("FILTERS",) for k in ("b0", "b1", "b2", "a1", "a2")}},
        ["signal"],
    ),
}


def _strip_comments(source: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", lambda m: " " * len(m[0]), source)


def instrument_reference(source: str, kernel: str) -> tuple[str, dict[str, Any]]:
    """Produce an initialization-only C executable, or reject unknown layouts."""
    clean = _strip_comments(source)
    main = re.search(r"\bint\s+main\s*\(", clean)
    if main is None:
        raise ValueError("C reference has no supported main entry point")
    tail = clean[main.start() :]
    fields: dict[str, tuple[str, ...]] = {}
    zero: set[str] = set()
    integers: list[str] = []
    if kernel in SCIENCE:
        anchor, fields, required = SCIENCE[kernel]
        if source.count(anchor) != 1:
            raise ValueError(f"scientific C computation boundary changed for {kernel}")
        boundary = source.index(anchor)
        fields = fields.copy()
        if kernel == "poisson-cg":
            zero.add("ap")  # C leaves this write-only workspace uninitialized.
        if kernel == "lorenz-rk4":
            fields["steps"] = ()
            integers.append("steps")
    else:
        # Match the conventional PolyBench main, not arbitrary C programs.
        call = re.search(r"\bkernel_[a-zA-Z0-9_]+\s*\(", tail)
        init = re.search(r"\binit_array\s*\([\s\S]*?;", tail)
        if call is None or init is None:
            raise ValueError(f"no supported C initialization boundary for {kernel}")
        boundary = main.start() + call.start()
        initialized = set(re.findall(r"POLYBENCH_ARRAY\s*\(\s*(\w+)\s*\)", init[0]))
        # Deriche's imgOut is accepted by init_array but never initialized.
        if kernel == "polybench-deriche":
            initialized.discard("imgOut")
        for declaration in re.finditer(r"POLYBENCH_(\d)D_ARRAY_DECL\(([^;]+?)\)\s*;", tail):
            rank = int(declaration[1])
            parts = [p.strip() for p in declaration[2].split(",")]
            if len(parts) != 2 + 2 * rank:
                raise ValueError("unsupported PolyBench array declaration")
            name, ctype = parts[:2]
            fields[name] = tuple(parts[2 : 2 + rank])
            if name not in initialized:
                zero.add(name)
            if ctype == "base" or kernel == "polybench-floyd-warshall":
                integers.append(name)
        if not fields or not initialized:
            raise ValueError("no supported initialized C data arrays found")
        required = sorted(initialized)
        for name in re.findall(r"&\s*(\w+)", init[0]):
            fields[name] = ()
        for name in re.findall(r"\bint\s+(\w+)\s*=", tail[: call.start()]):
            fields[name] = ()
            integers.append(name)
        if kernel == "polybench-nussinov":
            required.remove("table")  # zero DP workspace, not independent data
        if kernel == "polybench-gramschmidt":
            required = ["A"]
        if kernel == "polybench-gemver":
            required = [name for name in required if name not in ("w", "x")]
        if kernel == "polybench-ludcmp":
            required = [name for name in required if name not in ("x", "y")]
        if kernel == "polybench-trisolv":
            required.remove("x")
    dump = ["\n/* LASSI trusted pre-computation input capture. */\n"]
    for name, dims in fields.items():
        dim_args = "".join(f", (int)({d})" for d in dims)
        dim_formats = " %d" * len(dims)
        dump.append(f'printf("@ {name} {len(dims)}{dim_formats}\\n"{dim_args});\n')
        for axis, size in enumerate(dims):
            dump.append(
                f"for (int lassi_input_i{axis}=0; "
                f"lassi_input_i{axis}<({size}); ++lassi_input_i{axis}) {{\n"
            )
        base = f"(POLYBENCH_ARRAY({name}))" if dims and kernel not in SCIENCE else name
        value = base + "".join(f"[lassi_input_i{i}]" for i in range(len(dims)))
        if name in zero:
            value = "0.0"
        elif (kernel == "polybench-trmm" and name == "A") or (
            kernel == "polybench-trisolv" and name == "L"
        ):
            # The source never initializes/reads the strictly upper triangle.
            value = f"(lassi_input_i1 <= lassi_input_i0 ? {value} : 0.0)"
        if kernel == "lorenz-rk4" and name == "steps":
            value = "STEPS"
        dump.append(f'printf("%.17g\\n", (double)({value}));\n')
        dump.extend("}\n" for _ in dims)
    dump.append("return 0;\n")
    return source[:boundary] + "".join(dump) + source[boundary:], {
        "kernel": kernel,
        "required": required,
        "integer_fields": integers,
        "zero_canonicalized_workspaces": sorted(zero),
    }


def parse_capture(text: str) -> dict[str, np.ndarray]:
    lines = iter(text.splitlines())
    arrays = {}
    for line in lines:
        header = line.split()
        if len(header) < 3 or header[0] != "@":
            raise ValueError(f"unexpected C input capture line: {line[:120]}")
        name, rank = header[1], int(header[2])
        shape = tuple(int(x) for x in header[3:])
        if len(shape) != rank or name in arrays:
            raise ValueError("invalid C input capture shape or duplicate field")
        count = int(np.prod(shape)) if shape else 1
        arrays[name] = np.asarray([float(next(lines)) for _ in range(count)]).reshape(shape)
    if not arrays or not all(np.isfinite(v).all() for v in arrays.values()):
        raise ValueError("C input capture is empty or contains nonfinite values")
    return arrays


async def build_input_contract(config: RunConfig, directory: Path) -> Path:
    """Compile initialization using the same build command as the output oracle."""
    from .validation import _format_command, _run  # noqa: PLC0415

    reference = config.resolve_project_path(config.kernel.reference)
    kernel = reference.stem
    if "polybench.h" in reference.read_text() and kernel != "mutual-information":
        kernel = f"polybench-{kernel}"
    generated, metadata = instrument_reference(reference.read_text(), kernel)
    if config.oracle.input_fixture:
        raise ValueError("external input fixtures need an explicit C capture adapter")
    directory.mkdir(parents=True, exist_ok=True)
    source = directory / "capture.c"
    source.write_text(generated)
    values = {
        "reference": str(source.resolve()),
        "output": str((directory / "unused.csv").resolve()),
        "input": "",
        "project": str(config.project.root),
        "oracle_dir": str(directory.resolve()),
    }
    command = _format_command(config.oracle.build, values)
    # Preserve relative quoted includes from the original source location.
    command.extend([f"-I{reference.parent}"])
    (directory / "build-command.json").write_text(json.dumps(command, indent=2) + "\n")
    code, stdout, stderr = await _run(
        command, cwd=config.project.root, timeout_s=config.oracle.timeout_s
    )
    (directory / "build.stdout").write_text(stdout)
    (directory / "build.stderr").write_text(stderr)
    if code:
        raise RuntimeError(f"C input capture build failed: {stderr[-2000:]}")
    command_run = _format_command(config.oracle.run, values)
    code, stdout, stderr = await _run(
        command_run, cwd=config.project.root, timeout_s=config.oracle.timeout_s
    )
    (directory / "run.stdout").write_text(stdout)
    (directory / "run.stderr").write_text(stderr)
    if code:
        raise RuntimeError(f"C input capture execution failed: {stderr[-2000:]}")
    arrays = parse_capture(stdout)
    metadata.update(
        {
            "source": str(reference),
            "source_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
            "dataset": config.kernel.validation_dataset,
            "build_command": command,
            "schema_version": 1,
        }
    )
    path = directory / "inputs.npz"
    save_contract(path, arrays, metadata)
    (directory / "manifest.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return path


async def input_contract_for_dataset(config: RunConfig, oracle: OracleResult, dataset: str) -> Path:
    """Capture the actual evaluation profile, independently of validation size."""
    supplied = config.arena.input_check.contracts.get(dataset)
    if supplied is not None:
        path = config.resolve_project_path(supplied)
        _, metadata = load_contract(path)
        if metadata.get("dataset") != dataset:
            raise ValueError("configured input contract has the wrong dataset")
        return path
    if dataset == config.kernel.validation_dataset and oracle.input_contract_path is not None:
        return oracle.input_contract_path
    selected = config.model_copy(deep=True)
    if dataset != config.kernel.validation_dataset:
        if dataset not in {"mini", "small", "medium", "large", "extralarge"}:
            raise ValueError(f"dataset {dataset!r} requires an explicit trusted input contract")
        pattern = r"-D(?:MINI|SMALL|MEDIUM|LARGE|EXTRALARGE)_DATASET"
        selected.oracle.build = [
            re.sub(pattern, f"-D{dataset.upper()}_DATASET", part) for part in selected.oracle.build
        ]
        if not any(re.search(pattern, part) for part in selected.oracle.build):
            selected.oracle.build.insert(1, f"-D{dataset.upper()}_DATASET")
        selected.kernel.validation_dataset = dataset
    reference = selected.resolve_project_path(selected.kernel.reference)
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "source": hashlib.sha256(reference.read_bytes()).hexdigest(),
                "context": {
                    str(p): hashlib.sha256(
                        selected.resolve_project_path(p).read_bytes()
                    ).hexdigest()
                    for p in selected.kernel.context
                },
                "build": selected.oracle.build,
                "dataset": dataset,
                "capture_implementation": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()
    root = oracle.output_path.parent / "input-contracts" / fingerprint
    # Independent build directories avoid concurrent compiler/output races.
    for path in root.glob("*/inputs.npz"):
        if path.with_name("manifest.json").is_file():
            return path
    return await build_input_contract(selected, root / uuid.uuid4().hex)
