"""Export-friendly whole-grid triangular solve for PolyBench Seidel-2D.

The dense causal matrix has shape ``((n - 2) ** 2, (n - 2) ** 2)`` and
therefore quadratic storage in the number of interior cells. It is intended
for the MINI profile; larger profiles need a sparse or banded replacement.
"""
import torch
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}
_MINI_N = 2000
_TIMESTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET input from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    if fixture is not None:
        raise ValueError('seidel-2d does not use an input fixture')
    coordinates = torch.arange(_MINI_N, device=device, dtype=dtype)
    i = coordinates[:, None]
    j = coordinates[None, :]
    return ((i * (j + 2) + 2) / _MINI_N,)

class Seidel2D(torch.nn.Module):
    """Twenty C-raster Gauss--Seidel sweeps expressed as triangular solves."""

    def _causal_matrix(self, m, *, device, dtype):
        length = m * m
        indices = torch.arange(length, device=device)
        row = torch.div(indices, m, rounding_mode='floor')
        column = torch.remainder(indices, m)
        delta = indices[:, None] - indices[None, :]
        left = (delta == 1) & (column[:, None] > 0)
        upper_left = (delta == m + 1) & (row[:, None] > 0) & (column[:, None] > 0)
        upper = (delta == m) & (row[:, None] > 0)
        upper_right = (delta == m - 1) & (row[:, None] > 0) & (column[:, None] < m - 1)
        dependency = left | upper_left | upper | upper_right
        return torch.eye(length, device=device, dtype=dtype).masked_fill(dependency, -1.0 / 9.0)

    def forward(self, a):
        work = a.clone()
        n = work.shape[0]
        if n < 3:
            return work.reshape(-1)
        m = n - 2
        triangular = self._causal_matrix(m, device=work.device, dtype=work.dtype)
        top_padding = torch.zeros((m - 1, m), device=work.device, dtype=work.dtype)
        left_padding = torch.zeros((m, m - 1), device=work.device, dtype=work.dtype)
        right_padding = torch.zeros((m, m - 1), device=work.device, dtype=work.dtype)
        scalar_zero = torch.zeros((1, 1), device=work.device, dtype=work.dtype)
        for _ in range(_TIMESTEPS):
            rhs = (work[1:-1, 1:-1] + work[1:-1, 2:] + work[2:, :-2] + work[2:, 1:-1] + work[2:, 2:]) / 9.0
            top = work[0, :-2] + work[0, 1:-1] + work[0, 2:]
            top_boundary = torch.cat((top[None, :], top_padding), dim=0) / 9.0
            left_boundary = torch.cat((work[1:-1, :1], left_padding), dim=1) / 9.0
            upper_left_column = torch.cat((scalar_zero, work[1:-2, :1]), dim=0)
            upper_left_boundary = torch.cat((upper_left_column, left_padding), dim=1) / 9.0
            upper_right_column = torch.cat((scalar_zero, work[1:-2, -1:]), dim=0)
            upper_right_boundary = torch.cat((right_padding, upper_right_column), dim=1) / 9.0
            rhs = rhs + top_boundary + left_boundary + upper_left_boundary + upper_right_boundary
            interior = torch.linalg.solve_triangular(triangular, rhs.reshape(-1, 1), upper=False, unitriangular=True).reshape(m, m)
            middle = torch.cat((work[1:-1, :1], interior, work[1:-1, -1:]), dim=1)
            work = torch.cat((work[:1], middle, work[-1:]), dim=0)
        return work.reshape(-1)

def make_model():
    return Seidel2D()
