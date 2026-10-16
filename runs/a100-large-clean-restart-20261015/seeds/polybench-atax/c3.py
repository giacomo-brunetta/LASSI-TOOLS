"""Export-friendly PyTorch implementation of PolyBench ATAX (MINI profile)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_M = 1900
_N = 2100

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('ATAX does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    i = torch.arange(_M, device=device, dtype=torch.int64).reshape(_M, 1)
    j = torch.arange(_N, device=device, dtype=torch.int64).reshape(1, _N)
    A = ((i + j) % _N).to(dtype=dtype) / 9500
    x = 1 + torch.arange(_N, device=device, dtype=dtype) / _N
    return (A, x)

class ATAXModel(torch.nn.Module):

    def forward(self, A, x):
        gram = torch.matmul(A.transpose(0, 1), A)
        y = torch.matmul(gram, x)
        return y.reshape(-1)

def make_model():
    return ATAXModel()
