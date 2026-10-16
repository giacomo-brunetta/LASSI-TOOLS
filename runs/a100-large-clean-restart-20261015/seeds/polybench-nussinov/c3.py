"""Packed diagonal-major PyTorch translation of the PolyBench Nussinov kernel."""
import torch
LASSI_PRECISION = {'storage': 'int64', 'operator': 'int64', 'accumulator': 'int64', 'output': 'int64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET sequence input.

    The Nussinov reference uses an integer ``base`` sequence; ``dtype`` is
    accepted for the shared arena interface but does not change its integral
    representation.
    """
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    del dtype, fixture
    n = 2500
    seq = (torch.arange(n, device=device, dtype=torch.int64) + 1).remainder(4)
    return (seq,)

class NussinovPackedDiagonal(torch.nn.Module):
    """Compute the Nussinov chart using D[span, row] packed diagonals."""

    def forward(self, seq):
        seq_work = seq.clone()
        n = seq_work.shape[0]
        device = seq_work.device
        diag0 = torch.zeros(n, device=device, dtype=torch.int64)
        D = torch.zeros((n, n), device=device, dtype=torch.int64)
        D = torch.cat((diag0.unsqueeze(0), D[1:]), dim=0)
        for d in range(1, n):
            count = n - d
            i = torch.arange(count, device=device, dtype=torch.int64)
            left = D[d - 1, i]
            down = D[d - 1, i + 1]
            if d == 1:
                pair = torch.zeros(count, device=device, dtype=torch.int64)
                values = torch.maximum(torch.maximum(left, down), pair)
            else:
                pair = D[d - 2, i + 1] + (seq_work[i] + seq_work[i + d] == 3).to(torch.int64)
                values = torch.maximum(torch.maximum(left, down), pair)
                r = torch.arange(1, d, device=device, dtype=torch.int64)
                left_parts = D[r.unsqueeze(0), i.unsqueeze(1)]
                right_parts = D[(d - r - 1).unsqueeze(0), i.unsqueeze(1) + r.unsqueeze(0) + 1]
                split = torch.amax(left_parts + right_parts, dim=1)
                values = torch.maximum(values, split)
            updated_diagonal = torch.cat((values, torch.zeros(d, device=device, dtype=torch.int64)), dim=0)
            D = torch.cat((D[:d], updated_diagonal.unsqueeze(0), D[d + 1:]), dim=0)
        rows, cols = torch.triu_indices(n, n, offset=0, device=device)
        span = cols - rows
        return D[span, rows].reshape(-1)

def make_model():
    return NussinovPackedDiagonal()
