"""Export-friendly PolyBench GEMM candidate using a native matrix product."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'backend matmul accumulator for input dtype', 'output': 'input dtype'}
_DATASET_SIZES = {'default': (1000, 1100, 1200), 'large': (1000, 1100, 1200)}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build deterministic PolyBench GEMM inputs for the selected profile.

    Integer index arithmetic is completed before conversion to ``dtype``, as
    in the C initializer.  There is no fixture for this benchmark.
    """
    del fixture
    try:
        ni, nj, nk = _DATASET_SIZES[dataset]
    except KeyError as error:
        raise ValueError(f'unsupported dataset profile: {dataset!r}') from error
    i_ni = torch.arange(ni, device=device, dtype=torch.int64).reshape(ni, 1)
    j_nj = torch.arange(nj, device=device, dtype=torch.int64).reshape(1, nj)
    j_nk = torch.arange(nk, device=device, dtype=torch.int64).reshape(1, nk)
    i_nk = torch.arange(nk, device=device, dtype=torch.int64).reshape(nk, 1)
    c0 = ((i_ni * j_nj + 1) % ni).to(dtype) / ni
    a = (i_ni * (j_nk + 1) % nk).to(dtype) / nk
    b = (i_nk * (j_nj + 2) % nj).to(dtype) / nj
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, c0, a, b)

class _Gemm(nn.Module):

    def forward(self, alpha, beta, C0, A, B):
        if alpha.ndim != 0 or beta.ndim != 0:
            raise ValueError('alpha and beta must be scalar tensors')
        if C0.ndim != 2 or A.ndim != 2 or B.ndim != 2:
            raise ValueError('C0, A, and B must be rank-2 tensors')
        ni, nj = C0.shape
        a_ni, nk = A.shape
        b_nk, b_nj = B.shape
        if a_ni != ni or b_nk != nk or b_nj != nj:
            raise ValueError('incompatible GEMM shapes: expected C0=[NI,NJ], A=[NI,NK], and B=[NK,NJ]')
        C = beta * C0 + alpha * torch.matmul(A, B)
        return C.reshape(-1)

def make_model():
    return _Gemm()
