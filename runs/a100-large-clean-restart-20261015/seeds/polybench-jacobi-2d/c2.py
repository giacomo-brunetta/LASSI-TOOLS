"""Export-friendly PyTorch translation of PolyBench jacobi-2d (MINI)."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_N = 1300
_MINI_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic C-initialized MINI A and B arrays."""
    if fixture is not None:
        raise ValueError('jacobi-2d does not define an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise TypeError('jacobi-2d requires a floating-point dtype')
    indices = torch.arange(_MINI_N, device=device, dtype=dtype)
    i = indices.reshape(_MINI_N, 1)
    j = indices.reshape(1, _MINI_N)
    a = (i * (j + 2) + 2) / _MINI_N
    b = (i * (j + 3) + 3) / _MINI_N
    return (a, b)

class Jacobi2D(nn.Module):
    """Twenty completed Jacobi stages using 3x3 window views."""

    @staticmethod
    def _stage(source, target):
        windows = source.unfold(0, 3, 1).unfold(1, 3, 1)
        stencil_sum = windows[..., 1, 1] + windows[..., 1, 0]
        stencil_sum = stencil_sum + windows[..., 1, 2]
        stencil_sum = stencil_sum + windows[..., 2, 1]
        stencil_sum = stencil_sum + windows[..., 0, 1]
        interior = torch.tensor(0.2, dtype=source.dtype, device=source.device) * stencil_sum
        interior_rows = torch.cat((target[1:-1, :1], interior, target[1:-1, -1:]), dim=1)
        return torch.cat((target[:1, :], interior_rows, target[-1:, :]), dim=0)

    def forward(self, A_in, B_in):
        if not isinstance(A_in, torch.Tensor) or not isinstance(B_in, torch.Tensor):
            raise TypeError('A_in and B_in must be torch.Tensor instances')
        if A_in.ndim != 2 or B_in.ndim != 2:
            raise ValueError('A_in and B_in must be rank-2 tensors')
        if A_in.shape != B_in.shape:
            raise ValueError('A_in and B_in must have identical shapes')
        if A_in.shape[0] != A_in.shape[1]:
            raise ValueError('A_in and B_in must be square')
        if A_in.shape[0] < 3:
            raise ValueError('A_in and B_in must have side length at least 3')
        if A_in.dtype != B_in.dtype or A_in.device != B_in.device:
            raise ValueError('A_in and B_in must share dtype and device')
        if not A_in.is_floating_point():
            raise TypeError('jacobi-2d requires floating-point inputs')
        a = A_in.clone()
        b = B_in.clone()
        for _ in range(_MINI_TSTEPS):
            b = self._stage(a, b)
            a = self._stage(b, a)
        return a.reshape(-1)

def make_model():
    return Jacobi2D()
