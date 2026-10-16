"""Export-friendly PyTorch translation of the MINI iir-filter-bank kernel."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

class IIRFilterBank(nn.Module):
    """Four causal biquads evaluated as batched lower-triangular solves."""

    def __init__(self) -> None:
        super().__init__()
        self.register_buffer('b0', torch.tensor([0.06745527, 0.20657208, 0.39133577, 0.63894553], dtype=torch.float64))
        self.register_buffer('b1', torch.tensor([0.13491055, 0.41314417, 0.0, -1.27789105], dtype=torch.float64))
        self.register_buffer('b2', torch.tensor([0.06745527, 0.20657208, -0.39133577, 0.63894553], dtype=torch.float64))
        self.register_buffer('a1', torch.tensor([-1.1429805, -0.36952738, -0.36952738, -1.1429805], dtype=torch.float64))
        self.register_buffer('a2', torch.tensor([0.4128016, 0.19581571, 0.21767222, 0.4128016], dtype=torch.float64))

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        """Return filter-major output samples without modifying ``signal``."""
        original_signal = signal.clone()
        length = signal.shape[0]
        indices = torch.arange(length, device=signal.device)
        zero = torch.zeros(1, dtype=signal.dtype, device=signal.device)
        delayed_one = torch.cat((zero, signal))[:-1]
        delayed_two = torch.cat((zero, zero, signal))[:-2]
        b0 = self.b0.to(device=signal.device, dtype=signal.dtype).unsqueeze(1)
        b1 = self.b1.to(device=signal.device, dtype=signal.dtype).unsqueeze(1)
        b2 = self.b2.to(device=signal.device, dtype=signal.dtype).unsqueeze(1)
        rhs = b0 * signal.unsqueeze(0) + b1 * delayed_one.unsqueeze(0) + b2 * delayed_two.unsqueeze(0)
        row = indices.unsqueeze(1)
        column = indices.unsqueeze(0)
        distance = row - column
        diagonal = (distance == 0).to(dtype=signal.dtype).unsqueeze(0)
        subdiagonal_one = (distance == 1).to(dtype=signal.dtype).unsqueeze(0)
        subdiagonal_two = (distance == 2).to(dtype=signal.dtype).unsqueeze(0)
        a1 = self.a1.to(device=signal.device, dtype=signal.dtype).view(4, 1, 1)
        a2 = self.a2.to(device=signal.device, dtype=signal.dtype).view(4, 1, 1)
        triangular = diagonal + a1 * subdiagonal_one + a2 * subdiagonal_two
        output = torch.linalg.solve_triangular(triangular, rhs.unsqueeze(-1), upper=False).squeeze(-1)
        torch._assert(torch.equal(signal, original_signal), 'forward must not mutate signal')
        return output.reshape(-1)

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI reference signal (SIZE == 32)."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    sample_int = torch.arange(16384, device=device, dtype=torch.int64)
    sample = sample_int.to(dtype=dtype)
    signal = torch.sin(0.09 * sample) + 0.35 * torch.cos(0.31 * sample) + 0.12 * torch.sin(0.71 * sample) + (sample_int.remainder(17) == 0).to(dtype=dtype) * 0.5
    return (signal,)

def make_model() -> nn.Module:
    return IIRFilterBank()
