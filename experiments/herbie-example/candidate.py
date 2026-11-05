"""Synthetic cancellation example for adapter development, not a C-qualified kernel."""

import torch


class Difference(torch.nn.Module):
    def forward(self, x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        return (x * x - y * y) / (x - y)


def make_model() -> torch.nn.Module:
    return Difference()
