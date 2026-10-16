"""Export-friendly JPEG-like block DCT candidate."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_BLOCK = 8
_MINI_SIZE = 1024

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic image initialized by the C reference."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset}')
    del fixture
    size = _MINI_SIZE
    row = torch.arange(size, device=device, dtype=dtype).reshape(size, 1)
    column = torch.arange(size, device=device, dtype=dtype).reshape(1, size)
    pi = torch.acos(torch.tensor(-1.0, device=device, dtype=dtype))
    image = 96.0 + 28.0 * torch.sin(2.0 * pi * row / size) + 19.0 * torch.cos(4.0 * pi * column / size) + 0.15 * row + 0.08 * column + 7.0 * torch.sin(2.0 * pi * (row + column) / size)
    return (image,)

class JpegDct(nn.Module):

    def forward(self, image):
        if image.ndim != 2:
            raise ValueError('image must be a rank-2 square tensor')
        size0, size1 = image.shape
        if size0 != size1 or size0 % _BLOCK != 0:
            raise ValueError('image dimensions must be square and divisible by 8')
        size = size0
        axis = torch.arange(_BLOCK, device=image.device, dtype=image.dtype)
        pi = torch.acos(torch.tensor(-1.0, device=image.device, dtype=image.dtype))
        scale = torch.where(axis == 0, torch.rsqrt(torch.tensor(2.0, device=image.device, dtype=image.dtype)), torch.ones_like(axis))
        basis = scale[:, None] * torch.cos(pi * (2.0 * axis[None, :] + 1.0) * axis[:, None] / 16.0)
        quantum = 1.0 + 0.75 * (axis[:, None] + axis[None, :])
        blocks_per_axis = size // _BLOCK
        blocks = image.reshape(blocks_per_axis, _BLOCK, blocks_per_axis, _BLOCK).permute(0, 2, 1, 3).reshape(-1, _BLOCK, _BLOCK)
        transformed = 0.25 * torch.einsum('ux,nxy,vy->nuv', basis, blocks, basis)
        scaled = transformed / quantum
        coefficients = torch.sign(scaled) * torch.floor(torch.abs(scaled) + 0.5) * quantum
        nonzero = (coefficients != 0).sum().to(image.dtype)
        reconstructed_blocks = 0.25 * torch.einsum('ux,nuv,vy->nxy', basis, coefficients, basis)
        reconstructed = reconstructed_blocks.reshape(blocks_per_axis, blocks_per_axis, _BLOCK, _BLOCK).permute(0, 2, 1, 3).reshape(size, size)
        squared_error = ((reconstructed - image) * (reconstructed - image)).sum()
        mean_squared_error = squared_error / (size0 * size1)
        return (reconstructed.reshape(-1), mean_squared_error.reshape(1), nonzero.reshape(1))

def make_model():
    return JpegDct()
