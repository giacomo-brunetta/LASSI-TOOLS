"""Export-friendly PolyBench GEMM candidate using an explicit einsum contraction."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    ni, nj, nk = (1000, 1100, 1200)
    i = torch.arange(ni, device=device, dtype=torch.int64).unsqueeze(1)
    j = torch.arange(nj, device=device, dtype=torch.int64).unsqueeze(0)
    k = torch.arange(nk, device=device, dtype=torch.int64).unsqueeze(1)
    c0 = ((i * j + 1) % ni).to(dtype=dtype) / ni
    a = (i * (torch.arange(nk, device=device, dtype=torch.int64) + 1) % nk).to(dtype=dtype) / nk
    b = (k * (torch.arange(nj, device=device, dtype=torch.int64) + 2) % nj).to(dtype=dtype) / nj
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, c0, a, b)

class GemmEinsum(torch.nn.Module):
    """Compute C := beta * C0 + alpha * A * B without mutating inputs."""

    def forward(self, alpha, beta, C0, A, B):
        if alpha.ndim != 0 or beta.ndim != 0:
            raise ValueError('alpha and beta must be scalar tensors')
        if C0.ndim != 2 or A.ndim != 2 or B.ndim != 2:
            raise ValueError('C0, A, and B must be rank-2 tensors')
        if A.shape[1] != B.shape[0]:
            raise ValueError('A and B must have a shared k axis')
        if C0.shape[0] != A.shape[0] or C0.shape[1] != B.shape[1]:
            raise ValueError('C0 shape must match the A-by-B output axes')
        product = torch.einsum('ik,kj->ij', A, B)
        C = beta * C0 + alpha * product
        return C.reshape(-1)

def make_model():
    return GemmEinsum()
