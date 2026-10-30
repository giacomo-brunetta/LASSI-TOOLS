"""Analytical cost checks: counts must remain independent of profiler implementation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import torch
from torch._subclasses.fake_tensor import DataDependentOutputException

from lassi_x.roofline import HARDWARE, analyze, analyze_module, make_point, sha256


class Function(torch.nn.Module):
    def __init__(self, function: Any) -> None:
        super().__init__()
        self.function = function

    def forward(self, *args: Any) -> Any:
        return self.function(*args)


@pytest.mark.parametrize("execution", ["fake", "real"])
def test_gemm_and_tensor_traffic(execution: str) -> None:
    # M=3,K=5,N=7: conventional dense GEMM = 2*M*N*K; inputs/output FP16.
    report = analyze(
        Function(lambda a, b: a @ b),
        (torch.ones(3, 5, dtype=torch.float16), torch.ones(5, 7, dtype=torch.float16)),
        execution=execution,
    )
    assert report["complete"]
    assert report["totals"]["flops"] == 210
    assert report["totals"]["tensor_read_bytes"] == 100
    assert report["totals"]["tensor_write_bytes"] == 42


def test_three_mm_matches_closed_form() -> None:
    report = analyze_module(Path("tests/fixtures/three_mm.py"), setup="fake")
    assert report["complete"]
    assert report["totals"]["flops"] == 2 * (16 * 20 * 18 + 18 * 24 * 22 + 16 * 18 * 22)
    assert report["totals"]["tensor_bytes"] == 2 * (
        16 * 20 + 20 * 18 + 16 * 18 + 18 * 24 + 24 * 22 + 18 * 22 + 16 * 18 + 18 * 22 + 16 * 22
    )


def test_views_do_not_read_write_and_alias_storage_is_deduplicated() -> None:
    a = torch.ones(4, 6)
    report = analyze(Function(lambda x, y: (x.t(), y[:, :2])), (a, a))
    assert report["complete"]
    assert report["totals"]["tensor_bytes"] == 0
    assert report["totals"]["input_state_storage_bytes"] == 4 * 6 * 4


def test_broadcast_reduction_special_and_integer_work() -> None:
    a, b = torch.ones(2, 3), torch.ones(3)
    report = analyze(Function(lambda x, y: torch.sqrt(((x + y) * x).sum(1))), (a, b))
    assert report["complete"]
    assert report["totals"]["arithmetic_flops"] == 6 + 6 + 4
    assert report["totals"]["special_function_ops"] == 2
    assert report["totals"]["flops"] == 18
    ints = analyze(Function(lambda x: x + 1), (torch.ones(10, dtype=torch.int64),))
    assert ints["totals"]["flops"] == 0


def test_inplace_copy_and_fill() -> None:
    def forward(x: Any, y: Any) -> Any:
        x.copy_(y)
        return x.fill_(0)

    report = analyze(Function(forward), (torch.ones(8), torch.ones(8)))
    assert report["complete"]
    assert report["totals"]["tensor_read_bytes"] == 32
    assert report["totals"]["tensor_write_bytes"] == 64


def test_mixed_dtypes_and_state_preserved() -> None:
    class Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.register_buffer("bias", torch.ones(4, dtype=torch.float32))

        def forward(self, x: Any) -> Any:
            return x.float() + self.bias

    report = analyze(Model(), (torch.ones(4, dtype=torch.float16),))
    assert report["complete"]
    assert report["flops_by_dtype_signature"]["float32"] == 4
    assert report["totals"]["input_state_storage_bytes"] == 8 + 16


def test_unknown_complex_and_data_dependent_paths() -> None:
    report = analyze(Function(torch.linalg.det), (torch.eye(3),))
    assert not report["complete"]
    assert report["unsupported_operators"]
    complex_report = analyze(Function(lambda x: x * x), (torch.ones(4, dtype=torch.complex64),))
    assert not complex_report["complete"]

    def branch(x: Any) -> Any:
        return x + 1 if x.sum().item() > 0 else x * 2

    with pytest.raises(DataDependentOutputException):
        analyze(Function(branch), (torch.ones(4),))
    # Scalar extraction is deliberately not covered; real mode must report it explicitly.
    observed = analyze(Function(branch), (torch.ones(4),), execution="real")
    assert "aten._local_scalar_dense.default" in observed["unsupported_operators"]


def test_addmm_scales_and_convolution() -> None:
    report = analyze(
        Function(lambda a, b, c: torch.addmm(c, a, b, alpha=2, beta=3)),
        (torch.ones(2, 3), torch.ones(3, 4), torch.ones(4)),
    )
    assert report["totals"]["flops"] == 2 * 2 * 3 * 4 + 3 * 2 * 4
    conv = analyze(torch.nn.Conv2d(2, 3, 3), (torch.ones(1, 2, 5, 5),))
    assert conv["complete"]
    assert conv["totals"]["flops"] == 1 * 3 * 3 * 3 * (2 * 2 * 3 * 3 + 1)


def test_max_ops_stops_unrolled_loops() -> None:
    with pytest.raises(RuntimeError, match="max_ops"):
        analyze(Function(lambda x: x + x + x), (torch.ones(4),), max_ops=1)


def test_timing_binding_and_memory_tier(tmp_path: Path) -> None:
    path = tmp_path / "timing.json"
    path.write_text(json.dumps({"latency_s": 1e-5, "source_sha256": "abc"}))
    report = analyze(Function(lambda x: x + 1), (torch.ones(4, dtype=torch.float16),))
    report["provenance"] = {"source_sha256": "abc", "dataset": "large", "precision": "fp16"}
    hardware = json.loads(HARDWARE.read_text())["devices"]
    entry = {
        "id": "example",
        "hardware": "a100-pcie-40gb",
        **report["provenance"],
        "eligibility_note": "test only",
        "timing": {
            "path": path.name,
            "sha256": sha256(path),
            "latency_pointer": "/latency_s",
            "scope": "device_forward",
            "identity_pointers": {"source_sha256": "/source_sha256"},
        },
    }
    point = make_point(report, entry, hardware, tmp_path)
    assert point["arithmetic_intensity"] == 4 / 16
    assert point["flops_s"] == pytest.approx(4e5)
    entry["source_sha256"] = "different"
    with pytest.raises(ValueError, match="mismatch"):
        make_point(report, entry, hardware, tmp_path)
    entry["source_sha256"] = "abc"
    entry["byte_basis"] = "measured"
    entry["traffic"] = {
        "path": path.name,
        "sha256": sha256(path),
        "bytes_pointer": "/bytes",
        "memory_tier": "on-chip SRAM",
    }
    with pytest.raises(ValueError, match="memory tier"):
        make_point(report, entry, hardware, tmp_path)
    entry["byte_basis"] = "tensor"
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        make_point(report, entry, hardware, tmp_path)


def test_measured_traffic_is_bound_to_workload(tmp_path: Path) -> None:
    path = tmp_path / "evidence.json"
    evidence = {
        "latency_s": 1e-5,
        "source_sha256": "abc",
        "dataset": "large",
        "precision": "fp16",
        "bytes": 64,
        "scope": "device_forward",
    }
    path.write_text(json.dumps(evidence))
    report = analyze(Function(lambda x: x + 1), (torch.ones(4, dtype=torch.float16),))
    report["provenance"] = {"source_sha256": "abc", "dataset": "large", "precision": "fp16"}
    entry = {
        "id": "measured",
        "hardware": "a100-pcie-40gb",
        **report["provenance"],
        "eligibility_note": "test only",
        "byte_basis": "measured",
        "timing": {
            "path": path.name,
            "sha256": sha256(path),
            "latency_pointer": "/latency_s",
            "scope": "device_forward",
        },
        "traffic": {
            "path": path.name,
            "sha256": sha256(path),
            "bytes_pointer": "/bytes",
            "memory_tier": "HBM2",
        },
    }
    hardware = json.loads(HARDWARE.read_text())["devices"]
    point = make_point(report, entry, hardware, tmp_path)
    assert point["arithmetic_intensity"] == 4 / 64
    assert point["traffic_sha256"] == sha256(path)
    evidence["dataset"] = "mini"
    path.write_text(json.dumps(evidence))
    entry["timing"]["sha256"] = entry["traffic"]["sha256"] = sha256(path)
    with pytest.raises(ValueError, match="traffic evidence dataset mismatch"):
        make_point(report, entry, hardware, tmp_path)
