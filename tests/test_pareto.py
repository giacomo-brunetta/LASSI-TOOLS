from __future__ import annotations

from lassi_x.pareto import frontier_indices
from lassi_x.types import Measurement, Status


def point(latency: float, error: float) -> Measurement:
    return Measurement(
        kernel="k",
        candidate_id="c",
        variant_id="v",
        backend="cpu",
        precision="fp16",
        compensation="none",
        status=Status.OK,
        module_path="m.py",
        storage_precision="fp16",
        operator_precision="fp16",
        accumulator_precision="fp16",
        output_precision="fp16",
        latency_s=latency,
        max_rel_error=error,
        evaluation_output_checked=True,
        evaluation_output_finite=True,
        evaluation_semantic_verified=True,
        accuracy_source="timed_device_workload",
    )


def test_frontier_excludes_dominated_points() -> None:
    points = [point(1, 0.5), point(2, 0.3), point(3, 0.1), point(3, 0.6)]
    assert frontier_indices(points) == [0, 1, 2]


def test_frontier_excludes_nonphysical_axes() -> None:
    points = [point(1, 0.5), point(0, 0.1), point(2, -0.1)]
    assert frontier_indices(points) == [0]


def test_frontier_uses_measurement_selected_error_metric() -> None:
    fast = point(1, 0.001)
    slow = point(2, 0.1)
    fast.error_metric = "relative_l2"
    slow.error_metric = "relative_l2"
    fast.relative_l2 = 0.5
    slow.relative_l2 = 0.01
    assert frontier_indices([fast, slow]) == [0, 1]


def test_frontier_excludes_latency_without_device_accuracy_evidence() -> None:
    incomplete = point(1, 0.1)
    incomplete.accuracy_source = ""
    assert frontier_indices([incomplete]) == []


def test_host_latency_cannot_dominate_architectural_accelerator_frontier() -> None:
    host = point(0.1, 0.0)
    host.timing_protocol = "host-single-call-v1"
    accelerator = point(1.0, 0.1)
    accelerator.backend = "a100"
    accelerator.timing_protocol = "architectural-single-call-v1"
    assert frontier_indices([host, accelerator]) == [1]
