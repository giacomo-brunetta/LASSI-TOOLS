from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import torch

from lassi_x.precision import (
    REDUCTION_METHODS,
    blocked_fp32_sum,
    compensated_sum,
    pairwise_sum,
    stochastic_cast,
)


def test_high_precision_methods_collapse_to_plain_sum() -> None:
    values = torch.linspace(-2, 3, 101, dtype=torch.float64)
    expected = values.sum()
    for method in REDUCTION_METHODS:
        assert torch.equal(compensated_sum(values, method=method), expected)


def test_pairwise_supports_odd_length_and_negative_dimension() -> None:
    values = torch.arange(15, dtype=torch.float32).reshape(3, 5)
    assert torch.equal(pairwise_sum(values, dim=-1), values.sum(dim=-1))


def test_double_word_improves_sequential_fp16_swamping() -> None:
    values = torch.cat(
        (
            torch.ones(4096, dtype=torch.float16),
            torch.full((4096,), 0.001, dtype=torch.float16),
        )
    )
    oracle = values.double().sum()
    sequential = torch.zeros((), dtype=torch.float16)
    for value in values:
        sequential = sequential + value
    double_word = compensated_sum(values, method="double-word").double()
    assert (double_word - oracle).abs() < (sequential.double() - oracle).abs()


def test_blocked_fp32_reduces_low_precision_swamping() -> None:
    values = torch.cat(
        (
            torch.ones(4096, dtype=torch.float16),
            torch.full((4096,), 0.001, dtype=torch.float16),
        )
    )
    oracle = values.double().sum()
    blocked = blocked_fp32_sum(values, block_size=256).double()
    sequential = torch.zeros((), dtype=torch.float16)
    for value in values:
        sequential = sequential + value
    assert (blocked - oracle).abs() < (sequential.double() - oracle).abs()


def test_bfloat16_double_word_preserves_bfloat16_exponent_range() -> None:
    values = torch.tensor([1e10, 1e10], dtype=torch.bfloat16)
    result = compensated_sum(values, method="double-word")
    assert torch.isfinite(result)
    assert result == values.float().sum()


def test_stochastic_cast_preserves_exact_values() -> None:
    values = torch.tensor([0.0, 1.0, -2.0, 8.0], dtype=torch.float32)
    for _ in range(10):
        assert torch.equal(stochastic_cast(values, torch.float16).float(), values)


def test_stochastic_cast_does_not_silently_saturate_overflow() -> None:
    values = torch.tensor([70000.0, -70000.0], dtype=torch.float32)
    rounded = stochastic_cast(values, torch.float16)
    assert torch.equal(torch.isinf(rounded), torch.tensor([True, True]))


def test_precision_helpers_do_not_import_the_config_stack() -> None:
    """Compensation candidates reach these helpers from the accelerator's env.

    That environment -- groqflow on a GroqRack node -- has torch but no
    pydantic, so importing ``lassi_x.precision`` must not drag in
    ``lassi_x.config``.
    """
    code = (
        "import lassi_x.precision, sys\n"
        "assert 'lassi_x.config' not in sys.modules, sorted(\n"
        "    m for m in sys.modules if m.startswith('lassi_x')\n"
        ")\n"
        "assert 'pydantic' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)


def test_every_advertised_technique_executes_on_torch_cpu() -> None:
    script = (
        Path(__file__).parents[1]
        / "src/lassi_x/resources/hermes_skills/lassi-x-fp16-compensate/scripts"
        / "torch_cpu_techniques.py"
    )
    completed = subprocess.run(
        [sys.executable, str(script), "--smoke"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout)
    assert report["device"] == "cpu"
    assert set(report["results"]) == {
        "fp32-accumulate",
        "blocked-fp32",
        "pairwise",
        "kahan",
        "neumaier",
        "double-word",
        "double-word-fp32",
        "zero-center",
        "scaling",
        "equilibrate",
        "mixed-refine",
        "precision-ramp",
        "residual-carry",
        "ozaki-split",
        "stable-reformulation",
        "stochastic-round",
    }
