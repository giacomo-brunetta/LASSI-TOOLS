"""Forward-only Torch work/traffic estimates and reproducible roofline plots.

Run ``python -m lassi_x.roofline --help``. No accelerator SDK is required.
Tensor operand volumes are a software model, never hardware memory counters.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import inspect
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import torch
from torch._subclasses.fake_tensor import FakeTensorMode
from torch.utils._python_dispatch import TorchDispatchMode
from torch.utils._pytree import tree_flatten, tree_map
from torch.utils.flop_counter import flop_registry

from .candidate_runner import PRECISIONS, load_module

SCHEMA = "lassi-roofline-v1"
HARDWARE = Path(__file__).parent / "resources" / "roofline-hardware.json"

# Explicit zero-arithmetic rules; new operators must be classified, never silently ignored.
_MOVEMENT = set(
    [
        "clone",
        "copy",
        "copy_",
        "_to_copy",
        "cat",
        "stack",
        "flip",
        "roll",
        "gather",
        "scatter",
        "scatter_",
        "index",
        "index_put",
        "index_put_",
        "index_select",
        "masked_fill",
        "masked_fill_",
        "where",
        "tril",
        "triu",
        "diagonal_scatter",
        "slice_scatter",
        "select_scatter",
        "constant_pad_nd",
        "repeat",
        "repeat_interleave",
        "unbind",
        "split",
        "split_with_sizes",
        "chunk",
        "contiguous",
        "lift_fresh",
        "lift_fresh_copy",
        "detach",
        "detach_",
        "alias",
        "view",
        "_unsafe_view",
        "reshape",
        "_reshape_alias",
        "transpose",
        "transpose_",
        "t",
        "t_",
        "permute",
        "movedim",
        "slice",
        "select",
        "narrow",
        "expand",
        "expand_as",
        "as_strided",
        "squeeze",
        "squeeze_",
        "unsqueeze",
        "unsqueeze_",
        "diagonal",
        "unfold",
        "view_as_real",
        "view_as_complex",
        "resolve_conj",
        "resolve_neg",
        "empty",
        "empty_like",
        "empty_strided",
        "new_empty",
        "new_empty_strided",
        "zeros",
        "zeros_like",
        "new_zeros",
        "ones",
        "ones_like",
        "new_ones",
        "full",
        "full_like",
        "new_full",
        "fill",
        "fill_",
        "zero_",
        "scalar_tensor",
        "arange",
        "linspace",
        "logspace",
        "eye",
        "_pin_memory",
        "_assert_async",
        "_assert_scalar",
    ]
)
_BASIC = set("add sub rsub mul div true_divide neg abs reciprocal square".split())  # noqa: SIM905
_SPECIAL = set(
    [
        "sqrt",
        "rsqrt",
        "exp",
        "exp2",
        "expm1",
        "log",
        "log2",
        "log10",
        "log1p",
        "sin",
        "cos",
        "tan",
        "asin",
        "acos",
        "atan",
        "atan2",
        "sinh",
        "cosh",
        "tanh",
        "asinh",
        "acosh",
        "atanh",
        "sigmoid",
        "erf",
        "erfc",
        "lgamma",
        "pow",
    ]
)
_COMPARE = set(
    [
        "eq",
        "ne",
        "lt",
        "le",
        "gt",
        "ge",
        "maximum",
        "minimum",
        "clamp",
        "clamp_min",
        "clamp_max",
        "relu",
        "threshold",
        "isfinite",
        "isinf",
        "isnan",
        "sign",
        "signbit",
        "logical_and",
        "logical_or",
        "logical_not",
        "logical_xor",
        "bitwise_and",
        "bitwise_or",
        "bitwise_xor",
        "bitwise_not",
        "floor",
        "ceil",
        "round",
        "trunc",
    ]
)
_UNINITIALIZED = {"empty", "empty_like", "empty_strided", "new_empty", "new_empty_strided"}


def sha256(path: Path) -> str:
    """Hash an artifact without loading it into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tensors(value: Any) -> list[torch.Tensor]:
    return [v for v in tree_flatten(value)[0] if isinstance(v, torch.Tensor)]


def _storage(tensor: torch.Tensor) -> int:
    return int(tensor.untyped_storage()._cdata)


def _volume(tensors: list[torch.Tensor]) -> int:
    # Each operand once, including repeated operands. Expanded tensors use logical size.
    return sum(t.numel() * t.element_size() for t in tensors)


def _footprint(tensors: list[torch.Tensor]) -> int:
    """Unique backing storage, including unused regions of views; not compulsory I/O."""
    return sum({_storage(t): t.untyped_storage().nbytes() for t in tensors}.values())


def _work(func: Any, args: Any, kwargs: Any, output: Any) -> tuple[int, int, int, str]:
    """Return arithmetic, special-function, comparison counts, and coverage class."""
    name = func._schema.name.split("::")[-1]
    base = name.rstrip("_")
    ins, outs = _tensors((args, kwargs)), _tensors(output)
    n = sum(t.numel() for t in outs)
    floating = any(t.is_floating_point() for t in ins + outs)
    if str(func) in {"prim.device.default", "aten.is_same_size.default"}:
        return 0, 0, 0, "metadata"
    if any(t.is_complex() for t in ins + outs):
        return 0, 0, 0, "unsupported_complex"
    if base in {"linspace", "logspace"}:
        return 0, 0, 0, "unsupported"
    if base == "scatter" and ("reduce" in kwargs or len(args) > 4):
        return 0, 0, 0, "unsupported"
    if base == "index_put" and (kwargs.get("accumulate", False) or (len(args) > 3 and args[3])):
        return 0, 0, 0, "unsupported"
    if base in _BASIC:
        count = n * (2 if base in {"add", "sub"} and kwargs.get("alpha", 1) != 1 else 1)
        return (count if floating else 0), 0, 0, "arithmetic" if floating else "integer"
    if base in _SPECIAL:
        # General power/transcendentals count as one conventional FLOP; retain separately.
        return 0, n if floating else 0, 0, "special" if floating else "integer"
    if base in _COMPARE:
        return 0, 0, n, "comparison"
    if base in {"mm", "bmm", "mv", "dot", "vdot", "addmm", "baddbmm", "addmv"}:
        offset = 1 if base in {"addmm", "baddbmm", "addmv"} else 0
        a, b = args[offset : offset + 2]
        k = a.shape[-1]
        count = 2 * k * n
        if offset:
            alpha, beta = kwargs.get("alpha", 1), kwargs.get("beta", 1)
            count += n * (int(alpha != 1) + int(beta != 0) + int(beta not in (0, 1)))
        return count if floating else 0, 0, 0, "matrix" if floating else "integer"
    if base in {"sum", "mean", "prod", "amax", "amin", "max", "min", "all", "any"}:
        if base in {"max", "min"} and len(ins) > 1:
            return 0, 0, n, "comparison"
        # max/min(dim) return both values and indices; only values define the reduction.
        values = outs[0].numel() if outs else 0
        count = max(0, ins[0].numel() - values)
        if base in {"sum", "mean", "prod"}:
            count += values if base == "mean" else 0
            return count if floating else 0, 0, 0, "reduction" if floating else "integer"
        return 0, 0, count, "comparison"
    if base in {"cumsum", "cumprod"}:
        dim = args[1] if len(args) > 1 else kwargs["dim"]
        count = ins[0].numel() - ins[0].numel() // max(1, ins[0].shape[dim])
        return count if floating else 0, 0, 0, "reduction" if floating else "integer"
    if base in {"addcmul", "addcdiv"}:
        count = n * (2 + int(kwargs.get("value", 1) != 1))
        return count if floating else 0, 0, 0, "arithmetic" if floating else "integer"
    if base in {"_softmax", "_log_softmax"}:
        dim = args[1]
        rows = ins[0].numel() // max(1, ins[0].shape[dim])
        return 3 * n - rows, n + (rows if base == "_log_softmax" else 0), n - rows, "special"
    if base in {"linalg_vector_norm", "norm"}:
        order = args[1] if len(args) > 1 else kwargs.get("ord", 2)
        if order == 2:
            return max(0, 2 * ins[0].numel() - n), n, 0, "special"
    if name in _MOVEMENT or base in _MOVEMENT:
        return 0, 0, 0, "movement"
    # PyTorch supplies shape formulas for convolutions and fused attention. These count
    # MAC work only (2 FLOPs/MAC), not implementation-specific padding or SFU overhead.
    packet = func.overloadpacket
    if packet in flop_registry and base in {"convolution", "_convolution"}:
        count = int(flop_registry[packet](*args, **kwargs, out_val=output))
        if len(args) > 2 and isinstance(args[2], torch.Tensor):
            count += n
        return count, 0, 0, "convolution"
    return 0, 0, 0, "unsupported"


class _CostMode(TorchDispatchMode):  # type: ignore[no-untyped-call]
    def __init__(self, max_ops: int) -> None:
        super().__init__()  # type: ignore[no-untyped-call]
        self.max_ops = max_ops
        self.calls = 0
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}

    def __torch_dispatch__(self, func: Any, types: Any, args: Any = (), kwargs: Any = None) -> Any:
        kwargs = kwargs or {}
        self.calls += 1
        if self.calls > self.max_ops:
            raise RuntimeError(f"forward exceeded max_ops={self.max_ops}; raise --max-ops")
        output = func(*args, **kwargs)
        arithmetic, special, comparisons, category = _work(func, args, kwargs, output)
        ins, outs = _tensors((args, kwargs)), _tensors(output)
        name = func._schema.name.split("::")[-1]
        writes_alias = any(a.alias_info and a.alias_info.is_write for a in func._schema.arguments)
        aliases = {_storage(t) for t in ins}
        view = bool(outs) and not writes_alias and all(_storage(t) in aliases for t in outs)
        read, write = _volume(ins), _volume(outs)
        if view or name in _UNINITIALIZED or category == "metadata":
            read = write = 0
        elif name in {"copy_", "fill_", "zero_"}:
            read = _volume(_tensors(args[1:]))
        elif name.endswith("_like") or name.startswith("new_"):
            # Factory's template operand supplies metadata, not numerical data.
            read = 0
        dtype = ",".join(sorted({str(t.dtype).removeprefix("torch.") for t in ins + outs}))
        key = str(func), dtype
        row = self.rows.setdefault(
            key,
            {
                "operator": str(func),
                "dtypes": dtype,
                "category": category,
                "calls": 0,
                "arithmetic_flops": 0,
                "special_function_ops": 0,
                "comparison_ops": 0,
                "tensor_read_bytes": 0,
                "tensor_write_bytes": 0,
                "example_input_shapes": [list(t.shape) for t in ins],
                "example_output_shapes": [list(t.shape) for t in outs],
            },
        )
        for field, value in {
            "calls": 1,
            "arithmetic_flops": arithmetic,
            "special_function_ops": special,
            "comparison_ops": comparisons,
            "tensor_read_bytes": read,
            "tensor_write_bytes": write,
        }.items():
            row[field] += value
        return output


def analyze(
    model: torch.nn.Module, inputs: Any, *, execution: str = "fake", max_ops: int = 1_000_000
) -> dict[str, Any]:
    """Analyze one inference forward. The model and real-mode inputs may be mutated.

    Fake mode executes Python control flow and tensor metadata only. Tensor-valued
    branches require real mode, which counts only the observed input-dependent path.
    Parameters/buffers keep their actual dtypes; only the caller chooses input dtype.
    """
    if execution not in {"fake", "real"}:
        raise ValueError("execution must be fake or real")
    if max_ops < 1:
        raise ValueError("max_ops must be positive")
    mode = _CostMode(max_ops)
    fake = FakeTensorMode(allow_non_fake_inputs=True, allow_fallback_kernels=False)
    context = fake if execution == "fake" else contextlib.nullcontext()
    with torch.no_grad(), context:
        if execution == "fake":
            inputs = tree_map(
                lambda t: fake.from_tensor(t) if isinstance(t, torch.Tensor) else t, inputs
            )
        boundary = _tensors(inputs) + list(model.parameters()) + list(model.buffers())
        input_storage = _footprint(boundary)
        with mode:
            output = model(*inputs)
        outputs = _tensors(output)
        if not outputs:
            raise ValueError("forward returned no tensors")
        output_storage = _footprint(outputs)
    rows = sorted(mode.rows.values(), key=lambda r: (r["operator"], r["dtypes"]))
    fields = (
        "arithmetic_flops",
        "special_function_ops",
        "comparison_ops",
        "tensor_read_bytes",
        "tensor_write_bytes",
    )
    totals = {field: sum(row[field] for row in rows) for field in fields}
    totals["flops"] = totals["arithmetic_flops"] + totals["special_function_ops"]
    totals["tensor_bytes"] = totals["tensor_read_bytes"] + totals["tensor_write_bytes"]
    totals["input_state_storage_bytes"] = input_storage
    totals["output_storage_bytes"] = output_storage
    totals["boundary_storage_bytes"] = input_storage + output_storage
    unknown = [r["operator"] for r in rows if r["category"].startswith("unsupported")]
    by_dtype: Counter[str] = Counter()
    for row in rows:
        by_dtype[row["dtypes"]] += row["arithmetic_flops"] + row["special_function_ops"]
    return {
        "schema": SCHEMA,
        "torch_version": torch.__version__,
        "execution": execution,
        "complete": not unknown,
        "unsupported_operators": sorted(set(unknown)),
        "conventions": {
            "scope": "one inference forward; excludes model/input construction and backward",
            "flops": "dense MAC=2; each special function=1; comparisons/integer/movement=0",
            "tensor_bytes": "sum of operand/output tensor volumes per materializing ATen call; "
            "views/empty allocations=0; repeated operands counted separately",
            "boundary_storage_bytes": "input/state plus output backing storages; "
            "deduplicated within each side; not memory traffic",
            "hardware_traffic": "unknown; excludes fusion, caching, tiling, spills and placement",
            "dtypes": "observed ATen tensor dtypes, not hidden hardware accumulator precision",
        },
        "totals": totals,
        "flops_by_dtype_signature": dict(by_dtype),
        "inputs": [
            {"shape": list(t.shape), "stride": list(t.stride()), "dtype": str(t.dtype)}
            for t in _tensors(inputs)
        ],
        "outputs": [{"shape": list(t.shape), "dtype": str(t.dtype)} for t in outputs],
        "operators": rows,
    }


def analyze_module(
    path: Path,
    *,
    precision: str = "fp16",
    dataset: str = "default",
    fixture: Path | None = None,
    execution: str = "fake",
    setup: str = "real",
    seed: int = 0,
    max_ops: int = 1_000_000,
) -> dict[str, Any]:
    """Load the repository's make_model/build_inputs interface, then count forward only."""
    torch.manual_seed(seed)
    module = load_module(path)
    kwargs: dict[str, Any] = {"device": "cpu", "dtype": PRECISIONS[precision]}
    signature = inspect.signature(module.build_inputs).parameters
    if "dataset" in signature:
        kwargs["dataset"] = dataset
    elif dataset != "default":
        raise ValueError("build_inputs has no dataset argument; use default or a frozen source")
    if fixture is not None:
        if "fixture" not in signature:
            raise ValueError("build_inputs does not accept a fixture")
        kwargs["fixture"] = fixture
    setup_mode = (
        FakeTensorMode(allow_non_fake_inputs=True, allow_fallback_kernels=False)
        if setup == "fake"
        else contextlib.nullcontext()
    )
    if setup == "fake" and execution == "real":
        raise ValueError("real execution requires real setup")
    before = sha256(path)
    with torch.no_grad(), setup_mode:
        model = module.make_model().eval().to("cpu")
        inputs = module.build_inputs(**kwargs)
        if not isinstance(inputs, tuple):
            raise TypeError("build_inputs must return a tuple")
        report = analyze(model, inputs, execution=execution, max_ops=max_ops)
    if sha256(path) != before:
        raise ValueError("source changed during analysis")
    report["provenance"] = {
        "module": str(path.resolve()),
        "source_sha256": before,
        "precision": precision,
        "dataset": dataset,
        "seed": seed,
        "setup": setup,
        "fixture": str(fixture.resolve()) if fixture else None,
        "fixture_sha256": sha256(fixture) if fixture else None,
        "adjacent_assets": {
            p.name: sha256(p)
            for p in sorted(path.parent.iterdir())
            if p.suffix in {".npz", ".npy", ".json"} and p.is_file()
        },
    }
    return report


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def _positive(value: Any, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be finite and positive")
    return number


def _pointer(value: Any, pointer: str) -> Any:
    if pointer == "":
        return value
    if not pointer.startswith("/"):
        raise ValueError("JSON pointers must start with /")
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def make_point(
    report: dict[str, Any], entry: dict[str, Any], hardware: dict[str, Any], root: Path
) -> dict[str, Any]:
    """Bind a complete cost report to explicitly selected timing evidence.

    Manifest selection is the caller's eligibility decision. Existing status=ok fields
    alone do not establish paper validity; this function makes no such certification.
    """
    if not report["complete"]:
        raise ValueError(f"unsupported operators: {report['unsupported_operators']}")
    identity = report["provenance"]
    for field in ("source_sha256", "dataset", "precision"):
        if entry[field] != identity[field]:
            raise ValueError(f"cost/timing {field} mismatch")
    device = hardware[entry["hardware"]]
    if entry["precision"] != device["precision"]:
        raise ValueError("hardware precision does not match workload")
    timing = entry["timing"]
    evidence = (root / timing["path"]).resolve()
    if sha256(evidence) != timing["sha256"]:
        raise ValueError("timing evidence hash mismatch")
    data = json.loads(evidence.read_text())
    for field, pointer in timing.get("identity_pointers", {}).items():
        if field not in {"source_sha256", "dataset", "precision"}:
            raise ValueError(f"unsupported identity field {field}")
        if _pointer(data, pointer) != entry[field]:
            raise ValueError(f"timing evidence {field} mismatch")
    latency = _positive(_pointer(data, timing["latency_pointer"]), "latency_s")
    if timing["scope"] != "device_forward":
        raise ValueError("roofline requires device_forward latency")
    basis = entry.get("byte_basis", "tensor")
    if basis == "tensor":
        byte_count = report["totals"]["tensor_bytes"]
        tier = "ATen tensor volume (estimated)"
    elif basis == "measured":
        traffic = entry["traffic"]
        traffic_path = (root / traffic["path"]).resolve()
        if sha256(traffic_path) != traffic["sha256"]:
            raise ValueError("traffic evidence hash mismatch")
        if traffic["memory_tier"] != device["memory_tier"]:
            raise ValueError("traffic memory tier differs from hardware bandwidth tier")
        traffic_data = json.loads(traffic_path.read_text())
        for field in ("source_sha256", "dataset", "precision"):
            if traffic_data[field] != entry[field]:
                raise ValueError(f"traffic evidence {field} mismatch")
        if traffic_data["scope"] != "device_forward":
            raise ValueError("traffic evidence must cover device_forward")
        byte_count = _pointer(traffic_data, traffic["bytes_pointer"])
        tier = traffic["memory_tier"]
    else:
        raise ValueError("byte_basis must be tensor or measured")
    byte_count = _positive(byte_count, "bytes")
    flops = _positive(report["totals"]["flops"], "FLOPs")
    intensity = flops / byte_count
    peak = device.get("peak_flops_s")
    bandwidth = _positive(device["bandwidth_bytes_s"], "bandwidth_bytes_s")
    if peak is not None:
        peak = _positive(peak, "peak_flops_s")
    roof = min(peak, intensity * bandwidth) if peak else intensity * bandwidth
    return {
        "id": entry["id"],
        "hardware": entry["hardware"],
        **identity,
        "latency_s": latency,
        "flops": flops,
        "bytes": byte_count,
        "byte_basis": basis,
        "memory_tier": tier,
        "arithmetic_intensity": intensity,
        "flops_s": flops / latency,
        "reference_roof_flops_s": roof,
        "above_reference_roof": flops / latency > roof * 1.05,
        "special_function_ops": report["totals"]["special_function_ops"],
        "timing_evidence": str(evidence),
        "timing_sha256": timing["sha256"],
        "traffic_evidence": str(traffic_path) if basis == "measured" else None,
        "traffic_sha256": traffic["sha256"] if basis == "measured" else None,
        "eligibility_note": entry["eligibility_note"],
        "interpretation": "software-model coordinates; roof is a reference, not a measured bound"
        if basis == "tensor"
        else "measured traffic; verify matching forward scope",
    }


def batch(manifest: Path, output: Path, *, timeout: float = 180) -> int:
    """Analyze each selected model in an isolated child with a per-model timeout."""
    config = json.loads(manifest.read_text())
    root = manifest.resolve().parent
    hardware_path = root / config["hardware"] if "hardware" in config else HARDWARE
    hardware = json.loads(hardware_path.read_text())["devices"]
    output.mkdir(parents=True, exist_ok=True)
    points, results, costs = [], [], []
    ids = [e["id"] for e in config["entries"]]
    if len(ids) != len(set(ids)):
        raise ValueError("manifest IDs must be unique")
    for index, entry in enumerate(config["entries"]):
        report_path = output / f"{index:04d}-cost.json"
        command = [
            sys.executable,
            "-m",
            "lassi_x.roofline",
            "analyze",
            "--module",
            str((root / entry["module"]).resolve()),
            "--output",
            str(report_path.resolve()),
            "--precision",
            entry["precision"],
            "--dataset",
            entry["dataset"],
            "--execution",
            entry.get("execution", "fake"),
            "--setup",
            entry.get("setup", "real"),
            "--seed",
            str(entry.get("seed", 0)),
            "--max-ops",
            str(entry.get("max_ops", 1_000_000)),
        ]
        if entry.get("fixture"):
            command += ["--fixture", str((root / entry["fixture"]).resolve())]
        result: dict[str, Any] = {"id": entry["id"], "report": report_path.name}
        try:
            run = subprocess.run(
                command, capture_output=True, text=True, timeout=timeout, check=False
            )
            if run.returncode not in {0, 2}:
                raise ValueError(run.stderr.strip()[-4000:] or run.stdout[-4000:])
            report = json.loads(report_path.read_text())
            if "error" in report:
                raise ValueError(report["error"])
            costs.append(
                {
                    "id": entry["id"],
                    "complete": report["complete"],
                    **{
                        k: report["provenance"][k]
                        for k in ("source_sha256", "precision", "dataset")
                    },
                    **report["totals"],
                }
            )
            if "timing" in entry:
                point = make_point(report, entry, hardware, root)
                points.append(point)
            elif entry.get("source_sha256") != report["provenance"]["source_sha256"]:
                raise ValueError("source hash mismatch")
            if not report["complete"]:
                raise ValueError(f"unsupported operators: {report['unsupported_operators']}")
            result["status"] = "ok"
        except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as exc:
            result.update(status="error", error=str(exc))
        results.append(result)
        print(f"[{index + 1}/{len(ids)}] {entry['id']}: {result['status']}", flush=True)
    _write(
        output / "points.json",
        {
            "schema": SCHEMA,
            "hardware": hardware,
            "points": points,
            "manifest_sha256": sha256(manifest),
            "hardware_sha256": sha256(hardware_path),
            "results": results,
        },
    )
    if costs:
        with (output / "costs.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(costs[0]))
            writer.writeheader()
            writer.writerows(costs)
    # Flatten provenance-rich points to a convenient table; nested assets remain in JSON.
    if points:
        fields = list(
            dict.fromkeys(
                k for p in points for k, v in p.items() if not isinstance(v, (dict, list))
            )
        )
        with (output / "points.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(points)
    return int(any(r["status"] == "error" for r in results))


def plot(points_path: Path, output: Path) -> None:
    """Export vector PDF/SVG and 300-dpi PNG; panels keep memory tiers separate."""
    import matplotlib  # noqa: PLC0415

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt  # noqa: PLC0415

    data = json.loads(points_path.read_text())
    points, hardware = data["points"], data["hardware"]
    groups = sorted({(p["hardware"], p["byte_basis"]) for p in points})
    if not groups:
        raise ValueError("no complete, timing-bound points to plot")
    columns = min(2, len(groups))
    rows = math.ceil(len(groups) / columns)
    with plt.rc_context({"font.size": 9, "pdf.fonttype": 42, "svg.fonttype": "none"}):
        fig, axes = plt.subplots(
            rows,
            columns,
            figsize=(6.1 * columns, 4.2 * rows),
            squeeze=False,
            constrained_layout=True,
        )
        for ax, (key, basis) in zip(axes.flat, groups, strict=False):
            device = hardware[key]
            selected = [p for p in points if (p["hardware"], p["byte_basis"]) == (key, basis)]
            bw = device["bandwidth_bytes_s"]
            peak = device.get("peak_flops_s")
            xs = [p["arithmetic_intensity"] for p in selected]
            knee = peak / bw if peak else 1
            lower = 10 ** math.floor(math.log10(min(xs + [knee]) / 3))
            upper = 10 ** math.ceil(math.log10(max(xs + [knee]) * 3))
            grid = [
                10 ** (math.log10(lower) + i * math.log10(upper / lower) / 300) for i in range(301)
            ]
            roof = [min(peak, bw * x) / 1e12 if peak else bw * x / 1e12 for x in grid]
            ax.loglog(
                grid,
                roof,
                color="#444444",
                linewidth=1.6,
                label=f"{device['memory_tier']} {bw / 1e12:g} TB/s; "
                + (f"{peak / 1e12:g} TFLOP/s" if peak else "compute peak pending"),
            )
            for ceiling in device.get("additional_compute_ceilings", []):
                ax.axhline(
                    ceiling["peak_flops_s"] / 1e12,
                    color="#888888",
                    linestyle=":",
                    label=ceiling["label"],
                )
            for index, point in enumerate(selected):
                ax.scatter(
                    point["arithmetic_intensity"],
                    point["flops_s"] / 1e12,
                    s=32,
                    color="#0072B2",
                    marker="o" if basis == "measured" else "D",
                    zorder=3,
                )
                ax.annotate(
                    str(index + 1),
                    (point["arithmetic_intensity"], point["flops_s"] / 1e12),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=7,
                )
            ax.set_title(
                device["label"]
                + (
                    " — estimated tensor traffic"
                    if basis == "tensor"
                    else f" — measured {device['memory_tier']} traffic"
                )
            )
            ax.set_xlabel("Arithmetic intensity [FLOP/byte]")
            ax.set_ylabel("Forward performance [TFLOP/s]")
            ax.set_xlim(lower, upper)
            ax.grid(True, which="major", alpha=0.18)
            ax.legend(loc="upper left", fontsize=7)
        for ax in list(axes.flat)[len(groups) :]:
            ax.set_visible(False)
        fig.suptitle(
            "Roofline reference: one device, dense FP16; MAC = 2 FLOPs\n"
            "Estimated tensor volumes do not measure traffic at the hardware memory tier",
            fontsize=10,
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        for suffix in ("pdf", "svg", "png"):
            fig.savefig(output.with_suffix(f".{suffix}"), dpi=300)
        plt.close(fig)
    _write(
        output.with_suffix(".labels.json"),
        {
            f"{key}/{basis}": {
                str(i + 1): p["id"]
                for i, p in enumerate(
                    [p for p in points if (p["hardware"], p["byte_basis"]) == (key, basis)]
                )
            }
            for key, basis in groups
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    analyze_parser = commands.add_parser("analyze", help="estimate one candidate's forward cost")
    analyze_parser.add_argument("--module", type=Path, required=True)
    analyze_parser.add_argument("--output", type=Path, required=True)
    analyze_parser.add_argument("--precision", choices=sorted(PRECISIONS), default="fp16")
    analyze_parser.add_argument("--dataset", default="default")
    analyze_parser.add_argument("--fixture", type=Path)
    analyze_parser.add_argument("--execution", choices=("fake", "real"), default="fake")
    analyze_parser.add_argument("--setup", choices=("fake", "real"), default="real")
    analyze_parser.add_argument("--seed", type=int, default=0)
    analyze_parser.add_argument("--max-ops", type=int, default=1_000_000)
    batch_parser = commands.add_parser("batch", help="analyze a manifest and bind timing evidence")
    batch_parser.add_argument("--manifest", type=Path, required=True)
    batch_parser.add_argument("--output", type=Path, required=True)
    batch_parser.add_argument("--timeout", type=float, default=180)
    plot_parser = commands.add_parser("plot", help="export paper figures from batch points.json")
    plot_parser.add_argument("--points", type=Path, required=True)
    plot_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "analyze":
        try:
            report = analyze_module(
                args.module,
                precision=args.precision,
                dataset=args.dataset,
                fixture=args.fixture,
                execution=args.execution,
                setup=args.setup,
                seed=args.seed,
                max_ops=args.max_ops,
            )
        except Exception as exc:
            report = {
                "schema": SCHEMA,
                "complete": False,
                "error": f"{type(exc).__name__}: {exc}",
                "hint": "For tensor-dependent control flow try --execution real. "
                "For value-dependent input construction use --setup real.",
            }
        _write(args.output, report)
        print(
            json.dumps(
                {
                    k: report[k]
                    for k in ("complete", "totals", "unsupported_operators", "error")
                    if k in report
                }
            )
        )
        return 0 if report["complete"] else 2
    if args.command == "batch":
        return batch(args.manifest, args.output, timeout=args.timeout)
    plot(args.points, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
