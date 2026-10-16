"""Export-friendly PyTorch translation of PolyBench/C LU."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI PolyBench LU input matrix."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    n = 2000
    indices = torch.arange(n, device=device)
    rows = indices.unsqueeze(1)
    columns = indices.unsqueeze(0)
    lower_seed = torch.where(columns <= rows, 1 - columns.to(dtype) / n, torch.zeros((n, n), dtype=dtype, device=device))
    lower_seed.diagonal().fill_(1)
    matrix = torch.zeros((n, n), dtype=dtype, device=device)
    for t in range(n):
        column = lower_seed[:, t]
        matrix = matrix + column.unsqueeze(1) * column.unsqueeze(0)
    return (matrix,)

class _LUModule(torch.nn.Module):

    def forward(self, A_in):
        n = A_in.shape[0]
        L = torch.eye(n, dtype=A_in.dtype, device=A_in.device)
        U = torch.zeros_like(A_in)
        for i in range(n):
            if i == 0:
                u_row = A_in[0, :]
            else:
                products = L[i, :i].unsqueeze(1) * U[:i, i:]
                u_row = A_in[i, i:] - products.sum(dim=0)
            U[i, i:] = u_row
            if i + 1 < n:
                if i == 0:
                    l_column = A_in[1:, 0] / U[0, 0]
                else:
                    products = L[i + 1:, :i] * U[:i, i].unsqueeze(0)
                    l_column = (A_in[i + 1:, i] - products.sum(dim=1)) / U[i, i]
                L[i + 1:, i] = l_column
        packed = torch.tril(L, diagonal=-1) + torch.triu(U)
        return packed.reshape(-1)

def make_model():
    return _LUModule()
