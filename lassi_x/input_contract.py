"""Deterministic, harness-owned checks of the values supplied to forward.

This checks fixture parity, not the algorithm or an adversarial Python sandbox.
Candidate declarations never supply the expected values or binding rules.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    import argparse
    from pathlib import Path


class InputContractError(ValueError):
    """The candidate's supplied inputs do not satisfy the trusted contract."""


def save_contract(path: Path, arrays: dict[str, np.ndarray], metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = dict(arrays)
    metadata = dict(metadata)
    if metadata.get("schema_version") == 2:
        metadata["fixture_sha256"] = fixture_digest(arrays, metadata)
    payload["__metadata__"] = np.asarray(json.dumps(metadata))
    np.savez(path, **payload)


def load_contract(path: Path) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    with np.load(path, allow_pickle=False) as archive:
        metadata = json.loads(str(archive["__metadata__"].item()))
        arrays = {name: archive[name].copy() for name in archive.files if name != "__metadata__"}
    if metadata.get("schema_version") == 2 and metadata.get("fixture_sha256") != fixture_digest(
        arrays, metadata
    ):
        raise InputContractError("C fixture checksum mismatch")
    return arrays, metadata


def fixture_digest(arrays: dict[str, np.ndarray], metadata: dict[str, Any]) -> str:
    identity = {key: value for key, value in metadata.items() if key != "fixture_sha256"}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode())
    for name, array in sorted(arrays.items()):
        digest.update(json.dumps([name, array.dtype.str, array.shape]).encode())
        digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def _normalized(name: str) -> str:
    name = re.sub(r"(?:_input|_in|_init|_initial|0)$", "", name.lower())
    return name.replace("_", "")


def _binding(name: str, kernel: str, arrays: dict[str, np.ndarray]) -> str | None:
    names = {_normalized(key): key for key in arrays}
    normalized = _normalized(name)
    if normalized in names:
        return names[normalized]
    aliases = {
        "polybench-cholesky": {"matrix": "A"},
        "polybench-lu": {"matrix": "A"},
        "polybench-nussinov": {"zerotable": "table"},
        "polybench-deriche": {"img": "imgIn"},
        "poisson-cg": {"b": "r"},
    }
    return aliases.get(kernel, {}).get(normalized)


def compare_input_arrays(
    actual: dict[str, np.ndarray],
    expected: dict[str, np.ndarray],
    metadata: dict[str, Any],
    *,
    bindings: dict[str, str] | None = None,
    rtol: float = 1e-12,
    atol: float = 1e-14,
    precision: str = "fp64",
) -> dict[str, Any]:
    """Compare all supplied arguments; unknown inputs and missing data fail closed.

    Bindings are supplied by the harness configuration, never by the candidate.
    Only singleton batch/channel dimensions may be added or removed implicitly.
    Explicit bindings can select a trusted transpose with ``name.T``. Packed
    GESUMMV matrices have a fixed, independently specified A/B stack contract.
    Scalars embedded in the algorithm and unused workspace arguments may be
    absent. Every required data array must be represented by a checked argument.
    """
    kernel = metadata["kernel"]
    if metadata.get("schema_version") == 2:
        bindings = {item["argument"]: name for name, item in metadata["inputs"].items()}
    checked: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    covered: set[str] = set()
    for name, value in actual.items():
        value = np.asarray(value)
        explicit = metadata.get("schema_version") == 2
        target = (bindings or {}).get(name)
        if target is None and not explicit:
            target = _binding(name, kernel, expected)
        sources: list[str] = []
        if target is not None:
            transpose = target.endswith(".T")
            key = target[:-2] if transpose else target
            if key not in expected:
                errors.append(
                    {"argument": name, "reason": "unknown contract binding", "target": target}
                )
                continue
            reference = expected[key].T if transpose else expected[key]
            sources = [key]
        elif not explicit and kernel == "polybench-gesummv" and name == "M":
            reference = np.stack([expected["A"], expected["B"]])
            sources = ["A", "B"]
        elif not explicit and kernel == "polybench-doitgen" and name == "weight":
            reference = expected["C4"].T
            sources = ["C4"]
        else:
            errors.append(
                {"argument": name, "reason": "unmapped argument; trusted binding required"}
            )
            continue
        integral = all(key in metadata.get("integer_fields", []) for key in sources)
        if precision != "fp64" and not integral:
            reference = round_input_values(reference, precision)
        # Squeezing singleton dimensions accommodates NCHW stencils without
        # permitting arbitrary flattening, permutations, or broadcasting.
        if metadata.get("schema_version") == 2:
            left, right = value, reference
            if integral and value.dtype != reference.dtype:
                errors.append({"argument": name, "reason": "integer dtype mismatch"})
                continue
        else:
            left, right = np.squeeze(value), np.squeeze(reference)
        if left.shape != right.shape:
            errors.append(
                {
                    "argument": name,
                    "reason": "shape mismatch",
                    "actual": list(value.shape),
                    "expected": list(reference.shape),
                }
            )
            continue
        finite = bool(np.isfinite(left).all())
        # Integer-valued C inputs are compared exactly, independently of tolerances.
        exact_required = (
            explicit or precision != "fp64" or integral or bool(np.equal(right, 0).all())
        )
        close = (
            np.equal(left, right)
            if exact_required
            else np.isclose(left, right, rtol=rtol, atol=atol)
        )
        if not finite or not bool(close.all()):
            delta = np.abs(left.astype(np.float64) - right.astype(np.float64))
            bad = np.flatnonzero(~close.reshape(-1))[:5]
            errors.append(
                {
                    "argument": name,
                    "source": sources,
                    "reason": "value mismatch",
                    "finite": finite,
                    "max_abs_error": float(np.max(delta)) if finite else None,
                    "first_bad_flat_indices": bad.tolist(),
                }
            )
            continue
        covered.update(sources)
        checked.append(
            {
                "argument": name,
                "source": sources,
                "shape": list(value.shape),
                "exact": bool(np.array_equal(left, right)),
            }
        )
    missing = sorted(set(metadata["required"]) - covered)
    if missing:
        errors.append({"reason": "required C inputs absent", "fields": missing})
    return {
        "ok": not errors,
        "kernel": kernel,
        "checked": checked,
        "errors": errors,
        "rtol": rtol,
        "atol": atol,
        "precision": precision,
        "rounding_policy": "original_C_initialization_then_one_target_storage_cast",
        "scope": (
            "supplied forward inputs at the requested precision; "
            "not algorithmic correctness or model-state certification"
        ),
    }


def check_model_inputs(
    model: Any,
    inputs: tuple[Any, ...],
    contract_path: Path,
    *,
    bindings: dict[str, str] | None = None,
    rtol: float = 1e-12,
    atol: float = 1e-14,
    snapshot_path: Path | None = None,
    precision: str = "fp64",
) -> dict[str, Any]:
    """Snapshot inputs after construction and before forward can mutate them."""
    import torch  # noqa: PLC0415

    # The executed-dtype audit wraps the model with a variadic forward. Bind
    # against the original model's interface, while checking the actual inputs.
    while type(model).__name__ == "AuditedModel" and hasattr(model, "inner"):
        model = model.inner
    parameters = list(inspect.signature(model.forward).parameters.values())
    positional = [
        p.name for p in parameters if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    actual: dict[str, Any] = {}
    for index, item in enumerate(inputs):
        name = positional[index] if index < len(positional) else f"#{index}"
        if isinstance(item, torch.Tensor):
            if item.is_complex():
                raise InputContractError(f"complex input is outside the C input contract: {name}")
            stored = item.detach().cpu()
            # NumPy has no native BF16 dtype. Widen only for lossless transport.
            if stored.dtype == torch.bfloat16:
                stored = stored.double()
            actual[name] = stored.numpy().copy()
        elif isinstance(item, (int, float, bool)):
            actual[name] = np.asarray(item)
        else:
            raise InputContractError(f"unsupported input type for {name}: {type(item).__name__}")
    if snapshot_path is not None:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(snapshot_path, **actual)
    expected, metadata = load_contract(contract_path)
    return compare_input_arrays(
        actual,
        expected,
        metadata,
        bindings=bindings,
        rtol=rtol,
        atol=atol,
        precision=precision,
    )


def round_input_values(values: np.ndarray, precision: str) -> np.ndarray:
    """Apply one target-storage conversion to the original initialized C values."""
    import torch  # noqa: PLC0415

    dtypes = {
        "fp64": torch.float64,
        "fp32": torch.float32,
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
    }
    if precision not in dtypes:
        raise InputContractError(f"unsupported input precision: {precision}")
    value = torch.from_numpy(np.array(values, dtype=np.float64, copy=True))
    rounded = value.to(dtypes[precision]).double().numpy()
    if not np.isfinite(rounded).all():
        raise InputContractError(f"C inputs are not finite in {precision} after the storage cast")
    return rounded


def supplied_fixture_inputs(
    path: Path, *, device: str, dtype: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Construct fresh arguments from C bytes; never call candidate input builders."""
    import torch  # noqa: PLC0415

    arrays, metadata = load_contract(path)
    if metadata.get("schema_version") != 2:
        raise InputContractError(
            "direct fixture execution requires an explicit input specification"
        )
    arguments = {}
    for name, item in metadata["inputs"].items():
        value = arrays[name].copy()
        if item["scalar"]:
            if value.shape:
                raise InputContractError(f"scalar field {name} has an array shape")
            arguments[item["argument"]] = (
                torch.from_numpy(value).to(dtype=dtype).item()
                if value.dtype.kind == "f"
                else value.item()
            )
        else:
            tensor = torch.from_numpy(value)
            # Integral arrays keep their declared C storage type.
            arguments[item["argument"]] = tensor.to(
                device=device, dtype=dtype if tensor.is_floating_point() else tensor.dtype
            )
    return arguments, metadata


def add_input_check_arguments(parser: argparse.ArgumentParser) -> None:
    """Shared arguments for installed and standalone measurement workers."""
    from pathlib import Path  # noqa: PLC0415

    parser.add_argument("--input-contract", type=Path)
    parser.add_argument("--input-snapshot", type=Path)
    parser.add_argument("--input-bindings", default="{}")
    parser.add_argument("--input-rtol", type=float, default=1e-12)
    parser.add_argument("--input-atol", type=float, default=1e-14)


def check_worker_inputs(
    model: Any, inputs: tuple[Any, ...], args: Any, *, precision: str | None = None
) -> dict[str, Any] | None:
    """Validate the actual worker inputs outside all timing regions."""
    if not getattr(args, "input_contract", None):
        return None
    report = check_model_inputs(
        model,
        inputs,
        args.input_contract,
        bindings=json.loads(args.input_bindings),
        rtol=args.input_rtol,
        atol=args.input_atol,
        snapshot_path=args.input_snapshot,
        precision=precision or args.precision,
    )
    if not report["ok"]:
        raise InputContractError(json.dumps(report["errors"]))
    return report
