"""Export-friendly PyTorch translation of the softened N-body reference kernel."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_SIZE = 2048
_SOURCE_PANEL_WIDTH = 16

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic position and mass arrays from the C MINI profile."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    if fixture is not None:
        raise ValueError('softened-nbody does not use input fixtures')
    indices = torch.arange(_MINI_SIZE, device=device, dtype=dtype)
    dimensions = torch.arange(1, 4, device=device, dtype=dtype)
    position = torch.sin((indices.unsqueeze(1) + 1.0) * dimensions * 0.37)
    position = position + 0.01 * indices.unsqueeze(1)
    mass = 1.0 + torch.remainder(indices, 7.0) * 0.125
    return (position, mass)

class SoftenedNBody(torch.nn.Module):
    """Compute gravitational acceleration using fixed-width source panels."""

    def forward(self, position, mass):
        particle_count = position.shape[0]
        target_indices = torch.arange(particle_count, device=position.device).unsqueeze(1)
        acceleration = torch.zeros_like(position)
        for start in range(0, particle_count, _SOURCE_PANEL_WIDTH):
            end = min(start + _SOURCE_PANEL_WIDTH, particle_count)
            source_position = position[start:end]
            source_mass = mass[start:end]
            source_indices = torch.arange(start, end, device=position.device).unsqueeze(0)
            delta = source_position.unsqueeze(0) - position.unsqueeze(1)
            squared = 0.01 + (delta * delta).sum(dim=-1)
            weight = source_mass.unsqueeze(0) / (squared * torch.sqrt(squared))
            weight = torch.where(target_indices == source_indices, torch.zeros_like(weight), weight)
            panel_acceleration = (weight.unsqueeze(-1) * delta).sum(dim=1)
            acceleration = acceleration + panel_acceleration
        return acceleration.reshape(-1)

def make_model():
    return SoftenedNBody()
