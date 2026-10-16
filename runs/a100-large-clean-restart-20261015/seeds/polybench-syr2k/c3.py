import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_N = 1200
_M = 1000

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic PolyBench MINI_DATASET inputs."""
    if fixture is not None:
        raise ValueError('polybench-syr2k does not define input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    row_n = torch.arange(_N, device=device, dtype=torch.int64).unsqueeze(1)
    col_m = torch.arange(_M, device=device, dtype=torch.int64).unsqueeze(0)
    col_n = torch.arange(_N, device=device, dtype=torch.int64).unsqueeze(0)
    n_value = torch.tensor(_N, device=device, dtype=dtype)
    m_value = torch.tensor(_M, device=device, dtype=dtype)
    A = ((row_n * col_m + 1) % _N).to(dtype) / n_value
    B = ((row_n * col_m + 2) % _M).to(dtype) / m_value
    C = ((row_n * col_n + 3) % _N).to(dtype) / m_value
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, C, A, B)

class Syr2kModel(torch.nn.Module):

    def forward(self, alpha, beta, C, A, B):
        C_work = C.clone()
        first = A.unsqueeze(0) * alpha * B.unsqueeze(1)
        second = B.unsqueeze(0) * alpha * A.unsqueeze(1)
        contributions = (first + second).sum(dim=2)
        indices = torch.arange(C_work.shape[0], device=C_work.device)
        lower_mask = indices.unsqueeze(1) >= indices.unsqueeze(0)
        C_work = torch.where(lower_mask, C_work * beta + contributions, C_work)
        return C_work.reshape(-1)

def make_model():
    return Syr2kModel()
