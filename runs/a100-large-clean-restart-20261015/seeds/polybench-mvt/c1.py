"""Export-friendly PyTorch translation of PolyBench MVT."""
import torch
LASSI_PRECISION = {'storage': 'requested dtype', 'operator': 'requested dtype', 'accumulator': 'requested dtype', 'output': 'requested dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build deterministic MVT inputs for the MINI_DATASET profile."""
    if fixture is not None:
        raise ValueError('PolyBench MVT does not use input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}')
    n = 2000
    idx = torch.arange(n, device=device, dtype=torch.int64)
    x1 = (idx % n).to(dtype) / n
    x2 = ((idx + 1) % n).to(dtype) / n
    y_1 = ((idx + 3) % n).to(dtype) / n
    y_2 = ((idx + 4) % n).to(dtype) / n
    A = (idx[:, None] * idx[None, :] % n).to(dtype) / n
    return (x1, x2, y_1, y_2, A)

class MVTModel(torch.nn.Module):
    """Compute the two independent matrix-vector updates without mutation."""

    def forward(self, x1, x2, y_1, y_2, A):
        x1_out = x1 + torch.matmul(A, y_1)
        x2_out = x2 + torch.matmul(A.transpose(0, 1), y_2)
        return (x1_out.reshape(-1), x2_out.reshape(-1))

def make_model():
    return MVTModel()
