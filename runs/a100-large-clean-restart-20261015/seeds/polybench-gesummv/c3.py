"""Export-friendly PyTorch translation of PolyBench gesummv."""
import torch
LASSI_PRECISION = {'storage': 'requested', 'operator': 'requested', 'accumulator': 'requested', 'output': 'requested'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the MINI_DATASET inputs using the C initializer expressions."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f"unsupported dataset {dataset!r}; expected 'default' or 'mini'")
    n = 1300
    indices = torch.arange(n, device=device, dtype=torch.int64)
    products = indices.unsqueeze(1) * indices.unsqueeze(0)
    denominator = torch.tensor(n, device=device, dtype=dtype)
    x = indices.remainder(n).to(dtype) / denominator
    a = (products + 1).remainder(n).to(dtype) / denominator
    b = (products + 2).remainder(n).to(dtype) / denominator
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, a, b, x)

class Gesummv(torch.nn.Module):
    """Compute y = alpha * (A @ x) + beta * (B @ x) via row-wise scans."""

    def forward(self, alpha, beta, a, b, x):
        a_products = a * x.unsqueeze(0)
        b_products = b * x.unsqueeze(0)
        tmp = torch.cumsum(a_products, dim=1)[:, -1]
        b_sum = torch.cumsum(b_products, dim=1)[:, -1]
        y = alpha * tmp + beta * b_sum
        return y.reshape(-1)

def make_model():
    return Gesummv()
