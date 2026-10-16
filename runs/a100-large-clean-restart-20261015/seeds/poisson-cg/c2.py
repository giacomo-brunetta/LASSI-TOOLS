import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI Poisson-CG right-hand side."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    del fixture
    indices = torch.arange(16384, device=device, dtype=dtype)
    b = 1.0 + torch.sin(0.3 * (indices + 1.0))
    return (b,)

class PoissonCG(torch.nn.Module):

    def forward(self, b):
        b = b.clone().reshape(-1)
        n = b.numel()
        x = torch.zeros((n,), device=b.device, dtype=b.dtype)
        r = b.clone()
        p = b.clone()
        rr = torch.cumsum(r * r, dim=0)[-1]
        for _ in range(10):
            boundary = torch.zeros(1, device=p.device, dtype=p.dtype)
            q = torch.cat((boundary, p, boundary), dim=0)
            windows = q.unfold(0, 3, 1)
            ap = 2 * windows[:, 1] - windows[:, 0] - windows[:, 2]
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
