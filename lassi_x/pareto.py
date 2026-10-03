from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Measurement


def valid_point(point: Measurement) -> bool:
    """Return whether a point has a complete, device-derived latency/error pair."""

    return point.frontier_eligible


def frontier_indices(points: list[Measurement]) -> list[int]:
    valid = [
        (index, point, point.latency_s, point.y_error)
        for index, point in enumerate(points)
        if valid_point(point)
    ]
    # valid_point excludes host and orchestration timing unconditionally.
    frontier: list[int] = []
    for i, _, latency, error in valid:
        assert latency is not None
        assert error is not None
        dominated = False
        for j, _, other_latency, other_error in valid:
            if i == j:
                continue
            assert other_latency is not None
            assert other_error is not None
            if (
                other_latency <= latency
                and other_error <= error
                and (other_latency < latency or other_error < error)
            ):
                dominated = True
                break
        if not dominated:
            frontier.append(i)
    return frontier
