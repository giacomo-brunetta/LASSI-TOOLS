"""ADI (Alternating Direction Implicit) kernel translated from PolyBench/C reference.

Implements the algorithm using the Thomas tridiagonal solve exactly as the reference C code.
All calculations are performed in FP64 to match the oracle.
"""

import torch
from torch import nn


def build_inputs(device: str = "cpu", dtype: torch.dtype = torch.float64, fixture=None, dataset: str = "mini"):
    """Create the deterministic input tensor `u`.

    Reference `init_array` sets u[i, j] = (i + n - j) / n for i,j = 0..n-1.
    """
    n = 20 if dataset.lower() == "mini" else 20
    i = torch.arange(n, dtype=dtype, device=device).unsqueeze(1)
    j = torch.arange(n, dtype=dtype, device=device).unsqueeze(0)
    u = (i + n - j) / n
    return (u,)


class ADIModel(nn.Module):
    def __init__(self, n: int, tsteps: int, dtype: torch.dtype = torch.float64):
        super().__init__()
        self.n = n
        self.tsteps = tsteps
        self.dtype = dtype
        # coefficients (identical to C reference)
        DX = 1.0 / n
        DY = 1.0 / n
        DT = 1.0 / tsteps
        B1 = 2.0
        B2 = 1.0
        mul1 = B1 * DT / (DX * DX)
        mul2 = B2 * DT / (DY * DY)
        a = -mul1 / 2.0
        b = 1.0 + mul1
        c = a
        d = -mul2 / 2.0
        e = 1.0 + mul2
        f = d
        # store as buffers (move with module/device)
        self.register_buffer("a", torch.tensor(a, dtype=dtype))
        self.register_buffer("b", torch.tensor(b, dtype=dtype))
        self.register_buffer("c", torch.tensor(c, dtype=dtype))
        self.register_buffer("d", torch.tensor(d, dtype=dtype))
        self.register_buffer("e", torch.tensor(e, dtype=dtype))
        self.register_buffer("f", torch.tensor(f, dtype=dtype))

    def forward(self, u: torch.Tensor):
        u = u.to(dtype=self.dtype)
        n = self.n
        a, b, c = self.a, self.b, self.c
        d, e, f = self.d, self.e, self.f
        device = u.device
        # temporary tensors for the Thomas algorithm recurrences
        p = torch.empty((n, n), dtype=self.dtype, device=device)
        q = torch.empty((n, n), dtype=self.dtype, device=device)
        v = torch.empty_like(u)
        for _ in range(self.tsteps):
            # ---------- Column sweep ----------
            for i in range(1, n - 1):
                v[0, i] = 1.0
                v[-1, i] = 1.0
                # forward recurrence for p and q along rows (j)
                p[i, 0] = 0.0
                q[i, 0] = v[0, i]
                for j in range(1, n - 1):
                    p[i, j] = -c / (a * p[i, j - 1] + b)
                    q[i, j] = (
                        -d * u[j, i - 1]
                        + (1.0 + 2.0 * d) * u[j, i]
                        - f * u[j, i + 1]
                        - a * q[i, j - 1]
                    ) / (a * p[i, j - 1] + b)
                # backward substitution (Thomas algorithm)
                # v[n-1,i] already set to 1.0 (Dirichlet)
                for j in range(n - 2, 0, -1):
                    v[j, i] = p[i, j] * v[j + 1, i] + q[i, j]
            # ---------- Row sweep ----------
            for i in range(1, n - 1):
                u[i, 0] = 1.0
                u[i, -1] = 1.0
                # forward recurrence for p and q along columns (j)
                p[i, 0] = 0.0
                q[i, 0] = u[i, 0]
                for j in range(1, n - 1):
                    p[i, j] = -f / (d * p[i, j - 1] + e)
                    q[i, j] = (
                        -a * v[i - 1, j]
                        + (1.0 + 2.0 * a) * v[i, j]
                        - c * v[i + 1, j]
                        - d * q[i, j - 1]
                    ) / (d * p[i, j - 1] + e)
                # backward substitution for row sweep
                for j in range(n - 2, 0, -1):
                    u[i, j] = p[i, j] * u[i, j + 1] + q[i, j]
        return u


def make_model():
    return ADIModel(n=20, tsteps=20, dtype=torch.float64)

# Precision contract
LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float64",
    "accumulator": "float64",
    "output": "float64",
}
