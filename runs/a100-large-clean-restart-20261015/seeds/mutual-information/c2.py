"""Export-friendly PyTorch translation of the MINI mutual-information kernel."""
import torch
LASSI_PRECISION = {'storage': 'input dtype (FP64 for CPU reference validation)', 'operator': 'input dtype', 'accumulator': 'input dtype reduction accumulator', 'output': 'input dtype'}
_MINI_N = 256

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic C MINI joint-probability matrix."""
    if fixture is not None:
        raise ValueError('mutual-information does not define an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is available')
    n = _MINI_N
    independent = 0.5 / (n * n)
    diagonal = 0.5 / n
    joint = torch.full((n, n), independent, device=device, dtype=dtype)
    joint = joint + torch.eye(n, device=device, dtype=dtype) * diagonal
    return (joint,)

def _xlogx(values):
    """Compute x * log(x), retaining the C zero-guard semantics."""
    return torch.where(values > 0, values * torch.log(values), torch.zeros_like(values))

class MutualInformation(torch.nn.Module):

    def forward(self, joint):
        marginal_x = joint.sum(dim=1)
        marginal_y = joint.sum(dim=0)
        mi_nats = _xlogx(joint).sum() - _xlogx(marginal_x).sum() - _xlogx(marginal_y).sum()
        log_two = torch.log(torch.tensor(2.0, device=joint.device, dtype=joint.dtype))
        return (mi_nats / log_two).reshape(-1)

def make_model():
    return MutualInformation()
