"""Export-friendly PyTorch translation of PolyBench Jacobi-2D (MINI)."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_N = 1300
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic initial A and B arrays for the MINI profile."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    i = torch.arange(_N, device=device, dtype=torch.int64).reshape(_N, 1)
    j = torch.arange(_N, device=device, dtype=torch.int64).reshape(1, _N)
    a = (i * (j + 2)).to(dtype)
    a = (a + 2) / _N
    b = (i * (j + 3)).to(dtype)
    b = (b + 3) / _N
    return (a, b)

class Jacobi2D(torch.nn.Module):
    """Twenty functional Jacobi B-then-A stages with preserved boundaries."""

    def forward(self, A_in, B_in):
        if A_in.ndim != 2 or B_in.ndim != 2:
            raise ValueError('A_in and B_in must be rank-2 tensors')
        if A_in.shape != B_in.shape:
            raise ValueError('A_in and B_in must have identical shapes')
        n = A_in.shape[0]
        if A_in.shape[1] != n:
            raise ValueError('A_in and B_in must be square')
        if n < 3:
            raise ValueError('A_in and B_in must have side length at least 3')
        A = A_in.clone()
        B = B_in.clone()
        for _ in range(_TSTEPS):
            b_interior = 0.2 * (A[1:-1, 1:-1] + A[1:-1, :-2] + A[1:-1, 2:] + A[2:, 1:-1] + A[:-2, 1:-1])
            b_middle = torch.cat((B[1:-1, :1], b_interior, B[1:-1, -1:]), dim=1)
            B = torch.cat((B[:1, :], b_middle, B[-1:, :]), dim=0)
            a_interior = 0.2 * (B[1:-1, 1:-1] + B[1:-1, :-2] + B[1:-1, 2:] + B[2:, 1:-1] + B[:-2, 1:-1])
            a_middle = torch.cat((A[1:-1, :1], a_interior, A[1:-1, -1:]), dim=1)
            A = torch.cat((A[:1, :], a_middle, A[-1:, :]), dim=0)
        return A.reshape(-1)

def make_model():
    return Jacobi2D()
