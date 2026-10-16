"""Export-friendly PyTorch translation of PolyBench/C covariance."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    n, m = (1400, 1200)
    rows = torch.arange(n, device=device, dtype=torch.int64).reshape(n, 1)
    columns = torch.arange(m, device=device, dtype=torch.int64).reshape(1, m)
    data = (rows * columns).to(dtype=dtype) / m
    float_n = torch.tensor(n, device=device, dtype=dtype)
    return (data, float_n)

class Covariance(nn.Module):

    def forward(self, data, float_n):
        centered = data - data.sum(dim=0, keepdim=True) / float_n
        cov = torch.einsum('ni,nj->ij', centered, centered) / (float_n - 1)
        return (cov.reshape(-1),)

def make_model():
    return Covariance()
