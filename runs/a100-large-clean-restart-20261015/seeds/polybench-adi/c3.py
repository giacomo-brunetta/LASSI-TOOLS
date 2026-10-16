"""Dense-transfer/GEMM translation of PolyBench ADI (MINI profile)."""
import torch
from torch import nn
LASSI_PRECISION = {'storage': 'input dtype', 'operator': 'input dtype', 'accumulator': 'input dtype', 'output': 'input dtype'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Construct the deterministic MINI_DATASET input matrix from the C initializer."""
    if dataset not in ('default', 'large'):
        raise ValueError(f'unsupported dataset: {dataset!r}; only MINI_DATASET is staged')
    if fixture is not None:
        raise ValueError('polybench-adi has no input fixture')
    n = 1000
    i = torch.arange(n, device=device, dtype=dtype).reshape(n, 1)
    j = torch.arange(n, device=device, dtype=dtype).reshape(1, n)
    return ((i + float(n) - j) / float(n),)

class ADIDenseTransfer(nn.Module):
    """ADI with logarithmic Möbius scans and dense causal transfer matrices."""

    @staticmethod
    def _mobius_p(length, a, b, c):
        """Compute C's p[1:length+1] from p[0]=0 by a Hillis--Steele scan."""
        zero = torch.zeros_like(a)
        transitions = torch.stack((torch.stack((zero, -c)), torch.stack((a, b)))).expand(length, -1, -1)
        prefix = transitions
        offset = 1
        while offset < length:
            combined = torch.matmul(prefix[offset:], prefix[:-offset])
            prefix = torch.cat((prefix[:offset], combined), dim=0)
            offset *= 2
        state = torch.matmul(prefix, torch.stack((zero, torch.ones_like(a))))
        return state[:, 0] / state[:, 1]

    @staticmethod
    def _transfer(alpha):
        """Materialize F where F[k,r]=prod(alpha[r+1:k+1]) for r <= k."""
        length = alpha.shape[0]
        g = torch.cumprod(alpha, dim=0)
        lower = torch.tril(torch.ones((length, length), device=alpha.device, dtype=torch.bool))
        safe_denominator = torch.where(lower, g.reshape(1, length), torch.ones((1, length), device=alpha.device, dtype=alpha.dtype))
        ratios = g.reshape(length, 1) / safe_denominator
        transfer = torch.where(lower, ratios, torch.zeros_like(ratios))
        diagonal = torch.eye(length, device=alpha.device, dtype=torch.bool)
        return torch.where(diagonal, torch.ones_like(transfer), transfer)

    @classmethod
    def _solve_pass(cls, rhs, a, b, c):
        """Solve a pass with traversal position first and independent C lines second."""
        length = rhs.shape[0]
        p = cls._mobius_p(length, a, b, c)
        previous_p = torch.cat((torch.zeros_like(p[:1]), p[:-1]), dim=0)
        denominator = a * previous_p + b
        alpha = -a / denominator
        beta = rhs / denominator.reshape(length, 1)
        adjusted_beta = torch.cat((alpha[:1].reshape(1, 1) + beta[:1], beta[1:]), dim=0)
        q = torch.matmul(cls._transfer(alpha), adjusted_beta)
        reverse_p = torch.flip(p, dims=(0,))
        reverse_q = torch.flip(q, dims=(0,))
        reverse_adjusted_q = torch.cat((reverse_p[:1].reshape(1, 1) + reverse_q[:1], reverse_q[1:]), dim=0)
        solved_reversed = torch.matmul(cls._transfer(reverse_p), reverse_adjusted_q)
        return (p, q, torch.flip(solved_reversed, dims=(0,)))

    def forward(self, u0):
        u = u0.clone()
        n = u.shape[0]
        if u.ndim != 2 or u.shape[1] != n or n < 3:
            raise ValueError('u0 must be a square tensor with side length at least three')
        one = torch.ones((), device=u.device, dtype=u.dtype)
        n_scalar = torch.as_tensor(n, device=u.device, dtype=u.dtype)
        tsteps_scalar = torch.as_tensor(20, device=u.device, dtype=u.dtype)
        dx = one / n_scalar
        dy = one / n_scalar
        dt = one / tsteps_scalar
        mul1 = (one + one) * dt / (dx * dx)
        mul2 = one * dt / (dy * dy)
        a = -mul1 / (one + one)
        b = one + mul1
        c = a
        d = -mul2 / (one + one)
        e = one + mul2
        f = d
        for _ in range(500):
            column_rhs = -d * u[1:-1, :-2] + (one + (one + one) * d) * u[1:-1, 1:-1] - f * u[1:-1, 2:]
            _, _, column_interior = self._solve_pass(column_rhs, a, b, c)
            v = torch.cat((torch.ones((1, n - 2), device=u.device, dtype=u.dtype), column_interior, torch.ones((1, n - 2), device=u.device, dtype=u.dtype)), dim=0)
            row_rhs = -a * v[:-2, :] + (one + (one + one) * a) * v[1:-1, :] - c * v[2:, :]
            _, _, row_solved = self._solve_pass(row_rhs.transpose(0, 1), d, e, f)
            row_interior = row_solved.transpose(0, 1)
            updated_rows = torch.cat((torch.ones((n - 2, 1), device=u.device, dtype=u.dtype), row_interior, torch.ones((n - 2, 1), device=u.device, dtype=u.dtype)), dim=1)
            u = torch.cat((u[:1, :], updated_rows, u[-1:, :]), dim=0)
        return u.reshape(-1)

def make_model():
    return ADIDenseTransfer()
