import torch
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}
_DATASET_SIZES = {'default': 2000, 'large': 2000}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the MINI PolyBench Cholesky input without precomputing output."""
    if fixture is not None:
        raise ValueError('polybench-cholesky does not use input fixtures')
    if dataset not in _DATASET_SIZES:
        raise ValueError(f'unsupported dataset: {dataset}')
    n = _DATASET_SIZES[dataset]
    indices = torch.arange(n, device=device, dtype=torch.int64)
    row = indices[:, None]
    col = indices[None, :]
    lower_or_diagonal = col <= row
    initial_values = 1.0 - col.to(dtype=dtype) / n
    lower = torch.where(lower_or_diagonal, initial_values, torch.zeros((), device=device, dtype=dtype))
    lower = torch.where(torch.eye(n, device=device, dtype=torch.bool), torch.ones((), device=device, dtype=dtype), lower)
    a = torch.zeros((n, n), device=device, dtype=dtype)
    for t in range(n):
        column = lower[:, t]
        a = a + column[:, None] * column[None, :]
    return (a,)

class CholeskyModel(torch.nn.Module):

    def forward(self, a_in):
        a = a_in.clone()
        n = a.shape[0]
        if a.ndim != 2 or a.shape[1] != n:
            raise ValueError('A must be a square matrix')
        for k in range(n):
            radicand = a[k, k]
            torch._assert(radicand >= 0, 'Cholesky pivot radicand must be nonnegative')
            pivot = torch.sqrt(radicand)
            col = a[k + 1:, k] / pivot
            trailing = a[k + 1:, k + 1:]
            updated_trailing = trailing - col[:, None] * col[None, :]
            lower_mask = torch.tril(torch.ones(updated_trailing.shape, device=a.device, dtype=torch.bool))
            trailing = torch.where(lower_mask, updated_trailing, trailing)
            current_row = torch.cat((a[k:k + 1, :k], pivot.reshape(1, 1), a[k:k + 1, k + 1:]), dim=1)
            lower_rows = torch.cat((a[k + 1:, :k], col[:, None], trailing), dim=1)
            a = torch.cat((a[:k, :], current_row, lower_rows), dim=0)
        live_out_mask = torch.tril(torch.ones((n, n), device=a.device, dtype=torch.bool))
        return a[live_out_mask]

def make_model():
    return CholeskyModel()
