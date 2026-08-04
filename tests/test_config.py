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


def test_candidate_count_is_configurable_and_must_match_models(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    assert len(config.models.candidates) == 3
    data["models"]["candidates"].pop()
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(ValidationError, match="length must equal arena.candidates"):
        RunConfig.load(path)
    data["arena"] = {"candidates": 2}
    path.write_text(yaml.safe_dump(data))
    config = RunConfig.load(path)
    assert config.arena.candidates == 2
    assert len(config.models.candidates) == 2


def test_backend_requirements(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"][0].pop("device")
    with pytest.raises(ValidationError, match="requires device"):
        RunConfig.model_validate(data)


def test_groq_backend_requires_queue_or_resource_pbs(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    backend: dict[str, Any] = {
        "type": "groq",
        "name": "groq",
        "precisions": ["fp16"],
    }
    data["measure"]["backends"] = [backend]
    with pytest.raises(ValidationError, match="exactly one execution mode"):
        RunConfig.model_validate(data)

    backend["queue_dir"] = str(tmp_path / "queue")
    assert RunConfig.model_validate(data).measure.backends[0].queue_dir is not None

    backend.pop("queue_dir")
    backend["resource"] = "groq-login"
    backend["pbs"] = {
        "conda_sh": "/shared/miniconda3/etc/profile.d/conda.sh",
        "python": "/shared/miniconda3/envs/groqflow/bin/python",
    }
    data["execution"] = {
        "mode": "academy",
        "resources": {"groq-login": {}},
    }
    parsed = RunConfig.model_validate(data).measure.backends[0]
    assert parsed.pbs is not None
    assert parsed.pbs.select == "select=1,place=excl"

    backend["queue_dir"] = str(tmp_path / "queue")
    with pytest.raises(ValidationError, match="exactly one execution mode"):
        RunConfig.model_validate(data)


def test_execution_defaults_to_local_mode(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    assert config.execution.mode == "local"
    assert config.execution.resources == {}


def test_execution_validators_reject_inconsistent_targets(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["execution"] = {"default_resource": "gpu"}
    with pytest.raises(ValidationError, match="must name a configured resource"):
        RunConfig.model_validate(data)
    data["execution"] = {"mode": "local", "exchange_url": "https://exchange.example"}
    with pytest.raises(ValidationError, match="requires mode: academy"):
        RunConfig.model_validate(data)
    data["execution"] = {
        "mode": "academy",
        "resources": {"gpu": {"endpoint_id": "abc"}},
    }
    with pytest.raises(ValidationError, match="require execution.exchange_url"):
        RunConfig.model_validate(data)


def test_claude_settings_credential_helper(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text('{"apiKeyHelper": "printf test-credential"}')
    init = WorkerInit(model="planner", role="planner", claude_settings=str(settings))
    assert resolve_api_key(init) == "test-credential"


def test_memory_defaults_off_and_configures_from_yaml(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    assert not config.memory.enabled
    assert config.memory.user_id == "lassi-x"
    data = minimal_config(tmp_path)
    data["memory"] = {
        "enabled": True,
        "host": "http://localhost:9999",
        "api_key_env": "MEM0_API_KEY",
        "user_id": "team-lp",
    }
    config = RunConfig.model_validate(data)
    assert config.memory.enabled
    assert config.memory.host == "http://localhost:9999"
    assert config.memory.api_key_env == "MEM0_API_KEY"
    assert config.memory.user_id == "team-lp"


def test_memory_rejects_inline_credentials(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["memory"] = {"enabled": True, "api_key": "sk-inline-secret"}
    with pytest.raises(ValidationError):
        RunConfig.model_validate(data)
