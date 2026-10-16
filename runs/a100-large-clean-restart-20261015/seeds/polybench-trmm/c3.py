"""Export-friendly PolyBench TRMM translation for the MINI dataset."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_M = 1000
_MINI_N = 1200
_PANEL_WIDTH = 4

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from ``trmm.c``."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset {dataset!r}; only MINI_DATASET is available')
    if fixture is not None:
        raise ValueError('PolyBench TRMM has no input fixture')
    rows = torch.arange(_MINI_M, device=device, dtype=torch.int64).reshape(-1, 1)
    cols_m = torch.arange(_MINI_M, device=device, dtype=torch.int64).reshape(1, -1)
    lower = (rows + cols_m).remainder(_MINI_M).to(dtype) / _MINI_M
    diagonal = torch.eye(_MINI_M, device=device, dtype=torch.bool)
    strict_lower = rows > cols_m
    a = torch.where(strict_lower, lower, torch.zeros_like(lower))
    a = torch.where(diagonal, torch.ones_like(a), a)
    cols_n = torch.arange(_MINI_N, device=device, dtype=torch.int64).reshape(1, -1)
    b = (_MINI_N + rows - cols_n).remainder(_MINI_N).to(dtype) / _MINI_N
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    return (alpha, a, b)

class TRMMPanelModel(nn.Module):
    """Compute ``alpha * A.T * B`` using bounded reduction-axis panels."""

    def forward(self, alpha, a, b):
        out = b.clone()
        m = a.shape[0]
        for s in range(0, m, _PANEL_WIDTH):
            e = min(s + _PANEL_WIDTH, m)
            if s:
                prefix_delta = a[s:e, :s].transpose(0, 1) @ b[s:e, :]
            else:
                prefix_delta = out[:0]
            local_coefficients = torch.triu(a[s:e, s:e].transpose(0, 1), diagonal=1)
            local_delta = local_coefficients @ b[s:e, :]
            out = torch.cat((out[:s] + prefix_delta, out[s:e] + local_delta, out[e:]), dim=0)
        return (alpha * out).reshape(-1)

def make_model():
    return TRMMPanelModel()
