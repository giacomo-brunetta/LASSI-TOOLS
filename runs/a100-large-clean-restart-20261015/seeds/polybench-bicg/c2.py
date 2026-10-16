"""Export-friendly PyTorch translation of PolyBench BiCG."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic source inputs for the PolyBench MINI profile."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset}')
    if fixture is not None:
        raise ValueError('PolyBench BiCG does not define input fixtures')
    m, n = (1900, 2100)
    row_indices = torch.arange(n, device=device, dtype=torch.int64)
    column_indices = torch.arange(m, device=device, dtype=torch.int64)
    a_numerators = torch.remainder(row_indices.unsqueeze(1) * (column_indices.unsqueeze(0) + 1), n)
    A = a_numerators.to(dtype=dtype) / n
    r = torch.remainder(row_indices, n).to(dtype=dtype) / n
    p = torch.remainder(column_indices, m).to(dtype=dtype) / m
    return (A, r, p)

class BiCG(torch.nn.Module):
    """Compute the printed BiCG live-outs without mutating input tensors."""

    def forward(self, A, r, p):
        weighted_rows = A * r.unsqueeze(1)
        weighted_cols = A * p.unsqueeze(0)
        s = torch.sum(weighted_rows, dim=0)
        q = torch.sum(weighted_cols, dim=1)
        return (s.reshape(-1), q.reshape(-1))

def make_model():
    return BiCG()
