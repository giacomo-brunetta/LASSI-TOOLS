from __future__ import annotations

import ast
from typing import Any

from lassi_x.dataset_specialization import specialize_source


def test_atax_folded_normalization_scales_with_dimensions() -> None:
    result, _ = specialize_source(
        "_M=38\n_N=42\ndef build_inputs():\n return 1/190, 1/42\n",
        "polybench-atax",
        {"M": 38, "N": 42},
        {"M": 1900, "N": 2100},
    )
    values: dict[str, Any] = {}
    exec(result, values)
    assert values["build_inputs"]() == (1 / 9500, 1 / 2100)


def test_size_specialization_preserves_physical_coefficients() -> None:
    source = """
_MINI_N = 10
_TIMESTEPS = 20
def build_inputs(dataset='mini'):
    n = _MINI_N
    return 10 * n
"""
    result, changes = specialize_source(
        source, "polybench-heat-3d", {"N": 10, "TSTEPS": 20}, {"N": 120, "TSTEPS": 500}
    )
    values: dict[str, Any] = {}
    exec(result, values)
    assert values["build_inputs"]() == 1200
    assert values["_TIMESTEPS"] == 500
    assert len(changes) == 2


def test_adi_distinguishes_size_and_timestep_when_mini_values_match() -> None:
    source = """
def build_inputs(dataset='mini'):
    n = 20
    dt = 1.0 / 20
    return n, dt, len(range(20))
"""
    result, _ = specialize_source(
        source, "polybench-adi", {"N": 20, "TSTEPS": 20}, {"N": 1000, "TSTEPS": 500}
    )
    values: dict[str, Any] = {}
    exec(result, values)
    assert values["build_inputs"]() == (1000, 1 / 500, 500)


def test_dataset_tables_and_dimension_tuples() -> None:
    source = "SIZES = {'mini': (20, 25, 30), 'default': (20, 25, 30)}"
    result, _ = specialize_source(
        source,
        "polybench-gemm",
        {"NI": 20, "NJ": 25, "NK": 30},
        {"NI": 1000, "NJ": 1100, "NK": 1200},
    )
    values: dict[str, Any] = {}
    exec(result, values)
    assert values["SIZES"] == {"large": (1000, 1100, 1200), "default": (1000, 1100, 1200)}


def test_size_selector_and_literal_recurrence_bound() -> None:
    result, _ = specialize_source(
        "def _dataset_size(dataset):\n    return 32\n",
        "direct-dft",
        {"SIZE": 32},
        {"SIZE": 256},
    )
    values: dict[str, Any] = {}
    exec(result, values)
    assert values["_dataset_size"]("large") == 256
    result, _ = specialize_source(
        "def forward():\n    return range(1, 40)\n",
        "polybench-durbin",
        {"N": 40},
        {"N": 2000},
    )
    tree = ast.parse(result)
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    returned = function.body[0]
    assert isinstance(returned, ast.Return) and returned.value is not None
    assert ast.unparse(returned.value) == "range(1, 2000)"
