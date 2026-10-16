"""Panelized, integer-semantic PolyBench Nussinov translation."""
import torch
LASSI_PRECISION = {'storage': 'int64', 'operator': 'int64', 'accumulator': 'int64', 'output': 'int64'}
_MINI_N = 2500
_SPLIT_PANEL_WIDTH = 16

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the C initializer's sole input for the MINI Nussinov profile."""
    del dtype, fixture
    if dataset not in ('default', 'large'):
        raise ValueError('Nussinov candidate supports only the MINI dataset')
    indices = torch.arange(_MINI_N, device=device, dtype=torch.int64)
    seq = (indices + 1).remainder(4)
    return (seq,)

class NussinovPanelMax(torch.nn.Module):
    """Compute Nussinov DP spans with vectorized cells and split panels."""

    def forward(self, seq):
        seq = seq.clone()
        if seq.ndim != 1:
            raise ValueError('seq must be rank one')
        if seq.dtype not in (torch.int8, torch.int16, torch.int32, torch.int64, torch.uint8):
            raise TypeError('seq must have an integral dtype')
        n = seq.shape[0]
        table = torch.zeros((n, n), device=seq.device, dtype=torch.int64)
        for d in range(1, n):
            i = torch.arange(n - d, device=seq.device, dtype=torch.int64)
            j = i + d
            best = torch.maximum(table[i, j - 1], table[i + 1, j])
            if d == 1:
                paired = table[i + 1, j - 1]
            else:
                match = (seq[i] + seq[j] == 3).to(torch.int64)
                paired = table[i + 1, j - 1] + match
            best = torch.maximum(best, paired)
            split_best = torch.zeros_like(i)
            for q in range(0, d - 1, _SPLIT_PANEL_WIDTH):
                offset = torch.arange(q, min(q + _SPLIT_PANEL_WIDTH, d - 1), device=seq.device, dtype=torch.int64)
                k = i[:, None] + 1 + offset[None, :]
                panel = table[i[:, None], k] + table[k + 1, j[:, None]]
                split_best = torch.maximum(split_best, panel.amax(dim=1))
            best = torch.maximum(best, split_best)
            flat_positions = i * n + j
            table = table.reshape(-1).scatter(0, flat_positions, best).reshape(n, n)
        rows = torch.arange(n, device=seq.device, dtype=torch.int64)[:, None]
        columns = torch.arange(n, device=seq.device, dtype=torch.int64)[None, :]
        upper = rows <= columns
        return table.reshape(-1)[upper.reshape(-1)]

def make_model():
    return NussinovPanelMax()
