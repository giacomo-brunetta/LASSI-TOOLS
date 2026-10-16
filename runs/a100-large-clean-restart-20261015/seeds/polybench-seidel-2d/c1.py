"""Export-friendly PyTorch translation of PolyBench Seidel-2D."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_MINI_N = 2000
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic C initializer input for the MINI profile."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    indices = torch.arange(_MINI_N, device=device, dtype=torch.int64)
    i = indices[:, None]
    j = indices[None, :]
    numerator = i * (j + 2) + 2
    a = numerator.to(dtype=dtype) / _MINI_N
    return (a,)

class Seidel2D(nn.Module):

    def forward(self, A):
        if A.ndim != 2 or A.shape[0] != A.shape[1]:
            raise ValueError('A must be a square rank-2 tensor')
        work = A.clone()
        n = A.shape[0]
        if n < 3:
            return work.reshape(-1)
        for _ in range(_TSTEPS):
            next_rows = [work[:1, :]]
            for i in range(1, n - 1):
                old_row = work[i, :]
                below = work[i + 1, :]
                above = next_rows[-1][0, :]
                forcing = above[:-2] + above[1:-1] + above[2:] + old_row[1:-1] + old_row[2:] + below[:-2] + below[1:-1] + below[2:]
                ones = torch.ones_like(forcing)
                zeros = torch.zeros_like(forcing)
                ninth = ones / 9
                transitions = torch.stack((torch.stack((ninth, forcing / 9), dim=-1), torch.stack((zeros, ones), dim=-1)), dim=-2)
                prefix = transitions
                offset = 1
                while offset < n - 2:
                    updated = torch.matmul(prefix[offset:], prefix[:-offset])
                    prefix = torch.cat((prefix[:offset], updated), dim=0)
                    offset *= 2
                initial = torch.stack((old_row[0].expand_as(forcing), ones), dim=-1)
                interior = torch.bmm(prefix, initial.unsqueeze(-1)).squeeze(-1)[:, 0]
                next_rows.append(torch.cat((old_row[:1], interior, old_row[-1:]), dim=0).unsqueeze(0))
            next_rows.append(work[-1:, :])
            work = torch.cat(next_rows, dim=0)
        return work.reshape(-1)

def make_model():
    return Seidel2D()
