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
    )


def test_frontier_excludes_dominated_points() -> None:
    points = [point(1, 0.5), point(2, 0.3), point(3, 0.1), point(3, 0.6)]
    assert frontier_indices(points) == [0, 1, 2]
