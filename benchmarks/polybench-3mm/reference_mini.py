"""Auditable PolyBench/C 4.2.1 3mm MINI translation for pipeline reproduction."""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch
from torch import nn

if TYPE_CHECKING:
    from pathlib import Path

NI = 16
NJ = 18
NK = 20
NL = 22
NM = 24

# Empty values deliberately delegate reporting to the runtime-requested precision.
LASSI_PRECISION: dict[str, str] = {}


class ThreeMM(nn.Module):
    def forward(
        self,
        a: torch.Tensor,
        b: torch.Tensor,
        c: torch.Tensor,
        d: torch.Tensor,
    ) -> torch.Tensor:
        e = a @ b
        f = c @ d
        return e @ f


def build_inputs(
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.float64,
    fixture: Path | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    del fixture
    target = torch.device(device)
    i_ni = torch.arange(NI, device=target, dtype=torch.int64)[:, None]
    j_nk = torch.arange(NK, device=target, dtype=torch.int64)[None, :]
    i_nk = torch.arange(NK, device=target, dtype=torch.int64)[:, None]
    j_nj = torch.arange(NJ, device=target, dtype=torch.int64)[None, :]
    i_nj = torch.arange(NJ, device=target, dtype=torch.int64)[:, None]
    j_nm = torch.arange(NM, device=target, dtype=torch.int64)[None, :]
    i_nm = torch.arange(NM, device=target, dtype=torch.int64)[:, None]
    j_nl = torch.arange(NL, device=target, dtype=torch.int64)[None, :]

    # These are literal tensor forms of init_array in PolyBench's 3mm.c.
    a = ((i_ni * j_nk + 1) % NI).to(dtype) / (5 * NI)
    b = ((i_nk * (j_nj + 1) + 2) % NJ).to(dtype) / (5 * NJ)
    c = (i_nj * (j_nm + 3) % NL).to(dtype) / (5 * NL)
    d = ((i_nm * (j_nl + 2) + 2) % NK).to(dtype) / (5 * NK)
    return a.contiguous(), b.contiguous(), c.contiguous(), d.contiguous()


def make_model() -> nn.Module:
    return ThreeMM().eval()
