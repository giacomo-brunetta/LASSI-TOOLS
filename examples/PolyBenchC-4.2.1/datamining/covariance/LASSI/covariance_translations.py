import torch
from torch import nn


def polybench_init_data(n: int, m: int, *, device: torch.device | None = None) -> torch.Tensor:
    """Reproduce PolyBench init_array data[i][j] = (i*j)/m in float32."""
    i = torch.arange(n, dtype=torch.float32, device=device).unsqueeze(1)
    j = torch.arange(m, dtype=torch.float32, device=device).unsqueeze(0)
    return (i * j) / float(m)


class CovarianceMatmul(nn.Module):
    """Variant v1: center then GEMM: cov = (Xc^T @ Xc) / (n - 1)."""

    def forward(self, data: torch.Tensor) -> torch.Tensor:
        x = data.to(dtype=torch.float32)
        n = x.shape[0]
        mean = torch.mean(x, dim=0)
        centered = x - mean
        cov = torch.matmul(centered.transpose(0, 1), centered)
        return cov / (float(n) - 1.0)


class CovarianceMoment(nn.Module):
    """Variant v2: second-moment identity without explicit centered matrix.

    cov = (X^T X - n * (mean[:, None] @ mean[None, :])) / (n - 1)
    """

    def forward(self, data: torch.Tensor) -> torch.Tensor:
        x = data.to(dtype=torch.float32)
        n = x.shape[0]
        mean = torch.mean(x, dim=0)
        xtx = torch.matmul(x.transpose(0, 1), x)
        corr = float(n) * torch.matmul(mean.unsqueeze(1), mean.unsqueeze(0))
        cov = xtx - corr
        return cov / (float(n) - 1.0)


class CovarianceBatchedOuter(nn.Module):
    """Variant v3: batched outer accumulation via broadcast mul + reduction."""

    def forward(self, data: torch.Tensor) -> torch.Tensor:
        x = data.to(dtype=torch.float32)
        n = x.shape[0]
        mean = torch.mean(x, dim=0)
        centered = x - mean
        outer_terms = centered.unsqueeze(2) * centered.unsqueeze(1)
        cov = torch.sum(outer_terms, dim=0)
        return cov / (float(n) - 1.0)


def smoke_check() -> dict[str, float]:
    """Run tiny no-oracle consistency checks on two distinct input shapes."""
    variants = [CovarianceMatmul(), CovarianceMoment(), CovarianceBatchedOuter()]
    report: dict[str, float] = {}

    for n, m in [(32, 28), (100, 80)]:
        x = polybench_init_data(n, m)
        y = polybench_init_data(n, m) + 0.125
        outs_x = [v(x) for v in variants]
        outs_y = [v(y) for v in variants]

        max_pair_diff = torch.max(torch.abs(outs_x[0] - outs_x[1])).item()
        max_pair_diff = max(max_pair_diff, torch.max(torch.abs(outs_x[0] - outs_x[2])).item())
        max_pair_diff = max(max_pair_diff, torch.max(torch.abs(outs_x[1] - outs_x[2])).item())
        shift_effect = torch.max(torch.abs(outs_x[0] - outs_y[0])).item()

        report[f"n{n}_m{m}_variant_agreement_max_abs"] = float(max_pair_diff)
        report[f"n{n}_m{m}_shift_response_max_abs"] = float(shift_effect)

    return report


if __name__ == "__main__":
    print(smoke_check())
