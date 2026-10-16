"""Low-rank-eliminated PyTorch translation of PolyBench GEMVER."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('gemver does not define an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile (n=40) is supported')
    n = 2000
    indices = torch.arange(n, device=device, dtype=torch.int64)
    fn = torch.tensor(n, device=device, dtype=dtype)
    values = indices.to(dtype=dtype)
    one_based = values + 1
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    u1 = values
    u2 = one_based / fn / 2.0
    v1 = one_based / fn / 4.0
    v2 = one_based / fn / 6.0
    w = torch.zeros(n, device=device, dtype=dtype)
    x = torch.zeros(n, device=device, dtype=dtype)
    y = one_based / fn / 8.0
    z = one_based / fn / 9.0
    products_mod_n = indices[:, None] * indices[None, :] % n
    A = products_mod_n.to(dtype=dtype) / fn
    return (alpha, beta, A, u1, v1, u2, v2, w, x, y, z)

class GemverModel(torch.nn.Module):

    def forward(self, alpha, beta, A, u1, v1, u2, v2, w, x, y, z):
        uy1 = torch.dot(u1, y)
        uy2 = torch.dot(u2, y)
        x_out = x + beta * (torch.matmul(A.transpose(0, 1), y) + v1 * uy1 + v2 * uy2) + z
        vx1 = torch.dot(v1, x_out)
        vx2 = torch.dot(v2, x_out)
        w_out = w + alpha * (torch.matmul(A, x_out) + u1 * vx1 + u2 * vx2)
        return w_out.reshape(-1)

def make_model():
    return GemverModel()
