"""Export-friendly PyTorch translation of PolyBench Durbin."""

import torch


LASSI_PRECISION = {
    "storage": "float16",
    "operator": "float32",
    "accumulator": "float32",
    "output": "float32",
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
        if r.dtype in (torch.float16, torch.bfloat16):
            r = r.to(torch.float32)
        n = r.shape[0]
        y = torch.cat((-r[:1], torch.zeros_like(r[1:])))
        alpha = -r[0]
        beta = r.new_ones(())

        # The fixed-shape PolyBench kernel is statically unrolled instead of
        # lowering its dependent recurrences through nested higher-order loops.
        for k in range(1, n):
            beta = (1 - alpha * alpha) * beta
            total = r.new_zeros(())
            for i in range(k):
                total = total + r[k - i - 1] * y[i]
            alpha = -(r[k] + total) / beta
            reverse_indices = torch.arange(
                k - 1, -1, -1, dtype=torch.int64, device=r.device
            )
            prefix = y[:k] + alpha * y.gather(0, reverse_indices)
            y = torch.cat((prefix, alpha.reshape(1), y[k + 1 :]))
        return y.reshape(-1)


def make_model():
    return Durbin()
