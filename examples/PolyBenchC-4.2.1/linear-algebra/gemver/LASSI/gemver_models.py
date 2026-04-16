import torch


def polybench_init(n: int, dtype: torch.dtype = torch.float32):
    idx = torch.arange(n, dtype=dtype)
    ii = torch.arange(n, dtype=torch.int64).unsqueeze(1)
    jj = torch.arange(n, dtype=torch.int64).unsqueeze(0)

    a = ((ii * jj) % n).to(dtype) / float(n)

    fn = float(n)
    u1 = idx
    u2 = ((idx + 1.0) / fn) / 2.0
    v1 = ((idx + 1.0) / fn) / 4.0
    v2 = ((idx + 1.0) / fn) / 6.0
    y = ((idx + 1.0) / fn) / 8.0
    z = ((idx + 1.0) / fn) / 9.0
    x = torch.zeros(n, dtype=dtype)
    w = torch.zeros(n, dtype=dtype)

    alpha = torch.tensor(1.5, dtype=dtype)
    beta = torch.tensor(1.2, dtype=dtype)
    return alpha, beta, a, u1, v1, u2, v2, w, x, y, z


def gemver_oracle(alpha, beta, a, u1, v1, u2, v2, w, x, y, z):
    a2 = a + torch.matmul(u1.unsqueeze(1), v1.unsqueeze(0)) + torch.matmul(u2.unsqueeze(1), v2.unsqueeze(0))
    x2 = x + beta * torch.mv(a2.t(), y) + z
    w2 = w + alpha * torch.mv(a2, x2)
    return w2


class _GemverBase(torch.nn.Module):
    def __init__(self, alpha: float = 1.5, beta: float = 1.2):
        super().__init__()
        self.register_buffer("alpha", torch.tensor(alpha, dtype=torch.float32))
        self.register_buffer("beta", torch.tensor(beta, dtype=torch.float32))


class GemverMatmul(torch.nn.Module):
    def __init__(self, alpha: float = 1.5, beta: float = 1.2):
        super().__init__()
        self.register_buffer("alpha", torch.tensor(alpha, dtype=torch.float32))
        self.register_buffer("beta", torch.tensor(beta, dtype=torch.float32))

    def forward(self, a, u1, v1, u2, v2, w, x, y, z):
        a2 = a + torch.matmul(u1.unsqueeze(1), v1.unsqueeze(0)) + torch.matmul(u2.unsqueeze(1), v2.unsqueeze(0))
        x2 = x + self.beta * torch.matmul(a2.t(), y.unsqueeze(1)).squeeze(1) + z
        w2 = w + self.alpha * torch.matmul(a2, x2.unsqueeze(1)).squeeze(1)
        return w2


class GemverAddmm(_GemverBase):
    def forward(self, a, u1, v1, u2, v2, w, x, y, z):
        a2 = torch.addmm(a, u1.unsqueeze(1), v1.unsqueeze(0), beta=1.0, alpha=1.0)
        a2 = torch.addmm(a2, u2.unsqueeze(1), v2.unsqueeze(0), beta=1.0, alpha=1.0)
        x2 = x + self.beta * torch.mv(a2.t(), y) + z
        w2 = w + self.alpha * torch.mv(a2, x2)
        return w2


class GemverBmm(_GemverBase):
    def forward(self, a, u1, v1, u2, v2, w, x, y, z):
        rank1 = torch.bmm(u1.unsqueeze(0).unsqueeze(2), v1.unsqueeze(0).unsqueeze(1)).squeeze(0)
        rank2 = torch.bmm(u2.unsqueeze(0).unsqueeze(2), v2.unsqueeze(0).unsqueeze(1)).squeeze(0)
        a2 = a + rank1 + rank2
        x2 = x + self.beta * torch.mv(a2.t(), y) + z
        w2 = w + self.alpha * torch.mv(a2, x2)
        return w2
