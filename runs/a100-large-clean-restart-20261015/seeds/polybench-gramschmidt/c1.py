"""Export-friendly modified Gram-Schmidt translation of PolyBench gramschmidt."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs used by the C reference."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    m, n = (1000, 1200)
    i = torch.arange(m, device=device, dtype=torch.int64)
    j = torch.arange(n, device=device, dtype=torch.int64)
    products_mod_m = i[:, None] * j[None, :] % m
    a = products_mod_m.to(dtype=dtype).div(m).mul(100).add(10)
    r0 = torch.zeros((n, n), device=device, dtype=dtype)
    q0 = torch.zeros((m, n), device=device, dtype=dtype)
    return (a, r0, q0)

class GramSchmidt(nn.Module):
    """Stagewise sliced modified Gram-Schmidt with dynamic matrix dimensions."""

    def forward(self, A, R0, Q0):
        if A.ndim != 2:
            raise ValueError('A must be a two-dimensional tensor')
        m, n = A.shape
        if R0.shape != (n, n):
            raise ValueError('R0 must have shape (N, N) matching A')
        if Q0.shape != (m, n):
            raise ValueError('Q0 must have shape (M, N) matching A')
        if R0.device != A.device or Q0.device != A.device:
            raise ValueError('A, R0, and Q0 must be on the same device')
        if R0.dtype != A.dtype or Q0.dtype != A.dtype:
            raise ValueError('A, R0, and Q0 must have the same dtype')
        work = A.clone()
        r = R0.clone()
        q = Q0.clone()
        for k in range(n):
            col = work[:, k]
            nrm = torch.cumsum(col * col, dim=0)[-1]
            diag = torch.sqrt(nrm)
            r[k, k] = diag
            qk = col / diag
            q[:, k] = qk
            tail = work[:, k + 1:]
            r_tail = torch.cumsum(qk[:, None] * tail, dim=0)[-1]
            r[k, k + 1:] = r_tail
            work[:, k + 1:] = tail - qk[:, None] * r_tail[None, :]
        return (r.reshape(-1), q.reshape(-1))

def make_model():
    return GramSchmidt()
