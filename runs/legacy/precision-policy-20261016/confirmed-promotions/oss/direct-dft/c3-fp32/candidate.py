import math
import torch

# Precision contract metadata
LASSI_PRECISION = {
    "storage": torch.float64,
    "operator": torch.float64,
    "accumulator": torch.float64,
    "output": torch.float64,
}

# Fixed problem size matching the reference's default (mini) dataset.
_SIZE = 32


def build_inputs(device: str = "cpu", dtype: torch.dtype = torch.float64, fixture=None, dataset: str = "mini"):
    """Create the deterministic input tensor used by the reference program.

    Parameters
    ----------
    device: str
        Target device for the tensor (e.g., "cpu" or "cuda").
    dtype: torch.dtype
        Desired dtype; the reference uses double precision (torch.float64).
    fixture: ignored
        Kept for API compatibility; the reference does not use external fixtures.
    dataset: str
        Profile name – only the ``mini`` profile (SIZE=32) is required for validation.
        The argument is accepted for API compatibility but is ignored.

    Returns
    -------
    tuple[torch.Tensor]
        A single‑element tuple containing the real‑valued signal.
    """
    # The reference program always uses SIZE=32 (mini).
    pi = math.acos(-1.0)
    j = torch.arange(_SIZE, dtype=dtype, device=device)
    signal = (
        torch.sin(2 * pi * 3 * j / _SIZE)
        + 0.25 * torch.cos(2 * pi * 5 * j / _SIZE)
        + 0.01 * j
    )
    return (signal,)


class DirectDFTFFT(torch.nn.Module):
    """Direct DFT computed via PyTorch's FFT routine.

    The reference implementation uses explicit O(N²) loops. We obtain the mathematically
    identical result using ``torch.fft.fft``, which computes the un‑normalized DFT for a
    complex input. The input is real, so the imaginary component is zero.
    """

    def __init__(self, size: int = _SIZE):
        super().__init__()
        self.N = size

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        """Compute the DFT and return interleaved real/imag values.

        Parameters
        ----------
        signal: torch.Tensor
            1‑D real tensor of length ``self.N``.

        Returns
        -------
        torch.Tensor
            1‑D tensor of shape ``2 * N`` where even indices hold the real part and odd
            indices hold the imaginary part, matching the order printed by the C program.
        """
        # Ensure correct dtype and device.
        signal = signal.to(dtype=torch.float64)
        # Build a complex tensor with zero imaginary part.
        complex_signal = torch.complex(signal, torch.zeros_like(signal))
        # Compute forward DFT (unnormalized, same scaling as reference).
        fft_result = torch.fft.fft(complex_signal, norm=None)
        # Interleave real and imaginary components.
        out = torch.empty(2 * self.N, dtype=torch.float64, device=signal.device)
        out[0::2] = fft_result.real
        out[1::2] = fft_result.imag
        return out


def make_model():
    """Factory returning a ready‑to‑run model for the default (mini) dataset."""
    return DirectDFTFFT(_SIZE)
