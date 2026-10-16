"""Panelized functional PyTorch translation of PolyBench FDTD-2D."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_TMAX = 500
_MINI_NX = 1000
_MINI_NY = 1200
_PANEL_ROWS = 8

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError('fdtd-2d supports only the MINI_DATASET profile')
    if fixture is not None:
        raise ValueError('fdtd-2d does not use input fixtures')
    rows = torch.arange(_MINI_NX, device=device, dtype=dtype).reshape(-1, 1)
    cols = torch.arange(_MINI_NY, device=device, dtype=dtype).reshape(1, -1)
    ex = rows * (cols + 1.0) / float(_MINI_NX)
    ey = rows * (cols + 2.0) / float(_MINI_NY)
    hz = rows * (cols + 3.0) / float(_MINI_NX)
    fict = torch.arange(_MINI_TMAX, device=device, dtype=dtype)
    return (ex, ey, hz, fict)

class FDTD2D(torch.nn.Module):
    """FDTD-2D with stage-local spatial panels and functional assembly."""

    def forward(self, ex, ey, hz, fict):
        if ex.ndim != 2 or ey.ndim != 2 or hz.ndim != 2:
            raise ValueError('ex, ey, and hz must be rank-2 tensors')
        if fict.ndim != 1 or fict.numel() == 0:
            raise ValueError('fict must be a nonempty rank-1 tensor')
        if ex.shape != ey.shape or ex.shape != hz.shape:
            raise ValueError('ex, ey, and hz must have matching shapes')
        nx, ny = ex.shape
        if nx < 2 or ny < 2:
            raise ValueError('fdtd-2d requires nx >= 2 and ny >= 2')
        ex = ex.clone()
        ey = ey.clone()
        hz = hz.clone()
        fict = fict.clone()
        for t in range(fict.numel()):
            ey_start = ey
            ey_panels = []
            for row_start in range(1, nx, _PANEL_ROWS):
                row_end = min(row_start + _PANEL_ROWS, nx)
                ey_panels.append(ey_start[row_start:row_end, :] - 0.5 * (hz[row_start:row_end, :] - hz[row_start - 1:row_end - 1, :]))
            ey = torch.cat((fict[t].expand(1, ny), torch.cat(ey_panels, dim=0)), dim=0)
            ex_start = ex
            ex_panels = []
            for row_start in range(0, nx, _PANEL_ROWS):
                row_end = min(row_start + _PANEL_ROWS, nx)
                ex_panels.append(ex_start[row_start:row_end, 1:] - 0.5 * (hz[row_start:row_end, 1:] - hz[row_start:row_end, :-1]))
            ex = torch.cat((ex_start[:, :1], torch.cat(ex_panels, dim=0)), dim=1)
            hz_start = hz
            hz_panels = []
            for row_start in range(0, nx - 1, _PANEL_ROWS):
                row_end = min(row_start + _PANEL_ROWS, nx - 1)
                curl = ex[row_start:row_end, 1:] - ex[row_start:row_end, :-1] + ey[row_start + 1:row_end + 1, :-1] - ey[row_start:row_end, :-1]
                hz_panels.append(hz_start[row_start:row_end, :-1] - 0.7 * curl)
            hz_interior_rows = torch.cat(hz_panels, dim=0)
            hz = torch.cat((torch.cat((hz_interior_rows, hz_start[:-1, -1:]), dim=1), hz_start[-1:, :]), dim=0)
        return ex.reshape(-1)

def make_model():
    return FDTD2D()
