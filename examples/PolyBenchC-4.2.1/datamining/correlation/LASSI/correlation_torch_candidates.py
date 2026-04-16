"""PyTorch translation candidates for PolyBench correlation kernel.

Implements multiple deterministic candidate formulations equivalent to
`kernel_correlation` semantics from `correlation.c`.
"""

from __future__ import annotations

from typing import Callable, Dict

import torch


def polybench_init_data(n: int, m: int, device: torch.device | None = None) -> torch.Tensor:
    """Replicates PolyBench `init_array` data generation in float32."""
    i = torch.arange(n, dtype=torch.float32, device=device).unsqueeze(1)
    j = torch.arange(m, dtype=torch.float32, device=device).unsqueeze(0)
    return (i * j) / float(m) + i


def _normalize_columns(data: torch.Tensor, eps: float = 0.1) -> torch.Tensor:
    """Center and reduce columns per kernel semantics using float32 path."""
    x = data.to(dtype=torch.float32)
    n = x.shape[0]
    float_n = float(n)
    mean = torch.sum(x, dim=0) / float_n
    centered = x - mean
    stddev = torch.sqrt(torch.sum(centered * centered, dim=0) / float_n)
    eps_tensor = torch.full_like(stddev, eps)
    stddev = torch.where(stddev <= eps_tensor, torch.ones_like(stddev), stddev)
    sqrt_n = torch.sqrt(x.new_tensor(float_n))
    return centered / (sqrt_n * stddev)


def _with_unit_diagonal(corr: torch.Tensor) -> torch.Tensor:
    """Out-of-place unit-diagonal construction (no in-place diagonal mutation)."""
    m = corr.shape[0]
    eye = torch.eye(m, dtype=corr.dtype, device=corr.device)
    return corr * (1.0 - eye) + eye


def corr_v1(data: torch.Tensor, eps: float = 0.1) -> torch.Tensor:
    """Candidate 1: fully tensorized normalization + matmul correlation."""
    normalized = _normalize_columns(data, eps=eps)
    corr = normalized.transpose(0, 1) @ normalized
    corr = 0.5 * (corr + corr.transpose(0, 1))
    corr = corr.to(torch.float32)
    return _with_unit_diagonal(corr)


def corr_v2(data: torch.Tensor, eps: float = 0.1) -> torch.Tensor:
    """Candidate 2: block-vectorized accumulation with explicit symmetrization."""
    normalized = _normalize_columns(data, eps=eps)
    m = normalized.shape[1]
    block_size = 64

    row_blocks = []
    for i0 in range(0, m, block_size):
        i1 = min(i0 + block_size, m)
        block_corr = normalized[:, i0:i1].transpose(0, 1) @ normalized
        row_blocks.append(block_corr)

    corr = torch.cat(row_blocks, dim=0).to(torch.float32)
    corr = 0.5 * (corr + corr.transpose(0, 1))
    return _with_unit_diagonal(corr)


def corr_v3(data: torch.Tensor, eps: float = 0.1) -> torch.Tensor:
    """Candidate 3: decomposition with reciprocal scaling + einsum."""
    x = data.to(dtype=torch.float32)
    n = x.shape[0]
    float_n = float(n)

    mean = x.mean(dim=0)
    centered = x - mean
    variance = (centered * centered).sum(dim=0) / float_n
    stddev = torch.sqrt(variance)
    eps_tensor = torch.full_like(stddev, eps)
    stddev = torch.where(stddev <= eps_tensor, torch.ones_like(stddev), stddev)

    inv_scale = torch.reciprocal(torch.sqrt(x.new_tensor(float_n)) * stddev)
    normalized = centered * inv_scale

    corr = torch.einsum("ki,kj->ij", normalized, normalized)
    corr = torch.triu(corr) + torch.triu(corr, diagonal=1).transpose(0, 1)
    corr = corr.to(torch.float32)
    return _with_unit_diagonal(corr)


class CorrelationV1(torch.nn.Module):
    def forward(self, data: torch.Tensor) -> torch.Tensor:
        return corr_v1(data)


class CorrelationV2(torch.nn.Module):
    def forward(self, data: torch.Tensor) -> torch.Tensor:
        return corr_v2(data)


class CorrelationV3(torch.nn.Module):
    def forward(self, data: torch.Tensor) -> torch.Tensor:
        return corr_v3(data)


def smoke_check() -> Dict[str, float]:
    """Run deterministic smoke checks on two distinct inputs."""
    d1 = polybench_init_data(32, 28)
    row = torch.arange(32, dtype=torch.float32).unsqueeze(1)
    col = torch.arange(28, dtype=torch.float32).unsqueeze(0)
    perturb = 0.01 * torch.sin(0.17 * row + 0.11 * col)
    d2 = d1 + perturb

    out1_v1 = corr_v1(d1)
    out1_v2 = corr_v2(d1)
    out1_v3 = corr_v3(d1)

    out2_v1 = corr_v1(d2)
    out2_v2 = corr_v2(d2)
    out2_v3 = corr_v3(d2)

    max_pairwise_d1 = max(
        (out1_v1 - out1_v2).abs().max().item(),
        (out1_v1 - out1_v3).abs().max().item(),
        (out1_v2 - out1_v3).abs().max().item(),
    )
    max_pairwise_d2 = max(
        (out2_v1 - out2_v2).abs().max().item(),
        (out2_v1 - out2_v3).abs().max().item(),
        (out2_v2 - out2_v3).abs().max().item(),
    )
    input_delta = (out1_v1 - out2_v1).abs().max().item()

    return {
        "max_pairwise_d1": float(max_pairwise_d1),
        "max_pairwise_d2": float(max_pairwise_d2),
        "input_delta_v1": float(input_delta),
    }


if __name__ == "__main__":
    stats = smoke_check()
    print(stats)
