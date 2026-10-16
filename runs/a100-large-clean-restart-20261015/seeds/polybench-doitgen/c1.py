"""Export-friendly PyTorch translation of PolyBench/Doitgen."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'backend matmul accumulation in input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs used by the C reference."""
    if fixture is not None:
        raise ValueError('doitgen does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    nr, nq, np = (150, 140, 160)
    r = torch.arange(nr, device=device, dtype=torch.int64).reshape(nr, 1, 1)
    q = torch.arange(nq, device=device, dtype=torch.int64).reshape(1, nq, 1)
    k = torch.arange(np, device=device, dtype=torch.int64).reshape(1, 1, np)
    i = torch.arange(np, device=device, dtype=torch.int64).reshape(np, 1)
    j = torch.arange(np, device=device, dtype=torch.int64).reshape(1, np)
    a_indices = (r * q + k) % np
    c4_indices = i * j % np
    A = a_indices.to(dtype=dtype) / np
    C4 = c4_indices.to(dtype=dtype) / np
    return (A, C4)

class Doitgen(torch.nn.Module):

    def forward(self, A, C4):
        if A.ndim != 3:
            raise ValueError('A must have shape [nr, nq, np]')
        if C4.ndim != 2:
            raise ValueError('C4 must have shape [np, np]')
        np = A.shape[-1]
        if C4.shape[0] != np or C4.shape[1] != np:
            raise ValueError('A.shape[-1] must equal both dimensions of C4')
        rows = A.reshape(-1, np)
        result2d = torch.matmul(rows, C4)
        result = result2d.reshape(A.shape)
        return result.reshape(-1)

def make_model():
    return Doitgen()
