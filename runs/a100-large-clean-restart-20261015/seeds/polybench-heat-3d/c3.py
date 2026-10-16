"""Export-friendly PolyBench heat-3d candidate using unfolded neighborhoods."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_TSTEPS = 500
_MINI_N = 120

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the MINI_DATASET's two independent C-initialized arrays."""
    if dataset not in ('default', 'large'):
        raise ValueError('heat-3d supports only the MINI_DATASET profile')
    if fixture is not None:
        raise ValueError('heat-3d does not use input fixtures')
    n = _MINI_N
    indices = torch.arange(n, device=device, dtype=torch.int64)
    i = indices[:, None, None]
    j = indices[None, :, None]
    k = indices[None, None, :]
    values = (i + j + (n - k)).to(dtype) * 10 / n
    return (values.clone(), values.clone())

class Heat3D(nn.Module):

    def __init__(self):
        super().__init__()
        coefficients = torch.zeros(3, 3, 3, dtype=torch.float64)
        coefficients[0, 1, 1] = 0.125
        coefficients[2, 1, 1] = 0.125
        coefficients[1, 0, 1] = 0.125
        coefficients[1, 2, 1] = 0.125
        coefficients[1, 1, 0] = 0.125
        coefficients[1, 1, 2] = 0.125
        coefficients[1, 1, 1] = 0.25
        self.register_buffer('coefficients', coefficients.reshape(27))

    def _stage(self, source, destination):
        neighborhoods = source.unfold(0, 3, 1).unfold(1, 3, 1).unfold(2, 3, 1)
        neighborhoods = neighborhoods.reshape(source.shape[0] - 2, source.shape[1] - 2, source.shape[2] - 2, 27)
        coefficients = self.coefficients.to(device=source.device, dtype=source.dtype)
        interior = (neighborhoods * coefficients).sum(dim=-1)
        inner_planes = torch.cat((destination[:1, 1:-1, 1:-1], interior, destination[-1:, 1:-1, 1:-1]), dim=0)
        inner_columns = torch.cat((destination[:, :1, 1:-1], inner_planes, destination[:, -1:, 1:-1]), dim=1)
        return torch.cat((destination[:, :, :1], inner_columns, destination[:, :, -1:]), dim=2)

    def forward(self, A, B):
        if A.ndim != 3 or B.ndim != 3:
            raise ValueError('A and B must be rank-3 tensors')
        if A.shape != B.shape or A.shape[0] != A.shape[1] or A.shape[1] != A.shape[2]:
            raise ValueError('A and B must have equal cubic shapes')
        if A.shape[0] < 3:
            raise ValueError('the cubic dimension must be at least 3')
        A_work = A.clone()
        B_work = B.clone()
        for _ in range(_TSTEPS):
            B_work = self._stage(A_work, B_work)
            A_work = self._stage(B_work, A_work)
        return A_work.reshape(-1)

def make_model():
    return Heat3D()
