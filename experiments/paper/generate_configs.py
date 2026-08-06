#!/usr/bin/env python3
"""Generate fully resolved paper experiment configurations from the suite manifest."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

# Environment switch for the Groq leg. The paper matrix includes it by default,
# but it depends on a Globus Compute endpoint that must be started by hand on the
# Groq login node. When that endpoint is down, every measurement blocks for the
# backend timeout, so allow generating a CUDA-only matrix that still runs.
GROQ_ENV_VAR = "LASSI_PAPER_GROQ"

# Where CUDA measurements are timed. The paper reports A100 numbers, so the
# default is the remote Globus Compute endpoint, not whatever GPU happens to be
# in the machine driving the suite. Set to ``local`` only for smoke tests —
# results from the two devices are not comparable and must not be pooled.
GPU_ENV_VAR = "LASSI_PAPER_GPU"
GPU_ENDPOINT_ENV_VAR = "LASSI_PAPER_GPU_ENDPOINT"

# Two-A100 endpoint used for the August 3, 2026 end-to-end validation run.
A100_ENDPOINT_ID = "b162a840-38b4-4c1a-84cc-579fb62f4dfc"

# Where the Globus Compute endpoint serving the Groq leg actually runs.
#
# ``pbs``: the endpoint lives on a login node, which has no LPUs, so every
# measurement is submitted with ``qsub`` and waits in the batch queue.
# ``direct``: the endpoint lives on a compute node that owns the LPUs, so the
# worker runs in place. This removes PBS entirely, which also removes the
# failure mode where a blocking ``qsub`` occupies the endpoint's only worker
# and starves every later task into a silent hang.
#
# ``direct`` is the default. The login endpoint is normally stopped, so a
# defaulted-to-PBS run fails at the doctor with ENDPOINT_NOT_ONLINE naming a
# UUID that appears nowhere in the launch instructions -- an unhelpful failure
# for the mode nobody wants. PBS remains available, but opt in to it.
GROQ_MODE_ENV_VAR = "LASSI_PAPER_GROQ_MODE"

# A compute-node endpoint is a different registration with a different UUID, so
# it cannot be inferred. Override this when the node's endpoint is re-registered.
GROQ_ENDPOINT_ENV_VAR = "LASSI_PAPER_GROQ_ENDPOINT"

LOGIN_ENDPOINT_ID = "266f3128-cc9a-403e-ab61-9284ed57d54b"
COMPUTE_ENDPOINT_ID = "428a680f-1efb-488e-9558-96eb7f54a910"

# Home is shared between the Groq login and compute nodes, so one interpreter
# path serves both launch modes.
CONDA_SH = "/home/gbrun/miniconda3/etc/profile.d/conda.sh"
CONDA_ENV = "groqflow"
GROQ_PYTHON = "/home/gbrun/miniconda3/envs/groqflow/bin/python"
GROQ_PYTHONPATH = ["/home/gbrun/LASSI-TOOLS/src"]

# Per-measurement ceilings, enforced by the remote worker. These bound ONE cell,
# not the kernel and not the suite, so the useful question is "how long can a
# healthy measurement take?" rather than "how long are we willing to wait?".
#
# A candidate that declines to vectorise sets these apart from every other
# failure mode. The LU c1 arena entry wrote its forward as a triple-nested
# Python loop over an n=2000 matrix -- ~1.3e9 innermost iterations, each
# launching its own GPU op, so a single forward runs for hours against a
# 35-forward protocol. It cannot finish, but it also never errors, so only a
# deadline ends it. At the previous 7200 s that cost two hours per occurrence
# and starved the rest of the matrix; the shape recurs on any kernel where a
# candidate keeps the reference's scalar loop structure.
#
# Values are set from the observed distribution over one full session
# (65 CUDA measurements, 19 Groq):
#
#   a100-node      p50 3.0 s   p90 8.2 s   max 34.5 s
#   groq-compute   p50  71 s   p90 230 s   max 1084 s (cold compile, cache miss)
#
# CUDA is tightly clustered because the work is a fixed number of forwards on an
# already-warm device -- no compilation step hides in the tail. 180 s is ~5x the
# worst case ever observed and kills a wedged cell in three minutes instead of
# two hours. The margin is deliberately not tighter: the observed distribution
# comes from gemm, 3mm, covariance, and jacobi-2d, and a legitimately heavier
# kernel later in the matrix must not be cut off. A false timeout silently
# corrupts a paper row, while a late one now costs three minutes.
#
# Groq is exempt from the tightening, because its tail is compilation rather than
# execution. The GroqFlow assembler is single-threaded and `groq-cache` is keyed
# by build hash, so a first-touch compile is the expected worst case, not an
# anomaly. 1800 s is ~1.7x the slowest real compile.
#
# Raise via the environment rather than editing, so a one-off slow run does not
# become the checked-in default.
CUDA_TIMEOUT_ENV_VAR = "LASSI_PAPER_CUDA_TIMEOUT_S"
GROQ_TIMEOUT_ENV_VAR = "LASSI_PAPER_GROQ_TIMEOUT_S"
CUDA_TIMEOUT_S = 180
GROQ_TIMEOUT_S = 1800


def _groq_enabled() -> bool:
    """Report whether generated configs should include the Groq backend.

    Returns:
        ``False`` only when the environment explicitly disables the leg.
    """
    return os.environ.get(GROQ_ENV_VAR, "1").strip().lower() not in {"0", "false", "no"}


def _measurement_timeout_s(variable: str, default: int) -> int:
    """Resolve one backend's per-measurement ceiling from the environment.

    Args:
        variable: Environment variable holding an override, in seconds.
        default: Value to use when the variable is unset or empty.

    Returns:
        The ceiling to write into the backend entry.

    Raises:
        ValueError: If the override is not a positive integer.
    """
    raw = os.environ.get(variable, "").strip()
    if not raw:
        return default
    try:
        seconds = int(raw)
    except ValueError as error:
        raise ValueError(f"{variable} must be a positive integer, got {raw!r}") from error
    if seconds <= 0:
        raise ValueError(f"{variable} must be a positive integer, got {raw!r}")
    return seconds


def _groq_direct() -> bool:
    """Report whether the Groq endpoint runs on a compute node.

    Returns:
        ``True`` unless the environment explicitly selects PBS, meaning no
        ``qsub`` submission.

    Raises:
        ValueError: If the mode is neither ``pbs`` nor ``direct``.
    """
    mode = os.environ.get(GROQ_MODE_ENV_VAR, "direct").strip().lower()
    if mode not in {"pbs", "direct"}:
        raise ValueError(f"{GROQ_MODE_ENV_VAR} must be 'pbs' or 'direct', got {mode!r}")
    return mode == "direct"


def _groq_resource_name() -> str:
    """Name the execution resource serving the Groq leg.

    Returns:
        Resource key referenced by both the resource map and the backend.
    """
    return "groq-compute" if _groq_direct() else "groq-login"


def _gpu_remote() -> bool:
    """Report whether GPU measurements run on the remote A100 endpoint.

    Returns:
        ``True`` unless the environment explicitly selects the local harness.

    Raises:
        ValueError: If the target is neither ``a100`` nor ``local``.
    """
    target = os.environ.get(GPU_ENV_VAR, "a100").strip().lower()
    if target not in {"a100", "local"}:
        raise ValueError(f"{GPU_ENV_VAR} must be 'a100' or 'local', got {target!r}")
    return target == "a100"


def _gpu_backend_name() -> str:
    """Name the CUDA measurement backend after the device it actually times.

    Returns:
        Backend name recorded in every measurement artifact.
    """
    return "a100-cuda" if _gpu_remote() else "harness-cuda"


def _gpu_resource() -> tuple[str, dict[str, Any] | None]:
    """Build the execution resource that serves GPU measurements.

    Returns:
        The resource name, and its mapping when a new resource is needed. The
        local harness is already in the resource map, so it contributes
        ``None``.
    """
    if not _gpu_remote():
        return "harness", None
    return "a100-node", {
        "endpoint_id": os.environ.get(GPU_ENDPOINT_ENV_VAR, A100_ENDPOINT_ID),
        "workspace_root": "/tmp/lassi-x-a100",
        "labels": ["cuda", "a100"],
    }


def _model(endpoint_model: str, reasoning_effort: str) -> dict[str, Any]:
    """Build one Hermes/Argo model section.

    Args:
        endpoint_model: Argo internal model identifier (for example, ``gpt56sol``).
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
        f"accept dataset='mini' with {kernel['mini']} and dataset='large' with "
        f"{kernel['large']}. The same make_model()/forward implementation must support "
        f"both profiles. Return live-out {kernel['live_out']} in the exact PolyBench print order."
    )


def _groq_resource() -> dict[str, Any]:
    """Build the Groq Academy resource entry for the active launch mode.

    Returns:
        Resource mapping for the hand-started ``lassi-x`` Globus endpoint.
    """
    if _groq_direct():
        return {
            "endpoint_id": os.environ.get(GROQ_ENDPOINT_ENV_VAR, COMPUTE_ENDPOINT_ID),
            "workspace_root": "/home/gbrun/lassi-x-groq-academy",
            "labels": ["groq-compute", "lpu", "direct"],
        }
    return {
        "endpoint_id": LOGIN_ENDPOINT_ID,
        "workspace_root": "/home/gbrun/lassi-x-groq-academy",
        "labels": ["groq-login", "pbs"],
    }


def _groq_backend() -> dict[str, Any]:
    """Build the Groq LPU measurement backend entry.

    Returns:
        Backend mapping measuring fp16 on the LPU, through PBS or in place.
    """
    launch: dict[str, Any] = {
        "conda_sh": CONDA_SH,
        "conda_env": CONDA_ENV,
        "python": GROQ_PYTHON,
        "pythonpath": list(GROQ_PYTHONPATH),
    }
    if _groq_direct():
        mode_key = "runtime"
    else:
        mode_key = "pbs"
        launch |= {
            "qsub": "/opt/pbs/bin/qsub",
            "select": "select=1,place=excl",
            "walltime": "02:00:00",
        }
    return {
        "type": "groq",
        "name": "groq-lpu",
        "resource": _groq_resource_name(),
        "precisions": ["fp16"],
        "timeout_s": _measurement_timeout_s(GROQ_TIMEOUT_ENV_VAR, GROQ_TIMEOUT_S),
        # Execution may legitimately wait hours in the PBS queue, but staging
        # and qsub must not. An endpoint that heartbeats without a free worker
        # leaves them pending indefinitely; fail the cell instead of the suite.
        "submit_timeout_s": 300,
        mode_key: launch,
        "capabilities": {
            "storage": ["fp16"],
            "elementwise": ["fp16"],
            "matmul_accumulator": "backend-defined",
            "explicit_fp32_tensor_ops": False,
            "fp64": False,
        },
    }


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
    groq = _groq_enabled()
    # The oracle build/run and every agent tool call stay on the local harness;
    # only GPU timing moves. Keeping the reference compile in one place makes
    # the oracle identical across every cell in the matrix.
    resources: dict[str, Any] = {
        "harness": {
            "workspace_root": "/home/gbrun/lassi-x-local-academy",
            "labels": ["cpu", "cuda"],
        },
    }
    gpu_resource, gpu_spec = _gpu_resource()
    if gpu_spec is not None:
        resources[gpu_resource] = gpu_spec
    backends: list[dict[str, Any]] = [
        {
            "type": "torch",
            "name": _gpu_backend_name(),
            "device": "cuda",
            "resource": gpu_resource,
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "timeout_s": _measurement_timeout_s(CUDA_TIMEOUT_ENV_VAR, CUDA_TIMEOUT_S),
        },
    ]
    if groq:
        resources[_groq_resource_name()] = _groq_resource()
        backends.append(_groq_backend())
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
            "resources": resources,
            "mcp_timeout_s": 1200,
        },
        "measure": {
            "precisions": ["fp64", "fp32", "fp16", "bf16"],
            "strict_precisions": ["fp64", "fp32"],
            # PolyBench LARGE, not EXTRALARGE. GroqFlow sizes a build by parameter
            # count (build.py::calculate_num_chips), and these kernels are pure
            # dataflow with essentially no parameters, so it always picks one chip
            # regardless of dataset. EXTRALARGE then overruns the single-chip
            # scheduler and the compile dies in Proxy Buffer Allocation. LARGE fits
            # one chip on every kernel measured, keeping all backends comparable
            # without a multi-chip partition that would also rescale Groq latency.
            "performance_dataset": "large",
            "warmup": 5,
            "iterations": 30,
            "stochastic_seeds": [0, 1, 2, 3, 4],
            "serialize_torch_backends": True,
            "backends": backends,
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
