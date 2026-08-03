from __future__ import annotations

import math

from .types import Measurement, Status


def valid_point(point: Measurement) -> bool:
    return (
        point.status == Status.OK
        and point.latency_s is not None
        and point.y_error is not None
        and math.isfinite(point.latency_s)
        and math.isfinite(point.y_error)
    )


def frontier_indices(points: list[Measurement]) -> list[int]:
    valid = [
        (index, point, point.latency_s, point.y_error)
        for index, point in enumerate(points)
        if valid_point(point)
    ]
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
