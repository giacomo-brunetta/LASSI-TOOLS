"""Blocked, lower-triangular Cholesky translation of PolyBench cholesky."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_N = 2000

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the MINI PolyBench input with the C initializer's accumulation order."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError('polybench-cholesky provides only the MINI dataset (n=40)')
    n = _MINI_N
    indices = torch.arange(n, device=device)
    row = indices[:, None]
    col = indices[None, :]
    lower = col <= row
    base = 1 - col.to(dtype) / n
    a = torch.where(lower, base, torch.zeros((), device=device, dtype=dtype))
    diagonal = torch.eye(n, device=device, dtype=torch.bool)
    a = torch.where(diagonal, torch.ones((), device=device, dtype=dtype), a)
    psd = torch.zeros_like(a)
    for t in range(n):
        column = a[:, t:t + 1]
        psd = psd + column @ column.transpose(0, 1)
    return (psd,)

class BlockedCholesky(torch.nn.Module):
    """Right-looking Cholesky with bounded-width sequential panel work."""
    block_size = 8

    @staticmethod
    def _factor_panel(panel):
        """Factor one at-most-eight-wide symmetric diagonal panel."""
        width = panel.shape[0]
        lower = torch.zeros_like(panel)
        for pivot_index in range(width):
            prefix = lower[pivot_index, :pivot_index]
            pivot = torch.sqrt(panel[pivot_index, pivot_index] - prefix @ prefix)
            lower[pivot_index, pivot_index] = pivot
            if pivot_index + 1 < width:
                rows = lower[pivot_index + 1:, :pivot_index]
                numerator = panel[pivot_index + 1:, pivot_index] - rows @ prefix
                lower[pivot_index + 1:, pivot_index] = numerator / pivot
        return lower

    @staticmethod
    def _solve_below_panel(rhs, lower_panel):
        """Solve X L.T = rhs by bounded-width vectorized forward substitution."""
        width = lower_panel.shape[0]
        result = torch.zeros_like(rhs)
        for column_index in range(width):
            prefix = lower_panel[column_index, :column_index]
            result[:, column_index] = (rhs[:, column_index] - result[:, :column_index] @ prefix) / lower_panel[column_index, column_index]
        return result

    def forward(self, a_in):
        work = a_in.clone()
        n = work.shape[0]
        lower = torch.zeros_like(work)
        for panel_start in range(0, n, self.block_size):
            panel_end = min(panel_start + self.block_size, n)
            panel = work[panel_start:panel_end, panel_start:panel_end]
            lower_panel = self._factor_panel(panel)
            lower[panel_start:panel_end, panel_start:panel_end] = lower_panel
            if panel_end < n:
                below_rhs = work[panel_end:, panel_start:panel_end]
                below = self._solve_below_panel(below_rhs, lower_panel)
                lower[panel_end:, panel_start:panel_end] = below
                work[panel_end:, panel_end:] = work[panel_end:, panel_end:] - below @ below.transpose(0, 1)
        return lower[torch.tril(torch.ones_like(lower, dtype=torch.bool))]

def make_model():
    return BlockedCholesky()
