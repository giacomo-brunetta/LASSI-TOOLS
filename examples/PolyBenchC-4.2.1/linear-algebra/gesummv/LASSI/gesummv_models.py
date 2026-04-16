import torch


def polybench_init(n: int, dtype: torch.dtype = torch.float32):
    idx = torch.arange(n, dtype=torch.int64)
    i = idx.unsqueeze(1)
    j = idx.unsqueeze(0)

    x = (idx % n).to(dtype) / float(n)
    a = ((i * j + 1) % n).to(dtype) / float(n)
    b = ((i * j + 2) % n).to(dtype) / float(n)

    alpha = torch.tensor(1.5, dtype=dtype)
    beta = torch.tensor(1.2, dtype=dtype)
    return alpha, beta, a, b, x


def gesummv_oracle(alpha: torch.Tensor, beta: torch.Tensor, a: torch.Tensor, b: torch.Tensor, x: torch.Tensor):
    tmp = torch.mv(a, x)
    yb = torch.mv(b, x)
    return alpha * tmp + beta * yb


class _GesummvBase(torch.nn.Module):
    def __init__(self, alpha: float = 1.5, beta: float = 1.2):
        super().__init__()
        self.register_buffer("alpha", torch.tensor(alpha, dtype=torch.float32))
        self.register_buffer("beta", torch.tensor(beta, dtype=torch.float32))


class GesummvMv(_GesummvBase):
    def forward(self, a: torch.Tensor, b: torch.Tensor, x: torch.Tensor):
        tmp = torch.mv(a, x)
        yb = torch.mv(b, x)
        return self.alpha * tmp + self.beta * yb


class GesummvMatmul(_GesummvBase):
    def forward(self, a: torch.Tensor, b: torch.Tensor, x: torch.Tensor):
        x2 = x.unsqueeze(1)
        tmp = torch.matmul(a, x2).squeeze(1)
        yb = torch.matmul(b, x2).squeeze(1)
        return self.alpha * tmp + self.beta * yb


class GesummvEinsum(_GesummvBase):
    def forward(self, a: torch.Tensor, b: torch.Tensor, x: torch.Tensor):
        tmp = torch.einsum("ij,j->i", a, x)
        yb = torch.einsum("ij,j->i", b, x)
        return self.alpha * tmp + self.beta * yb
