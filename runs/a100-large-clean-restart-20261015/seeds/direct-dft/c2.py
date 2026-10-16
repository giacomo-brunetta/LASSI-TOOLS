"""Export-friendly dense real direct-DFT arena candidate."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def _dataset_size(dataset: str) -> int:
    if dataset in ('default', 'large'):
        return 4096
    raise ValueError(f'unsupported dataset profile: {dataset!r}')

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the reference signal for the selected fixed-size profile."""
    del fixture
    n = _dataset_size(dataset)
    j = torch.arange(n, device=device, dtype=dtype)
    pi = torch.acos(torch.tensor(-1.0, device=device, dtype=dtype))
    signal = torch.sin(2 * pi * 3 * j / n) + 0.25 * torch.cos(2 * pi * 5 * j / n) + 0.01 * j
    return (signal,)

class DirectDFT(torch.nn.Module):

    def forward(self, signal):
        if signal.ndim != 1:
            raise ValueError('signal must be one-dimensional')
        n = signal.shape[0]
        indices = torch.arange(n, device=signal.device, dtype=signal.dtype)
        pi = torch.acos(torch.tensor(-1.0, device=signal.device, dtype=signal.dtype))
        angle = 2 * pi * indices[:, None] * indices[None, :] / n
        real_kernel = torch.cos(angle)
        imag_kernel = -torch.sin(angle)
        real = torch.matmul(real_kernel, signal)
        imag = torch.matmul(imag_kernel, signal)
        return torch.stack((real, imag), dim=1).reshape(-1)

def make_model():
    return DirectDFT()
