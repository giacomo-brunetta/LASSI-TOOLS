"""Export-friendly four-block translation of the MINI iir-filter-bank kernel."""

import torch
from torch import nn
import torch.nn.functional as F


LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float64",
    "accumulator": "float64",
    "output": "float64",
}

_FILTERS = 4
_BLOCK = 8
_BLOCKS = 4
_MINI_SIZE = _BLOCK * _BLOCKS


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Construct the reference program's deterministic MINI input signal."""
    if dataset not in ("default", "mini"):
        raise ValueError("iir-filter-bank supports only the MINI dataset")
    if fixture is not None:
        raise ValueError("iir-filter-bank has no input fixtures")
    sample = torch.arange(_MINI_SIZE, device=device, dtype=dtype)
    signal = (
        torch.sin(0.09 * sample)
        + 0.35 * torch.cos(0.31 * sample)
        + 0.12 * torch.sin(0.71 * sample)
        + (torch.remainder(sample, 17) == 0).to(dtype) * 0.5
    )
    return (signal,)


class IIRFilterBank(nn.Module):
    def __init__(self):
        super().__init__()
        self.register_buffer("b0", torch.tensor([0.06745527, 0.20657208, 0.39133577, 0.63894553], dtype=torch.float64))
        self.register_buffer("b1", torch.tensor([0.13491055, 0.41314417, 0.0, -1.27789105], dtype=torch.float64))
        self.register_buffer("b2", torch.tensor([0.06745527, 0.20657208, -0.39133577, 0.63894553], dtype=torch.float64))
        self.register_buffer("a1", torch.tensor([-1.14298050, -0.36952738, -0.36952738, -1.14298050], dtype=torch.float64))
        self.register_buffer("a2", torch.tensor([0.41280160, 0.19581571, 0.21767222, 0.41280160], dtype=torch.float64))

    def forward(self, signal):
        if signal.ndim != 1:
            raise ValueError("signal must be a one-dimensional tensor")
        length = signal.shape[0]
        if length < 1 or length > _MINI_SIZE:
            raise ValueError("signal length must be between 1 and 32")

        b0 = self.b0.to(device=signal.device, dtype=signal.dtype)
        b1 = self.b1.to(device=signal.device, dtype=signal.dtype)
        b2 = self.b2.to(device=signal.device, dtype=signal.dtype)
        a1 = self.a1.to(device=signal.device, dtype=signal.dtype)
        a2 = self.a2.to(device=signal.device, dtype=signal.dtype)

        matrix = torch.stack(
            (
                torch.stack((-a1, torch.ones_like(a1)), dim=-1),
                torch.stack((-a2, torch.zeros_like(a2)), dim=-1),
            ),
            dim=-2,
        )
        drive = torch.stack((b1 - a1 * b0, b2 - a2 * b0), dim=-1)

        # The fixed eight-step power sequence is independent of data length.
        identity = torch.eye(2, dtype=signal.dtype, device=signal.device).expand(_FILTERS, -1, -1)
        powers = [identity]
        for _ in range(_BLOCK):
            powers.append(torch.bmm(matrix, powers[-1]))
        powers = torch.stack(powers, dim=1)  # [filter, exponent, row, column]

        padded = F.pad(signal, (0, _MINI_SIZE - length))
        blocks = padded.reshape(_BLOCKS, _BLOCK)

        # h[f, block] = sum_j A^(7-j) g x[block,j].
        h_weights = torch.matmul(
            powers[:, :_BLOCK].flip(1), drive[:, None, :, None]
        ).squeeze(-1)
        h = torch.einsum("fts,bt->fbs", h_weights, blocks)
        transition = powers[:, _BLOCK]

        # Four coarse block-state propagations, each over all filters.
        state = torch.zeros((_FILTERS, 2), dtype=signal.dtype, device=signal.device)
        starts = []
        for block in range(_BLOCKS):
            starts.append(state)
            state = torch.bmm(transition, state.unsqueeze(-1)).squeeze(-1) + h[:, block]
        starts = torch.stack(starts, dim=1)

        # Zero-start causal response within each eight-sample block.
        time = torch.arange(_BLOCK, device=signal.device)
        lag = time[:, None] - time[None, :]
        causal = lag >= 0
        exponent = torch.clamp(lag - 1, min=0)
        propagated_drive = torch.matmul(powers[:, exponent], drive[:, None, None, :, None]).squeeze(-1)[..., 0]
        impulse = torch.where(causal.unsqueeze(0), propagated_drive, torch.zeros_like(propagated_drive))
        impulse[:, time, time] = b0[:, None]
        local = torch.einsum("fjk,bk->fbj", impulse, blocks)

        # y_j's correction from the state before the first block sample is e0 A^j q.
        state_correction = torch.einsum("fjs,fbs->fbj", powers[:, :_BLOCK, 0, :], starts)
        output = (local + state_correction).reshape(_FILTERS, _MINI_SIZE)
        return output[:, :length].flatten()


def make_model():
    return IIRFilterBank()
