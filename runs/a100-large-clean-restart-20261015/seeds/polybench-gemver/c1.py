"""Export-friendly PyTorch translation of PolyBench/GEMVER."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs in forward argument order."""
    if fixture is not None:
        raise ValueError('gemver does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    n = 2000
    i = torch.arange(n, device=device, dtype=torch.int64)
    values = i.to(dtype)
    n_as_dtype = torch.tensor(n, device=device, dtype=dtype)
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    A = (i[:, None] * i[None, :] % n).to(dtype) / n_as_dtype
    u1 = values
    u2 = (values + 1) / n_as_dtype / 2
    v1 = (values + 1) / n_as_dtype / 4
    v2 = (values + 1) / n_as_dtype / 6
    w = torch.zeros(n, device=device, dtype=dtype)
    x = torch.zeros(n, device=device, dtype=dtype)
    y = (values + 1) / n_as_dtype / 8
    z = (values + 1) / n_as_dtype / 9
    return (alpha, beta, A, u1, v1, u2, v2, w, x, y, z)

class Gemver(torch.nn.Module):
    """Vectorized GEMVER kernel preserving supplied input tensors."""

    def forward(self, alpha, beta, A, u1, v1, u2, v2, w, x, y, z):
        A_updated = A + u1[:, None] * v1[None, :] + u2[:, None] * v2[None, :]
        x_out = x + beta * torch.matmul(A_updated.transpose(0, 1), y) + z
        w_out = w + alpha * torch.matmul(A_updated, x_out)
        return w_out.reshape(-1)

def make_model():
    return Gemver()
