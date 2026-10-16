"""Export-friendly PyTorch translation of PolyBench Durbin."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the reference initializer input for the MINI profile."""
    if fixture is not None:
        raise ValueError('polybench-durbin does not define input fixtures')
    if dataset not in {'default', 'large'}:
        raise ValueError(f'unsupported dataset: {dataset}')
    n = 2000
    r = (n + 1 - torch.arange(n, device=device, dtype=torch.long)).to(dtype)
    return (r,)

class Durbin(torch.nn.Module):

    def forward(self, r):
        n = r.shape[0]
        position = torch.arange(n, device=r.device, dtype=torch.long)
        y = torch.where(position == 0, -r[0], torch.zeros_like(r))
        alpha = -r[0]
        beta = torch.ones((), device=r.device, dtype=r.dtype)
        for k in range(1, n):
            beta = (1 - alpha * alpha) * beta
            source_index = (k - 1 - position).clamp(0, n - 1)
            y_rev = torch.flip(y, dims=(0,))
            reverse_index = n - 1 - source_index
            gathered_old_y = torch.gather(y_rev, 0, reverse_index)
            gathered_r = torch.gather(r, 0, source_index)
            prefix = position < k
            products = torch.where(prefix, gathered_r * y, torch.zeros_like(y))
            sum_value = torch.cumsum(products, dim=0)[k - 1]
            alpha = -(r[k] + sum_value) / beta
            candidate = y + alpha * gathered_old_y
            y = torch.where(position < k, candidate, torch.where(position == k, alpha.expand_as(y), y))
        return y.reshape(-1)

def make_model():
    return Durbin()
