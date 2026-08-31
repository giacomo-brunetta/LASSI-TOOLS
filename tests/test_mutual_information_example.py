from __future__ import annotations

import runpy
from pathlib import Path
from typing import TYPE_CHECKING, cast

import torch
from torch import nn

if TYPE_CHECKING:
    from collections.abc import Callable

EXAMPLE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "mutual-information-groq"
    / "mutual_information.py"
)
MATRIX_SIZE = 256


def _make_model() -> nn.Module:
    namespace = runpy.run_path(str(EXAMPLE))
    factory = cast("Callable[[], nn.Module]", namespace["make_model"])
    return factory()


def _reference_mi(joint: torch.Tensor) -> torch.Tensor:
    probability = joint.double()
    marginal_x = probability.sum(dim=1, keepdim=True)
    marginal_y = probability.sum(dim=0, keepdim=True)
    positive = probability > 0.0
    return (
        probability[positive]
        * torch.log2(probability[positive] / (marginal_x * marginal_y)[positive])
    ).sum()


def test_mutual_information_known_and_dense_distributions() -> None:
    model = _make_model()
    diagonal = torch.eye(MATRIX_SIZE, dtype=torch.float32) / MATRIX_SIZE
    uniform = torch.full((MATRIX_SIZE, MATRIX_SIZE), 1.0 / MATRIX_SIZE**2)
    correlated = 0.5 * diagonal + 0.5 * uniform

    assert torch.isclose(model(diagonal), torch.tensor(8.0), atol=1e-6)
    assert torch.isclose(model(uniform), torch.tensor(0.0), atol=1e-6)
    assert torch.isclose(model(correlated).double(), _reference_mi(correlated), atol=2e-6)
