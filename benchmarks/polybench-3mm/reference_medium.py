"""Canonical PyTorch implementation of PolyBench 3mm at MEDIUM size."""

import torch

NI, NJ, NK, NL, NM = 180, 190, 200, 210, 220

LASSI_PRECISION = {
    "storage": "requested",
    "operator": "requested",
    "accumulator": "requested",
    "output": "requested",
}


class ThreeMM(torch.nn.Module):
    def forward(
        self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor
    ) -> torch.Tensor:
        return torch.mm(torch.mm(a, b), torch.mm(c, d))


def build_inputs(device: str = "cpu", dtype: torch.dtype = torch.float64):
    integer = torch.int64
    a_i, a_j = torch.arange(NI, dtype=integer).unsqueeze(1), torch.arange(NK, dtype=integer)
    b_i, b_j = torch.arange(NK, dtype=integer).unsqueeze(1), torch.arange(NJ, dtype=integer)
    c_i, c_j = torch.arange(NJ, dtype=integer).unsqueeze(1), torch.arange(NM, dtype=integer)
    d_i, d_j = torch.arange(NM, dtype=integer).unsqueeze(1), torch.arange(NL, dtype=integer)
    values = (
        ((a_i * a_j + 1) % NI).to(dtype) / (5 * NI),
        ((b_i * (b_j + 1) + 2) % NJ).to(dtype) / (5 * NJ),
        ((c_i * (c_j + 3)) % NL).to(dtype) / (5 * NL),
        ((d_i * (d_j + 2) + 2) % NK).to(dtype) / (5 * NK),
    )
    return tuple(value.to(device) for value in values)


def make_model() -> torch.nn.Module:
    return ThreeMM()
