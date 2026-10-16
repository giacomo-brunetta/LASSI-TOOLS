"""Stage-axis RK4 translation of the MINI Lorenz integration reference."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_SIZE = 1024
_MINI_STEPS = 200
_DT = 0.001

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the reference MINI initial state; fixtures are intentionally unsupported."""
    if fixture is not None:
        raise ValueError('lorenz-rk4 uses deterministic generated inputs, not fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    indices = torch.arange(_MINI_SIZE, device=device, dtype=dtype).unsqueeze(1)
    components = torch.arange(3, device=device, dtype=dtype).unsqueeze(0)
    state = 1.0 + 0.01 * indices + 0.1 * components
    return (state,)

class LorenzRK4(nn.Module):
    """Twenty RK4 steps with first-class stage-axis derivatives."""
    steps = _MINI_STEPS
    dt = _DT

    def __init__(self):
        super().__init__()
        self.register_buffer('rk4_weights', torch.tensor([1, 2, 2, 1]))

    @staticmethod
    def rhs(y):
        y0, y1, y2 = y.unbind(dim=-1)
        return torch.stack((10 * (y1 - y0), y0 * (28 - y2) - y1, y0 * y1 - 8.0 / 3.0 * y2), dim=-1)

    def forward(self, state):
        if state.ndim != 2 or state.shape[1] != 3:
            raise ValueError('state must have shape [N, 3]')
        state = state.clone()
        dt = state.new_tensor(self.dt)
        weights = self.rk4_weights.to(device=state.device, dtype=state.dtype)
        for _ in range(self.steps):
            k1 = self.rhs(state)
            k2 = self.rhs(state + dt * 0.5 * k1)
            k3 = self.rhs(state + dt * 0.5 * k2)
            k4 = self.rhs(state + dt * k3)
            stages = torch.stack((k1, k2, k3, k4), dim=0)
            increment = torch.einsum('s,snd->nd', weights, stages)
            state = state + dt * increment / 6.0
        return state.contiguous().reshape(-1)

def make_model():
    return LorenzRK4()
