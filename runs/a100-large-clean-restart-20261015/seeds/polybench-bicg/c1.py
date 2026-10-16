"""Export-friendly PyTorch translation of the PolyBench BICG kernel."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

class BICG(torch.nn.Module):
    """Compute the two BICG matrix-vector products without mutating inputs."""

    def forward(self, A: torch.Tensor, r: torch.Tensor, p: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        s = torch.matmul(A.transpose(0, 1), r)
        q = torch.matmul(A, p)
        return (s.reshape(-1), q.reshape(-1))

def build_inputs(device: str | torch.device='cpu', dtype: torch.dtype=torch.float64, fixture=None, dataset: str='default') -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Build MINI_DATASET inputs using the reference's integer-first formulas."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    m = 1900
    n = 2100
    i = torch.arange(n, device=device, dtype=torch.int64)
    j = torch.arange(m, device=device, dtype=torch.int64)
    p = j.remainder(m).to(dtype) / m
    r = i.remainder(n).to(dtype) / n
    A = (i[:, None] * (j[None, :] + 1)).remainder(n).to(dtype) / n
    return (A, r, p)

def make_model() -> torch.nn.Module:
    """Return a fresh, stateless BICG module."""
    return BICG()
