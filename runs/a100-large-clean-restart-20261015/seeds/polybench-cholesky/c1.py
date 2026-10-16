"""Export-friendly PyTorch translation of PolyBench Cholesky (MINI)."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic pre-factor matrix initialized by the C source."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    n = 2000
    indices = torch.arange(n, device=device)
    lower = indices.unsqueeze(1) >= indices.unsqueeze(0)
    columns = indices.to(dtype=dtype).unsqueeze(0)
    a0 = torch.where(lower, 1 - columns / n, torch.zeros((n, n), device=device, dtype=dtype))
    a0 = torch.where(torch.eye(n, device=device, dtype=torch.bool), torch.ones((n, n), device=device, dtype=dtype), a0)
    b = torch.zeros_like(a0)
    for t in range(n):
        column = a0[:, t:t + 1]
        b = b + column * column.transpose(0, 1)
    return (b,)

class Cholesky(nn.Module):

    def forward(self, A_in):
        if A_in.ndim != 2 or A_in.shape[0] != A_in.shape[1]:
            raise ValueError('A_in must be a square rank-2 tensor')
        A = A_in.clone()
        n = A.shape[0]
        for i in range(n):
            if i:
                solved = torch.linalg.solve_triangular(A[:i, :i], A[i, :i].unsqueeze(1), upper=False).squeeze(1)
                radicand = A[i, i] - (solved * solved).sum()
                row = torch.cat((solved, torch.sqrt(radicand).reshape(1), A[i, i + 1:]))
            else:
                row = torch.cat((torch.sqrt(A[i, i]).reshape(1), A[i, i + 1:]))
            A = torch.cat((A[:i], row.unsqueeze(0), A[i + 1:]), dim=0)
        rows, columns = torch.tril_indices(n, n, device=A.device)
        return A[rows, columns]

def make_model():
    return Cholesky()
