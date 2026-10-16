"""Export-friendly three-level 2D Haar wavelet compression candidate."""
import math
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_LEVELS = 3
_THRESHOLD = 0.6

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic source image using the reference C expression."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    size = 1024
    rows = torch.arange(size, dtype=torch.int64, device='cpu').reshape(size, 1)
    columns = torch.arange(size, dtype=torch.int64, device='cpu').reshape(1, size)
    row_values = rows.to(torch.float64)
    column_values = columns.to(torch.float64)
    checkerboard = ((rows // 8 + columns // 8) % 2).to(torch.float64)
    image = 64.0 + 18.0 * torch.sin(2.0 * row_values / size) + 11.0 * torch.cos(3.0 * column_values / size) + 0.2 * checkerboard + 0.04 * row_values * column_values / size
    return (image.to(device=device, dtype=dtype),)

class WaveletCompression(torch.nn.Module):
    """Three analysis and synthesis passes using batched two-vector matmuls."""

    @staticmethod
    def _haar(dtype, device):
        scale = 1.0 / math.sqrt(2.0)
        return torch.tensor(((scale, scale), (scale, -scale)), dtype=dtype, device=device)

    @staticmethod
    def _replace_active(array, active, width):
        top = torch.cat((active, array[:width, width:]), dim=1)
        return torch.cat((top, array[width:, :]), dim=0)

    def forward(self, image):
        if image.ndim != 2 or image.shape[0] != image.shape[1]:
            raise ValueError('image must be a square rank-2 tensor')
        size = image.shape[-1]
        if size % 2 ** _LEVELS != 0:
            raise ValueError('image width must be divisible by 8')
        haar_transpose = self._haar(image.dtype, image.device).transpose(-1, -2)
        coefficients = image.clone()
        width = size
        for _ in range(_LEVELS):
            half = width // 2
            active = coefficients[:width, :width]
            horizontal_input = active.reshape(width, half, 2)
            horizontal_pairs = torch.matmul(horizontal_input, haar_transpose)
            horizontal = torch.cat((horizontal_pairs[..., 0], horizontal_pairs[..., 1]), dim=1)
            vertical_input = horizontal.reshape(half, 2, width).permute(0, 2, 1)
            vertical_pairs = torch.matmul(vertical_input, haar_transpose)
            transformed = torch.cat((vertical_pairs[..., 0], vertical_pairs[..., 1]), dim=0)
            coefficients = self._replace_active(coefficients, transformed, width)
            width = half
        low_pass_width = size // 2 ** _LEVELS
        row_indices = torch.arange(size, device=image.device).reshape(size, 1)
        column_indices = torch.arange(size, device=image.device).reshape(1, size)
        outside_low_pass = (row_indices >= low_pass_width) | (column_indices >= low_pass_width)
        coefficients = torch.where(outside_low_pass & (coefficients.abs() < _THRESHOLD), torch.zeros((), dtype=image.dtype, device=image.device), coefficients)
        retained = (coefficients != 0).sum().to(dtype=image.dtype).reshape(1)
        width = low_pass_width * 2
        for _ in range(_LEVELS):
            half = width // 2
            active = coefficients[:width, :width]
            vertical_coefficients = torch.stack((active[:half, :], active[half:, :]), dim=1)
            vertical_pairs = torch.matmul(vertical_coefficients.permute(0, 2, 1), haar_transpose)
            temporary = vertical_pairs.permute(0, 2, 1).reshape(width, width)
            horizontal_coefficients = torch.stack((temporary[:, :half], temporary[:, half:]), dim=-1)
            horizontal_pairs = torch.matmul(horizontal_coefficients, haar_transpose)
            reconstructed = horizontal_pairs.reshape(width, width)
            coefficients = self._replace_active(coefficients, reconstructed, width)
            width *= 2
        reconstruction = coefficients.reshape(-1)
        squared_errors = (reconstruction - image.reshape(-1)) ** 2
        mse = (torch.cumsum(squared_errors, dim=0)[-1] / (size * size)).reshape(1)
        return (reconstruction, mse, retained)

def make_model():
    return WaveletCompression()
