"""Export-friendly PyTorch translation of PolyBench/Doitgen."""

import torch
from torch import nn


LASSI_PRECISION = {
    "storage": "fp64",
    "operator": "fp64",
    "accumulator": "fp64",
    "output": "fp64",
}


_MINI_SHAPE = (10, 8, 12)


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Construct the deterministic MINI_DATASET inputs from doitgen.c."""
    del fixture
    if dataset not in ("default", "mini"):
        raise ValueError(f"unsupported dataset: {dataset!r}; expected 'mini'")

    nr, nq, np_ = _MINI_SHAPE
    r = torch.arange(nr, device=device, dtype=torch.int64).reshape(nr, 1, 1)
    q = torch.arange(nq, device=device, dtype=torch.int64).reshape(1, nq, 1)
    k = torch.arange(np_, device=device, dtype=torch.int64).reshape(1, 1, np_)
    i = torch.arange(np_, device=device, dtype=torch.int64).reshape(np_, 1)
    j = torch.arange(np_, device=device, dtype=torch.int64).reshape(1, np_)

    a = (r * q + k).remainder(np_).to(dtype=dtype) / np_
    c4 = (i * j).remainder(np_).to(dtype=dtype) / np_
    return (a, c4)


class Doitgen(nn.Module):
    def forward(self, a, c4):
        output = torch.einsum("rqs,sp->rqp", a, c4)
        return output.reshape(-1)


def make_model():
    return Doitgen()
