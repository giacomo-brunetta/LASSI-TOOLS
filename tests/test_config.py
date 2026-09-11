from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
import yaml
from pydantic import ValidationError

from lassi_x.config import (
    GroqBackendConfig,
    NativeBackendConfig,
    RunConfig,
    compatibility_target_for,
)
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
    parsed = RunConfig.model_validate(data).measure.backends[0]
    assert isinstance(parsed, GroqBackendConfig)
    assert parsed.queue_dir is not None

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
    assert isinstance(parsed, GroqBackendConfig)
    assert parsed.pbs is not None
    assert parsed.pbs.select == "select=1,place=excl"

    backend["queue_dir"] = str(tmp_path / "queue")
    with pytest.raises(ValidationError, match="exactly one execution mode"):
        RunConfig.model_validate(data)


def test_native_backend_requires_architecture_and_cerebras_worker(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    backend: dict[str, Any] = {
        "type": "native",
        "name": "ipu",
        "resource": "graphcore",
        "precisions": ["fp16"],
        "worker": {"python": "/opt/poplar/bin/python"},
    }
    data["measure"]["backends"] = [backend]
    data["execution"] = {"mode": "academy", "resources": {"graphcore": {}}}
    with pytest.raises(ValidationError, match="requires architecture"):
        RunConfig.model_validate(data)

    backend["architecture"] = "graphcore_ipu"
    parsed = RunConfig.model_validate(data)
    assert parsed.required_backends == ["ipu"]

    backend["architecture"] = "cerebras_wse3"
    with pytest.raises(ValidationError, match="requires a site measurement script"):
        RunConfig.model_validate(data)
    backend["worker"]["script"] = "tools/cerebras_worker.py"
    parsed_backend = RunConfig.model_validate(data).measure.backends[0]
    assert isinstance(parsed_backend, NativeBackendConfig)
    assert parsed_backend.architecture == "cerebras_wse3"


def test_execution_defaults_to_local_mode(tmp_path: Path) -> None:
    config = RunConfig.model_validate(minimal_config(tmp_path))
    assert config.execution.mode == "local"
    assert config.execution.resources == {}


def test_success_defaults_to_all_configured_accelerators(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda",
            "precisions": ["fp16"],
        }
    )
    config = RunConfig.model_validate(data)
    assert config.required_backends == ["cuda"]
    assert config.pareto_error_metric == "max_rel_error"
    assert config.compensation.measurement_scope == "all"


def test_accelerator_measurement_requires_warmup(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["warmup"] = 0
    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda:0",
            "precisions": ["fp16"],
        }
    )
    with pytest.raises(ValidationError, match="at least one warmup"):
        RunConfig.model_validate(data)


def test_success_rejects_unknown_required_backend(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["success"] = {"required_backends": ["missing"]}
    with pytest.raises(ValidationError, match="unknown measurement backends"):
        RunConfig.model_validate(data)


def test_success_rejects_duplicate_or_inactive_requirements(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["success"] = {"required_backends": ["cpu", "cpu"]}
    with pytest.raises(ValidationError, match="must be unique"):
        RunConfig.model_validate(data)

    data["success"] = {"required_backends": [], "required_precisions": {"cpu": ["fp32"]}}
    with pytest.raises(ValidationError, match="required accelerator backends"):
        RunConfig.model_validate(data)


def test_merged_evaluation_requires_oracle_for_distinct_dataset(
    tmp_path: Path,
) -> None:
    data = minimal_config(tmp_path)
    data["kernel"]["validation_dataset"] = "mini"
    data["measure"]["performance_dataset"] = "large"
    with pytest.raises(ValidationError, match="measure.evaluation_oracle"):
        RunConfig.model_validate(data)
    data["measure"]["performance_oracle"] = "large-oracle.csv"
    assert RunConfig.model_validate(data).measure.performance_dataset == "large"


def test_merged_evaluation_output_verification_cannot_be_disabled(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["verify_performance_output"] = False
    with pytest.raises(ValidationError, match="merged accelerator evaluation"):
        RunConfig.model_validate(data)


def test_success_rejects_unmeasured_required_precision(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["success"] = {"required_precisions": {"cpu": ["fp16"]}}
    with pytest.raises(ValidationError, match="unmeasured cells"):
        RunConfig.model_validate(data)


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


def test_compatibility_targets_are_explicit_and_architecture_specific(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["measure"]["backends"] = [
        {
            "type": "groq",
            "name": "groq",
            "queue_dir": str(tmp_path / "queue"),
            "precisions": ["fp16"],
        },
        {
            "type": "native",
            "name": "ipu",
            "resource": "ipu",
            "architecture": "graphcore_ipu",
            "precisions": ["fp16"],
            "worker": {"python": "python"},
        },
    ]
    data["execution"] = {"resources": {"ipu": {}}}
    config = RunConfig.model_validate(data)
    assert [compatibility_target_for(spec) for spec in config.measure.backends] == [
        "groq-r01-groqflow",
        "graphcore-pod64-poptorch",
    ]
    overridden = config.measure.backends[1].model_copy(
        update={"compatibility_target": "torch-mlir-tosa"}
    )
    assert compatibility_target_for(overridden) == "torch-mlir-tosa"


def test_compile_targets_must_be_packaged_unique_and_use_known_resources(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["compatibility"] = {
        "compile_targets": [
            {"target_id": "torch-mlir-tosa", "resource": "compiler"},
        ]
    }
    with pytest.raises(ValidationError, match="unknown execution resources"):
        RunConfig.model_validate(data)

    data["execution"] = {"resources": {"compiler": {}}}
    config = RunConfig.model_validate(data)
    assert config.compatibility.compile_targets[0].precisions == ["fp32"]
    data["compatibility"]["compile_targets"].append(
        {"target_id": "torch-mlir-tosa", "resource": "compiler"}
    )
    with pytest.raises(ValidationError, match="must be unique"):
        RunConfig.model_validate(data)

    data["compatibility"]["compile_targets"] = [{"target_id": "missing-target"}]
    with pytest.raises(ValidationError, match="unknown packaged targets"):
        RunConfig.model_validate(data)


def test_pruning_requires_an_architectural_accelerator_probe(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["pruning"] = {"enabled": True, "probe_backend": "cpu", "probe_precision": "fp32"}
    with pytest.raises(ValidationError, match="must use an accelerator"):
        RunConfig.model_validate(data)

    data["measure"]["backends"].append(
        {
            "type": "torch",
            "name": "cuda",
            "device": "cuda:0",
            "precisions": ["fp32"],
        }
    )
    data["pruning"]["probe_backend"] = "cuda"
    assert RunConfig.model_validate(data).pruning.enabled


def test_scheduler_resource_limits_must_name_configured_resources(tmp_path: Path) -> None:
    data = minimal_config(tmp_path)
    data["scheduler"] = {"resource_concurrency": {"missing": 2}}
    with pytest.raises(ValidationError, match="unknown execution resources"):
        RunConfig.model_validate(data)
