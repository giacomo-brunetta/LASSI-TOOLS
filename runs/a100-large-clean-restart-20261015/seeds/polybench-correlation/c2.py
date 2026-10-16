import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic PolyBench MINI correlation input."""
    if dataset not in {'default', 'large'}:
        raise ValueError(f'unsupported dataset profile: {dataset}')
    del fixture
    n, m = (1400, 1200)
    rows = torch.arange(n, device=device, dtype=dtype).unsqueeze(1)
    columns = torch.arange(m, device=device, dtype=dtype).unsqueeze(0)
    data = rows * columns / m + rows
    return (data,)

class Correlation(torch.nn.Module):

    def forward(self, data):
        float_n = data.new_tensor(data.shape[0])
        mean = data.sum(dim=0) / float_n
        delta = data - mean
        variance = (delta * delta).sum(dim=0) / float_n
        stddev = torch.sqrt(variance)
        stddev = torch.where(stddev <= 0.1, torch.ones_like(stddev), stddev)
        normalized = delta / (torch.sqrt(float_n) * stddev)
        columns = normalized.transpose(0, 1)
        products = columns[:, None, :] * columns[None, :, :]
        pair_sums = products.sum(dim=2)
        upper = torch.triu(pair_sums, diagonal=1)
        corr = upper + upper.transpose(0, 1) + torch.diag_embed(torch.ones_like(mean))
        return corr.reshape(-1)

def make_model():
    return Correlation()
