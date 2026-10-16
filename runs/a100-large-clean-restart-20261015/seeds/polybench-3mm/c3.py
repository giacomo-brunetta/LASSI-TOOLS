"""Export-friendly eight-row-batched implementation of PolyBench 3mm."""
import torch
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype (torch.bmm)', 'output': 'input dtype'}
_BLOCK_ROWS = 8
_MINI_SHAPE = (800, 900, 1000, 1100, 1200)

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('polybench-3mm does not use an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is available')
    ni, nj, nk, nl, nm = _MINI_SHAPE
    i_a = torch.arange(ni, device=device, dtype=torch.int64).reshape(ni, 1)
    j_a = torch.arange(nk, device=device, dtype=torch.int64).reshape(1, nk)
    a = ((i_a * j_a + 1) % ni).to(dtype) / (5 * ni)
    i_b = torch.arange(nk, device=device, dtype=torch.int64).reshape(nk, 1)
    j_b = torch.arange(nj, device=device, dtype=torch.int64).reshape(1, nj)
    b = ((i_b * (j_b + 1) + 2) % nj).to(dtype) / (5 * nj)
    i_c = torch.arange(nj, device=device, dtype=torch.int64).reshape(nj, 1)
    j_c = torch.arange(nm, device=device, dtype=torch.int64).reshape(1, nm)
    c = (i_c * (j_c + 3) % nl).to(dtype) / (5 * nl)
    i_d = torch.arange(nm, device=device, dtype=torch.int64).reshape(nm, 1)
    j_d = torch.arange(nl, device=device, dtype=torch.int64).reshape(1, nl)
    d = ((i_d * (j_d + 2) + 2) % nk).to(dtype) / (5 * nk)
    return (a, b, c, d)

def block8_mm(x, y):
    """Multiply rank-2 matrices using an explicit batch axis of eight rows."""
    rows = x.shape[0]
    inner = x.shape[1]
    if x.ndim != 2 or y.ndim != 2 or y.shape[0] != inner:
        raise ValueError('expected conformable rank-2 matrices')
    pad_rows = -rows % _BLOCK_ROWS
    if pad_rows:
        padding = torch.zeros((pad_rows, inner), dtype=x.dtype, device=x.device)
        x_padded = torch.cat((x, padding), dim=0)
    else:
        x_padded = x
    num_blocks = x_padded.shape[0] // _BLOCK_ROWS
    x_blocks = x_padded.reshape(num_blocks, _BLOCK_ROWS, inner)
    y_batched = y.unsqueeze(0).expand(num_blocks, y.shape[0], y.shape[1])
    result = torch.bmm(x_blocks, y_batched).reshape(x_padded.shape[0], y.shape[1])
    return result[:rows, :]

class ThreeMM(torch.nn.Module):

    def forward(self, a, b, c, d):
        e = block8_mm(a, b)
        f = block8_mm(c, d)
        g = block8_mm(e, f)
        return g.reshape(-1)

def make_model():
    return ThreeMM()
