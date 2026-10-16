"""Export-friendly PyTorch translation of PolyBench syr2k (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs in forward argument order."""
    del fixture
    if dataset != 'large':
        raise ValueError("syr2k supports only dataset='mini'")
    n, m = (1200, 1000)
    rows = torch.arange(n, device=device, dtype=torch.int64).unsqueeze(1)
    cols_m = torch.arange(m, device=device, dtype=torch.int64).unsqueeze(0)
    cols_n = torch.arange(n, device=device, dtype=torch.int64).unsqueeze(0)
    a = ((rows * cols_m + 1) % n).to(dtype=dtype) / n
    b = ((rows * cols_m + 2) % m).to(dtype=dtype) / m
    c = ((rows * cols_n + 3) % n).to(dtype=dtype) / m
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, c, a, b)

class Syr2kModel(torch.nn.Module):

    def forward(self, alpha, beta, c, a, b):
        if alpha.ndim != 0 or beta.ndim != 0:
            raise ValueError('alpha and beta must be scalar tensors')
        if a.ndim != 2 or b.ndim != 2 or c.ndim != 2:
            raise ValueError('A, B, and C must be rank-2 tensors')
        n, m = a.shape
        if b.shape != (n, m) or c.shape != (n, n):
            raise ValueError('A and B must be [N, M], and C must be [N, N]')
        c_work = c.clone()
        term_ab = torch.matmul(a * alpha, b.transpose(0, 1))
        term_ba = torch.matmul(b * alpha, a.transpose(0, 1))
        updated = c_work * beta + term_ab + term_ba
        rows = torch.arange(n, device=c.device).unsqueeze(1)
        cols = torch.arange(n, device=c.device).unsqueeze(0)
        lower_mask = cols <= rows
        return torch.where(lower_mask, updated, c_work).reshape(-1)

def make_model():
    return Syr2kModel()
