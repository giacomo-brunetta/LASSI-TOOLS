"""Export-friendly PyTorch translation of the MINI JPEG-like DCT kernel."""
import math
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_BLOCK = 8
_MINI_SIZE = 1024

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic reference image for the supported MINI profile."""
    if fixture is not None:
        raise ValueError('jpeg-dct does not accept an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    indices = torch.arange(_MINI_SIZE, device=device, dtype=torch.float64)
    row, column = torch.meshgrid(indices, indices, indexing='ij')
    pi = torch.tensor(math.pi, device=device, dtype=torch.float64)
    image = 96.0 + 28.0 * torch.sin(2.0 * pi * row / _MINI_SIZE) + 19.0 * torch.cos(4.0 * pi * column / _MINI_SIZE) + 0.15 * row + 0.08 * column + 7.0 * torch.sin(2.0 * pi * (row + column) / _MINI_SIZE)
    return (image.to(dtype=dtype),)

class JpegDct(torch.nn.Module):

    def __init__(self):
        super().__init__()
        frequencies = torch.arange(_BLOCK, dtype=torch.float64).reshape(_BLOCK, 1)
        positions = torch.arange(_BLOCK, dtype=torch.float64).reshape(1, _BLOCK)
        scales = torch.ones(_BLOCK, dtype=torch.float64)
        scales[0] = 1.0 / math.sqrt(2.0)
        basis = scales.reshape(_BLOCK, 1) * torch.cos(math.pi * (2.0 * positions + 1.0) * frequencies / 16.0)
        quantization = 1.0 + 0.75 * (torch.arange(_BLOCK, dtype=torch.float64).reshape(_BLOCK, 1) + torch.arange(_BLOCK, dtype=torch.float64).reshape(1, _BLOCK))
        self.register_buffer('basis', basis)
        self.register_buffer('quantization', quantization)

    @staticmethod
    def _round_away_from_zero(values):
        return torch.sign(values) * torch.floor(torch.abs(values) + 0.5)

    def forward(self, image):
        if image.ndim != 2:
            raise ValueError('image must have shape [S, S]')
        height, width = image.shape
        if height != width or height % _BLOCK != 0:
            raise ValueError('image dimensions must be equal and divisible by 8')
        size = height
        block_count = size // _BLOCK
        blocks = image.reshape(block_count, _BLOCK, block_count, _BLOCK).permute(0, 2, 1, 3).reshape(-1, _BLOCK, _BLOCK)
        basis = self.basis.to(device=image.device, dtype=image.dtype)
        quantization = self.quantization.to(device=image.device, dtype=image.dtype)
        transformed = 0.25 * (basis @ blocks @ basis.transpose(-1, -2))
        coefficients = self._round_away_from_zero(transformed / quantization) * quantization
        nonzero = (coefficients != 0).sum()
        reconstructed_blocks = 0.25 * (basis.transpose(-1, -2) @ coefficients @ basis)
        reconstructed = reconstructed_blocks.reshape(block_count, block_count, _BLOCK, _BLOCK).permute(0, 2, 1, 3).reshape(size, size)
        errors = (reconstructed - image).reshape(-1)
        mean_squared_error = (errors * errors).sum() / (size * size)
        return (reconstructed.reshape(-1), mean_squared_error.reshape(-1), nonzero.to(image.dtype).reshape(-1))

def make_model():
    return JpegDct()
