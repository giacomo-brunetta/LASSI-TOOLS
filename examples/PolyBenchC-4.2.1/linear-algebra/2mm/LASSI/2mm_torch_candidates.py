"""PyTorch translation candidates for PolyBench 2mm kernel.

Implements multiple deterministic, export-oriented formulations of:
  tmp = alpha * A * B
  D   = beta * D + tmp * C

Source semantics: linear-algebra/kernels/2mm/2mm.c
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import torch


def polybench_init_arrays(
    ni: int,
    nj: int,
    nk: int,
    nl: int,
    device: torch.device | None = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Replicate PolyBench `init_array` in float32."""
    i_ni = torch.arange(ni, dtype=torch.int64, device=device).unsqueeze(1)
    j_nk = torch.arange(nk, dtype=torch.int64, device=device).unsqueeze(0)
    i_nk = torch.arange(nk, dtype=torch.int64, device=device).unsqueeze(1)
    j_nj = torch.arange(nj, dtype=torch.int64, device=device).unsqueeze(0)
    i_nj = torch.arange(nj, dtype=torch.int64, device=device).unsqueeze(1)
    j_nl = torch.arange(nl, dtype=torch.int64, device=device).unsqueeze(0)

    alpha = torch.tensor(1.5, dtype=torch.float32, device=device)
    beta = torch.tensor(1.2, dtype=torch.float32, device=device)

    a = torch.remainder(i_ni * j_nk + 1, ni).to(torch.float32) / float(ni)
    b = torch.remainder(i_nk * (j_nj + 1), nj).to(torch.float32) / float(nj)
    c = torch.remainder(i_nj * (j_nl + 3) + 1, nl).to(torch.float32) / float(nl)
    d = torch.remainder(i_ni * (j_nl + 2), nk).to(torch.float32) / float(nk)

    tmp = torch.zeros((ni, nj), dtype=torch.float32, device=device)
    return alpha, beta, tmp, a, b, c, d


def _to_f32(x: torch.Tensor) -> torch.Tensor:
    return x.to(dtype=torch.float32)


def mm2_v1(
    alpha: torch.Tensor,
    beta: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 1: baseline two matmuls, fully out-of-place."""
    alpha_f = _to_f32(alpha)
    beta_f = _to_f32(beta)
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)

    tmp = alpha_f * (a_f @ b_f)
    out = beta_f * d_f + (tmp @ c_f)
    return out.to(torch.float32)


def mm2_v2(
    alpha: torch.Tensor,
    beta: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 2: scalar reassociation-safe variant (scale A before first GEMM)."""
    alpha_f = _to_f32(alpha)
    beta_f = _to_f32(beta)
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)

    tmp = (a_f * alpha_f) @ b_f
    out = beta_f * d_f + (tmp @ c_f)
    return out.to(torch.float32)


def mm2_v3(
    alpha: torch.Tensor,
    beta: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 3: equivalent op formulation via einsum in stage 2."""
    alpha_f = _to_f32(alpha)
    beta_f = _to_f32(beta)
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)

    tmp = torch.mm(a_f, b_f)
    tmp = tmp * alpha_f
    out = torch.einsum("ik,kj->ij", tmp, c_f) + beta_f * d_f
    return out.to(torch.float32)


def mm2_v4(
    alpha: torch.Tensor,
    beta: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
    block_nj: int = 128,
) -> torch.Tensor:
    """Candidate 4: block-partitioned stage-2 accumulation across NJ."""
    alpha_f = _to_f32(alpha)
    beta_f = _to_f32(beta)
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)

    tmp = alpha_f * (a_f @ b_f)
    out = beta_f * d_f

    nj = tmp.shape[1]
    for k0 in range(0, nj, block_nj):
        k1 = min(k0 + block_nj, nj)
        out = out + (tmp[:, k0:k1] @ c_f[k0:k1, :])

    return out.to(torch.float32)


def mm2_v5(
    alpha: torch.Tensor,
    beta: torch.Tensor,
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 5: in-place-style rewrite on private clone of D."""
    alpha_f = _to_f32(alpha)
    beta_f = _to_f32(beta)
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)

    tmp = alpha_f * (a_f @ b_f)
    out = d_f.clone()
    out.mul_(beta_f)
    out.addmm_(tmp, c_f, beta=1.0, alpha=1.0)
    return out.to(torch.float32)


class TwoMMV1(torch.nn.Module):
    def forward(
        self,
        alpha: torch.Tensor,
        beta: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        return mm2_v1(alpha, beta, a, b, c, d)


class TwoMMV2(torch.nn.Module):
    def forward(
        self,
        alpha: torch.Tensor,
        beta: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        return mm2_v2(alpha, beta, a, b, c, d)


class TwoMMV3(torch.nn.Module):
    def forward(
        self,
        alpha: torch.Tensor,
        beta: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        return mm2_v3(alpha, beta, a, b, c, d)


class TwoMMV4(torch.nn.Module):
    def __init__(self, block_nj: int = 128):
        super().__init__()
        self.block_nj = block_nj

    def forward(
        self,
        alpha: torch.Tensor,
        beta: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        return mm2_v4(alpha, beta, a, b, c, d, block_nj=self.block_nj)


class TwoMMV5(torch.nn.Module):
    def forward(
        self,
        alpha: torch.Tensor,
        beta: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        return mm2_v5(alpha, beta, a, b, c, d)


VARIANTS: Dict[str, Callable[..., torch.Tensor]] = {
    "mm2_v1": mm2_v1,
    "mm2_v2": mm2_v2,
    "mm2_v3": mm2_v3,
    "mm2_v4": mm2_v4,
    "mm2_v5": mm2_v5,
}


def smoke_check() -> Dict[str, float]:
    """Deterministic self-check on two distinct shape-compatible inputs."""
    alpha, beta, _, a, b, c, d = polybench_init_arrays(40, 50, 70, 80)
    row = torch.arange(40, dtype=torch.float32).unsqueeze(1)
    col = torch.arange(70, dtype=torch.float32).unsqueeze(0)
    pert_a = a + 0.001 * torch.sin(0.13 * row + 0.07 * col)

    base_outputs = {
        "v1": mm2_v1(alpha, beta, a, b, c, d),
        "v2": mm2_v2(alpha, beta, a, b, c, d),
        "v3": mm2_v3(alpha, beta, a, b, c, d),
        "v4": mm2_v4(alpha, beta, a, b, c, d, block_nj=16),
        "v5": mm2_v5(alpha, beta, a, b, c, d),
    }
    pert_outputs = {
        "v1": mm2_v1(alpha, beta, pert_a, b, c, d),
        "v2": mm2_v2(alpha, beta, pert_a, b, c, d),
        "v3": mm2_v3(alpha, beta, pert_a, b, c, d),
        "v4": mm2_v4(alpha, beta, pert_a, b, c, d, block_nj=16),
        "v5": mm2_v5(alpha, beta, pert_a, b, c, d),
    }

    ref = base_outputs["v1"]
    max_pairwise_base = max(float((ref - base_outputs[k]).abs().max()) for k in ("v2", "v3", "v4", "v5"))
    max_pairwise_pert = max(float((pert_outputs["v1"] - pert_outputs[k]).abs().max()) for k in ("v2", "v3", "v4", "v5"))
    input_sensitivity = float((base_outputs["v1"] - pert_outputs["v1"]).abs().max())

    return {
        "max_pairwise_base": max_pairwise_base,
        "max_pairwise_pert": max_pairwise_pert,
        "input_sensitivity_v1": input_sensitivity,
    }


if __name__ == "__main__":
    print(smoke_check())
