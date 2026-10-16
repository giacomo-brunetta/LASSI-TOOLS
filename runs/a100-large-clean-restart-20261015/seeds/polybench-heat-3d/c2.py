"""Export-friendly PyTorch translation of PolyBench heat-3d (MINI profile)."""
import torch
import torch.nn.functional as F
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype (backend conv3d accumulation)', 'output': 'input dtype'}
_MINI_N = 120
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the two separately allocated C-initialized MINI input arrays."""
    if fixture is not None:
        raise ValueError('heat-3d does not use an input fixture')
    if dataset not in {'default', 'large'}:
        raise ValueError(f"unsupported dataset: {dataset!r}; expected 'default' or 'mini'")
    n = _MINI_N
    i = torch.arange(n, device=device).reshape(n, 1, 1)
    j = torch.arange(n, device=device).reshape(1, n, 1)
    k = torch.arange(n, device=device).reshape(1, 1, n)
    values = (i + j + (n - k)).to(dtype) * 10 / n
    return (values.clone(), values.clone())

class Heat3D(torch.nn.Module):
    """Twenty two-phase Jacobi stencil steps using padding-free Conv3d."""

    def _step(self, source):
        x = source.unsqueeze(0).unsqueeze(0)
        weight = x.new_tensor([[[[[0.0, 0.125, 0.0], [0.125, 0.25, 0.125], [0.0, 0.125, 0.0]], [[0.125, 0.25, 0.125], [0.25, 0.25, 0.25], [0.125, 0.25, 0.125]], [[0.0, 0.125, 0.0], [0.125, 0.25, 0.125], [0.0, 0.125, 0.0]]]]])
        weight.zero_()
        weight[0, 0, 0, 1, 1] = 0.125
        weight[0, 0, 2, 1, 1] = 0.125
        weight[0, 0, 1, 0, 1] = 0.125
        weight[0, 0, 1, 2, 1] = 0.125
        weight[0, 0, 1, 1, 0] = 0.125
        weight[0, 0, 1, 1, 2] = 0.125
        weight[0, 0, 1, 1, 1] = 0.25
        interior = F.conv3d(x, weight, padding=0).squeeze(0).squeeze(0)
        middle_planes = torch.cat((source[1:-1, :1, :], torch.cat((source[1:-1, 1:-1, :1], interior, source[1:-1, 1:-1, -1:]), dim=2), source[1:-1, -1:, :]), dim=1)
        return torch.cat((source[:1, :, :], middle_planes, source[-1:, :, :]), dim=0)

    def forward(self, A, B):
        if A.ndim != 3 or B.ndim != 3:
            raise ValueError('A and B must be rank-3 tensors')
        if A.shape != B.shape or A.shape[0] != A.shape[1] or A.shape[1] != A.shape[2]:
            raise ValueError('A and B must have equal cubic shapes')
        if A.shape[0] < 3:
            raise ValueError('heat-3d requires n >= 3')
        if A.device != B.device or A.dtype != B.dtype:
            raise ValueError('A and B must have the same device and dtype')
        A_state = A.clone()
        B_state = B.clone()
        for _ in range(_TSTEPS):
            B_state = self._step(A_state)
            A_state = self._step(B_state)
        return A_state.reshape(-1)

def make_model():
    return Heat3D()
