"""Vectorized JPEG-like 8x8 DCT using one dense 64-dimensional transform."""
import math
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_BLOCK = 8
_MINI_SIZE = 1024
_SUPPORTED_DATASETS = {'default', 'large'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET image from the C initializer."""
    del fixture
    if dataset not in _SUPPORTED_DATASETS:
        raise ValueError(f'unsupported dataset {dataset!r}; expected one of {_SUPPORTED_DATASETS}')
    size = _MINI_SIZE
    pi = torch.tensor(math.pi, device=device, dtype=dtype)
    rows = torch.arange(size, device=device, dtype=dtype).reshape(size, 1)
    columns = torch.arange(size, device=device, dtype=dtype).reshape(1, size)
    image = 96.0 + 28.0 * torch.sin(2.0 * pi * rows / size) + 19.0 * torch.cos(4.0 * pi * columns / size) + 0.15 * rows + 0.08 * columns + 7.0 * torch.sin(2.0 * pi * (rows + columns) / size)
    return (image,)

class JpegDctDense(torch.nn.Module):
    """JPEG DCT, scalar quantization, and reconstruction for square 8x8 blocks."""

    def forward(self, image):
        if image.ndim != 2:
            raise ValueError('image must be a rank-2 tensor')
        size_rows, size_columns = image.shape
        if size_rows != size_columns or size_rows % _BLOCK != 0:
            raise ValueError('image must be square with both dimensions divisible by 8')
        device = image.device
        dtype = image.dtype
        indices = torch.arange(_BLOCK, device=device, dtype=dtype)
        scales = torch.where(indices == 0, torch.rsqrt(torch.tensor(2.0, device=device, dtype=dtype)), torch.ones_like(indices))
        pi = torch.tensor(math.pi, device=device, dtype=dtype)
        dct_basis = scales[:, None] * torch.cos(pi * (2.0 * indices[None, :] + 1.0) * indices[:, None] / 16.0)
        transform = torch.outer(dct_basis.reshape(-1), dct_basis.reshape(-1))
        transform = transform.reshape(_BLOCK, _BLOCK, _BLOCK, _BLOCK)
        transform = transform.permute(0, 2, 1, 3).reshape(64, 64)
        blocks_per_side = size_rows // _BLOCK
        blocks_flat = image.reshape(blocks_per_side, _BLOCK, blocks_per_side, _BLOCK).permute(0, 2, 1, 3).reshape(-1, 64)
        transformed_flat = 0.25 * (blocks_flat @ transform.transpose(0, 1))
        quantization = 1.0 + 0.75 * (indices[:, None] + indices[None, :])
        quantization_flat = quantization.reshape(1, 64)
        scaled = transformed_flat / quantization_flat
        rounded = torch.sign(scaled) * torch.floor(torch.abs(scaled) + 0.5)
        coefficients_flat = rounded * quantization_flat
        nonzero = (coefficients_flat != 0.0).sum().to(dtype)
        reconstructed_flat = 0.25 * (coefficients_flat @ transform)
        reconstructed = reconstructed_flat.reshape(blocks_per_side, blocks_per_side, _BLOCK, _BLOCK).permute(0, 2, 1, 3).reshape(size_rows, size_columns)
        squared_error = ((reconstructed - image) * (reconstructed - image)).sum()
        mean_squared_error = squared_error / (size_rows * size_columns)
        return (reconstructed.reshape(-1), mean_squared_error.reshape(1), nonzero.reshape(1))

def make_model():
    return JpegDctDense()
