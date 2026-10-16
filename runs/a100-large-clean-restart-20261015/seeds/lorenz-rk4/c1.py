"""Export-friendly PyTorch translation of the MINI Lorenz RK4 reference kernel."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

class LorenzRK4(torch.nn.Module):
    """Advance an independent batch of Lorenz systems for 20 RK4 steps."""

    def rhs(self, y: torch.Tensor) -> torch.Tensor:
        x = y[..., 0]
        yy = y[..., 1]
        z = y[..., 2]
        return torch.stack((10.0 * (yy - x), x * (28.0 - z) - yy, x * yy - 8.0 / 3.0 * z), dim=-1)

    def forward(self, state: torch.Tensor) -> torch.Tensor:
        state = state.clone()
        dt = state.new_tensor(0.001)
        for _ in range(200):
            k1 = self.rhs(state)
            k2 = self.rhs(state + dt * 0.5 * k1)
            k3 = self.rhs(state + dt * 0.5 * k2)
            k4 = self.rhs(state + dt * k3)
            state = state + dt * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        return state.contiguous().reshape(-1)

def build_inputs(device: str='cpu', dtype: torch.dtype=torch.float64, fixture=None, dataset: str='default') -> tuple[torch.Tensor]:
    """Construct the deterministic MINI reference state without final-output precomputation."""
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset: {dataset!r}; supported datasets are 'default' and 'mini'")
    i = torch.arange(1024, device=device, dtype=dtype).unsqueeze(1)
    d = torch.arange(3, device=device, dtype=dtype).unsqueeze(0)
    state = 1.0 + 0.01 * i + 0.1 * d
    return (state,)

def make_model() -> torch.nn.Module:
    return LorenzRK4()
