"""Backend-testable low-precision arithmetic primitives."""

from __future__ import annotations

import torch

HALF_DTYPES = (torch.float16, torch.bfloat16)
REDUCTION_METHODS = (
    "fp32-accumulate",
    "blocked-fp32",
    "pairwise",
    "kahan",
    "neumaier",
    "double-word",
    "double-word-fp32",
)


def two_sum(a: torch.Tensor, b: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Return a rounded sum and residual under unreassociated round-to-nearest operations."""
    summed = a + b
    virtual_b = summed - a
    error = (a - (summed - virtual_b)) + (b - virtual_b)
    return summed, error


def fast_two_sum(a: torch.Tensor, b: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Return sum/residual assuming ``abs(a) >= abs(b)`` and round-to-nearest."""
    summed = a + b
    return summed, b - (summed - a)


def _front(x: torch.Tensor, dim: int) -> torch.Tensor:
    if x.ndim == 0:
        raise ValueError("cannot reduce a scalar")
    dim = dim % x.ndim
    return x.movedim(dim, 0)


def pairwise_sum(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    values = _front(x, dim)
    if values.shape[0] == 0:
        return torch.zeros(values.shape[1:], dtype=x.dtype, device=x.device)
    while values.shape[0] > 1:
        count = values.shape[0]
        pairs = count // 2
        reduced = values[: 2 * pairs : 2] + values[1 : 2 * pairs : 2]
        if count % 2:
            reduced = torch.cat((reduced, values[-1:]), dim=0)
        values = reduced.to(x.dtype)
    return values[0]


def blocked_fp32_sum(
    x: torch.Tensor,
    dim: int = 0,
    *,
    block_size: int = 256,
) -> torch.Tensor:
    """Sum low-precision blocks locally, then combine their partial sums in FP32.

    This is a vectorized FABsum-style specialization: most additions remain in the
    input precision while only the much shorter reduction of block totals uses FP32.
    The block size is an accuracy/performance parameter and must be benchmarked on
    the target backend.
    """
    if block_size < 1:
        raise ValueError("block_size must be positive")
    values = _front(x, dim)
    count = values.shape[0]
    if count == 0:
        return torch.zeros(values.shape[1:], dtype=torch.float32, device=x.device)
    remainder = count % block_size
    if remainder:
        padding = torch.zeros(
            (block_size - remainder, *values.shape[1:]),
            dtype=x.dtype,
            device=x.device,
        )
        values = torch.cat((values, padding), dim=0)
    blocks = values.reshape(-1, block_size, *values.shape[1:])
    partials = blocks.sum(dim=1, dtype=x.dtype)
    return partials.sum(dim=0, dtype=torch.float32)


def kahan_sum(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    values = _front(x, dim)
    total = torch.zeros(values.shape[1:], dtype=x.dtype, device=x.device)
    correction = torch.zeros_like(total)
    for value in values:
        adjusted = value - correction
        updated = total + adjusted
        correction = (updated - total) - adjusted
        total = updated
    return total


def neumaier_sum(x: torch.Tensor, dim: int = 0) -> torch.Tensor:
    values = _front(x, dim)
    total = torch.zeros(values.shape[1:], dtype=x.dtype, device=x.device)
    correction = torch.zeros_like(total)
    for value in values:
        updated = total + value
        correction = correction + torch.where(
            total.abs() >= value.abs(),
            (total - updated) + value,
            (value - updated) + total,
        )
        total = updated
    return (total + correction).to(x.dtype)


def double_word_sum(
    x: torch.Tensor,
    dim: int = 0,
    *,
    component_dtype: torch.dtype | None = None,
) -> torch.Tensor:
    values = _front(x, dim)
    component_dtype = component_dtype or x.dtype
    values = values.to(component_dtype)
    high = torch.zeros(values.shape[1:], dtype=component_dtype, device=x.device)
    low = torch.zeros_like(high)
    for value in values:
        summed, error = two_sum(high, value)
        residual = (error + low).to(component_dtype)
        # Enforce the FastTwoSum magnitude precondition rather than assuming it.
        first = torch.where(summed.abs() >= residual.abs(), summed, residual)
        second = torch.where(summed.abs() >= residual.abs(), residual, summed)
        high, low = fast_two_sum(first, second)
        high = high.to(component_dtype)
        low = low.to(component_dtype)
    output_dtype = torch.float32 if component_dtype in HALF_DTYPES else component_dtype
    return high.to(output_dtype) + low.to(output_dtype)


def compensated_sum(
    x: torch.Tensor,
    dim: int = 0,
    *,
    method: str = "fp32-accumulate",
) -> torch.Tensor:
    if method not in REDUCTION_METHODS:
        raise ValueError(f"unknown compensation method {method!r}")
    if x.dtype not in HALF_DTYPES:
        return x.sum(dim=dim, dtype=x.dtype)
    if method == "fp32-accumulate":
        return x.sum(dim=dim, dtype=torch.float32)
    if method == "blocked-fp32":
        return blocked_fp32_sum(x, dim)
    if method == "pairwise":
        return pairwise_sum(x, dim)
    if method == "kahan":
        return kahan_sum(x, dim)
    if method == "neumaier":
        return neumaier_sum(x, dim)
    if method == "double-word":
        return double_word_sum(x, dim, component_dtype=x.dtype)
    return double_word_sum(x, dim, component_dtype=torch.float32)


def stochastic_cast(x: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """Apply mode-1 stochastic rounding at one explicit cast site.

    For finite source values within the target's finite range, this chooses the
    adjacent lower/upper values with probabilities proportional to distance. It
    does not change the rounding mode of intervening arithmetic. Non-finite and
    finite out-of-range values follow the ordinary PyTorch cast, including Inf on
    overflow, rather than being silently saturated.
    """
    if dtype not in HALF_DTYPES:
        return x.to(dtype)
    rounded = x.to(dtype)
    rounded_hi = rounded.to(x.dtype)
    negative_inf = torch.full_like(rounded, -torch.inf)
    positive_inf = torch.full_like(rounded, torch.inf)
    lower = torch.where(
        rounded_hi <= x,
        rounded,
        torch.nextafter(rounded, negative_inf),
    )
    upper = torch.where(
        rounded_hi >= x,
        rounded,
        torch.nextafter(rounded, positive_inf),
    )
    lower_hi = lower.to(x.dtype)
    upper_hi = upper.to(x.dtype)
    width = upper_hi - lower_hi
    probability_upper = torch.where(
        width > 0,
        ((x - lower_hi) / width).clamp(0, 1),
        torch.zeros_like(x),
    )
    choose_upper = torch.rand_like(x) < probability_upper
    result = torch.where(choose_upper, upper, lower)
    finite_limit = torch.finfo(dtype).max
    stochastic_range = torch.isfinite(x) & (x.abs() <= finite_limit)
    return torch.where(stochastic_range, result, rounded)
