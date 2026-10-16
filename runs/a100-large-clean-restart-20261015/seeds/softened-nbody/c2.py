"""Export-friendly PyTorch translation of the softened N-body MINI_DATASET kernel."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_SIZE = 2048

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic inputs used by the C MINI_DATASET profile."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise TypeError('softened-nbody inputs require a floating-point dtype')
    indices = torch.arange(_MINI_SIZE, device=device, dtype=dtype)
    dimensions = torch.arange(1, 4, device=device, dtype=dtype)
    position = torch.sin((indices[:, None] + 1.0) * dimensions[None, :] * 0.37)
    position = position + 0.01 * indices[:, None]
    mass = 1.0 + torch.remainder(indices, 7.0) * 0.125
    return (position, mass)

class SoftenedNBody(torch.nn.Module):

    def forward(self, position, mass):
        delta = position.unsqueeze(0) - position.unsqueeze(1)
        squared = (delta * delta).sum(dim=2) + 0.01
        coefficient = mass.unsqueeze(0) / (squared * torch.sqrt(squared))
        diagonal = torch.eye(coefficient.shape[0], device=coefficient.device, dtype=torch.bool)
        coefficient = coefficient.masked_fill(diagonal, 0.0)
        acceleration = coefficient @ position
        acceleration = acceleration - coefficient.sum(dim=1, keepdim=True) * position
        return acceleration.reshape(-1)

def make_model():
    return SoftenedNBody()
