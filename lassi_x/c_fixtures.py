"""Typed fixtures exported by trusted C, with explicit computation boundaries.

Only structural PolyBench declarations/call sites are recognized. Initialization
expressions are always executed by the configured C compiler.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import TYPE_CHECKING, Literal

import numpy as np
import yaml
from pydantic import Field, model_validator

from .config import StrictModel
from .input_contract import load_contract, save_contract

if TYPE_CHECKING:
    from pathlib import Path

    from .config import RunConfig
    from .validation import OracleResult

Identifier = r"^[A-Za-z_][A-Za-z0-9_]*$"


class Input(StrictModel):
    argument: str = Field(pattern=Identifier)
    access: Literal["read_only", "read_write"]
    scalar: bool = False


class FieldSpec(StrictModel):
    expression: str
    shape: list[str] = Field(default_factory=list)


class FixtureSpec(StrictModel):
    inputs: dict[str, Input] = Field(min_length=1)
    outputs: list[str] = Field(min_length=1)
    # Non-PolyBench sources specify two unique literal insertion anchors.
    before: str | None = None
    after: str | None = None
    fields: dict[str, FieldSpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid(self) -> FixtureSpec:
        names = set(self.inputs) | set(self.outputs) | set(self.fields)
        if any(re.fullmatch(Identifier, name) is None for name in names):
            raise ValueError("fixture field names must be C identifiers")
        arguments = [item.argument for item in self.inputs.values()]
        if len(set(arguments)) != len(arguments) or len(set(self.outputs)) != len(self.outputs):
            raise ValueError("duplicate fixture arguments or outputs")
        if (self.before is None) != (self.after is None):
            raise ValueError("both computation anchors are required")
        return self


def instrument(source: str, spec: FixtureSpec, directory: Path) -> str:
    """Insert binary import/export; types and dimensions are evaluated in C."""
    fields = dict(spec.fields)
    if spec.before is not None:
        assert spec.after is not None
        if source.count(spec.before) != 1 or source.count(spec.after) != 1:
            raise ValueError("fixture computation anchors must be unique")
        before, after = source.index(spec.before), source.index(spec.after)
    else:
        # Use the original source offsets after removing comments without shifting text.
        clean = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", lambda m: " " * len(m[0]), source)
        main = re.search(r"\bint\s+main\s*\(", clean)
        if main is None:
            raise ValueError("reference has no main")
        tail = clean[main.start() :]
        call = re.search(r"\bkernel_\w+\s*\([^;]+;", tail)
        if call is None:
            raise ValueError("explicit computation anchors required for this reference")
        before, after = main.start() + call.start(), main.start() + call.end()
        for decl in re.finditer(r"POLYBENCH_(\d)D_ARRAY_DECL\(([^;]+?)\)\s*;", tail):
            rank = int(decl[1])
            parts = [part.strip() for part in decl[2].split(",")]
            if len(parts) != 2 + 2 * rank:
                raise ValueError("unsupported PolyBench declaration")
            fields.setdefault(
                parts[0],
                FieldSpec(expression=f"POLYBENCH_ARRAY({parts[0]})", shape=parts[2 : 2 + rank]),
            )
    if before >= after:
        raise ValueError("fixture boundaries must enclose the computation")
    for name in set(spec.inputs) | set(spec.outputs):
        if name not in fields:
            # Scalar names are explicit, never discovered from initialization expressions.
            fields[name] = FieldSpec(expression=name)
    for name, item in spec.inputs.items():
        if item.scalar and fields[name].shape:
            raise ValueError(f"scalar argument {name} has an array shape")

    def transfer(name: str, phase: str, importing: bool = False) -> str:
        field = fields[name]
        value = f"({field.expression})" + "[0]" * len(field.shape)
        count = " * ".join(f"(size_t)({size})" for size in field.shape) or "1"
        dims = ", ".join(f"(size_t)({size})" for size in field.shape)
        # C11 generic selection avoids guessing typedefs or transporting integers as doubles.
        kind = (
            f"_Generic(({value}), float: 'f', double: 'f', char: (CHAR_MIN < 0 ? 'i' : 'u'), "
            "signed char: 'i', short: 'i', int: 'i', long: 'i', long long: 'i', "
            "unsigned char: 'u', unsigned short: 'u', unsigned int: 'u', "
            "unsigned long: 'u', unsigned long long: 'u', default: '?')"
        )
        path = json.dumps(str(directory / f"{phase}-{name}.bin"))
        return (
            f"{{ size_t lassi_dims[] = {{{dims or '0'}}}; "
            f"lassi_fixture_io({path}, &({value}), sizeof({value}), {kind}, "
            f"{len(field.shape)}, lassi_dims, {count}, {int(importing)}); }}\n"
        )

    pre = "\n" + "".join(transfer(name, "import", True) for name in spec.inputs)
    pre += "".join(transfer(name, "input") for name in spec.inputs)
    post = "\n" + "".join(transfer(name, "output") for name in spec.outputs)
    helpers = r"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static void lassi_fixture_io(const char *path, void *data, size_t width, char kind,
                            int rank, size_t *dims, size_t count, int importing) {
  char header[4096], actual[4096];
  if (kind == '?' || (kind == 'f' && width > 8)) exit(91);
  int length = snprintf(header, sizeof(header), "%c%zu %d", kind, width, rank);
  for (int i = 0; i < rank; ++i)
    length += snprintf(header + length, sizeof(header) - length, " %zu", dims[i]);
  if (length < 0 || length >= (int)sizeof(header) - 2) exit(92);
  strcat(header, "\n");
  FILE *file = fopen(path, importing ? "rb" : "wb");
  if (!file) { if (importing) return; perror(path); exit(93); }
  if (importing) {
    if (!fgets(actual, sizeof(actual), file) || strcmp(header, actual) ||
        fread(data, width, count, file) != count || fgetc(file) != EOF) exit(94);
  } else {
    if (fputs(header, file) < 0 || fwrite(data, width, count, file) != count) exit(95);
  }
  if (fclose(file)) exit(96);
}
"""
    return helpers + source[:before] + pre + source[before:after] + post + source[after:]


def read_field(path: Path) -> np.ndarray:
    with path.open("rb") as stream:
        header = stream.readline().decode("ascii").split()
        dtype, rank = np.dtype(header[0]), int(header[1])
        shape = tuple(map(int, header[2:]))
        if len(shape) != rank or any(size < 0 for size in shape):
            raise ValueError("invalid C fixture dimensions")
        data = stream.read()
    expected = (int(np.prod(shape)) if shape else 1) * dtype.itemsize
    if len(data) != expected:
        raise ValueError("invalid C fixture byte count")
    return np.frombuffer(data, dtype=dtype).reshape(shape).copy()


async def build_fixture_oracle(config: RunConfig, run_dir: Path) -> OracleResult:
    from .validation import OracleResult, _format_command, _run  # noqa: PLC0415

    assert config.oracle.fixture_spec is not None
    spec_path = config.resolve_project_path(config.oracle.fixture_spec)
    spec = FixtureSpec.model_validate(yaml.safe_load(spec_path.read_text()))
    reference = config.resolve_project_path(config.kernel.reference)
    directory = (run_dir / "oracle" / "c-fixture").resolve()
    directory.mkdir(parents=True, exist_ok=False)
    if config.oracle.input_fixture:
        arrays, _ = load_contract(config.resolve_project_path(config.oracle.input_fixture))
        if set(arrays) != set(spec.inputs):
            raise ValueError("alternate fixture must provide every specified C input exactly once")
        for name, array in arrays.items():
            if array.dtype.kind not in "fiu" or not array.dtype.isnative:
                raise ValueError("alternate fixtures require native floating/integer arrays")
            header = f"{array.dtype.kind}{array.dtype.itemsize} {array.ndim}"
            header += "".join(f" {size}" for size in array.shape) + "\n"
            (directory / f"import-{name}.bin").write_bytes(
                header.encode() + array.tobytes(order="C")
            )
    source = directory / "reference.c"
    source.write_text(instrument(reference.read_text(), spec, directory))
    values = {
        "reference": str(source),
        "oracle_dir": str(directory),
        "project": str(config.project.root),
        "input": "",
        "output": str(directory / "unused.csv"),
    }
    build = _format_command(config.oracle.build, values) + [f"-I{reference.parent}"]
    run = _format_command(config.oracle.run, values)
    (directory / "commands.json").write_text(json.dumps({"build": build, "run": run}, indent=2))
    code, out, err = await _run(build, cwd=config.project.root, timeout_s=config.oracle.timeout_s)
    (directory / "build.stdout").write_text(out)
    (directory / "build.stderr").write_text(err)
    if code:
        raise RuntimeError(f"C fixture compilation failed: {err[-4000:]}")
    first_inputs = first_outputs = None
    logs = []
    for attempt in range(config.oracle.determinism_runs):
        code, stdout, stderr = await _run(
            run, cwd=config.project.root, timeout_s=config.oracle.timeout_s
        )
        (directory / f"run-{attempt}.stdout").write_text(stdout)
        (directory / f"run-{attempt}.stderr").write_text(stderr)
        if code:
            raise RuntimeError(f"C fixture execution failed ({code}): {stderr[-4000:]}")
        inputs = {name: read_field(directory / f"input-{name}.bin") for name in spec.inputs}
        outputs = {name: read_field(directory / f"output-{name}.bin") for name in spec.outputs}
        if not all(np.isfinite(value).all() for value in [*inputs.values(), *outputs.values()]):
            raise ValueError("C fixture contains nonfinite values")
        if first_inputs is not None:
            assert first_outputs is not None
            if any(not np.array_equal(value, first_inputs[name]) for name, value in inputs.items()):
                raise ValueError("C fixture inputs are nondeterministic")
            if any(
                not np.array_equal(value, first_outputs[name]) for name, value in outputs.items()
            ):
                raise ValueError("C fixture outputs are nondeterministic")
        first_inputs, first_outputs = inputs, outputs
        logs.append(stdout + stderr)
    assert first_inputs is not None and first_outputs is not None
    metadata = {
        "schema_version": 2,
        "kernel": config.kernel.name,
        "dataset": config.kernel.validation_dataset,
        "required": list(spec.inputs),
        "integer_fields": [
            name for name, value in first_inputs.items() if value.dtype.kind in "iu"
        ],
        "inputs": {name: item.model_dump() for name, item in spec.inputs.items()},
        "outputs": spec.outputs,
        "source_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
        "spec_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "byteorder": sys.byteorder,
        "build_command": build,
    }
    contract = directory / "inputs.npz"
    save_contract(contract, first_inputs, metadata)
    output = directory / "outputs.npz"
    save_contract(output, first_outputs, metadata)
    manifest = {
        **metadata,
        "inputs_sha256": hashlib.sha256(contract.read_bytes()).hexdigest(),
        "outputs_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    flattened = np.concatenate([first_outputs[name].reshape(-1) for name in spec.outputs])
    numeric = directory / "expected.npy"
    np.save(numeric, flattened)
    return OracleResult(
        numeric,
        flattened,
        out + err,
        "".join(logs),
        str(metadata["source_sha256"]),
        hashlib.sha256(numeric.read_bytes()).hexdigest(),
        config.oracle.determinism_runs,
        contract,
    )
