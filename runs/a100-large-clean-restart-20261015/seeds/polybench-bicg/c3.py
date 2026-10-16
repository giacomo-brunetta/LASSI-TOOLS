"""Export-friendly PyTorch translation of PolyBench BiCG."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('polybench-bicg does not define input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    m = 1900
    n = 2100
    rows = torch.arange(n, device=device, dtype=torch.int64)
    cols = torch.arange(m, device=device, dtype=torch.int64)
    p = cols.remainder(m).to(dtype=dtype) / m
    r = rows.remainder(n).to(dtype=dtype) / n
    A = (rows.unsqueeze(1) * (cols.unsqueeze(0) + 1)).remainder(n).to(dtype=dtype) / n
    return (A, r, p)

class BiCG(torch.nn.Module):
    """Compute the two BiCG live-outs with ordered prefix accumulations."""

    def forward(self, A, r, p):
        s_terms = A * r.unsqueeze(1)
        q_terms = A * p.unsqueeze(0)
        s_prefix = torch.cumsum(s_terms, dim=0)
        q_prefix = torch.cumsum(q_terms, dim=1)
        s = s_prefix[-1, :]
        q = q_prefix[:, -1]
        return (s.reshape(-1), q.reshape(-1))

def make_model():
    return BiCG()
