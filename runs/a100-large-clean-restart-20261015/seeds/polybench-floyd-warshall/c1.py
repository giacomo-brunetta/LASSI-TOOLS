"""Export-friendly PyTorch translation of PolyBench Floyd--Warshall."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_N = 2800

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET path matrix from the C initializer."""
    if dataset != 'large':
        raise ValueError(f"unsupported dataset {dataset!r}; only 'mini' is available")
    indices = torch.arange(_MINI_N, dtype=torch.int64)
    i = indices[:, None]
    j = indices[None, :]
    path = i * j % 7 + 1
    blocked = ((i + j) % 13 == 0) | ((i + j) % 7 == 0) | ((i + j) % 11 == 0)
    path = torch.where(blocked, torch.full_like(path, 999), path)
    return (path.to(device=device, dtype=dtype),)

class FloydWarshall(torch.nn.Module):

    def forward(self, path):
        d = path.clone()
        n = d.shape[0]
        for k in range(n):
            candidate = d[:, k:k + 1] + d[k:k + 1, :]
            d = torch.minimum(d, candidate)
        return d.reshape(-1)

def make_model():
    return FloydWarshall()
