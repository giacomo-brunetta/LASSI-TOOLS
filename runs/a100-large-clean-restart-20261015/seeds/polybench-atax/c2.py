"""Export-friendly PyTorch translation of PolyBench ATAX (MINI profile)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_M = 1900
_N = 2100

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs used by the C reference."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    if fixture is not None:
        raise ValueError('ATAX does not define an input fixture')
    rows = torch.arange(_M, device=device, dtype=torch.int64).unsqueeze(1)
    columns = torch.arange(_N, device=device, dtype=torch.int64).unsqueeze(0)
    A = ((rows + columns) % _N).to(dtype=dtype) / 9500
    x = 1 + torch.arange(_N, device=device, dtype=dtype) / 2100
    return (A, x)

class ATAXModel(torch.nn.Module):
    """Compute y = A^T(Ax) using explicit broadcast and reduction stages."""

    def forward(self, A, x):
        row_products = A * x.unsqueeze(0)
        tmp = row_products.sum(dim=1)
        column_contributions = A * tmp.unsqueeze(1)
        y = column_contributions.sum(dim=0)
        return y.contiguous().reshape(-1)

def make_model():
    return ATAXModel()
