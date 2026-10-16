"""Blocked, no-pivot LU factorization for PolyBench LU."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the MINI_DATASET input using the source's ordered initializer."""
    if fixture is not None:
        raise ValueError('polybench-lu does not define an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset: {dataset!r}; expected 'mini'")
    n = 2000
    columns = torch.arange(n, device=device, dtype=dtype)
    lower_seed = 1.0 - columns / n
    seed = torch.tril(lower_seed.expand(n, n)).clone()
    diagonal = torch.arange(n, device=device)
    seed[diagonal, diagonal] = 1.0
    matrix = torch.zeros((n, n), device=device, dtype=dtype)
    for t in range(n):
        column = seed[:, t:t + 1]
        matrix = matrix + column * column.transpose(0, 1)
    return (matrix,)

class BlockedSchurLU(torch.nn.Module):
    """Right-looking Doolittle LU with fixed-width panels and no pivoting."""

    def __init__(self, block_size=8):
        super().__init__()
        if block_size <= 0:
            raise ValueError('block_size must be positive')
        self.block_size = block_size

    def forward(self, a_in):
        if a_in.ndim != 2 or a_in.shape[0] != a_in.shape[1]:
            raise ValueError('expected a square rank-2 matrix')
        n = a_in.shape[0]
        work = a_in.clone()
        for p in range(0, n, self.block_size):
            q = min(p + self.block_size, n)
            for pivot in range(p, q):
                if pivot + 1 < q:
                    work[pivot + 1:q, pivot] = work[pivot + 1:q, pivot] / work[pivot, pivot]
                    work[pivot + 1:q, pivot + 1:q] = work[pivot + 1:q, pivot + 1:q] - work[pivot + 1:q, pivot:pivot + 1] * work[pivot:pivot + 1, pivot + 1:q]
            if q == n:
                continue
            for row in range(p, q):
                if row > p:
                    correction = (work[row, p:row].unsqueeze(1) * work[p:row, q:n]).sum(dim=0)
                    work[row, q:n] = work[row, q:n] - correction
            for column in range(p, q):
                if column > p:
                    correction = (work[q:n, p:column] * work[p:column, column]).sum(dim=1)
                    rhs = work[q:n, column] - correction
                else:
                    rhs = work[q:n, column]
                work[q:n, column] = rhs / work[column, column]
            schur_rhs = work[q:n, q:n] - work[q:n, p:q] @ work[p:q, q:n]
            work[q:n, q:n] = schur_rhs
        return work.reshape(-1)

def make_model():
    return BlockedSchurLU(block_size=8)
