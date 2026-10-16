"""Export-friendly packed no-pivot LU for PolyBench LU."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic pre-kernel PolyBench LU matrix."""
    if fixture is not None:
        raise ValueError('polybench-lu does not define input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    n = 2000
    indices = torch.arange(n, device=device)
    row = indices.unsqueeze(1)
    col = indices.unsqueeze(0)
    lower = col <= row
    c = torch.where(lower, 1.0 - col.to(dtype=dtype) / n, torch.zeros((n, n), device=device, dtype=dtype))
    c.diagonal().fill_(1)
    b = torch.zeros((n, n), device=device, dtype=dtype)
    for t in range(n):
        column = c[:, t:t + 1]
        b = b + column * column.transpose(0, 1)
    return (b,)

class PackedLU(torch.nn.Module):
    """No-pivot Doolittle factorization stored in the input matrix layout."""

    def forward(self, a_in):
        if a_in.ndim != 2 or a_in.shape[0] != a_in.shape[1]:
            raise ValueError('PackedLU expects one square rank-2 tensor')
        if not a_in.is_floating_point():
            raise TypeError('PackedLU expects a floating-point tensor')
        a = a_in.clone()
        n = a.shape[0]
        for i in range(n):
            if i == 0:
                a[i, i:n] = a[i, i:n]
            else:
                upper_update = (a[i, 0:i].unsqueeze(1) * a[0:i, i:n]).sum(dim=0)
                a[i, i:n] = a[i, i:n] - upper_update
            if i + 1 < n:
                if i == 0:
                    lower_numerator = a[i + 1:n, i]
                else:
                    lower_update = (a[i + 1:n, 0:i] * a[0:i, i].unsqueeze(0)).sum(dim=1)
                    lower_numerator = a[i + 1:n, i] - lower_update
                a[i + 1:n, i] = lower_numerator / a[i, i]
        return a.reshape(-1)

def make_model():
    return PackedLU()
