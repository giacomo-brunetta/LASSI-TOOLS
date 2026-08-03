from __future__ import annotations

import json
import subprocess
import sys
from typing import TYPE_CHECKING, Any, cast

import numpy as np
import pytest

if TYPE_CHECKING:
    from pathlib import Path


def _measure(tmp_path: Path, values: str, oracle: list[float]) -> dict[str, Any]:
    module = tmp_path / "candidate.py"
    module.write_text(
        "import torch\n"
        "from torch import nn\n"
        "def build_inputs(device='cpu', dtype=torch.float64): return ()\n"
        "class Model(nn.Module):\n"
        f"    def forward(self): return torch.tensor({values}, dtype=torch.float64)\n"
        "def make_model(): return Model()\n"
    )
    oracle_path = tmp_path / "oracle.npy"
    np.save(oracle_path, np.asarray(oracle, dtype=np.float64))
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "lassi_x.measure_worker",
            "--module",
            str(module),
            "--oracle",
            str(oracle_path),
            "--device",
            "cpu",
            "--precision",
            "fp64",
            "--warmup",
            "0",
            "--iterations",
            "1",
            "--rtol",
            "1e-12",
            "--atol",
            "1e-12",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return cast("dict[str, Any]", json.loads(result.stdout))


def test_numeric_error_is_a_valid_pareto_measurement(tmp_path: Path) -> None:
    payload = _measure(tmp_path, "[1.1]", [1.0])
    assert payload["valid"] is True
    assert payload["equivalent"] is False
    assert payload["metrics"]["max_abs_error"] == pytest.approx(0.1)


def test_shape_error_is_not_a_valid_measurement(tmp_path: Path) -> None:
    payload = _measure(tmp_path, "[1.0]", [1.0, 2.0])
    assert payload["valid"] is False
    assert payload["equivalent"] is False
