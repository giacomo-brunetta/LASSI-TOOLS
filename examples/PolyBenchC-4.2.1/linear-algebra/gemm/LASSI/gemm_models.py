import torch


def polybench_init(ni: int, nj: int, nk: int, dtype: torch.dtype = torch.float32):
    i_ni = torch.arange(ni, dtype=torch.int64).unsqueeze(1)
    j_nj = torch.arange(nj, dtype=torch.int64).unsqueeze(0)
    j_nk = torch.arange(nk, dtype=torch.int64).unsqueeze(0)
    i_nk = torch.arange(nk, dtype=torch.int64).unsqueeze(1)

    c_int = (i_ni * j_nj + 1) % ni
    a_int = (i_ni * (j_nk + 1)) % nk
    b_int = (i_nk * (j_nj + 2)) % nj

    c = c_int.to(dtype) / float(ni)
    a = a_int.to(dtype) / float(nk)
    b = b_int.to(dtype) / float(nj)

    alpha = torch.tensor(1.5, dtype=dtype)
    beta = torch.tensor(1.2, dtype=dtype)
    return alpha, beta, c, a, b


def gemm_oracle(alpha: torch.Tensor, beta: torch.Tensor, c: torch.Tensor, a: torch.Tensor, b: torch.Tensor):
    return beta * c + alpha * torch.matmul(a, b)


class _GemmBase(torch.nn.Module):
    def __init__(self, alpha: float = 1.5, beta: float = 1.2):
        super().__init__()
        self.register_buffer("alpha", torch.tensor(alpha, dtype=torch.float32))
        self.register_buffer("beta", torch.tensor(beta, dtype=torch.float32))


class GemmMatmul(_GemmBase):
    def forward(self, c: torch.Tensor, a: torch.Tensor, b: torch.Tensor):
        return self.beta * c + self.alpha * torch.matmul(a, b)


class GemmEinsum(_GemmBase):
    def forward(self, c: torch.Tensor, a: torch.Tensor, b: torch.Tensor):
        return self.beta * c + self.alpha * torch.einsum("ik,kj->ij", a, b)


class GemmBmm(_GemmBase):
    def forward(self, c: torch.Tensor, a: torch.Tensor, b: torch.Tensor):
        mm = torch.bmm(a.unsqueeze(0), b.unsqueeze(0)).squeeze(0)
        return self.beta * c + self.alpha * mm
