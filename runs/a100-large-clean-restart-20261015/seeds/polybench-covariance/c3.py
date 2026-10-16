import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic PolyBench covariance input for MINI."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    n, m = (1400, 1200)
    rows = torch.arange(n, device=device, dtype=torch.int64).unsqueeze(1)
    columns = torch.arange(m, device=device, dtype=torch.int64).unsqueeze(0)
    data = (rows * columns).to(dtype=dtype) / torch.as_tensor(m, device=device, dtype=dtype)
    float_n = torch.as_tensor(n, device=device, dtype=dtype)
    return (data, float_n)

class CovarianceModel(nn.Module):

    def forward(self, data, float_n):
        centered = data - data.sum(dim=0, keepdim=True) / float_n
        outer_products = centered.unsqueeze(2) * centered.unsqueeze(1)
        covariance = outer_products.sum(dim=0) / (float_n - 1)
        return (covariance.reshape(-1),)

def make_model():
    return CovarianceModel()
