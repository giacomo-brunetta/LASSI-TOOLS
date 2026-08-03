from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import yaml
from pydantic import ValidationError

from lassi_x.config import RunConfig
from lassi_x.hermes_worker import resolve_api_key
from lassi_x.protocol import WorkerInit

if TYPE_CHECKING:
    from pathlib import Path


def minimal_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "version": 1,
        "project": {"root": str(tmp_path)},
        "kernel": {
            "name": "tiny",
            "reference": "tiny.c",
            "task": "Translate tiny.",
        },
        "oracle": {
            "build": ["gcc", "{reference}", "-o", "{oracle_dir}/tiny"],
            "run": ["{oracle_dir}/tiny", "{output}"],
        },
        "models": {
            "planner": {"model": "planner"},
            "candidates": [
                {"model": "one"},
                {"model": "two"},
                {"model": "three"},
            ],
            "compensation": {"model": "compensator"},
        },
        "measure": {
            "precisions": ["fp64", "fp32"],
            "backends": [
                {
                    "type": "torch",
                    "name": "cpu",
                    "device": "cpu",
                    "precisions": ["fp64", "fp32"],
                }
            ],
        },
    }


def test_load_config_requires_exactly_three_candidates(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    assert len(config.models.candidates) == 3
    data["models"]["candidates"].pop()
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError, match="exactly three"):
        RunConfig.load(path)


def test_backend_requirements(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0].pop("device")
    with pytest.raises(ValidationError, match="requires device"):
        RunConfig.model_validate(data)


def test_claude_settings_credential_helper(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text('{"apiKeyHelper": "printf test-credential"}')
    init = WorkerInit(model="planner", role="planner", claude_settings=str(settings))
    assert resolve_api_key(init) == "test-credential"
