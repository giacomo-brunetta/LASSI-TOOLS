import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic PolyBench GESUMMV MINI_DATASET inputs."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset}')
    n = 1300
    indices = torch.arange(n, device=device, dtype=torch.int64)
    i = indices[:, None]
    j = indices[None, :]
    a = ((i * j + 1) % n).to(dtype=dtype) / n
    b = ((i * j + 2) % n).to(dtype=dtype) / n
    x = (indices % n).to(dtype=dtype) / n
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, a, b, x)

class GESUMMV(torch.nn.Module):

    def forward(self, alpha, beta, a, b, x):
        tmp = torch.matmul(a, x)
        b_sum = torch.matmul(b, x)
        y = alpha * tmp + beta * b_sum
        return y.reshape(-1)

def make_model():
    return GESUMMV()
