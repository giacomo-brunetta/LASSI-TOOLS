"""Export-friendly PyTorch translation of the MINI direct forward DFT."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET signal used by the C fixture."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    n = 4096
    j = torch.arange(n, device=device, dtype=dtype)
    pi = torch.acos(torch.full((), -1.0, device=device, dtype=dtype))
    phase3 = 2 * pi * 3 * j / n
    phase5 = 2 * pi * 5 * j / n
    signal = torch.sin(phase3) + 0.25 * torch.cos(phase5) + 0.01 * j
    return (signal,)

class DirectDFT(torch.nn.Module):

    def forward(self, signal):
        n = signal.numel()
        j = torch.arange(n, device=signal.device, dtype=signal.dtype)
        k = torch.arange(n, device=signal.device, dtype=signal.dtype)
        pi = torch.acos(torch.full((), -1.0, device=signal.device, dtype=signal.dtype))
        angle = 2 * pi * k[:, None] * j[None, :] / n
        cos_angle = torch.cos(angle)
        sin_angle = torch.sin(angle)
        real_terms = signal[None, :] * cos_angle
        imag_terms = -(signal[None, :] * sin_angle)
        real = torch.cumsum(real_terms, dim=1)[:, -1]
        imag = torch.cumsum(imag_terms, dim=1)[:, -1]
        return torch.stack((real, imag), dim=1).reshape(-1)

def make_model():
    return DirectDFT()
