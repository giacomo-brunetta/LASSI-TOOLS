import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}
_M = 1000
_N = 1200

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic PolyBench MINI_DATASET inputs."""
    del fixture
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset profile: {dataset!r}')
    row = torch.arange(_M, device=device, dtype=torch.int64)
    col_a = torch.arange(_M, device=device, dtype=torch.int64)
    col_b = torch.arange(_N, device=device, dtype=torch.int64)
    lower = col_a.unsqueeze(0) < row.unsqueeze(1)
    diagonal = col_a.unsqueeze(0) == row.unsqueeze(1)
    a_values = torch.remainder(row.unsqueeze(1) + col_a.unsqueeze(0), _M)
    A = torch.where(lower, a_values, torch.zeros_like(a_values)).to(dtype) / _M
    A = torch.where(diagonal, torch.ones_like(A), A)
    b_values = torch.remainder(_N + row.unsqueeze(1) - col_b.unsqueeze(0), _N)
    B = b_values.to(dtype) / _N
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    return (alpha, A, B)

class TRMM(torch.nn.Module):

    def forward(self, alpha, A, B):
        m = A.shape[0]
        row = torch.arange(m, device=A.device)
        k = torch.arange(m, device=A.device)
        strict_lower = k.unsqueeze(0) > row.unsqueeze(1)
        terms = A.transpose(0, 1).unsqueeze(-1) * B.unsqueeze(0)
        terms = torch.where(strict_lower.unsqueeze(-1), terms, torch.zeros_like(terms))
        accumulated = torch.cumsum(terms, dim=1)
        result = alpha * (B + accumulated[:, m - 1, :])
        return result.reshape(-1)

def make_model():
    return TRMM()
