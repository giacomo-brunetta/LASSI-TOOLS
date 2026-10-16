import torch


LASSI_PRECISION = {
    "storage": "float64",
    "operator": "float32",
    "accumulator": "float32",
    "output": "float64",
}


_MINI_W = 64
_MINI_H = 64


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Construct the source's MINI_DATASET input image and scalar alpha."""
    if fixture is not None:
        raise ValueError("polybench-deriche does not define an input fixture")
    if dataset not in ("default", "mini"):
        raise ValueError("only the MINI_DATASET profile is available")
    rows = torch.arange(_MINI_W, device=device, dtype=torch.int64).reshape(_MINI_W, 1)
    cols = torch.arange(_MINI_H, device=device, dtype=torch.int64).reshape(1, _MINI_H)
    img_in = ((313 * rows + 991 * cols) % 65536).to(torch.float32)
    img_in = (img_in / torch.tensor(65535.0, device=device, dtype=torch.float32)).to(dtype)
    alpha = torch.tensor(0.25, device=device, dtype=torch.float32).to(dtype)
    return (img_in, alpha)


def _forward_pass(lines, a1, a2, b1, b2):
    """C-order causal recurrence, vectorized across all independent lines."""
    count, length = lines.shape
    zero = torch.zeros(count, device=lines.device, dtype=lines.dtype)
    xm1 = zero
    ym1 = zero
    ym2 = zero
    values = []
    for position in range(length):
        value = a1 * lines[:, position] + a2 * xm1 + b1 * ym1 + b2 * ym2
        values.append(value)
        xm1 = lines[:, position]
        ym2 = ym1
        ym1 = value
    return torch.stack(values, dim=1)


def _reverse_pass(lines, a3, a4, b1, b2):
    """C-order anti-causal recurrence, vectorized across all independent lines."""
    count, length = lines.shape
    zero = torch.zeros(count, device=lines.device, dtype=lines.dtype)
    xp1 = zero
    xp2 = zero
    yp1 = zero
    yp2 = zero
    values = []
    for position in range(length - 1, -1, -1):
        value = a3 * xp1 + a4 * xp2 + b1 * yp1 + b2 * yp2
        values.append(value)
        xp2 = xp1
        xp1 = lines[:, position]
        yp2 = yp1
        yp1 = value
    return torch.stack(tuple(reversed(values)), dim=1)


class Deriche(torch.nn.Module):
    def forward(self, img_in, alpha):
        if img_in.ndim != 2:
            raise ValueError("img_in must be a rank-2 W-by-H tensor")
        if alpha.numel() != 1:
            raise ValueError("alpha must contain exactly one scalar")

        # deriche.h defaults DATA_TYPE to float.  Keep all source scalar
        # operations in float32, then restore the caller's requested storage type.
        output_dtype = img_in.dtype
        img = img_in.to(torch.float32)
        alpha32 = alpha.to(torch.float32)
        one = torch.ones((), device=img.device, dtype=torch.float32)
        two = torch.tensor(2.0, device=img.device, dtype=torch.float32)
        exp_neg_alpha = torch.exp(-alpha32)
        k = ((one - exp_neg_alpha) * (one - exp_neg_alpha)) / (
            one + two * alpha32 * exp_neg_alpha - torch.exp(two * alpha32)
        )
        a1 = k
        a2 = k * torch.exp(-alpha32) * (alpha32 - one)
        a3 = k * torch.exp(-alpha32) * (alpha32 + one)
        a4 = -k * torch.exp(-two * alpha32)
        b1 = torch.pow(two, -alpha32)
        b2 = -torch.exp(-two * alpha32)

        horizontal = _forward_pass(img, a1, a2, b1, b2) + _reverse_pass(img, a3, a4, b1, b2)
        vertical_lines = horizontal.transpose(0, 1)
        img_out = (
            _forward_pass(vertical_lines, a1, a2, b1, b2)
            + _reverse_pass(vertical_lines, a3, a4, b1, b2)
        ).transpose(0, 1)
        return img_out.to(output_dtype).reshape(-1)


def make_model():
    return Deriche()
