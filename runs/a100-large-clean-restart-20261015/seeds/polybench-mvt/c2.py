"""Export-friendly PyTorch translation of PolyBench/C MVT."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_DATASET_SIZES = {'default': 2000, 'large': 2000}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    del fixture
    try:
        n = _DATASET_SIZES[dataset]
    except KeyError as exc:
        raise ValueError(f'unsupported dataset: {dataset!r}') from exc
    indices = torch.arange(n, device=device, dtype=torch.int64)
    row_indices = indices.reshape(n, 1)
    col_indices = indices.reshape(1, n)
    x1_int = indices.remainder(n)
    x2_int = (indices + 1).remainder(n)
    y1_int = (indices + 3).remainder(n)
    y2_int = (indices + 4).remainder(n)
    a_int = (row_indices * col_indices).remainder(n)
    divisor = float(n)
    x1 = x1_int.to(dtype=dtype) / divisor
    x2 = x2_int.to(dtype=dtype) / divisor
    y_1 = y1_int.to(dtype=dtype) / divisor
    y_2 = y2_int.to(dtype=dtype) / divisor
    A = a_int.to(dtype=dtype) / divisor
    return (x1, x2, y_1, y_2, A)

class MVT(torch.nn.Module):

    def forward(self, x1, x2, y_1, y_2, A):
        row_sum = torch.einsum('ij,j->i', A, y_1)
        col_sum = torch.einsum('ji,j->i', A, y_2)
        out1 = x1 + row_sum
        out2 = x2 + col_sum
        return (out1.reshape(-1), out2.reshape(-1))

def make_model():
    return MVT()
