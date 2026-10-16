"""Export-friendly PyTorch translation of PolyBench TRMM."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype (backend matmul accumulation)', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('TRMM does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    m, n = (1000, 1200)
    row = torch.arange(m, device=device, dtype=torch.int64).reshape(m, 1)
    col_a = torch.arange(m, device=device, dtype=torch.int64).reshape(1, m)
    col_b = torch.arange(n, device=device, dtype=torch.int64).reshape(1, n)
    lower_values = ((row + col_a) % m).to(dtype=dtype) / m
    a = torch.where(row > col_a, lower_values, torch.zeros_like(lower_values))
    a = a + torch.eye(m, device=device, dtype=dtype)
    b = ((n + row - col_b) % n).to(dtype=dtype) / n
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    return (alpha, a, b)

class TrmmModel(nn.Module):

    def forward(self, alpha, a, b):
        if a.ndim != 2 or b.ndim != 2:
            raise ValueError('A and B must be rank-2 tensors')
        m, width = a.shape
        if m != width:
            raise ValueError('A must be square')
        if b.shape[0] != m:
            raise ValueError('A and B must have compatible leading dimensions')
        if alpha.numel() != 1:
            raise ValueError('alpha must be a scalar tensor')
        if alpha.device != a.device or b.device != a.device:
            raise ValueError('alpha, A, and B must be on the same device')
        if alpha.dtype != a.dtype or b.dtype != a.dtype:
            raise ValueError('alpha, A, and B must have the same dtype')
        u = torch.triu(a.transpose(0, 1), diagonal=1) + torch.eye(m, device=a.device, dtype=a.dtype)
        out = alpha * (u @ b)
        return out.reshape(-1)

def make_model():
    return TrmmModel()
