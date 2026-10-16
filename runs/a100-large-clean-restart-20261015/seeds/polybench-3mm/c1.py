"""Export-friendly PyTorch translation of PolyBench 3mm (MINI dataset)."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'caller-provided dtype', 'operator': 'caller-provided dtype', 'accumulator': 'caller-provided dtype', 'output': 'caller-provided dtype'}
_MINI_DIMS = (800, 900, 1000, 1100, 1200)

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic PolyBench MINI input matrices A, B, C, and D."""
    if fixture not in (None, 'large'):
        raise ValueError("only the 'mini' fixture is supported")
    if dataset == 'default':
        dataset = 'large'
    if dataset != 'large':
        raise ValueError("only dataset='mini' is supported")
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise TypeError('dtype must be a floating-point torch dtype')
    ni, nj, nk, nl, nm = _MINI_DIMS
    ai = torch.arange(ni, dtype=torch.int64, device=device).reshape(ni, 1)
    ak = torch.arange(nk, dtype=torch.int64, device=device).reshape(1, nk)
    bk = torch.arange(nk, dtype=torch.int64, device=device).reshape(nk, 1)
    bj = torch.arange(nj, dtype=torch.int64, device=device).reshape(1, nj)
    ci = torch.arange(nj, dtype=torch.int64, device=device).reshape(nj, 1)
    cm = torch.arange(nm, dtype=torch.int64, device=device).reshape(1, nm)
    dm = torch.arange(nm, dtype=torch.int64, device=device).reshape(nm, 1)
    dl = torch.arange(nl, dtype=torch.int64, device=device).reshape(1, nl)
    a_num = (ai * ak + 1).remainder(ni)
    b_num = (bk * (bj + 1) + 2).remainder(nj)
    c_num = (ci * (cm + 3)).remainder(nl)
    d_num = (dm * (dl + 2) + 2).remainder(nk)
    a = a_num.to(dtype=dtype) / (5 * ni)
    b = b_num.to(dtype=dtype) / (5 * nj)
    c = c_num.to(dtype=dtype) / (5 * nl)
    d = d_num.to(dtype=dtype) / (5 * nk)
    return (a, b, c, d)

class ThreeMM(nn.Module):
    """Compute G = (A @ B) @ (C @ D) without mutating supplied inputs."""

    def forward(self, a, b, c, d):
        if a.ndim != 2 or b.ndim != 2 or c.ndim != 2 or (d.ndim != 2):
            raise ValueError('A, B, C, and D must all be rank-2 tensors')
        if a.shape[1] != b.shape[0]:
            raise ValueError('A and B have incompatible matrix dimensions')
        if c.shape[1] != d.shape[0]:
            raise ValueError('C and D have incompatible matrix dimensions')
        if b.shape[1] != c.shape[0]:
            raise ValueError('A @ B and C @ D have incompatible matrix dimensions')
        e = torch.matmul(a, b)
        f = torch.matmul(c, d)
        g = torch.matmul(e, f)
        return g.reshape(-1)

def make_model():
    return ThreeMM()
