"""Export-friendly three-level 2D Haar wavelet compression candidate."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype (row-major cumsum for squared error)', 'output': 'input dtype'}
_LEVELS = 3

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET source image without precomputing outputs."""
    if fixture is not None:
        raise ValueError('fixtures are not supported')
    if dataset not in ('default', 'large'):
        raise ValueError('wavelet-compression supports only the mini dataset')
    n = 1024
    row = torch.arange(n, device='cpu', dtype=torch.int64).reshape(n, 1)
    column = torch.arange(n, device='cpu', dtype=torch.int64).reshape(1, n)
    row_f = row.to(torch.float64)
    column_f = column.to(torch.float64)
    image = 64.0 + 18.0 * torch.sin(2.0 * row_f / n) + 11.0 * torch.cos(3.0 * column_f / n) + 0.2 * ((row // 8 + column // 8) % 2).to(torch.float64) + 0.04 * row_f * column_f / n
    return (image.to(device=device, dtype=dtype),)

class WaveletCompression(nn.Module):

    @staticmethod
    def _replace_active(full, active, width):
        """Functionally replace the top-left ``width`` square of ``full``."""
        upper = torch.cat((active, full[:width, width:]), dim=1)
        return torch.cat((upper, full[width:, :]), dim=0)

    def forward(self, image):
        if image.ndim != 2:
            raise ValueError('image must be a rank-2 tensor')
        n, columns = image.shape
        if n != columns or n % 2 ** _LEVELS != 0:
            raise ValueError('image must be square with dimensions divisible by 8')
        coefficients = image.clone()
        width = n
        for _ in range(_LEVELS):
            half = width // 2
            active = coefficients[:width, :width]
            scale = torch.rsqrt(torch.tensor(2.0, dtype=active.dtype, device=active.device))
            even = active[:, 0::2]
            odd = active[:, 1::2]
            horizontal = torch.cat(((even + odd) * scale, (even - odd) * scale), dim=1)
            even = horizontal[0::2, :]
            odd = horizontal[1::2, :]
            transformed = torch.cat(((even + odd) * scale, (even - odd) * scale), dim=0)
            coefficients = self._replace_active(coefficients, transformed, width)
            width = half
        low_pass_width = n // 2 ** _LEVELS
        indices = torch.arange(n, device=coefficients.device)
        rows = indices.reshape(n, 1)
        columns = indices.reshape(1, n)
        outside_low_pass = (rows >= low_pass_width) | (columns >= low_pass_width)
        threshold = outside_low_pass & (torch.abs(coefficients) < 0.6)
        coefficients = torch.where(threshold, torch.zeros_like(coefficients), coefficients)
        retained = torch.count_nonzero(coefficients).to(coefficients.dtype)
        width = low_pass_width * 2
        reconstructed = coefficients
        for _ in range(_LEVELS):
            half = width // 2
            active = reconstructed[:width, :width]
            scale = torch.rsqrt(torch.tensor(2.0, dtype=active.dtype, device=active.device))
            average = active[:half, :]
            detail = active[half:, :]
            vertical = torch.stack(((average + detail) * scale, (average - detail) * scale), dim=1).reshape(width, width)
            average = vertical[:, :half]
            detail = vertical[:, half:]
            restored = torch.stack(((average + detail) * scale, (average - detail) * scale), dim=2).reshape(width, width)
            reconstructed = self._replace_active(reconstructed, restored, width)
            width *= 2
        error = reconstructed - image
        squared_error = error.reshape(-1).square().cumsum(dim=0)[-1] / (n * n)
        return (reconstructed.reshape(-1), squared_error.reshape(-1), retained.reshape(-1))

def make_model():
    return WaveletCompression()
