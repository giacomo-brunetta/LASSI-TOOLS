"""Export-friendly PyTorch translation of the MINI Lorenz RK4 kernel."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

class LorenzRK4(torch.nn.Module):
    """Twenty whole-batch RK4 steps for independently evolving Lorenz states."""

    def __init__(self) -> None:
        super().__init__()
        coefficients = torch.tensor([[10.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, -1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -(8.0 / 3.0)]], dtype=torch.float64)
        self.register_buffer('coefficients', coefficients)

    def _rhs(self, y: torch.Tensor) -> torch.Tensor:
        x, yy, z = y.unbind(dim=-1)
        features = torch.stack((yy - x, x * (28.0 - z), yy, x * yy, z), dim=-1)
        coefficients = self.coefficients.to(device=y.device, dtype=y.dtype)
        return torch.einsum('...f,fo->...o', features, coefficients)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        state = state.clone()
        dt = 0.001
        for _ in range(200):
            k1 = self._rhs(state)
            k2 = self._rhs(state + 0.5 * dt * k1)
            k3 = self._rhs(state + 0.5 * dt * k2)
            k4 = self._rhs(state + dt * k3)
            state = state + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        return state.contiguous().reshape(-1)

def build_inputs(device: str='cpu', dtype: torch.dtype=torch.float64, fixture=None, dataset: str='default') -> tuple[torch.Tensor]:
    """Construct the reference MINI input state without precomputing its result."""
    if fixture is not None:
        raise ValueError('lorenz-rk4 has no input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset}')
    systems = torch.arange(1024, device=device, dtype=dtype)
    dimensions = torch.arange(3, device=device, dtype=dtype)
    state = (1.0 + 0.01 * systems).unsqueeze(-1) + 0.1 * dimensions
    return (state,)

def make_model() -> torch.nn.Module:
    return LorenzRK4()
