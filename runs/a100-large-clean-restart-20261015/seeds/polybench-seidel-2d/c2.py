"""Blocked triangular-solve translation of PolyBench seidel-2d (MINI)."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_N = 2000
_TSTEPS = 500
_BLOCK_ROWS = 8

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Return the deterministic MINI_DATASET input array from the C initializer."""
    if fixture is not None:
        raise ValueError('polybench-seidel-2d does not use an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    indices = torch.arange(_MINI_N, device=device, dtype=torch.int64)
    rows = indices[:, None]
    cols = indices[None, :]
    array = rows * (cols + 2) + 2
    return (array.to(dtype=dtype) / _MINI_N,)

class Seidel2D(torch.nn.Module):
    """Twenty in-place C sweeps represented by fixed-height triangular solves."""

    def forward(self, A):
        if A.ndim != 2 or A.shape[0] != A.shape[1]:
            raise ValueError('A must be a square rank-2 tensor')
        if A.shape[0] < 3:
            raise ValueError('A must have a nonempty interior')
        work = A.clone()
        n = work.shape[0]
        m = n - 2
        one_ninth = work.new_tensor(1.0 / 9.0)
        for _ in range(_TSTEPS):
            completed = [work[:1]]
            for panel_start in range(0, m, _BLOCK_ROWS):
                b = min(_BLOCK_ROWS, m - panel_start)
                source_start = panel_start + 1
                source_stop = source_start + b
                old_panel = work[source_start:source_stop]
                rhs = (old_panel[:, 1:-1] + old_panel[:, 2:] + work[source_start + 1:source_stop + 1, :-2] + work[source_start + 1:source_stop + 1, 1:-1] + work[source_start + 1:source_stop + 1, 2:]) * one_ninth
                upper_left_edge = torch.cat((torch.zeros_like(old_panel[:1, :1]), old_panel[:-1, :1]), dim=0)
                upper_right_edge = torch.cat((torch.zeros_like(old_panel[:1, -1:]), old_panel[:-1, -1:]), dim=0)
                rhs = torch.cat((rhs[:, :1] + (old_panel[:, :1] + upper_left_edge) * one_ninth, rhs[:, 1:-1], rhs[:, -1:] + upper_right_edge * one_ninth), dim=1)
                top = completed[-1][-1:, :-2] + completed[-1][-1:, 1:-1] + completed[-1][-1:, 2:]
                rhs = torch.cat((rhs[:1] + top * one_ninth, rhs[1:]), dim=0)
                positions = torch.arange(b * m, device=work.device, dtype=torch.int64)
                target_row = positions[:, None] // m
                target_col = positions[:, None] % m
                source_row = positions[None, :] // m
                source_col = positions[None, :] % m
                same_row_left = (source_row == target_row) & (source_col + 1 == target_col)
                previous_row = (source_row + 1 == target_row) & (source_col >= target_col - 1) & (source_col <= target_col + 1)
                dependency = same_row_left | previous_row
                zeros = torch.zeros((b * m, b * m), dtype=work.dtype, device=work.device)
                coefficients = torch.where(dependency, -one_ninth, zeros)
                triangular = torch.eye(b * m, dtype=work.dtype, device=work.device) + coefficients
                solved = torch.linalg.solve_triangular(triangular, rhs.reshape(-1, 1), upper=False, unitriangular=True).squeeze(-1).reshape(b, m)
                completed.append(torch.cat((old_panel[:, :1], solved, old_panel[:, -1:]), dim=1))
            work = torch.cat(tuple(completed) + (work[-1:],), dim=0)
        return work.reshape(-1)

def make_model():
    return Seidel2D()
