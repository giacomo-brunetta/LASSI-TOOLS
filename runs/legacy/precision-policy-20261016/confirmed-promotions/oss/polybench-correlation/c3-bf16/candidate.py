import torch
from typing import Tuple

# Dataset dimensions for MINI_DATASET (as defined in reference headers)
M = 28
N = 32

LASSI_PRECISION = {
    "storage": torch.float64,
    "operator": torch.float64,
    "accumulator": torch.float64,
    "output": torch.float64,
}

def build_inputs(device: str = "cpu", dtype: torch.dtype = torch.float64, fixture=None, dataset: str = "default") -> Tuple[torch.Tensor]:
    """Construct the input tensor(s) matching the reference initialization.

    Parameters
    ----------
    device: str
        Target device for the tensors.
    dtype: torch.dtype
        Desired data type (must be torch.float64 for reference verification).
    fixture: optional
        Unused – placeholder for compatibility with validation harness.
    dataset: str
        Name of the dataset profile. Only ``"mini"`` is supported; other values fall back to the same dimensions.
    """
    # The reference always uses the MINI_DATASET dimensions for this arena.
    # Compute data[i, j] = (i * j) / M + i, where i indexes N rows and j indexes M columns.
    i = torch.arange(N, dtype=dtype, device=device).unsqueeze(1)  # (N, 1)
    j = torch.arange(M, dtype=dtype, device=device).unsqueeze(0)  # (1, M)
    data = (i * j) / M + i
    return (data,)

def make_model() -> torch.nn.Module:
    class CorrBlockwise(torch.nn.Module):
        def __init__(self, block_size: int = 8):
            super().__init__()
            self.block_size = block_size
            self.eps = torch.tensor(0.1, dtype=torch.float64)

        def forward(self, data: torch.Tensor) -> torch.Tensor:
            """Compute the correlation matrix using a blockwise algorithm.

            Parameters
            ----------
            data: torch.Tensor of shape (N, M)
                Input matrix as produced by ``build_inputs``.
            """
            # Ensure we work with FP64 tensors on the same device.
            data = data.to(dtype=torch.float64)
            device = data.device

            float_n = torch.tensor(N, dtype=torch.float64, device=device)
            # Mean of each column (size M)
            mean = data.mean(dim=0)
            # Variance and standard deviation per column
            var = ((data - mean) ** 2).mean(dim=0)
            stddev = torch.sqrt(var)
            # Guard against near‑zero stddev
            stddev = torch.where(stddev <= self.eps, torch.tensor(1.0, dtype=torch.float64, device=device), stddev)
            # Scale factor sqrt(N) * stddev
            scale = torch.sqrt(float_n) * stddev
            # Normalized data
            data_norm = (data - mean) / scale  # shape (N, M)

            # Allocate correlation matrix
            corr = torch.empty((M, M), dtype=torch.float64, device=device)
            diag_idx = torch.arange(M, device=device)
            corr[diag_idx, diag_idx] = 1.0

            bs = self.block_size
            for i_start in range(0, M, bs):
                i_end = min(i_start + bs, M)
                sub_i = slice(i_start, i_end)
                # Diagonal block (including full sub‑matrix)
                block = torch.matmul(data_norm[:, sub_i].t(), data_norm[:, sub_i])
                corr[sub_i, sub_i] = block
                # Off‑diagonal blocks
                for j_start in range(i_end, M, bs):
                    j_end = min(j_start + bs, M)
                    sub_j = slice(j_start, j_end)
                    off_block = torch.matmul(data_norm[:, sub_i].t(), data_norm[:, sub_j])
                    corr[sub_i, sub_j] = off_block
                    corr[sub_j, sub_i] = off_block.t()

            # Final safeguard for exact diagonal values
            corr[diag_idx, diag_idx] = 1.0
            return corr

    return CorrBlockwise()
