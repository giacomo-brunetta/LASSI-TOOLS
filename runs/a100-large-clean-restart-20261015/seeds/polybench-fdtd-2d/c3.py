"""Export-friendly PyTorch translation of PolyBench FDTD-2D."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    tmax, nx, ny = (500, 1000, 1200)
    i = torch.arange(nx, device=device, dtype=dtype).reshape(nx, 1)
    j = torch.arange(ny, device=device, dtype=dtype).reshape(1, ny)
    fict = torch.arange(tmax, device=device, dtype=dtype)
    ex = i * (j + 1) / nx
    ey = i * (j + 2) / ny
    hz = i * (j + 3) / nx
    return (ex, ey, hz, fict)

class FDTD2D(torch.nn.Module):

    def forward(self, ex, ey, hz, fict):
        ex = ex.clone()
        ey = ey.clone()
        hz = hz.clone()
        fict = fict.clone()
        for t in range(fict.numel()):
            ey = torch.cat((fict[t].expand(1, ey.shape[1]), ey[1:, :]), dim=0)
            d_hz_i = hz[1:, :] - hz[:-1, :]
            ey = torch.cat((ey[:1, :], ey[1:, :] - 0.5 * d_hz_i), dim=0)
            d_hz_j = hz[:, 1:] - hz[:, :-1]
            ex = torch.cat((ex[:, :1], ex[:, 1:] - 0.5 * d_hz_j), dim=1)
            d_ex_j = ex[:-1, 1:] - ex[:-1, :-1]
            d_ey_i = ey[1:, :-1] - ey[:-1, :-1]
            hz_inner = hz[:-1, :-1] - 0.7 * (d_ex_j + d_ey_i)
            hz_without_last_column = torch.cat((hz_inner, hz[:-1, -1:]), dim=1)
            hz = torch.cat((hz_without_last_column, hz[-1:, :]), dim=0)
        return ex.reshape(-1)

def make_model():
    return FDTD2D()
