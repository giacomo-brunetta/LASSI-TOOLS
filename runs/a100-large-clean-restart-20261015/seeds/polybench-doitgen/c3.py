"""Vectorized PyTorch translation of PolyBench/C doitgen (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic PolyBench MINI_DATASET inputs A and C4."""
    if dataset not in ('default', 'large'):
        raise ValueError('doitgen supports only the MINI_DATASET profile')
    if fixture is not None:
        raise ValueError('doitgen does not define input fixtures')
    nr, nq, np = (150, 140, 160)
    r = torch.arange(nr, device=device, dtype=torch.int64).view(nr, 1, 1)
    q = torch.arange(nq, device=device, dtype=torch.int64).view(1, nq, 1)
    s = torch.arange(np, device=device, dtype=torch.int64).view(1, 1, np)
    A = ((r * q + s) % np).to(dtype=dtype) / np
    c_s = torch.arange(np, device=device, dtype=torch.int64).view(np, 1)
    p = torch.arange(np, device=device, dtype=torch.int64).view(1, np)
    C4 = (c_s * p % np).to(dtype=dtype) / np
    return (A, C4)

class Doitgen(torch.nn.Module):

    def forward(self, A, C4):
        if A.ndim != 3:
            raise ValueError('A must have shape [nr, nq, np]')
        if C4.ndim != 2:
            raise ValueError('C4 must have shape [np, np]')
        np = A.shape[2]
        if C4.shape[0] != np or C4.shape[1] != np:
            raise ValueError('C4 must be square with side length A.shape[2]')
        products = A.unsqueeze(-1) * C4.unsqueeze(0).unsqueeze(0)
        output = products.sum(dim=2)
        return output.reshape(-1)

def make_model():
    return Doitgen()
