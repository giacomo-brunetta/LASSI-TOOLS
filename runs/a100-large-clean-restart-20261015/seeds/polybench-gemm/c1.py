"""Export-friendly PolyBench GEMM candidate using prefix-scan accumulation."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    if dataset == 'default':
        dataset = 'large'
    if dataset != 'large':
        raise ValueError(f'unsupported dataset: {dataset}')
    ni, nj, nk = (1000, 1100, 1200)
    i_c = torch.arange(ni, device=device, dtype=torch.int64).unsqueeze(1)
    j_c = torch.arange(nj, device=device, dtype=torch.int64).unsqueeze(0)
    i_a = torch.arange(ni, device=device, dtype=torch.int64).unsqueeze(1)
    k_a = torch.arange(nk, device=device, dtype=torch.int64).unsqueeze(0)
    k_b = torch.arange(nk, device=device, dtype=torch.int64).unsqueeze(1)
    j_b = torch.arange(nj, device=device, dtype=torch.int64).unsqueeze(0)
    c0 = ((i_c * j_c + 1) % ni).to(dtype=dtype) / ni
    a = (i_a * (k_a + 1) % nk).to(dtype=dtype) / nk
    b = (k_b * (j_b + 2) % nj).to(dtype=dtype) / nj
    return (torch.tensor(1.5, device=device, dtype=dtype), torch.tensor(1.2, device=device, dtype=dtype), c0, a, b)

class GemmPrefixScan(nn.Module):
    """C := beta * C0 + alpha * A * B, preserving ascending-k updates."""

    def forward(self, alpha, beta, C0, A, B):
        ni, nk = A.shape
        _, nj = C0.shape
        if C0.shape != (ni, nj):
            raise ValueError('C0 must have shape (ni, nj) matching A')
        if B.shape != (nk, nj):
            raise ValueError('B must have shape (nk, nj) matching A and C0')
        terms = alpha * A.unsqueeze(2) * B.unsqueeze(0)
        accumulated = torch.cumsum(terms, dim=1)[:, -1, :]
        C = beta * C0 + accumulated
        return C.reshape(-1)

def make_model():
    return GemmPrefixScan()
