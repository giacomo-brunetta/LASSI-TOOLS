import torch
from torch import nn


LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float64",
    "accumulator": "float64",
    "output": "float64",
}


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Build the deterministic MINI direct-DFT signal from the C initializer."""
    if dataset not in ("default", "mini"):
        raise ValueError(f"unsupported dataset profile: {dataset!r}")
    if fixture is not None:
        raise ValueError("direct-dft does not use input fixtures")

    n = 32
    j = torch.arange(n, device=device, dtype=dtype)
    pi = torch.acos(torch.tensor(-1.0, device=device, dtype=dtype))
    signal = (
        torch.sin(((2 * pi) * 3 * j) / n)
        + 0.25 * torch.cos(((2 * pi) * 5 * j) / n)
        + 0.01 * j
    )
    return (signal,)


class DirectDFT(nn.Module):
    def forward(self, signal):
        signal_readonly = signal.clone()
        if signal_readonly.dtype == torch.bfloat16:
            signal_readonly = signal_readonly.to(torch.float32)
        n = signal_readonly.shape[0]
        j = torch.arange(n, device=signal_readonly.device, dtype=signal_readonly.dtype)
        k = torch.arange(n, device=signal_readonly.device, dtype=signal_readonly.dtype)
        pi = torch.acos(-(signal_readonly[0] * 4))
        angle = (((2 * pi) * k[:, None]) * j[None, :]) / n
        basis = torch.stack((torch.cos(angle), -torch.sin(angle)), dim=0)
        outputs = torch.matmul(basis, signal_readonly)
        return torch.stack((outputs[0], outputs[1]), dim=1).reshape(-1)


def make_model():
    return DirectDFT()
