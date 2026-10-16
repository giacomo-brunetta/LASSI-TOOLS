"""Export-friendly PyTorch implementation of PolyBench ATAX (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_M = 1900
_N = 2100

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic C initializer inputs for MINI_DATASET."""
    if fixture is not None:
        raise ValueError('ATAX does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    i_m = torch.arange(_M, device=device, dtype=torch.int64)[:, None]
    j_n = torch.arange(_N, device=device, dtype=torch.int64)[None, :]
    A = ((i_m + j_n) % _N).to(dtype) / (5 * _M)
    x = 1 + torch.arange(_N, device=device, dtype=dtype) / _N
    return (A, x)

class ATAXModel(torch.nn.Module):

    def forward(self, A, x):
        tmp = torch.matmul(A, x)
        y = torch.matmul(A.transpose(0, 1), tmp)
        return y.reshape(-1)

def make_model():
    return ATAXModel()
