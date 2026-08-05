#!/usr/bin/env python3
"""Generate fully resolved paper experiment configurations from the suite manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def _model(endpoint_model: str, reasoning_effort: str) -> dict[str, Any]:
    """Build one Hermes/Argo model section.

    Args:
        endpoint_model: Exact identifier reported by the Argo model catalog.
        reasoning_effort: Hermes reasoning effort forwarded to the provider.

    Returns:
        A complete LASSI-X model configuration mapping.
    """
    return {
        "provider": "custom",
        "model": endpoint_model,
        "base_url": "https://apps.inside.anl.gov/argoapi/v1",
        "api_mode": "chat_completions",
        "reasoning_effort": reasoning_effort,
        "claude_settings": "/home/gbrun/.claude/settings.json",
        "max_tokens": 32768,
        "max_iterations": 120,
        "turn_timeout_s": 1200,
        "turn_retries": 3,
    }


def _task(kernel: dict[str, Any]) -> str:
    """Render the dual-dataset implementation contract for one kernel.

    Args:
        kernel: Kernel manifest entry.

    Returns:
        Detailed agent task text embedded in the generated YAML.
    """
    return (
        f"Translate the cited C kernel into a semantically equivalent, export-friendly "
        f"PyTorch module. Reproduce init_array and operation order from the staged source. "
        f"{kernel['task']} build_inputs(device, dtype, fixture=None, dataset='mini') must "
        f"accept dataset='mini' with {kernel['mini']} and dataset='extralarge' with "
        f"{kernel['extralarge']}. The same make_model()/forward implementation must support "
        f"both profiles. Return live-out {kernel['live_out']} in the exact PolyBench print order."
    )


def _config(kernel: dict[str, Any], model: dict[str, Any]) -> dict[str, Any]:
    """Construct one model/kernel RunConfig mapping.

    Args:
        kernel: Benchmark manifest entry.
        model: Model manifest entry.

    Returns:
        Mapping accepted by :class:`lassi_x.config.RunConfig`.
    """
    endpoint_model = str(model["endpoint_model"])
    reasoning_effort = str(model["reasoning_effort"])
    model_spec = _model(endpoint_model, reasoning_effort)
    reference = str(kernel["reference"])
    header = str(kernel["header"])
    include_dir = str(Path(reference).parent)
    return {
        "version": 1,
        "project": {"root": "../../../../../PolyBenchC-4.2.1"},
        "kernel": {
            "name": str(kernel["id"]),
            "reference": reference,
            "context": [header],
            "validation_dataset": "mini",
            "task": _task(kernel),
        },
        "oracle": {
            "build": [
                "gcc",
                "-O0",
                "-DMINI_DATASET",
                "-DPOLYBENCH_DUMP_ARRAYS",
                "-include",
                "../LASSI-TOOLS/experiments/paper/oracle_precision.h",
                "{reference}",
                "utilities/polybench.c",
                "-Iutilities",
                f"-I{include_dir}",
                "-lm",
                "-o",
                "{oracle_dir}/reference",
            ],
            "run": ["{oracle_dir}/reference"],
            "output": "oracle.csv",
            "capture": "stderr",
            "format": "polybench",
            "timeout_s": 600,
        },
        "arena": {
            "candidates": 3,
            "planner_format_retries": 2,
            "correction_rounds": 2,
            "timeout_s": 900,
            "equivalence": {"rtol": 1e-10, "atol": 1e-12, "max_mismatches": 20},
        },
        "models": {
            "planner": dict(model_spec),
            "candidates": [dict(model_spec) for _ in range(3)],
            "compensation": dict(model_spec),
        },
        # Paper trials must remain independent: do not retrieve or persist
        # cross-run agent memory. Keep this explicit in each generated
        # artifact instead of relying on MemoryConfig's default.
        "memory": {"enabled": False},
        "execution": {
            "mode": "academy",
            "exchange_url": "https://exchange.academy-agents.org",
            "auth": "globus",
            "default_resource": "harness",
            "resources": {
                "harness": {
                    "workspace_root": "/home/gbrun/lassi-x-local-academy",
                    "labels": ["cpu", "cuda"],
                },
                "groq-login": {
                    "endpoint_id": "266f3128-cc9a-403e-ab61-9284ed57d54b",
                    "workspace_root": "/home/gbrun/lassi-x-groq-academy",
                    "labels": ["groq-login", "pbs"],
                },
            },
            "mcp_timeout_s": 1200,
        },
        "measure": {
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "strict_precisions": ["fp64", "fp32"],
            "performance_dataset": "extralarge",
            "warmup": 5,
            "iterations": 30,
            "stochastic_seeds": [0, 1, 2, 3, 4],
            "serialize_torch_backends": True,
            "backends": [
                {
                    "type": "torch",
                    "name": "harness-cuda",
                    "device": "cuda",
                    "resource": "harness",
                    "precisions": ["fp64", "fp32", "fp16", "bf16"],
                    "timeout_s": 7200,
                },
                {
                    "type": "groq",
                    "name": "groq-lpu",
                    "resource": "groq-login",
                    "precisions": ["fp16"],
                    "timeout_s": 7200,
                    "pbs": {
                        "qsub": "/opt/pbs/bin/qsub",
                        "conda_sh": "/home/gbrun/miniconda3/etc/profile.d/conda.sh",
                        "conda_env": "groqflow",
                        "python": "/home/gbrun/miniconda3/envs/groqflow/bin/python",
                        "pythonpath": ["/home/gbrun/LASSI-TOOLS/src"],
                        "select": "select=1,place=excl",
                        "walltime": "02:00:00",
                    },
                    "capabilities": {
                        "storage": ["fp16"],
                        "elementwise": ["fp16"],
                        "matmul_accumulator": "backend-defined",
                        "explicit_fp32_tensor_ops": False,
                        "fp64": False,
                    },
                },
            ],
        },
        "compensation": {
            "enabled": True,
            "correction_rounds": 2,
            "error_threshold": 0.01,
            "error_metric": "max_rel_error",
            "comparison_scope": "same_candidate",
            "measurement_scope": "target",
        },
        "runs_dir": f"../LASSI-TOOLS/runs/paper-suite/{model['id']}/{kernel['id']}",
    }


def generate() -> list[Path]:
    """Generate every model/kernel YAML in deterministic suite order.

    Returns:
        Paths of generated configuration files.
    """
    manifest = yaml.safe_load((HERE / "benchmarks.yaml").read_text())
    generated: list[Path] = []
    for model in manifest["models"]:
        output_dir = HERE / "configs" / str(model["id"])
        output_dir.mkdir(parents=True, exist_ok=True)
        for kernel in manifest["kernels"]:
            path = output_dir / f"{kernel['id']}.yaml"
            path.write_text(
                "# Generated by experiments/paper/generate_configs.py; do not edit.\n"
                + yaml.safe_dump(_config(kernel, model), sort_keys=False, width=100)
            )
            generated.append(path)
    return generated


if __name__ == "__main__":
    for generated_path in generate():
        print(generated_path.relative_to(REPO))
