"""PyTorch translation candidates for PolyBench 3mm kernel.

Implements multiple deterministic, export-oriented formulations of:
  E = A * B
  F = C * D
  G = E * F

Source semantics: linear-algebra/kernels/3mm/3mm.c
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import torch


def polybench_init_arrays(
    ni: int,
    nj: int,
    nk: int,
    nl: int,
    nm: int,
    device: torch.device | None = None,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Replicate PolyBench `init_array` in float32."""
    i_ni = torch.arange(ni, dtype=torch.int64, device=device).unsqueeze(1)
    j_nk = torch.arange(nk, dtype=torch.int64, device=device).unsqueeze(0)

    i_nk = torch.arange(nk, dtype=torch.int64, device=device).unsqueeze(1)
    j_nj = torch.arange(nj, dtype=torch.int64, device=device).unsqueeze(0)

    i_nj = torch.arange(nj, dtype=torch.int64, device=device).unsqueeze(1)
    j_nm = torch.arange(nm, dtype=torch.int64, device=device).unsqueeze(0)

    i_nm = torch.arange(nm, dtype=torch.int64, device=device).unsqueeze(1)
    j_nl = torch.arange(nl, dtype=torch.int64, device=device).unsqueeze(0)

    a = torch.remainder(i_ni * j_nk + 1, ni).to(torch.float32) / float(5 * ni)
    b = torch.remainder(i_nk * (j_nj + 1) + 2, nj).to(torch.float32) / float(5 * nj)
    c = torch.remainder(i_nj * (j_nm + 3), nl).to(torch.float32) / float(5 * nl)
    d = torch.remainder(i_nm * (j_nl + 2) + 2, nk).to(torch.float32) / float(5 * nk)

    return a, b, c, d


def _to_f32(x: torch.Tensor) -> torch.Tensor:
    return x.to(dtype=torch.float32)


def mm3_v1(
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 1: baseline explicit two intermediates then final matmul."""
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)
    e = a_f @ b_f
    f = c_f @ d_f
    g = e @ f
    return g.to(torch.float32)


def mm3_v2(
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 2: chained dense product via linalg.multi_dot (ABCD)."""
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)
    g = torch.linalg.multi_dot([a_f, b_f, c_f, d_f])
    return g.to(torch.float32)


def mm3_v3(
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 3: equivalent formulation using einsum for stage F and G."""
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)
    e = torch.mm(a_f, b_f)
    f = torch.einsum("ik,kj->ij", c_f, d_f)
    g = torch.einsum("ik,kj->ij", e, f)
    return g.to(torch.float32)


def mm3_v4(
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
    block_nj: int = 128,
) -> torch.Tensor:
    """Candidate 4: blocked accumulation over NJ in final G = E*F stage."""
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)
    e = a_f @ b_f
    f = c_f @ d_f

    g = torch.zeros((a_f.shape[0], d_f.shape[1]), dtype=torch.float32, device=a_f.device)
    nj = e.shape[1]
    for k0 in range(0, nj, block_nj):
        k1 = min(k0 + block_nj, nj)
        g = g + (e[:, k0:k1] @ f[k0:k1, :])

    return g.to(torch.float32)


def mm3_v5(
    a: torch.Tensor,
    b: torch.Tensor,
    c: torch.Tensor,
    d: torch.Tensor,
) -> torch.Tensor:
    """Candidate 5: reassociated chain ((A*B)*C)*D using addmm_ style last stage."""
    a_f, b_f, c_f, d_f = _to_f32(a), _to_f32(b), _to_f32(c), _to_f32(d)
    h = (a_f @ b_f) @ c_f
    g = torch.zeros((h.shape[0], d_f.shape[1]), dtype=torch.float32, device=h.device)
    g.addmm_(h, d_f, beta=0.0, alpha=1.0)
    return g.to(torch.float32)


class ThreeMMV1(torch.nn.Module):
    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        return mm3_v1(a, b, c, d)


class ThreeMMV2(torch.nn.Module):
    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        return mm3_v2(a, b, c, d)


class ThreeMMV3(torch.nn.Module):
    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        return mm3_v3(a, b, c, d)


class ThreeMMV4(torch.nn.Module):
    def __init__(self, block_nj: int = 128):
        super().__init__()
        self.block_nj = block_nj

    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        return mm3_v4(a, b, c, d, block_nj=self.block_nj)


class ThreeMMV5(torch.nn.Module):
    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        return mm3_v5(a, b, c, d)


VARIANTS: Dict[str, Callable[..., torch.Tensor]] = {
    "mm3_v1": mm3_v1,
    "mm3_v2": mm3_v2,
    "mm3_v3": mm3_v3,
    "mm3_v4": mm3_v4,
    "mm3_v5": mm3_v5,
}


def smoke_check() -> Dict[str, float]:
    """Deterministic self-check on two distinct shape-compatible inputs."""
    a, b, c, d = polybench_init_arrays(40, 50, 60, 70, 80)

    row = torch.arange(40, dtype=torch.float32).unsqueeze(1)
    col = torch.arange(60, dtype=torch.float32).unsqueeze(0)
    pert_a = a + 0.001 * torch.sin(0.11 * row + 0.17 * col)

    base_outputs = {
        "v1": mm3_v1(a, b, c, d),
        "v2": mm3_v2(a, b, c, d),
        "v3": mm3_v3(a, b, c, d),
        "v4": mm3_v4(a, b, c, d, block_nj=16),
        "v5": mm3_v5(a, b, c, d),
    }
    pert_outputs = {
        "v1": mm3_v1(pert_a, b, c, d),
        "v2": mm3_v2(pert_a, b, c, d),
        "v3": mm3_v3(pert_a, b, c, d),
        "v4": mm3_v4(pert_a, b, c, d, block_nj=16),
        "v5": mm3_v5(pert_a, b, c, d),
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
