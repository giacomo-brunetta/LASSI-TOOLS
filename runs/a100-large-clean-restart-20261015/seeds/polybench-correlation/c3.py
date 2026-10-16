"""Export-friendly PolyBench correlation candidate using batched dot products."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET input from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    if fixture is not None:
        raise ValueError('correlation does not use an input fixture')
    n, m = (1400, 1200)
    rows = torch.arange(n, device=device, dtype=dtype).reshape(n, 1)
    columns = torch.arange(m, device=device, dtype=dtype).reshape(1, m)
    data = rows * columns / m + rows
    return (data,)

class Correlation(torch.nn.Module):

    def forward(self, data):
        if data.ndim != 2:
            raise ValueError('data must have shape [n, m]')
        float_n = data.new_tensor(data.shape[0])
        mean = data.sum(dim=0) / float_n
        delta = data - mean
        variance = (delta * delta).sum(dim=0) / float_n
        computed_stddev = torch.sqrt(variance)
        stddev = torch.where(computed_stddev <= data.new_tensor(0.1), torch.ones_like(computed_stddev), computed_stddev)
        normalized = delta / (torch.sqrt(float_n) * stddev)
        columns = normalized.transpose(0, 1)
        m, n = columns.shape
        left = columns[:, None, :].expand(m, m, n).reshape(m * m, 1, n)
        right = columns[None, :, :].expand(m, m, n).reshape(m * m, n, 1)
        dots = torch.bmm(left, right).reshape(m, m)
        upper = torch.triu(dots, diagonal=1)
        corr = upper + upper.transpose(0, 1) + torch.diag_embed(torch.ones_like(mean))
        return corr.reshape(-1)

def make_model():
    return Correlation()
