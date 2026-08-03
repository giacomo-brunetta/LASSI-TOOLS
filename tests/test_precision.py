from __future__ import annotations

import torch

from lassi_x.precision import (
    REDUCTION_METHODS,
    compensated_sum,
    pairwise_sum,
    stochastic_cast,
)


def test_high_precision_methods_collapse_to_plain_sum() -> None:
    values = torch.linspace(-2, 3, 101, dtype=torch.float64)
    expected = values.sum()
    for method in REDUCTION_METHODS:
        assert torch.equal(compensated_sum(values, method=method), expected)


def test_pairwise_supports_odd_length_and_negative_dimension() -> None:
    values = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    assert torch.equal(pairwise_sum(values, dim=-1), values.sum(dim=-1))


def test_double_word_improves_sequential_fp16_swamping() -> None:
    values = torch.cat(
        (
            torch.ones(4096, dtype=torch.float16),
            torch.full((4096,), 0.001, dtype=torch.float16),
        )
    )
    oracle = values.double().sum()
    sequential = torch.zeros((), dtype=torch.float16)
    for value in values:
        sequential = sequential + value
    double_word = compensated_sum(values, method="double-word").double()
    assert (double_word - oracle).abs() < (sequential.double() - oracle).abs()


def test_stochastic_cast_preserves_exact_values() -> None:
    values = torch.tensor([0.0, 1.0, -2.0, 8.0], dtype=torch.float32)
    for _ in range(10):
        assert torch.equal(stochastic_cast(values, torch.float16).float(), values)
