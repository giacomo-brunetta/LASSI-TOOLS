"""Export-friendly PyTorch translation of PolyBench MVT (MINI_DATASET)."""
import torch
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the C `init_array` inputs for the selected dataset."""
    if fixture is not None:
        raise ValueError('polybench-mvt has no input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    n = 2000
    indices = torch.arange(n, device=device, dtype=torch.int64)
    matrix_indices = indices.unsqueeze(1) * indices.unsqueeze(0)
    x1 = (indices % n).to(dtype=dtype) / n
    x2 = ((indices + 1) % n).to(dtype=dtype) / n
    y_1 = ((indices + 3) % n).to(dtype=dtype) / n
    y_2 = ((indices + 4) % n).to(dtype=dtype) / n
    A = (matrix_indices % n).to(dtype=dtype) / n
    return (x1, x2, y_1, y_2, A)

class MVT(torch.nn.Module):
    """Compute the two MVT live-outs without mutating supplied inputs."""

    def forward(self, x1, x2, y_1, y_2, A):
        products1 = A * y_1.unsqueeze(0)
        sums1 = torch.sum(products1, dim=1)
        products2 = A * y_2.unsqueeze(1)
        sums2 = torch.sum(products2, dim=0)
        out1 = x1 + sums1
        out2 = x2 + sums2
        return (out1.reshape(-1), out2.reshape(-1))

def make_model():
    """Return the stateless MVT module."""
    return MVT()
