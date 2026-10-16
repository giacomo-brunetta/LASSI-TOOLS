"""Export-friendly fixed-step conjugate-gradient solve for 1D Dirichlet Poisson."""
import torch
import torch.nn.functional as F
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the MINI_DATASET right-hand side used by the C reference."""
    if fixture is not None:
        raise ValueError('poisson-cg does not support input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset {dataset!r}; only 'mini' is available")
    i = torch.arange(1, 16385, device=device, dtype=dtype)
    b = 1.0 + torch.sin(0.3 * i)
    return (b,)

class PoissonCG(torch.nn.Module):
    """Ten C-order CG steps using the Dirichlet stencil as a 1D convolution."""

    def forward(self, b):
        x = torch.zeros_like(b)
        r = b.clone()
        p = b.clone()
        rr = torch.cumsum(r * r, dim=0)[-1]
        for _ in range(10):
            p_3d = p.reshape(1, 1, -1)
            padded_p = F.pad(p_3d, (1, 1), mode='constant', value=0.0)
            kernel = p.new_tensor((-1.0, 2.0, -1.0)).reshape(1, 1, 3)
            ap = F.conv1d(padded_p, kernel).reshape(-1)
            pap = torch.cumsum(p * ap, dim=0)[-1]
            alpha = rr / pap
            x_new = x + alpha * p
            r_new = r - alpha * ap
            next_rr = torch.cumsum(r_new * r_new, dim=0)[-1]
            beta = next_rr / rr
            p_new = r_new + beta * p
            x, r, p, rr = (x_new, r_new, p_new, next_rr)
        return x.reshape(-1)

def make_model():
    return PoissonCG()
