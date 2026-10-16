"""Export-friendly PyTorch translation of PolyBench covariance."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET C initializer inputs."""
    if fixture is not None:
        raise ValueError('covariance does not define input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    n, m = (1400, 1200)
    rows = torch.arange(n, device=device, dtype=torch.int64).unsqueeze(1)
    cols = torch.arange(m, device=device, dtype=torch.int64).unsqueeze(0)
    products = rows * cols
    data = products.to(dtype=dtype) / torch.tensor(m, device=device, dtype=dtype)
    float_n = torch.tensor(n, device=device, dtype=dtype)
    return (data, float_n)

class CovarianceModel(nn.Module):

    def forward(self, data, float_n):
        centered = data - data.sum(dim=0, keepdim=True) / float_n
        cov = centered.transpose(0, 1).matmul(centered) / (float_n - 1)
        return (cov.reshape(-1),)

def make_model():
    return CovarianceModel()
