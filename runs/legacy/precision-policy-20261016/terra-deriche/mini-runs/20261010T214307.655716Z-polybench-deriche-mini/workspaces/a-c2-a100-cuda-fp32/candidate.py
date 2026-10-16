import torch


# The unconfigured PolyBench Deriche header selects DATA_TYPE_IS_FLOAT.
LASSI_PRECISION = {
    "storage": "float32",
    "operator": "float32",
    "accumulator": "float32",
    "output": "float32",
}


def build_inputs(device="cpu", dtype=torch.float64, fixture=None, dataset="default"):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError("deriche does not use an input fixture")
    if dataset not in ("default", "mini"):
        raise ValueError("only the MINI_DATASET profile is supported")

    width = 64
    height = 64
    rows = torch.arange(width, device=device, dtype=torch.int64).reshape(width, 1)
    cols = torch.arange(height, device=device, dtype=torch.int64).reshape(1, height)
    pixels = (313 * rows + 991 * cols) % 65536
    img_in = pixels.to(dtype) / 65535.0
    alpha = torch.tensor(0.25, device=device, dtype=dtype)
    return img_in, alpha


class Deriche(torch.nn.Module):
    @staticmethod
    def _passes(lines, a1, a2, a3, a4, b1, b2):
        """Run the C-ordered paired recurrences over all lines in parallel."""
        count, length = lines.shape
        zero = torch.zeros(count, device=lines.device, dtype=lines.dtype)

        previous_x = zero
        previous_y1 = zero
        previous_y2 = zero
        forward_values = []
        for index in range(length):
            current_x = lines[:, index]
            current_y = a1 * current_x
            current_y = current_y + a2 * previous_x
            current_y = current_y + b1 * previous_y1
            current_y = current_y + b2 * previous_y2
            forward_values.append(current_y)
            previous_x = current_x
            previous_y2 = previous_y1
            previous_y1 = current_y
        forward = torch.stack(forward_values, dim=1)

        previous_x1 = zero
        previous_x2 = zero
        previous_y1 = zero
        previous_y2 = zero
        reverse_values = []
        for index in range(length - 1, -1, -1):
            current_y = a3 * previous_x1
            current_y = current_y + a4 * previous_x2
            current_y = current_y + b1 * previous_y1
            current_y = current_y + b2 * previous_y2
            reverse_values.append(current_y)
            current_x = lines[:, index]
            previous_x2 = previous_x1
            previous_x1 = current_x
            previous_y2 = previous_y1
            previous_y1 = current_y
        reverse = torch.stack(reverse_values[::-1], dim=1)
        return forward + reverse

    def forward(self, img_in, alpha):
        if img_in.ndim != 2:
            raise ValueError("img_in must have shape (W, H)")
        if not img_in.is_floating_point() or not alpha.is_floating_point():
            raise TypeError("img_in and alpha must be floating-point tensors")
        if img_in.device != alpha.device:
            raise ValueError("img_in and alpha must share a device")

        # DATA_TYPE defaults to float in the authoritative header.  Preserve
        # every scalar state rounding from the C recurrence even if validation
        # supplies FP64 fixture tensors.
        lines = img_in.to(torch.float32)
        alpha = alpha.to(dtype=torch.float32)
        exp_neg_alpha = torch.exp(-alpha)
        one = torch.ones_like(alpha)
        two = one + one
        k = ((one - exp_neg_alpha) * (one - exp_neg_alpha)) / (
            one + two * alpha * exp_neg_alpha - torch.exp(two * alpha)
        )
        a1 = k
        a2 = k * exp_neg_alpha * (alpha - one)
        a3 = k * exp_neg_alpha * (alpha + one)
        a4 = -k * torch.exp(-two * alpha)
        b1 = torch.pow(two, -alpha)
        b2 = -torch.exp(-two * alpha)

        horizontal = self._passes(lines, a1, a2, a3, a4, b1, b2)
        vertical = self._passes(
            horizontal.transpose(0, 1), a1, a2, a3, a4, b1, b2
        )
        return vertical.transpose(0, 1).reshape(-1)


def make_model():
    return Deriche()
