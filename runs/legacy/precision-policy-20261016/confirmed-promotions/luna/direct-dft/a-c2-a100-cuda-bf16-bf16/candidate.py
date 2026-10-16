"""Export-friendly dense real direct-DFT arena candidate."""

import torch


LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float64",
    "accumulator": "float64",
    "output": "float64",
}


def _dataset_size(dataset: str) -> int:
    if dataset in ("default", "mini"):
        return 32
    raise ValueError(f"unsupported dataset profile: {dataset!r}")


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Construct the reference signal for the selected fixed-size profile."""
    del fixture
    n = _dataset_size(dataset)
    low_precision = dtype in (torch.float16, torch.bfloat16)
    work_dtype = torch.float32 if low_precision else dtype
    j = torch.arange(n, device=device, dtype=work_dtype)
    pi = torch.pi
    signal = (
        torch.sin(((2 * pi) * 3 * j) / n)
        + 0.25 * torch.cos(((2 * pi) * 5 * j) / n)
    ) + 0.01 * j
    return (signal.to(dtype=dtype) if low_precision else signal,)


class DirectDFT(torch.nn.Module):
    def forward(self, signal):
        if signal.ndim != 1:
            raise ValueError("signal must be one-dimensional")

        n = signal.shape[0]
        work_signal = (
            signal.to(dtype=torch.float32)
            if signal.dtype in (torch.float16, torch.bfloat16)
            else signal
        )
        indices = torch.arange(n, device=signal.device, dtype=work_signal.dtype)
        pi = torch.pi
        angle = (((2 * pi) * indices[:, None]) * indices[None, :]) / n
        real_kernel = torch.cos(angle)
        imag_kernel = -torch.sin(angle)
        real = torch.matmul(real_kernel, work_signal)
        imag = torch.matmul(imag_kernel, work_signal)
        return torch.stack((real, imag), dim=1).reshape(-1)


def make_model():
    return DirectDFT()
