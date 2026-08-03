from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pytest
import yaml

from lassi_x.config import RunConfig
from lassi_x.execution import LocalExecutionBackend
from lassi_x.measurement import TorchBackend
from lassi_x.types import Status
from lassi_x.validation import build_oracle

from .test_config import minimal_config
from .test_validation import C_REFERENCE, GOOD_MODULE

if TYPE_CHECKING:
    from pathlib import Path

    from lassi_x.validation import OracleResult


def _setup(tmp_path: Path) -> tuple[RunConfig, OracleResult, Path]:
    (tmp_path / "tiny.c").write_text(C_REFERENCE)
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(minimal_config(tmp_path)))
    config = RunConfig.load(config_path)
    oracle = asyncio.run(build_oracle(config, tmp_path / "run"))
    module = tmp_path / "candidate.py"
    module.write_text(GOOD_MODULE)
    return config, oracle, module


def test_torch_backend_measures_through_execution_backend(tmp_path: Path) -> None:
    config, oracle, module = _setup(tmp_path)
    execution_root = tmp_path / "exec"
    backend = TorchBackend(
        config.measure.backends[0], LocalExecutionBackend(execution_root, "here"), "here"
    )
    measurement = asyncio.run(
        backend.measure(
            config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp64",
            compensation="none",
        )
    )
    assert measurement.status == Status.OK
    assert measurement.resource == "here"
    assert measurement.latency_s is not None and measurement.latency_s > 0
    workspace = execution_root / "m-c1-base"
    assert (workspace / "candidate.py").is_file()
    assert (workspace / "oracle.csv").is_file()


def test_torch_backend_reports_unavailable_device_from_handshake(tmp_path: Path) -> None:
    config, oracle, module = _setup(tmp_path)
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0]["device"] = "cuda:0"
    cuda_config = RunConfig.model_validate(data)
    backend = TorchBackend(
        cuda_config.measure.backends[0],
        LocalExecutionBackend(tmp_path / "exec", "cpu-box"),
        "cpu-box",
    )
    measurement = asyncio.run(
        backend.measure(
            cuda_config,
            oracle,
            module,
            candidate_id="c1",
            variant_id="c1-base",
            precision="fp64",
            compensation="none",
        )
    )
    if measurement.status == Status.OK:
        pytest.skip("host actually has CUDA")
    assert measurement.status == Status.UNSUPPORTED
    assert "cpu-box" in measurement.notes


def test_backend_resource_must_be_configured(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0]["resource"] = "nvidia"
    with pytest.raises(ValueError, match="unknown execution resources"):
        RunConfig.model_validate(data)
    data["execution"] = {"mode": "academy", "resources": {"nvidia": {}}}
    assert RunConfig.model_validate(data).measure.backends[0].resource == "nvidia"
