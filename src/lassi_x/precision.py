"""Backend-testable low-precision arithmetic primitives."""

from __future__ import annotations

import torch

HALF_DTYPES = (torch.float16, torch.bfloat16)
REDUCTION_METHODS = (
    "fp32-accumulate",
    "pairwise",
    "kahan",
    "neumaier",
    "double-word",
    "double-word-fp32",
)


def two_sum(a: torch.Tensor, b: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Return rounded sum and its residual under strict IEEE evaluation."""
    summed = a + b
    virtual_b = summed - a
    error = (a - (summed - virtual_b)) + (b - virtual_b)
    return summed, error


def fast_two_sum(a: torch.Tensor, b: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Return sum/residual assuming abs(a) >= abs(b)."""
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
    component_dtype = component_dtype or (torch.float16 if x.dtype in HALF_DTYPES else x.dtype)
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
    if method == "pairwise":
        return pairwise_sum(x, dim)
    if method == "kahan":
        return kahan_sum(x, dim)
    if method == "neumaier":
        return neumaier_sum(x, dim)
    if method == "double-word":
        return double_word_sum(x, dim, component_dtype=torch.float16)
    return double_word_sum(x, dim, component_dtype=torch.float32)


def stochastic_cast(x: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """Unbiased stochastic rounding between adjacent values of ``dtype``.

    Unlike half-ULP dithering, this chooses the lower/upper representable values
    with probabilities proportional to their distances from the source value.
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
    return torch.where(torch.isfinite(x), result, rounded)
