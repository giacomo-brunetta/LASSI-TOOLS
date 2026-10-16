import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic PolyBench GESUMMV MINI inputs."""
    if fixture is not None:
        raise ValueError('gesummv does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile (N=30) is supported')
    n = 1300
    indices = torch.arange(n, device=device, dtype=torch.int64)
    i = indices.reshape(n, 1)
    j = indices.reshape(1, n)
    a_numerators = (i * j + 1) % n
    b_numerators = (i * j + 2) % n
    a = a_numerators.to(dtype=dtype) / n
    b = b_numerators.to(dtype=dtype) / n
    x = (indices % n).to(dtype=dtype) / n
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, a, b, x)

class Gesummv(torch.nn.Module):

    def forward(self, alpha, beta, a, b, x):
        matrices = torch.stack((a, b), dim=0)
        x_batched = x.reshape(1, x.shape[0], 1)
        products = torch.matmul(matrices, x_batched).squeeze(-1)
        y = alpha * products[0] + beta * products[1]
        return y.reshape(-1)

def make_model():
    return Gesummv()
