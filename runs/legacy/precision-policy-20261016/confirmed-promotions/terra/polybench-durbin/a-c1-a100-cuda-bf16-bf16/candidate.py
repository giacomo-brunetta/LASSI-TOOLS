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
        r = r.to(dtype=torch.float64)
        n = r.shape[0]
        y = torch.cat((-r[:1], torch.zeros_like(r[1:])))
        alpha = -r[0]
        beta = r.new_ones(())

        for k in range(1, n):
            beta = (1 - alpha * alpha) * beta
            total = r.new_zeros(())
            for i in range(k):
                total = total + r[k - i - 1] * y[i]
            alpha = -(r[k] + total) / beta
            prefix = y[:k] + alpha * torch.flip(y[:k], dims=(0,))
            y = torch.cat((prefix, alpha.reshape(1), y[k + 1 :]))

        return y.reshape(-1)


def make_model():
    return Durbin()
