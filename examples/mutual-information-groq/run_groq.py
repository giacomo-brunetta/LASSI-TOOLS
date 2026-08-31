"""Compile, execute, and benchmark the mutual-information kernel on Groq."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import torch
from groqflow import groqit
from mutual_information import MATRIX_SIZE, build_inputs, make_model


def invoke(model: Any, joint: torch.Tensor) -> Any:
    """Invoke GroqModel across the APIs used by deployed GroqFlow releases."""
    try:
        return model(joint=joint)
    except TypeError:
        return model.run({"joint": joint})


def scalar(output: Any) -> float:
    """Convert a scalar Torch, NumPy, or Groq output to a Python float."""
    if hasattr(output, "detach"):
        return float(output.detach().cpu().item())
    if hasattr(output, "item"):
        return float(output.item())
    return float(output)


def reference_mi(joint: torch.Tensor) -> float:
    """Evaluate the definition in FP64 on CPU for independent verification."""
    probability = joint.double()
    marginal_x = probability.sum(dim=1, keepdim=True)
    marginal_y = probability.sum(dim=0, keepdim=True)
    positive = probability > 0.0
    terms = probability[positive] * torch.log2(
        probability[positive] / (marginal_x * marginal_y).expand_as(probability)[positive]
    )
    return float(terms.sum().item())


def main() -> None:
    """Compile once, check three distributions, and report SDK latency."""
    diagonal = build_inputs(dtype=torch.float32)[0]
    cache_dir = Path.home() / ".cache" / "lassi-groq-mi"
    cache_dir.mkdir(parents=True, exist_ok=True)
    kwargs = {
        "build_name": "lassi-mutual-information-256-v1",
        "cache_dir": str(cache_dir),
        "rebuild": "if_needed",
    }
    try:
        compiled = groqit(make_model(), {"joint": diagonal}, monitor=False, **kwargs)
    except TypeError:
        compiled = groqit(make_model(), {"joint": diagonal}, **kwargs)

    uniform = torch.full(
        (MATRIX_SIZE, MATRIX_SIZE),
        1.0 / (MATRIX_SIZE * MATRIX_SIZE),
        dtype=torch.float32,
    )
    correlated = 0.5 * diagonal + 0.5 * uniform
    cases = {
        "diagonal": diagonal,
        "independent_uniform": uniform,
        "dense_correlated": correlated,
    }
    for name, joint in cases.items():
        expected = reference_mi(joint)
        actual = scalar(invoke(compiled, joint))
        print(
            f"{name}: groq={actual:.9f} bits reference={expected:.9f} "
            f"abs_error={abs(actual - expected):.3e}"
        )
        if not math.isclose(actual, expected, rel_tol=1e-2, abs_tol=5e-2):
            raise RuntimeError(f"{name} failed numerical validation")

    benchmark = compiled.benchmark(repetitions=20)
    print(f"latency_s={float(benchmark.latency):.9g}")


if __name__ == "__main__":
    main()
