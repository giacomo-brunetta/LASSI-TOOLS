"""Export-friendly PyTorch translation of PolyBench 3mm (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_NI = 800
_NJ = 900
_NK = 1000
_NL = 1100
_NM = 1200

def _indices(rows: int, cols: int, device: torch.device | str) -> tuple[torch.Tensor, torch.Tensor]:
    return (torch.arange(rows, device=device, dtype=torch.int64).reshape(rows, 1), torch.arange(cols, device=device, dtype=torch.int64).reshape(1, cols))

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic C `init_array` inputs for MINI_DATASET."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    if fixture is not None:
        raise ValueError('polybench-3mm has no input fixture')
    i, j = _indices(_NI, _NK, device)
    a = ((i * j + 1) % _NI).to(dtype=dtype) / (5 * _NI)
    i, j = _indices(_NK, _NJ, device)
    b = ((i * (j + 1) + 2) % _NJ).to(dtype=dtype) / (5 * _NJ)
    i, j = _indices(_NJ, _NM, device)
    c = (i * (j + 3) % _NL).to(dtype=dtype) / (5 * _NL)
    i, j = _indices(_NM, _NL, device)
    d = ((i * (j + 2) + 2) % _NK).to(dtype=dtype) / (5 * _NK)
    return (a, b, c, d)

class ThreeMM(torch.nn.Module):

    def forward(self, a: torch.Tensor, b: torch.Tensor, c: torch.Tensor, d: torch.Tensor) -> torch.Tensor:
        a = a.clone()
        b = b.clone()
        c = c.clone()
        d = d.clone()
        e = torch.einsum('ik,kj->ij', a, b)
        f = torch.einsum('jm,ml->jl', c, d)
        g = torch.einsum('ij,jl->il', e, f)
        return g.reshape(-1)

def make_model():
    return ThreeMM()
