import torch
from torch._higher_order_ops import scan
LASSI_PRECISION = {'storage': 'float32', 'operator': 'float32', 'accumulator': 'float32', 'output': 'float32'}

def build_inputs(device='cpu', dtype=torch.float64, fixture=None, dataset='default'):
    """Build the deterministic MINI_DATASET inputs from the C initializer."""
    if fixture is not None:
        raise ValueError('deriche does not use an input fixture')
    if dataset not in ('default', 'large'):
        raise ValueError('only the MINI_DATASET profile is supported')
    width = 4096
    height = 2160
    rows = torch.arange(width, device=device, dtype=torch.int64).reshape(width, 1)
    cols = torch.arange(height, device=device, dtype=torch.int64).reshape(1, height)
    pixels = (313 * rows + 991 * cols) % 65536
    img_in = pixels.to(dtype) / 65535.0
    alpha = torch.tensor(0.25, device=device, dtype=dtype)
    return (img_in, alpha)

class Deriche(torch.nn.Module):

    @staticmethod
    def _passes(lines, a1, a2, a3, a4, b1, b2):
        """Run the C-ordered paired recurrences over all lines in parallel."""
        count, length = lines.shape
        coefficients = torch.stack((a1, a2, a3, a4, b1, b2)).reshape(1, 6)
        coefficients = coefficients.expand(length, 6)
        zero = torch.zeros(count, device=lines.device, dtype=lines.dtype)

        def forward_step(carry, item):
            previous_x, previous_y1, previous_y2 = carry
            current_x, coeff = item
            current_y = coeff[0] * current_x
            current_y = current_y + coeff[1] * previous_x
            current_y = current_y + coeff[4] * previous_y1
            current_y = current_y + coeff[5] * previous_y2
            return ((current_x.clone(), current_y.clone(), previous_y1.clone()), current_y.clone())
        _, forward = scan(forward_step, (zero, zero, zero), (lines.transpose(0, 1), coefficients), dim=0)

        def reverse_step(carry, item):
            previous_x1, previous_x2, previous_y1, previous_y2 = carry
            current_x, coeff = item
            current_y = coeff[2] * previous_x1
            current_y = current_y + coeff[3] * previous_x2
            current_y = current_y + coeff[4] * previous_y1
            current_y = current_y + coeff[5] * previous_y2
            return ((current_x.clone(), previous_x1.clone(), current_y.clone(), previous_y1.clone()), current_y.clone())
        _, reverse = scan(reverse_step, (zero, zero, zero, zero), (lines.transpose(0, 1), coefficients), dim=0, reverse=True)
        return (forward + reverse).transpose(0, 1)

    def forward(self, img_in, alpha):
        if img_in.ndim != 2:
            raise ValueError('img_in must have shape (W, H)')
        if not img_in.is_floating_point() or not alpha.is_floating_point():
            raise TypeError('img_in and alpha must be floating-point tensors')
        if img_in.device != alpha.device:
            raise ValueError('img_in and alpha must share a device')
        lines = img_in.to(torch.float32)
        alpha = alpha.to(dtype=torch.float32)
        exp_neg_alpha = torch.exp(-alpha)
        one = alpha.new_tensor(1.0)
        two = one + one
        k = (one - exp_neg_alpha) * (one - exp_neg_alpha) / (one + two * alpha * exp_neg_alpha - torch.exp(two * alpha))
        a1 = k
        a2 = k * exp_neg_alpha * (alpha - one)
        a3 = k * exp_neg_alpha * (alpha + one)
        a4 = -k * torch.exp(-two * alpha)
        b1 = torch.pow(two, -alpha)
        b2 = -torch.exp(-two * alpha)
        horizontal = self._passes(lines, a1, a2, a3, a4, b1, b2)
        vertical = self._passes(horizontal.transpose(0, 1), a1, a2, a3, a4, b1, b2)
        return vertical.transpose(0, 1).reshape(-1)

def make_model():
    return Deriche()
