"""Export-friendly PyTorch translation of PolyBench/C gemver."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('gemver does not use an input fixture')
    if dataset not in {'default', 'large'}:
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    n = 2000
    indices = torch.arange(n, device=device, dtype=torch.int64)
    n_scalar = torch.tensor(n, device=device, dtype=dtype)
    one = torch.tensor(1, device=device, dtype=dtype)
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    u1 = indices.to(dtype)
    u2 = (indices.to(dtype) + one) / n_scalar / 2.0
    v1 = (indices.to(dtype) + one) / n_scalar / 4.0
    v2 = (indices.to(dtype) + one) / n_scalar / 6.0
    y = (indices.to(dtype) + one) / n_scalar / 8.0
    z = (indices.to(dtype) + one) / n_scalar / 9.0
    x = torch.zeros(n, device=device, dtype=dtype)
    w = torch.zeros(n, device=device, dtype=dtype)
    A = (indices[:, None] * indices[None, :]).remainder(n).to(dtype) / n_scalar
    return (alpha, beta, A, u1, v1, u2, v2, w, x, y, z)

class Gemver(torch.nn.Module):

    def forward(self, alpha, beta, A, u1, v1, u2, v2, w, x, y, z):
        U = torch.stack((u1, u2), dim=1)
        V = torch.stack((v1, v2), dim=1)
        A_updated = A + torch.matmul(U, V.transpose(0, 1))
        x_out = x + beta * torch.matmul(A_updated.transpose(0, 1), y) + z
        w_out = w + alpha * torch.matmul(A_updated, x_out)
        return w_out.reshape(-1)

def make_model():
    return Gemver()
