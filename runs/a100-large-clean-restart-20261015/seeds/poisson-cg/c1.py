"""Export-friendly PyTorch translation of the fixed-step 1D Poisson CG kernel."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic SIZE=32 right-hand-side used by the mini fixture."""
    if fixture is not None:
        raise ValueError('poisson-cg does not define named input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    indices = torch.arange(1, 16385, device=device, dtype=dtype)
    b = 1.0 + torch.sin(0.3 * indices)
    return (b,)

class PoissonCG(torch.nn.Module):

    def forward(self, b):
        b = b.clone()
        x = torch.zeros_like(b)
        r = b.clone()
        p = b.clone()
        rr = torch.cumsum(r * r, dim=0)[-1]
        for _ in range(10):
            left = torch.cat((torch.zeros_like(p[:1]), p[:-1]))
            right = torch.cat((p[1:], torch.zeros_like(p[:1])))
            ap = 2 * p - left - right
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
