"""Export-friendly PyTorch implementation of PolyBench SYR2K (MINI profile)."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'fp64', 'operator': 'fp64', 'accumulator': 'fp64', 'output': 'fp64'}
_MINI_N = 1200
_MINI_M = 1000

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build deterministic MINI_DATASET inputs using the C initializer."""
    if fixture is not None:
        raise ValueError('syr2k does not define input fixtures')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    indices_n = torch.arange(_MINI_N, device=device, dtype=torch.int64)
    indices_m = torch.arange(_MINI_M, device=device, dtype=torch.int64)
    i_nm = indices_n.unsqueeze(1)
    j_nm = indices_m.unsqueeze(0)
    i_nn = indices_n.unsqueeze(1)
    j_nn = indices_n.unsqueeze(0)
    A = ((i_nm * j_nm + 1) % _MINI_N).to(dtype=dtype) / _MINI_N
    B = ((i_nm * j_nm + 2) % _MINI_M).to(dtype=dtype) / _MINI_M
    C = ((i_nn * j_nn + 3) % _MINI_N).to(dtype=dtype) / _MINI_M
    alpha = torch.tensor(1.5, device=device, dtype=dtype)
    beta = torch.tensor(1.2, device=device, dtype=dtype)
    return (alpha, beta, C, A, B)

class Syr2k(nn.Module):

    def forward(self, alpha, beta, C, A, B):
        C_work = C.clone()
        left = torch.cat((A * alpha, B * alpha), dim=1)
        right = torch.cat((B, A), dim=1)
        rank2k = torch.matmul(left, right.transpose(0, 1))
        beta_scaled = C_work * beta
        row_indices = torch.arange(C_work.shape[0], device=C_work.device)
        col_indices = torch.arange(C_work.shape[1], device=C_work.device)
        lower_mask = col_indices.unsqueeze(0) <= row_indices.unsqueeze(1)
        result = torch.where(lower_mask, beta_scaled + rank2k, C_work)
        return result.reshape(-1)

def make_model():
    return Syr2k()
