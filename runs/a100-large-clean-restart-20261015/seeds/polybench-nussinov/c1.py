"""Export-friendly PyTorch translation of PolyBench Nussinov (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'int64', 'operator': 'int64', 'accumulator': 'int64', 'output': 'int64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic integer RNA-base input for MINI_DATASET."""
    if dataset != 'large':
        raise ValueError("only the 'mini' dataset is supported")
    if fixture is not None:
        raise ValueError('nussinov has no input fixtures')
    del dtype
    n = 2500
    seq = (torch.arange(n, device=device, dtype=torch.int64) + 1) % 4
    return (seq,)

class Nussinov(torch.nn.Module):
    """Compute the Nussinov dynamic-programming table from an RNA sequence."""

    def forward(self, seq):
        if seq.ndim != 1:
            raise ValueError('seq must have shape (n,)')
        if seq.dtype != torch.int64:
            raise TypeError('seq must have dtype torch.int64')
        seq = seq.clone()
        n = seq.shape[0]
        table = torch.zeros((n, n), device=seq.device, dtype=torch.int64)
        for d in range(1, n):
            i = torch.arange(n - d, device=seq.device, dtype=torch.int64)
            j = i + d
            left = table[i, j - 1]
            down = table[i + 1, j]
            diag = table[i + 1, j - 1]
            if d > 1:
                diag = diag + (seq[i] + seq[j] == 3).to(table.dtype)
            current = torch.maximum(torch.maximum(left, down), diag)
            if d > 1:
                offset = torch.arange(d - 1, device=seq.device, dtype=torch.int64)
                k = i[:, None] + 1 + offset[None, :]
                split_scores = table[i[:, None], k] + table[k + 1, j[:, None]]
                current = torch.maximum(current, split_scores.amax(dim=1))
            update = torch.zeros_like(table).reshape(-1).scatter(0, i * n + j, current).reshape(n, n)
            table = table + update
        upper = torch.triu_indices(n, n, offset=0, device=seq.device)
        return table[upper[0], upper[1]]

def make_model():
    return Nussinov()
