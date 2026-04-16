import torch
from torch import Tensor, nn


def init_array_float32(nr: int, nq: int, np_: int) -> tuple[Tensor, Tensor]:
    """PolyBench doitgen init_array semantics in float32.

    A[i, j, k] = ((i*j + k) % np) / np
    C4[i, j]   = ((i*j) % np) / np
    """
    i = torch.arange(nr, dtype=torch.int64).view(nr, 1, 1)
    j = torch.arange(nq, dtype=torch.int64).view(1, nq, 1)
    k = torch.arange(np_, dtype=torch.int64).view(1, 1, np_)
    A = ((i * j + k) % np_).to(dtype=torch.float32) / float(np_)

    p = torch.arange(np_, dtype=torch.int64).view(np_, 1)
    q = torch.arange(np_, dtype=torch.int64).view(1, np_)
    C4 = ((p * q) % np_).to(dtype=torch.float32) / float(np_)
    return A, C4


def doitgen_candidate_a_matmul_flatten(A: Tensor, C4: Tensor) -> Tensor:
    """Candidate A: rank-stable 3D matmul with broadcasted RHS [NP, NP]."""
    A_f32 = A.to(dtype=torch.float32)
    C4_f32 = C4.to(dtype=torch.float32)
    return torch.matmul(A_f32, C4_f32)


def doitgen_candidate_b_einsum(A: Tensor, C4: Tensor) -> Tensor:
    """Candidate B: explicit contraction notation matching C reduction index s."""
    A_f32 = A.to(dtype=torch.float32)
    C4_f32 = C4.to(dtype=torch.float32)
    return torch.einsum("rqs,sp->rqp", A_f32, C4_f32)


def doitgen_candidate_c_bmm_broadcast(A: Tensor, C4: Tensor) -> Tensor:
    """Candidate C: batched matrix multiply with broadcasted C4 per (r,q) slice."""
    A_f32 = A.to(dtype=torch.float32)
    C4_f32 = C4.to(dtype=torch.float32)
    nr, nq, np_ = A_f32.shape
    batch = nr * nq
    lhs = A_f32.reshape(batch, 1, np_)
    rhs = C4_f32.unsqueeze(0).expand(batch, np_, np_)
    out = torch.bmm(lhs, rhs)
    return out.reshape(nr, nq, np_)


def doitgen_candidate_d_loop_over_r(A: Tensor, C4: Tensor) -> Tensor:
    """Candidate D: transpose-associated rank-stable matmul variant.

    Equivalent to A @ C4, but expressed as (C4^T @ A^T_{q,s})^T to preserve candidate diversity
    while avoiding Python loops/indexed writes that caused lowering failures.
    """
    A_f32 = A.to(dtype=torch.float32)
    C4_f32 = C4.to(dtype=torch.float32)
    return torch.matmul(C4_f32.transpose(0, 1), A_f32.transpose(1, 2)).transpose(1, 2)


class DoitgenCandidateAModule(nn.Module):
    def forward(self, A: Tensor, C4: Tensor) -> Tensor:
        return doitgen_candidate_a_matmul_flatten(A, C4)


class DoitgenCandidateBModule(nn.Module):
    def forward(self, A: Tensor, C4: Tensor) -> Tensor:
        return doitgen_candidate_b_einsum(A, C4)


class DoitgenCandidateCModule(nn.Module):
    def forward(self, A: Tensor, C4: Tensor) -> Tensor:
        return doitgen_candidate_c_bmm_broadcast(A, C4)


class DoitgenCandidateDModule(nn.Module):
    def forward(self, A: Tensor, C4: Tensor) -> Tensor:
        return doitgen_candidate_d_loop_over_r(A, C4)


def smoke_check_two_inputs() -> dict[str, float]:
    """Basic sanity-only checks (not oracle verification).

    Returns max absolute deltas against candidate A baseline and cross-input delta.
    """
    results: dict[str, float] = {}

    A1, C41 = init_array_float32(4, 3, 5)
    A2, C42 = init_array_float32(5, 4, 6)

    base1 = doitgen_candidate_a_matmul_flatten(A1, C41)
    base2 = doitgen_candidate_a_matmul_flatten(A2, C42)

    for name, fn in {
        "candidate_b": doitgen_candidate_b_einsum,
        "candidate_c": doitgen_candidate_c_bmm_broadcast,
        "candidate_d": doitgen_candidate_d_loop_over_r,
    }.items():
        d1 = (fn(A1, C41) - base1).abs().max().item()
        d2 = (fn(A2, C42) - base2).abs().max().item()
        results[f"{name}_max_abs_delta_input1"] = float(d1)
        results[f"{name}_max_abs_delta_input2"] = float(d2)

    cross_input_change = (base1.mean() - base2.mean()).abs().item()
    results["candidate_a_cross_input_mean_change"] = float(cross_input_change)
    return results


if __name__ == "__main__":
    print(smoke_check_two_inputs())
