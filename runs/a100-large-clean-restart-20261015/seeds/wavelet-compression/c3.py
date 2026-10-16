"""Export-friendly three-level 2D Haar wavelet compression candidate."""
import math
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_LEVELS = 3
_MINI_SIZE = 1024

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the literal deterministic C image initialization for the MINI profile."""
    if fixture is not None:
        raise ValueError('wavelet-compression does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    indices = torch.arange(_MINI_SIZE, device=device, dtype=torch.int64)
    row, column = torch.meshgrid(indices, indices, indexing='ij')
    row64 = row.to(torch.float64)
    column64 = column.to(torch.float64)
    checker = ((torch.div(row, 8, rounding_mode='floor') + torch.div(column, 8, rounding_mode='floor')) % 2).to(torch.float64)
    image64 = 64.0 + 18.0 * torch.sin(2.0 * row64 / _MINI_SIZE) + 11.0 * torch.cos(3.0 * column64 / _MINI_SIZE) + 0.2 * checker + 0.04 * row64 * column64 / _MINI_SIZE
    return (image64.to(dtype=dtype),)

class WaveletCompression(torch.nn.Module):
    """Three-level packed 2D Haar analysis, thresholding, and synthesis."""

    def _haar_matrix(self, image):
        scale = image.new_tensor(1.0 / math.sqrt(2.0))
        return torch.stack((torch.stack((scale, scale)), torch.stack((scale, -scale))))

    def _analysis_stage(self, coefficients, width, haar):
        half = width // 2
        active = coefficients[:width, :width]
        tiles = active.reshape(half, 2, half, 2)
        transformed = torch.einsum('ua,paqb,vb->puqv', haar, tiles, haar)
        packed = transformed.permute(1, 0, 3, 2).reshape(width, width)
        result = coefficients.clone()
        result[:width, :width] = packed
        return result

    def _synthesis_stage(self, coefficients, width, haar):
        half = width // 2
        active = coefficients[:width, :width]
        packed = active.reshape(2, half, 2, half).permute(1, 0, 3, 2)
        spatial_tiles = torch.einsum('ua,puqv,vb->paqb', haar, packed, haar)
        reconstructed = spatial_tiles.reshape(width, width)
        result = coefficients.clone()
        result[:width, :width] = reconstructed
        return result

    def forward(self, image):
        if image.ndim != 2 or image.shape[0] != image.shape[1]:
            raise ValueError('image must be a square rank-2 tensor')
        size = image.shape[0]
        if size <= 0 or size % 2 ** _LEVELS != 0:
            raise ValueError('image side length must be divisible by eight')
        if not image.is_floating_point():
            raise ValueError('image must have a floating-point dtype')
        haar = self._haar_matrix(image)
        coefficients = image.clone()
        width = size
        for _ in range(_LEVELS):
            coefficients = self._analysis_stage(coefficients, width, haar)
            width //= 2
        low_pass_width = width
        indices = torch.arange(size, device=image.device)
        row, column = torch.meshgrid(indices, indices, indexing='ij')
        detail_region = (row >= low_pass_width) | (column >= low_pass_width)
        threshold = detail_region & (torch.abs(coefficients) < 0.6)
        coefficients = torch.where(threshold, torch.zeros_like(coefficients), coefficients)
        retained = torch.count_nonzero(coefficients).to(dtype=image.dtype)
        width = low_pass_width * 2
        for _ in range(_LEVELS):
            coefficients = self._synthesis_stage(coefficients, width, haar)
            width *= 2
        error = coefficients - image
        squared_prefix = torch.cumsum(error.reshape(-1) * error.reshape(-1), dim=0)
        mse = (squared_prefix[-1] / error.numel()).reshape(1)
        return (coefficients.reshape(-1), mse, retained.reshape(1))

def make_model():
    return WaveletCompression()
