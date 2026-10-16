"""Export-friendly PyTorch implementation of the softened N-body kernel."""
import math
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

class SoftenedNBody(torch.nn.Module):
    """Compute directed softened gravitational accelerations for arbitrary N."""

    def forward(self, position: torch.Tensor, mass: torch.Tensor) -> torch.Tensor:
        delta = position.unsqueeze(0) - position.unsqueeze(1)
        squared = 0.01 + (delta * delta).sum(dim=-1)
        particle_indices = torch.arange(position.shape[0], device=position.device)
        diagonal = particle_indices.unsqueeze(0) == particle_indices.unsqueeze(1)
        weight = mass.unsqueeze(0) / (squared * torch.sqrt(squared))
        weight = torch.where(diagonal, torch.zeros_like(weight), weight)
        acceleration = (weight.unsqueeze(-1) * delta).sum(dim=1)
        return acceleration.reshape(-1)

def build_inputs(device: str='cpu', dtype: torch.dtype=torch.float64, fixture=None, dataset: str='default') -> tuple[torch.Tensor, torch.Tensor]:
    """Create the deterministic default/MINI_DATASET inputs from the C source."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset: {dataset!r}; expected 'default' or 'mini'")
    n = 2048
    indices = torch.arange(n, device=device, dtype=torch.int64)
    dimensions = torch.arange(3, device=device, dtype=torch.int64)
    mass64 = 1.0 + (indices % 7).to(torch.float64) * 0.125
    phase = (indices.unsqueeze(1) + 1) * (dimensions.unsqueeze(0) + 1)
    position64 = torch.sin(phase.to(torch.float64) * 0.37) + 0.01 * indices.unsqueeze(1).to(torch.float64)
    return (position64.to(dtype=dtype), mass64.to(dtype=dtype))

def make_model() -> torch.nn.Module:
    return SoftenedNBody()
