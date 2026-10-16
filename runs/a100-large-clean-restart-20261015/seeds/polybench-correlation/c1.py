"""Export-friendly PyTorch translation of PolyBench correlation."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET input tensor."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset}')
    n, m = (1400, 1200)
    i = torch.arange(n, device=device, dtype=dtype)[:, None]
    j = torch.arange(m, device=device, dtype=dtype)[None, :]
    data = i * j / m + i
    return (data,)

class Correlation(nn.Module):

    def forward(self, data):
        float_n = torch.tensor(data.shape[0], device=data.device, dtype=data.dtype)
        mean = data.sum(dim=0) / float_n
        delta = data - mean
        stddev = torch.sqrt((delta * delta).sum(dim=0) / float_n)
        stddev = torch.where(stddev <= 0.1, torch.ones_like(stddev), stddev)
        normalized = delta / (torch.sqrt(float_n) * stddev)
        gram = normalized.transpose(0, 1) @ normalized
        upper = torch.triu(gram, diagonal=1)
        corr = upper + upper.transpose(0, 1) + torch.diag_embed(torch.ones_like(mean))
        return corr.reshape(-1)

def make_model():
    return Correlation()
