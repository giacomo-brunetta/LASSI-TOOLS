"""Functional, export-friendly PolyBench FDTD-2D translation."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

class FDTD2D(torch.nn.Module):

    def forward(self, ex_in: torch.Tensor, ey_in: torch.Tensor, hz_in: torch.Tensor, fict_in: torch.Tensor):
        ex = ex_in.clone()
        ey = ey_in.clone()
        hz = hz_in.clone()
        fict = fict_in.clone()
        if ex.ndim != 2 or ey.ndim != 2 or hz.ndim != 2:
            raise ValueError('ex, ey, and hz must be rank-2 tensors')
        if ex.shape != ey.shape or ex.shape != hz.shape:
            raise ValueError('ex, ey, and hz must have equal shapes')
        if fict.ndim != 1:
            raise ValueError('fict must be a rank-1 tensor')
        nx, ny = ex.shape
        tmax = fict.numel()
        if tmax <= 0:
            raise ValueError('fict must contain at least one timestep')
        if nx < 2 or ny < 2:
            raise ValueError('field dimensions must both be at least 2')
        for t in range(tmax):
            ey = torch.cat((fict[t].reshape(1, 1).expand(1, ny), ey[1:, :]), dim=0)
            updated_ey = ey[1:, :] - 0.5 * (hz[1:, :] - hz[:-1, :])
            ey = torch.cat((ey[:1, :], updated_ey), dim=0)
            updated_ex = ex[:, 1:] - 0.5 * (hz[:, 1:] - hz[:, :-1])
            ex = torch.cat((ex[:, :1], updated_ex), dim=1)
            hz_inner = hz[:-1, :-1] - 0.7 * (ex[:-1, 1:] - ex[:-1, :-1] + (ey[1:, :-1] - ey[:-1, :-1]))
            hz_top = torch.cat((hz_inner, hz[:-1, -1:]), dim=1)
            hz = torch.cat((hz_top, hz[-1:, :]), dim=0)
        return ex.reshape(-1)

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset: {dataset!r}; only 'mini' is supported")
    tmax, nx, ny = (500, 1000, 1200)
    i = torch.arange(nx, device=device, dtype=torch.int64).reshape(nx, 1)
    j = torch.arange(ny, device=device, dtype=torch.int64).reshape(1, ny)
    i_float = i.to(dtype=dtype)
    j_float = j.to(dtype=dtype)
    fict = torch.arange(tmax, device=device, dtype=torch.int64).to(dtype=dtype)
    ex = i_float * (j_float + 1) / nx
    ey = i_float * (j_float + 2) / ny
    hz = i_float * (j_float + 3) / nx
    return (ex, ey, hz, fict)

def make_model():
    return FDTD2D()
