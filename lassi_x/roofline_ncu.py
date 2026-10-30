"""Capture one CUDA graph forward with Nsight Compute, or import its raw CSV.

See docs/roofline.md for the ncu invocation. This module does not launch remote jobs.
"""

from __future__ import annotations

import argparse
import csv
import inspect
import io
import json
import math
from pathlib import Path
from typing import Any

import torch

from .candidate_runner import PRECISIONS, load_module
from .roofline import _write, sha256

_METRICS = {"dram__bytes_read.sum": "read_bytes", "dram__bytes_write.sum": "write_bytes"}


def capture(
    module_path: Path,
    output: Path,
    *,
    precision: str,
    dataset: str,
    fixture: Path | None = None,
    warmup: int = 3,
    seed: int = 0,
) -> None:
    """Bracket exactly one graph replay; construction, warmup and capture are excluded.

    Run under ncu --profile-from-start off. Latency must come from an unprofiled run;
    profiler overhead makes timings from this process unsuitable for the roofline.
    """
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for capture; import works on CPU hosts")
    if "A100" not in torch.cuda.get_device_name():
        raise ValueError("this HBM2 capture profile targets A100; use a matching hardware profile")
    if warmup < 1:
        raise ValueError("warmup must be positive")
    torch.manual_seed(seed)
    before = sha256(module_path)
    module = load_module(module_path)
    parameters = inspect.signature(module.build_inputs).parameters
    kwargs: dict[str, Any] = {"device": "cuda", "dtype": PRECISIONS[precision]}
    if "dataset" in parameters:
        kwargs["dataset"] = dataset
    elif dataset != "default":
        raise ValueError("model does not accept a dataset argument")
    if fixture is not None:
        if "fixture" not in parameters:
            raise ValueError("model does not accept a fixture")
        kwargs["fixture"] = fixture
    with torch.no_grad():
        model = module.make_model().eval().to("cuda")
        inputs = module.build_inputs(**kwargs)
        if not isinstance(inputs, tuple):
            raise TypeError("build_inputs must return a tuple")
        for _ in range(warmup):
            model(*inputs)
        torch.cuda.synchronize()
        graphed = torch.cuda.make_graphed_callables(model, inputs)
        graphed(*inputs)
        torch.cuda.synchronize()
        torch.cuda.profiler.start()  # type: ignore[no-untyped-call]
        try:
            result = graphed(*inputs)
            torch.cuda.synchronize()
        finally:
            torch.cuda.profiler.stop()  # type: ignore[no-untyped-call]
    del result
    if sha256(module_path) != before:
        raise ValueError("source changed during capture")
    _write(
        output,
        {
            "schema": "lassi-roofline-cuda-capture-v1",
            "source_sha256": before,
            "module": str(module_path.resolve()),
            "precision": precision,
            "dataset": dataset,
            "fixture_sha256": sha256(fixture) if fixture else None,
            "device": torch.cuda.get_device_name(),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "seed": seed,
            "warmup": warmup,
            "forward_invocations": 1,
            "scope": "device_forward",
            "capture": "cuda_graph_replay",
            "memory_tier": "HBM2",
        },
    )


def import_ncu(path: Path, capture_path: Path) -> dict[str, Any]:
    """Sum read/write byte counters across launches of the one captured forward.

    Accept raw metric rows, not summary averages. Reject duplicate/incomplete metrics,
    multiple GPUs, invalid values and unknown units instead of silently changing scale.
    """
    metadata = json.loads(capture_path.read_text())
    if metadata["forward_invocations"] != 1 or metadata["scope"] != "device_forward":
        raise ValueError("capture must bracket exactly one device forward")
    rows = list(csv.reader(io.StringIO(path.read_text())))
    required = {"ID", "Metric Name", "Metric Unit", "Metric Value"}
    header_index = next((i for i, row in enumerate(rows) if required.issubset(row)), None)
    if header_index is None:
        raise ValueError("no raw Nsight metric table found; use --csv --page raw")
    header = rows[header_index]
    groups: dict[tuple[str, ...], dict[str, float]] = {}
    devices = set()
    for values in rows[header_index + 1 :]:
        if len(values) != len(header):
            continue
        row = dict(zip(header, values, strict=True))
        metric = row["Metric Name"]
        if metric not in _METRICS:
            continue
        devices.add(row.get("device__attribute_display_name", row.get("Device", "unknown")))
        key = tuple(row.get(k, "") for k in ("Process ID", "Device", "Context", "Stream", "ID"))
        group = groups.setdefault(key, {})
        if metric in group:
            raise ValueError(f"duplicate {metric} for launch {key}; use raw, non-summary CSV")
        scales = {"byte": 1, "Kbyte": 1e3, "Mbyte": 1e6, "Gbyte": 1e9}
        if row["Metric Unit"] not in scales:
            raise ValueError(f"unknown byte unit: {row['Metric Unit']}")
        value = float(row["Metric Value"].replace(",", "")) * scales[row["Metric Unit"]]
        if not math.isfinite(value) or value < 0:
            raise ValueError("byte counters must be finite and nonnegative")
        group[metric] = value
    if not groups or len(devices) != 1:
        raise ValueError("expected counter records from exactly one GPU")
    if any(set(group) != set(_METRICS) for group in groups.values()):
        raise ValueError("each kernel launch must have both read and write counters")
    totals = {field: sum(g[metric] for g in groups.values()) for metric, field in _METRICS.items()}
    return {
        **metadata,
        "schema": "lassi-roofline-ncu-traffic-v1",
        **totals,
        "bytes": totals["read_bytes"] + totals["write_bytes"],
        "kernel_launches": len(groups),
        "ncu_csv": str(path.resolve()),
        "ncu_csv_sha256": sha256(path),
        "capture_metadata_sha256": sha256(capture_path),
        "caveat": "HBM traffic for the profiled replay; profiler replay/cache policies can "
        "affect traffic. Pair only with the matching unprofiled forward workload.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture_parser = commands.add_parser("capture")
    capture_parser.add_argument("--module", type=Path, required=True)
    capture_parser.add_argument("--output", type=Path, required=True)
    capture_parser.add_argument("--precision", choices=sorted(PRECISIONS), default="fp16")
    capture_parser.add_argument("--dataset", default="default")
    capture_parser.add_argument("--fixture", type=Path)
    capture_parser.add_argument("--warmup", type=int, default=3)
    capture_parser.add_argument("--seed", type=int, default=0)
    import_parser = commands.add_parser("import")
    import_parser.add_argument("--csv", type=Path, required=True)
    import_parser.add_argument("--capture", type=Path, required=True)
    import_parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "capture":
        capture(
            args.module,
            args.output,
            precision=args.precision,
            dataset=args.dataset,
            fixture=args.fixture,
            warmup=args.warmup,
            seed=args.seed,
        )
    else:
        _write(args.output, import_ncu(args.csv, args.capture))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
