"""Export-friendly PyTorch translation of the low-rank-compression MINI kernel."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_SIZE = 1024
_COMPONENTS = 4
_POWER_STEPS = 8

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI image fixture from the C initialization."""
    if fixture is not None:
        raise ValueError('fixtures are not supported for low-rank-compression')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI dataset is supported')
    coordinates = torch.arange(1, _MINI_SIZE + 1, device=device, dtype=dtype)
    row = coordinates.reshape(_MINI_SIZE, 1)
    column = coordinates.reshape(1, _MINI_SIZE)
    image = 2.0 * torch.sin(0.07 * row) * torch.cos(0.11 * column) + 1.3 * torch.cos(0.03 * row) * torch.sin(0.05 * column) + 0.8 * row * column / (_MINI_SIZE * _MINI_SIZE) + 0.12 * torch.sin(0.013 * row * column)
    return (image,)

class LowRankCompression(torch.nn.Module):
    """Four fixed power iterations with rank-one deflation."""

    def forward(self, image):
        if image.ndim != 2 or image.shape[0] != image.shape[1]:
            raise ValueError('image must be a square rank-2 tensor')
        n = image.shape[-1]
        residual = image.clone()
        approximation = torch.zeros_like(image)
        indices = torch.arange(n, device=image.device, dtype=image.dtype)
        for component in range(_COMPONENTS):
            right = 1.0 + 0.01 * (indices + component)
            right = right / torch.sqrt(torch.sum(right * right))
            for _ in range(_POWER_STEPS):
                left = torch.mv(residual, right)
                left = left / torch.sqrt(torch.sum(left * left))
                right = torch.mv(residual.transpose(0, 1), left)
                right = right / torch.sqrt(torch.sum(right * right))
            singular_value = torch.dot(left, torch.mv(residual, right))
            contribution = torch.outer(left, right) * singular_value
            approximation = approximation + contribution
            residual = residual - contribution
        squared_error = torch.sum(residual * residual)
        signal_energy = torch.sum(image * image)
        return (approximation.reshape(-1), (squared_error / signal_energy).reshape(1), image.new_tensor([4.0]))

def make_model():
    return LowRankCompression()
