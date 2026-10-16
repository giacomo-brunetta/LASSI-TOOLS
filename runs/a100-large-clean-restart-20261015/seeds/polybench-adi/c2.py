"""Export-friendly PyTorch translation of PolyBench ADI (MINI profile)."""
import torch
LASSI_PRECISION = {'storage': 'float64', 'operator': 'float64', 'accumulator': 'float64', 'output': 'float64'}
_MINI_N = 1000
_TSTEPS = 500

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the sole deterministic input, C's initialized ``u`` array."""
    if fixture is not None:
        raise ValueError('ADI does not accept an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    indices = torch.arange(_MINI_N, device=device, dtype=dtype)
    rows = indices[:, None]
    columns = indices[None, :]
    u = (rows + _MINI_N - columns) / _MINI_N
    return (u,)

def _mobius_p(length, numerator, lower_left, lower_right, *, device, dtype):
    """Return p[1:] from a fresh-stage inclusive Möbius matrix scan."""
    zero = torch.zeros((), device=device, dtype=dtype)
    matrix = torch.stack((torch.stack((zero, numerator)), torch.stack((lower_left, lower_right))))
    prefix = matrix.unsqueeze(0).expand(length, -1, -1)
    offset = 1
    while offset < length:
        previous = prefix
        prefix = torch.cat((previous[:offset], previous[offset:] @ previous[:-offset]), dim=0)
        offset *= 2
    return prefix[:, 0, 1] / prefix[:, 1, 1]

def _lower_bidiagonal(subdiagonal, *, device, dtype):
    length = subdiagonal.numel() + 1
    identity = torch.eye(length, device=device, dtype=dtype)
    return identity + torch.diag(subdiagonal, diagonal=-1)

def _solve_sweep(source, p, previous_p, a, b, c, d, e, f):
    """Perform one source-ordered ADI sweep using triangular recurrences."""
    length = source.shape[0] - 2
    one = torch.ones((), device=source.device, dtype=source.dtype)
    rhs = -d * source[1:-1, :-2] + (one + one * d + d) * source[1:-1, 1:-1] - f * source[1:-1, 2:]
    denominator = a * previous_p + b
    alpha = -a / denominator
    beta = rhs / denominator[:, None]
    forward_rhs = torch.cat(((alpha[0] * one + beta[0]).unsqueeze(0), beta[1:]), dim=0)
    forward_matrix = _lower_bidiagonal(-alpha[1:], device=source.device, dtype=source.dtype)
    q = torch.linalg.solve_triangular(forward_matrix, forward_rhs, upper=False)
    reverse_p = torch.flip(p, dims=(0,))
    reverse_q = torch.flip(q, dims=(0,))
    reverse_rhs = torch.cat(((reverse_p[0] * one + reverse_q[0]).unsqueeze(0), reverse_q[1:]), dim=0)
    reverse_matrix = _lower_bidiagonal(-reverse_p[1:], device=source.device, dtype=source.dtype)
    reverse = torch.linalg.solve_triangular(reverse_matrix, reverse_rhs, upper=False)
    return torch.flip(reverse, dims=(0,))

class ADI(torch.nn.Module):

    def forward(self, u0):
        if u0.ndim != 2 or u0.shape[0] != u0.shape[1] or u0.shape[0] < 3:
            raise ValueError('u0 must be a square rank-2 tensor with n >= 3')
        u = u0.clone()
        n = u.shape[0]
        length = n - 2
        one = torch.ones((), device=u.device, dtype=u.dtype)
        n_value = torch.as_tensor(n, device=u.device, dtype=u.dtype)
        steps = torch.as_tensor(_TSTEPS, device=u.device, dtype=u.dtype)
        dx = one / n_value
        dy = one / n_value
        dt = one / steps
        mul1 = (one + one) * dt / (dx * dx)
        mul2 = one * dt / (dy * dy)
        a = -mul1 / (one + one)
        b = one + mul1
        c = a
        d = -mul2 / (one + one)
        e = one + mul2
        f = d
        column_p = _mobius_p(length, -c, a, b, device=u.device, dtype=u.dtype)
        row_p = _mobius_p(length, -f, d, e, device=u.device, dtype=u.dtype)
        zero = torch.zeros(1, device=u.device, dtype=u.dtype)
        column_previous_p = torch.cat((zero, column_p[:-1]), dim=0)
        row_previous_p = torch.cat((zero, row_p[:-1]), dim=0)
        for _ in range(_TSTEPS):
            column_interior = _solve_sweep(u, column_p, column_previous_p, a, b, c, d, e, f)
            v_middle = torch.cat((torch.ones((length, 1), device=u.device, dtype=u.dtype), column_interior, torch.ones((length, 1), device=u.device, dtype=u.dtype)), dim=1)
            v = torch.cat((torch.ones((1, n), device=u.device, dtype=u.dtype), v_middle, torch.ones((1, n), device=u.device, dtype=u.dtype)), dim=0)
            row_interior_by_row = _solve_sweep(v.transpose(0, 1), row_p, row_previous_p, d, e, f, a, b, c).transpose(0, 1)
            u_middle = torch.cat((torch.ones((length, 1), device=u.device, dtype=u.dtype), row_interior_by_row, torch.ones((length, 1), device=u.device, dtype=u.dtype)), dim=1)
            u = torch.cat((u[:1], u_middle, u[-1:]), dim=0)
        return u.reshape(-1)

def make_model():
    return ADI()
