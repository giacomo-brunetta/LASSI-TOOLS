"""Static 256x256 Shannon mutual-information kernel for GroqFlow."""

from __future__ import annotations

import math

import torch
from torch import nn

MATRIX_SIZE = 256
NATS_TO_BITS = 1.0 / math.log(2.0)


class MutualInformation(nn.Module):
    """Compute ``I(X; Y)`` in bits from a normalized joint distribution.

    The input must be a nonnegative 256x256 matrix whose entries sum to one.
    Rows index values of X and columns index values of Y.
    """

    def forward(self, joint: torch.Tensor) -> torch.Tensor:
        marginal_x = torch.sum(joint, dim=1).unsqueeze(1)
        marginal_y = torch.sum(joint, dim=0).unsqueeze(0)

        # Shannon defines 0 * log(0 / q) as zero. Substituting one only at
        # zero-valued log arguments realizes that convention without log(0).
        # ``p + 1`` also avoids aten.ones_like, which GroqFlow rejects.
        safe_joint = torch.where(joint > 0.0, joint, joint + 1.0)
        safe_x = torch.where(marginal_x > 0.0, marginal_x, marginal_x + 1.0)
        safe_y = torch.where(marginal_y > 0.0, marginal_y, marginal_y + 1.0)

        pointwise_nats = torch.log(safe_joint) - torch.log(safe_x) - torch.log(safe_y)
        return torch.sum(joint * pointwise_nats) * NATS_TO_BITS


def make_model() -> nn.Module:
    """Return the inference-only kernel module."""
    return MutualInformation().eval()


def build_inputs(
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.float32,
) -> tuple[torch.Tensor]:
    """Build a diagonal distribution with the exact reference MI of 8 bits."""
    joint = torch.eye(MATRIX_SIZE, device=device, dtype=dtype) / MATRIX_SIZE
    return (joint.contiguous(),)
