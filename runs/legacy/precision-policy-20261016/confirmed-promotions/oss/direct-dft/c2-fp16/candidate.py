import math
import torch

# Precision contract for LASSI validation
LASSI_PRECISION = {
    "storage": torch.float64,
    "operator": torch.float64,
    "accumulator": torch.float64,
    "output": torch.float64,
}


def build_inputs(device: str = "cpu", dtype: torch.dtype = torch.float64, fixture=None, dataset: str = "mini"):
    """Create deterministic inputs matching the reference C implementation.

    The reference uses a fixed SIZE macro (32 for the mini dataset) and initializes
    `signal[j] = sin(2*pi*3*j/SIZE) + 0.25*cos(2*pi*5*j/SIZE) + 0.01*j`.
    This function reproduces that exactly for the requested device and dtype.
    """
    # Map dataset name to the corresponding SIZE used by the reference.
    size_map = {"mini": 32, "small": 64, "medium": 128, "large": 256}
    size = size_map.get(dataset.lower(), 32)
    j = torch.arange(size, dtype=dtype, device=device)
    pi = math.acos(-1.0)
    signal = torch.sin(2 * pi * 3 * j / size) + 0.25 * torch.cos(2 * pi * 5 * j / size) + 0.01 * j
    return (signal,)


class DirectDFTEinsum(torch.nn.Module):
    """Direct DFT computed with Einstein summation.

    The implementation follows the reference C loops exactly but uses a vectorised
    `torch.einsum` contraction to avoid an explicit inner‑loop.
    """

    def __init__(self, size: int = None):
        super().__init__()
        self.size = size  # optional hint; can be inferred from input if None

    def forward(self, signal: torch.Tensor) -> torch.Tensor:
        # Ensure FP64 for correctness irrespective of input dtype
        signal = signal.to(torch.float64)
        N = signal.shape[-1] if self.size is None else self.size
        device = signal.device
        pi = math.acos(-1.0)
        # Create index tensors
        k = torch.arange(N, dtype=torch.float64, device=device)
        j = torch.arange(N, dtype=torch.float64, device=device)
        # Compute angle matrix (N, N)
        angle = 2 * pi * k[:, None] * j[None, :] / N
        cos_mat = torch.cos(angle)
        sin_mat = torch.sin(angle)
        # Einstein summation replaces the inner j‑loop
        real = torch.einsum("kj,j->k", cos_mat, signal)
        imag = -torch.einsum("kj,j->k", sin_mat, signal)
        # Interleave real and imag as the reference prints them
        out = torch.empty(2 * N, dtype=torch.float64, device=device)
        out[0::2] = real
        out[1::2] = imag
        return out


def make_model():
    """Instantiate the model for the default mini dataset (SIZE=32)."""
    return DirectDFTEinsum()
