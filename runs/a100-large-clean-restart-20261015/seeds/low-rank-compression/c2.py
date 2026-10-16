"""Batched-GEMM rank-four power-deflation translation of low-rank-compression."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_COMPONENTS = 4
_POWER_STEPS = 8
_MINI_SIZE = 1024

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI image fixture from the C initialization."""
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset: {dataset!r}; expected 'mini'")
    if fixture is not None:
        raise ValueError('low-rank-compression does not accept an external fixture')
    coordinates = torch.arange(1, _MINI_SIZE + 1, device=device, dtype=dtype)
    rows = coordinates.reshape(_MINI_SIZE, 1)
    columns = coordinates.reshape(1, _MINI_SIZE)
    image = 2.0 * torch.sin(0.07 * rows) * torch.cos(0.11 * columns) + 1.3 * torch.cos(0.03 * rows) * torch.sin(0.05 * columns) + 0.8 * rows * columns / (_MINI_SIZE * _MINI_SIZE) + 0.12 * torch.sin(0.013 * rows * columns)
    return (image,)

class LowRankCompression(torch.nn.Module):
    """Four fixed batched-GEMM power iterations and rank-one deflations."""

    def forward(self, image):
        if image.ndim != 2 or image.shape[0] != image.shape[1]:
            raise ValueError('image must be a square rank-2 tensor')
        n = image.shape[0]
        residual = image.clone()
        approximation = torch.zeros_like(image)
        for component in range(_COMPONENTS):
            columns = torch.arange(n, device=image.device, dtype=image.dtype)
            right = 1.0 + 0.01 * (columns + component)
            right = right / torch.sqrt(torch.sum(right * right))
            for _ in range(_POWER_STEPS):
                residual_3d = residual.unsqueeze(0)
                right_col = right.reshape(1, n, 1)
                left = torch.bmm(residual_3d, right_col).reshape(n)
                left = left / torch.sqrt(torch.sum(left * left))
                right = torch.bmm(residual_3d.transpose(1, 2), left.reshape(1, n, 1)).reshape(n)
                right = right / torch.sqrt(torch.sum(right * right))
            residual_3d = residual.unsqueeze(0)
            left_row = left.reshape(1, 1, n)
            right_col = right.reshape(1, n, 1)
            singular_value = torch.bmm(torch.bmm(left_row, residual_3d), right_col).reshape(())
            contribution = torch.bmm(left.reshape(1, n, 1), right.reshape(1, 1, n)).reshape(n, n) * singular_value
            approximation = approximation + contribution
            residual = residual - contribution
        squared_error = torch.sum(residual * residual)
        signal_energy = torch.sum(image * image)
        relative_error = squared_error / signal_energy
        return (approximation.reshape(-1), relative_error.reshape(1), image.new_tensor([4.0]))

def make_model():
    return LowRankCompression()
