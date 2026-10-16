import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_N = 120
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    if fixture is not None:
        raise ValueError('heat-3d does not use an input fixture')
    n = _MINI_N
    i = torch.arange(n, device=device, dtype=torch.int64).view(n, 1, 1)
    j = torch.arange(n, device=device, dtype=torch.int64).view(1, n, 1)
    k = torch.arange(n, device=device, dtype=torch.int64).view(1, 1, n)
    initial = (i + j + (n - k)).to(dtype) * 10 / n
    return (initial.clone(), initial.clone())

class Heat3D(nn.Module):

    @staticmethod
    def _next_stage(source, destination):
        center = source[1:-1, 1:-1, 1:-1]
        xp = source[2:, 1:-1, 1:-1]
        xm = source[:-2, 1:-1, 1:-1]
        yp = source[1:-1, 2:, 1:-1]
        ym = source[1:-1, :-2, 1:-1]
        zp = source[1:-1, 1:-1, 2:]
        zm = source[1:-1, 1:-1, :-2]
        new_interior = 0.125 * (xp - 2.0 * center + xm) + 0.125 * (yp - 2.0 * center + ym) + 0.125 * (zp - 2.0 * center + zm) + center
        middle_panel = torch.cat((destination[1:-1, 1:-1, :1], new_interior, destination[1:-1, 1:-1, -1:]), dim=2)
        middle_block = torch.cat((destination[1:-1, :1, :], middle_panel, destination[1:-1, -1:, :]), dim=1)
        return torch.cat((destination[:1, :, :], middle_block, destination[-1:, :, :]), dim=0)

    def forward(self, A, B):
        if A.ndim != 3 or B.ndim != 3:
            raise ValueError('A and B must be rank-3 tensors')
        if A.shape != B.shape:
            raise ValueError('A and B must have identical shapes')
        n = A.shape[0]
        if n < 3 or A.shape[1] != n or A.shape[2] != n:
            raise ValueError('A and B must be cubic tensors with side length at least 3')
        A = A.clone()
        B = B.clone()
        for _ in range(_TSTEPS):
            B = self._next_stage(A, B)
            A = self._next_stage(B, A)
        return A.reshape(-1)

def make_model():
    return Heat3D()
