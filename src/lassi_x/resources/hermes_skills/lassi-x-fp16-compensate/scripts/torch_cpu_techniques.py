#!/usr/bin/env python3
"""Runnable PyTorch CPU templates for every advertised compensation technique."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

import torch

from lassi_x.precision import (
    blocked_fp32_sum,
    compensated_sum,
    pairwise_sum,
    stochastic_cast,
)

if TYPE_CHECKING:
    from collections.abc import Callable

TECHNIQUES = (
    "fp32-accumulate",
    "blocked-fp32",
    "pairwise",
    "kahan",
    "neumaier",
    "double-word",
    "double-word-fp32",
    "zero-center",
    "scaling",
    "equilibrate",
    "mixed-refine",
    "precision-ramp",
    "residual-carry",
    "ozaki-split",
    "stable-reformulation",
    "stochastic-round",
)


def fp32_accumulate(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Accumulate an FP16/BF16 reduction in FP32."""
    return x.sum(dim=dim, dtype=torch.float32)


def blocked_fp32(x: torch.Tensor, dim: int = 0, block_size: int = 256) -> torch.Tensor:
    """Accumulate low-precision blocks, then combine their totals in FP32."""
    return blocked_fp32_sum(x, dim=dim, block_size=block_size)


def pairwise(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Reduce with a balanced pairwise tree."""
    return pairwise_sum(x, dim=dim)


def kahan(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Reduce sequentially with a Kahan correction."""
    return compensated_sum(x, dim=dim, method="kahan")


def neumaier(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Reduce sequentially with a Neumaier correction."""
    return compensated_sum(x, dim=dim, method="neumaier")


def double_word(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Represent the accumulator as two words in the input format."""
    return compensated_sum(x, dim=dim, method="double-word")


def double_word_fp32(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    """Represent the accumulator as two FP32 words."""
    return compensated_sum(x, dim=dim, method="double-word-fp32")


def zero_center_store(
    values: torch.Tensor,
    baseline: torch.Tensor | float,
    *,
    dtype: torch.dtype = torch.float16,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Store low-precision deviations and retain the baseline in FP32."""
    values_fp32 = values.to(torch.float32)
    baseline_fp32 = torch.as_tensor(baseline, device=values.device, dtype=torch.float32)
    deviations = (values_fp32 - baseline_fp32).to(dtype)
    return deviations, baseline_fp32


def zero_center_restore(deviations: torch.Tensor, baseline: torch.Tensor) -> torch.Tensor:
    """Reconstruct centered values in FP32."""
    return baseline.to(torch.float32) + deviations.to(torch.float32)


def power_of_two_scaled_matmul(
    left: torch.Tensor,
    right: torch.Tensor,
    *,
    left_exponent: int,
    right_exponent: int = 0,
    dtype: torch.dtype = torch.float16,
) -> torch.Tensor:
    """Scale before the low-precision matmul and undo the exact binary scale in FP32."""
    left_power = torch.tensor(left_exponent, device=left.device, dtype=torch.int32)
    right_power = torch.tensor(right_exponent, device=right.device, dtype=torch.int32)
    left_low = torch.ldexp(left.to(torch.float32), left_power).to(dtype)
    right_low = torch.ldexp(right.to(torch.float32), right_power).to(dtype)
    product = torch.matmul(left_low, right_low).to(torch.float32)
    output_power = torch.tensor(
        -(left_exponent + right_exponent), device=product.device, dtype=torch.int32
    )
    return torch.ldexp(product, output_power)


def _power_of_two_normalizer(x: torch.Tensor, dim: int) -> torch.Tensor:
    maximum = x.abs().amax(dim=dim, keepdim=True)
    safe = torch.where(maximum > 0, maximum, torch.ones_like(maximum))
    return torch.pow(torch.tensor(2.0, device=x.device), -torch.floor(torch.log2(safe)))


def equilibrated_matvec(
    matrix: torch.Tensor,
    vector: torch.Tensor,
    *,
    dtype: torch.dtype = torch.float16,
) -> torch.Tensor:
    """Apply power-of-two row/column equilibration around a low-precision matvec."""
    matrix_fp32 = matrix.to(torch.float32)
    vector_fp32 = vector.to(torch.float32)
    row_scale = _power_of_two_normalizer(matrix_fp32, dim=1)
    row_scaled = row_scale * matrix_fp32
    column_scale = _power_of_two_normalizer(row_scaled, dim=0)
    equilibrated = (row_scaled * column_scale).to(dtype)
    transformed_vector = (vector_fp32 / column_scale.squeeze(0)).to(dtype)
    transformed_result = torch.matmul(equilibrated, transformed_vector).to(torch.float32)
    return transformed_result / row_scale.squeeze(1)


def _low_precision_gaussian_solve(
    matrix: torch.Tensor,
    rhs: torch.Tensor,
    *,
    dtype: torch.dtype,
) -> torch.Tensor:
    """Small dense partial-pivoting solver expressed only with Torch tensor operations."""
    matrix_low = matrix.to(dtype).clone()
    rhs_low = rhs.to(dtype).clone()
    size = matrix_low.shape[0]
    if matrix_low.shape != (size, size) or rhs_low.shape != (size,):
        raise ValueError("expected a square matrix and one-dimensional right-hand side")

    for column in range(size):
        pivot = column + int(matrix_low[column:, column].abs().argmax().item())
        if matrix_low[pivot, column] == 0:
            raise ValueError("singular matrix")
        if pivot != column:
            matrix_row = matrix_low[column].clone()
            rhs_value = rhs_low[column].clone()
            matrix_low[column] = matrix_low[pivot]
            rhs_low[column] = rhs_low[pivot]
            matrix_low[pivot] = matrix_row
            rhs_low[pivot] = rhs_value
        for row in range(column + 1, size):
            factor = (matrix_low[row, column] / matrix_low[column, column]).to(dtype)
            matrix_low[row, column:] = (
                matrix_low[row, column:] - factor * matrix_low[column, column:]
            ).to(dtype)
            rhs_low[row] = (rhs_low[row] - factor * rhs_low[column]).to(dtype)

    solution = torch.zeros_like(rhs_low)
    for row in range(size - 1, -1, -1):
        tail = torch.sum(matrix_low[row, row + 1 :] * solution[row + 1 :], dtype=dtype)
        solution[row] = ((rhs_low[row] - tail) / matrix_low[row, row]).to(dtype)
    return solution


def mixed_refine(
    matrix: torch.Tensor,
    rhs: torch.Tensor,
    *,
    steps: int = 2,
    dtype: torch.dtype = torch.float16,
) -> torch.Tensor:
    """Use a low-precision solve with FP32 residuals and state corrections."""
    matrix_fp32 = matrix.to(torch.float32)
    rhs_fp32 = rhs.to(torch.float32)
    solution = _low_precision_gaussian_solve(matrix_fp32, rhs_fp32, dtype=dtype).to(torch.float32)
    for _ in range(steps):
        residual = rhs_fp32 - torch.matmul(matrix_fp32, solution)
        correction = _low_precision_gaussian_solve(matrix_fp32, residual, dtype=dtype).to(
            torch.float32
        )
        solution = solution + correction
    return solution


def precision_ramp(
    state: torch.Tensor,
    step: Callable[[torch.Tensor], torch.Tensor],
    *,
    low_steps: int,
    high_steps: int,
    low_dtype: torch.dtype = torch.float16,
) -> torch.Tensor:
    """Run early iterations in low precision and finish them in FP32."""
    current = state.to(low_dtype)
    for _ in range(low_steps):
        current = step(current).to(low_dtype)
    current = current.to(torch.float32)
    for _ in range(high_steps):
        current = step(current).to(torch.float32)
    return current


def residual_carry(
    state: torch.Tensor,
    updates: torch.Tensor,
    *,
    dtype: torch.dtype = torch.float16,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Carry update parts discarded at each low-precision storage boundary."""
    stored = state.to(dtype)
    residual = torch.zeros_like(stored, dtype=torch.float32)
    for update in updates:
        exact_update = update.to(torch.float32) + residual
        exact_state = stored.to(torch.float32) + exact_update
        rounded_state = exact_state.to(dtype)
        residual = exact_state - rounded_state.to(torch.float32)
        stored = rounded_state
    return stored, residual


def _split_words(
    value: torch.Tensor,
    *,
    terms: int,
    dtype: torch.dtype,
) -> list[torch.Tensor]:
    residual = value.to(torch.float32)
    words: list[torch.Tensor] = []
    for _ in range(terms):
        word = residual.to(dtype)
        words.append(word)
        residual = residual - word.to(torch.float32)
    return words


def ozaki_split_matmul(
    left: torch.Tensor,
    right: torch.Tensor,
    *,
    terms: int = 2,
    dtype: torch.dtype = torch.float16,
) -> torch.Tensor:
    """Split operands into low-precision words and combine all word products in FP32."""
    left_words = _split_words(left, terms=terms, dtype=dtype)
    right_words = _split_words(right, terms=terms, dtype=dtype)
    result = torch.zeros((left.shape[-2], right.shape[-1]), device=left.device, dtype=torch.float32)
    for left_word in left_words:
        for right_word in right_words:
            result = result + torch.matmul(left_word, right_word).to(torch.float32)
    return result


def stable_softplus(x: torch.Tensor) -> torch.Tensor:
    """Evaluate log(1 + exp(x)) without overflowing for large positive x."""
    return torch.clamp_min(x, 0) + torch.log1p(torch.exp(-x.abs()))


def stochastic_round(x: torch.Tensor, dtype: torch.dtype = torch.float16) -> torch.Tensor:
    """Apply mode-1 stochastic rounding at an explicit cast boundary."""
    return stochastic_cast(x, dtype)


def smoke_test() -> dict[str, float]:
    """Execute every advertised technique with FP16 tensors on this CPU."""
    results: dict[str, torch.Tensor] = {}
    values = torch.tensor([1.0, 2.0, 3.0, 0.001], dtype=torch.float16)
    results["fp32-accumulate"] = fp32_accumulate(values)
    results["blocked-fp32"] = blocked_fp32(values, block_size=2)
    results["pairwise"] = pairwise(values)
    results["kahan"] = kahan(values)
    results["neumaier"] = neumaier(values)
    results["double-word"] = double_word(values)
    results["double-word-fp32"] = double_word_fp32(values)

    original = torch.tensor([4096.25, 4095.5], dtype=torch.float32)
    deviations, baseline = zero_center_store(original, 4096.0)
    results["zero-center"] = zero_center_restore(deviations, baseline).sum()

    left = torch.tensor([[70000.0, 35000.0]], dtype=torch.float32)
    right = torch.tensor([[1.0], [2.0]], dtype=torch.float32)
    results["scaling"] = power_of_two_scaled_matmul(left, right, left_exponent=-2).squeeze()

    matrix = torch.tensor([[1024.0, 0.5], [2.0, 0.001]], dtype=torch.float32)
    vector = torch.tensor([0.5, 2.0], dtype=torch.float32)
    results["equilibrate"] = equilibrated_matvec(matrix, vector).sum()

    solve_matrix = torch.tensor([[4.0, 1.0], [1.0, 3.0]], dtype=torch.float32)
    solve_rhs = torch.tensor([1.0, 2.0], dtype=torch.float32)
    results["mixed-refine"] = mixed_refine(solve_matrix, solve_rhs).sum()

    target = torch.tensor(2.0, dtype=torch.float32)

    def newton_sqrt(state: torch.Tensor) -> torch.Tensor:
        return (state + target.to(state.dtype) / state) * 0.5

    results["precision-ramp"] = precision_ramp(
        torch.tensor(1.0), newton_sqrt, low_steps=2, high_steps=2
    )

    stored, residual = residual_carry(torch.tensor(2048.0), torch.ones(8, dtype=torch.float32))
    results["residual-carry"] = stored.to(torch.float32) + residual

    ozaki_left = torch.tensor([[1.0001, 2.0002], [3.0003, 4.0004]])
    ozaki_right = torch.tensor([[0.9999, 0.4999], [1.5001, 2.5001]])
    results["ozaki-split"] = ozaki_split_matmul(ozaki_left, ozaki_right).sum()

    results["stable-reformulation"] = stable_softplus(torch.tensor(20.0, dtype=torch.float16))
    torch.manual_seed(0)
    results["stochastic-round"] = stochastic_round(torch.tensor([1.0001])).float().sum()

    if tuple(results) != TECHNIQUES:
        raise AssertionError("smoke test and advertised technique lists disagree")
    expected = {
        "fp32-accumulate": 6.001,
        "blocked-fp32": 6.002,
        "pairwise": 6.0,
        "kahan": 6.0,
        "neumaier": 6.0,
        "double-word": 6.001,
        "double-word-fp32": 6.001,
        "zero-center": 8191.75,
        "scaling": 140000.0,
        "equilibrate": 514.002,
        "mixed-refine": 8.0 / 11.0,
        "precision-ramp": 2.0**0.5,
        "residual-carry": 2056.0,
        "ozaki-split": float((ozaki_left @ ozaki_right).sum()),
        "stable-reformulation": 20.0,
        "stochastic-round": 1.0,
    }
    serialized: dict[str, float] = {}
    for name, result in results.items():
        if not bool(torch.isfinite(result).all()):
            raise AssertionError(f"{name} produced a non-finite result")
        value = float(result.detach().to(torch.float64).sum().item())
        if not bool(torch.isclose(torch.tensor(value), torch.tensor(expected[name]), rtol=5e-4)):
            raise AssertionError(
                f"{name} produced {value}, expected approximately {expected[name]}"
            )
        serialized[name] = value
    return serialized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="run every CPU implementation")
    args = parser.parse_args()
    if not args.smoke:
        parser.error("pass --smoke to run the implementations")
    print(json.dumps({"torch": torch.__version__, "device": "cpu", "results": smoke_test()}))


if __name__ == "__main__":
    main()
