"""Export-friendly PyTorch translation of low-rank-compression.c (MINI profile)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_COMPONENTS = 4
_POWER_STEPS = 8
_MINI_SIZE = 1024

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI image defined by the C reference initializer."""
    if fixture is not None:
        raise ValueError('low-rank-compression has no alternate input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is available')
    if not torch.empty((), dtype=dtype).is_floating_point():
        raise TypeError('image dtype must be floating point')
    coordinates = torch.arange(1, _MINI_SIZE + 1, device=device, dtype=dtype)
    row = coordinates.reshape(_MINI_SIZE, 1)
    column = coordinates.reshape(1, _MINI_SIZE)
    image = 2.0 * torch.sin(0.07 * row) * torch.cos(0.11 * column) + 1.3 * torch.cos(0.03 * row) * torch.sin(0.05 * column) + 0.8 * row * column / (_MINI_SIZE * _MINI_SIZE) + 0.12 * torch.sin(0.013 * row * column)
    return (image,)

def _ordered_sum(values):
    """Source-order sum represented as a prefix scan over row-major values."""
    return torch.cumsum(values.reshape(-1), dim=0)[-1]

class LowRankCompression(torch.nn.Module):

    def forward(self, image):
        if not isinstance(image, torch.Tensor):
            raise TypeError('image must be a tensor')
        if image.ndim != 2 or image.shape[0] != image.shape[1]:
            raise ValueError('image must be a non-empty square rank-2 tensor')
        if image.shape[0] == 0:
            raise ValueError('image must be non-empty')
        if not image.is_floating_point():
            raise TypeError('image must have a floating-point dtype')
        n = image.shape[0]
        residual = image.clone()
        approximation = torch.zeros_like(image)
        for component in range(_COMPONENTS):
            columns = torch.arange(n, device=image.device, dtype=image.dtype)
            right = 1.0 + 0.01 * (columns + component)
            right = right / torch.sqrt(_ordered_sum(right * right))
            for _ in range(_POWER_STEPS):
                left_terms = residual * right.reshape(1, n)
                left = torch.cumsum(left_terms, dim=1)[:, -1]
                left = left / torch.sqrt(_ordered_sum(left * left))
                right_terms = residual * left.reshape(n, 1)
                right = torch.cumsum(right_terms, dim=0)[-1, :]
                right = right / torch.sqrt(_ordered_sum(right * right))
            singular_terms = left.reshape(n, 1) * residual * right.reshape(1, n)
            singular_value = _ordered_sum(singular_terms)
            contribution = singular_value * left.reshape(n, 1) * right.reshape(1, n)
            approximation = approximation + contribution
            residual = residual - contribution
        squared_error = _ordered_sum(residual * residual)
        signal_energy = _ordered_sum(image * image)
        return (approximation.reshape(-1), (squared_error / signal_energy).reshape(1), image.new_tensor([4.0]))

def make_model():
    return LowRankCompression()
