import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI direct-DFT signal from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    if fixture is not None:
        raise ValueError('direct-dft does not use input fixtures')
    n = 4096
    j = torch.arange(n, device=device, dtype=dtype)
    pi = torch.acos(torch.tensor(-1.0, device=device, dtype=dtype))
    signal = torch.sin(2 * pi * 3 * j / n) + 0.25 * torch.cos(2 * pi * 5 * j / n) + 0.01 * j
    return (signal,)

class DirectDFT(nn.Module):

    def forward(self, signal):
        signal_readonly = signal.clone()
        n = signal_readonly.shape[0]
        j = torch.arange(n, device=signal_readonly.device, dtype=signal_readonly.dtype)
        k = torch.arange(n, device=signal_readonly.device, dtype=signal_readonly.dtype)
        pi = torch.acos(torch.tensor(-1.0, device=signal_readonly.device, dtype=signal_readonly.dtype))
        angle = 2 * pi * k[:, None] * j[None, :] / n
        basis = torch.stack((torch.cos(angle), -torch.sin(angle)), dim=0)
        rhs = signal_readonly.reshape(1, n, 1).expand(2, n, 1)
        outputs = torch.bmm(basis, rhs).squeeze(-1)
        return torch.stack((outputs[0], outputs[1]), dim=1).reshape(-1)

def make_model():
    return DirectDFT()
