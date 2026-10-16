"""Source-order Modified Gram--Schmidt for PolyBench gramschmidt (MINI)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_M = 1000
_MINI_N = 1200

def _c_order_sum(values):
    """Reduce the leading M axis in ascending-index accumulation order."""
    return torch.cumsum(values, dim=0)[-1]

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the reference MINI_DATASET inputs without precomputing outputs."""
    if fixture is not None:
        raise ValueError('gramschmidt does not define an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is available')
    i = torch.arange(_MINI_M, device=device, dtype=torch.int64).reshape(_MINI_M, 1)
    j = torch.arange(_MINI_N, device=device, dtype=torch.int64).reshape(1, _MINI_N)
    a = (i * j % _MINI_M).to(dtype) / _MINI_M * 100 + 10
    r0 = torch.zeros((_MINI_N, _MINI_N), device=device, dtype=dtype)
    q0 = torch.zeros((_MINI_M, _MINI_N), device=device, dtype=dtype)
    return (a, r0, q0)

class GramSchmidtPanelMGS(torch.nn.Module):
    """MGS using one-column panels to preserve the C update association."""
    panel_width = 1

    def forward(self, a, r0, q0):
        if a.ndim != 2 or r0.ndim != 2 or q0.ndim != 2:
            raise ValueError('A, R0, and Q0 must be rank-2 tensors')
        m, n = a.shape
        if m < 1:
            raise ValueError('M must be positive')
        if r0.shape != (n, n) or q0.shape != (m, n):
            raise ValueError('expected A=(M,N), R0=(N,N), and Q0=(M,N)')
        if a.device != r0.device or a.device != q0.device:
            raise ValueError('all inputs must be on the same device')
        if a.dtype != r0.dtype or a.dtype != q0.dtype:
            raise ValueError('all inputs must have the same dtype')
        work = a.clone()
        r = r0.clone()
        q = q0.clone()
        for p in range(0, n, self.panel_width):
            end = min(p + self.panel_width, n)
            width = end - p
            panel_work = work[:, p:end]
            q_columns = []
            for local_col in range(width):
                column = panel_work[:, local_col]
                diagonal = torch.sqrt(_c_order_sum(column * column))
                q_column = column / diagonal
                q_columns.append(q_column.unsqueeze(1))
                if local_col + 1 < width:
                    remaining = panel_work[:, local_col + 1:]
                    coefficients = _c_order_sum(q_column.unsqueeze(1) * remaining)
                    updated_remaining = remaining - q_column.unsqueeze(1) * coefficients.unsqueeze(0)
                    panel_work = torch.cat((panel_work[:, :local_col + 1], updated_remaining), dim=1)
                    r[p + local_col, p + local_col + 1:end] = coefficients
                r[p + local_col, p + local_col] = diagonal
            q_panel = torch.cat(q_columns, dim=1)
            q = torch.cat((q[:, :p], q_panel, q[:, end:]), dim=1)
            if end < n:
                trailing_before_panel = work[:, end:]
                r_panel_trailing = _c_order_sum(q_panel.unsqueeze(2) * trailing_before_panel.unsqueeze(1))
                trailing_new = trailing_before_panel - q_panel @ r_panel_trailing
                r[p:end, end:] = r_panel_trailing
                work = torch.cat((work[:, :p], panel_work, trailing_new), dim=1)
            else:
                work = torch.cat((work[:, :p], panel_work), dim=1)
        return (r.reshape(-1), q.reshape(-1))

def make_model():
    return GramSchmidtPanelMGS()
