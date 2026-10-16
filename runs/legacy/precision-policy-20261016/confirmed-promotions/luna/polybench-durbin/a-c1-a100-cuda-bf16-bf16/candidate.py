"""Export-friendly PyTorch translation of PolyBench Durbin."""

import torch


LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float64",
    "accumulator": "float64",
    "output": "float64",
}


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Construct the C initializer r[i] = n + 1 - i for MINI_DATASET."""
    del fixture
    if dataset not in ("default", "mini"):
        raise ValueError(f"unsupported dataset: {dataset!r}")
    n = 40
    r = (n + 1 - torch.arange(n, device=device)).to(dtype=dtype)
    return (r,)


class Durbin(torch.nn.Module):
    def forward(self, r):
        n = r.shape[0]
        # Keep the declared PolyBench FP64 operator/accumulator semantics when
        # the accelerator supplies a BF16 storage tensor.
        r = r.to(dtype=torch.float64)
        indices = torch.arange(n, dtype=torch.int64, device=r.device)
        y = torch.cat((-r[:1], torch.zeros_like(r[1:])))
        alpha = -r[0]
        beta = r.new_ones(())

        # The MINI_DATASET shape is static at the accelerator boundary. Unroll
        # only the loop regions; retain the original vectorized state update.
        for k in range(1, n):
            beta = (1 - alpha * alpha) * beta
            total = r.new_zeros(())
            for i in range(k):
                total = total + r[k - i - 1] * y[i]
            alpha = -(r[k] + total) / beta
            active = indices < k
            reverse_indices = (k - indices - 1).clamp(min=0)
            new_prefix = y + alpha * y.gather(0, reverse_indices)
            y = torch.where(active, new_prefix, y)
            y = torch.where(indices == k, alpha.expand_as(y), y)

        return y.reshape(-1)


def make_model():
    return Durbin()
