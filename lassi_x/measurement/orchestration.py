from __future__ import annotations

import asyncio
import statistics
from typing import TYPE_CHECKING, Any

from ..types import Status
from .groq import GroqBackend
from .native import NativeBackend
from .torch import TorchBackend

if TYPE_CHECKING:
    from pathlib import Path

    from ..config import RunConfig
    from ..execution import ExecutionContext
    from ..types import Measurement
    from ..validation import OracleResult
    from .common import Backend

def build_backends(config: RunConfig, execution: ExecutionContext) -> list[Backend[Any]]:
    """Instantiate one measurement backend per configured cell provider.

    Args:
        config: Validated run configuration.
        execution: Running execution context supplying per-resource backends.

    Returns:
        The measurement backends, with torch backends bound to the execution
        resource named by their ``resource`` field (default resource when
        omitted).

    """
    result: list[Backend[Any]] = []
    torch_lock = asyncio.Semaphore(1) if config.measure.serialize_torch_backends else None
    for spec in config.measure.backends:
        if spec.type == "torch":
            resource = spec.resource or execution.default_resource
            result.append(
                TorchBackend(
                    spec,
                    execution.backend(spec.resource),
                    resource,
                    semaphore=torch_lock,
                )
            )
        elif spec.type == "groq":
            if spec.queue_dir is not None:
                result.append(GroqBackend(spec))
            else:
                resource = spec.resource or execution.default_resource
                result.append(
                    GroqBackend(
                        spec,
                        execution.backend(spec.resource),
                        resource,
                        semaphore=asyncio.Semaphore(1),
                    )
                )
        else:
            resource = spec.resource or execution.default_resource
            result.append(
                NativeBackend(
                    spec,
                    execution.backend(spec.resource),
                    resource,
                    semaphore=asyncio.Semaphore(1),
                )
            )
    return result

async def measure_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str]],
    backends: list[Backend[Any]],
) -> list[Measurement]:
    calls = []
    for candidate_id, variant_id, module_path, compensation in variants:
        for backend in backends:
            for precision in config.measure.precisions:
                calls.append(
                    backend.measure(
                        config,
                        oracle,
                        module_path,
                        candidate_id=candidate_id,
                        variant_id=variant_id,
                        precision=precision,
                        compensation=compensation,
                    )
                )
    return list(await asyncio.gather(*calls))

async def measure_compensation_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str, str, str]],
    backends: list[Backend[Any]],
) -> list[Measurement]:
    """Broadcast portable numerical variants across every configured backend and precision.

    The target backend/precision fields are retained in the tuple for artifact compatibility,
    but no longer restrict measurement. Platform-specific compatibility branches are created
    only after this complete numerical probe.
    """
    results: list[Measurement] = []
    for (
        candidate_id,
        variant_id,
        module_path,
        compensation,
        target_backend,
        target_precision,
    ) in variants:
        del target_backend, target_precision
        for backend in backends:
            for precision in config.measure.precisions:
                seeds = (
                    config.measure.stochastic_seeds if compensation == "stochastic-round" else [0]
                )
                samples = await asyncio.gather(
                    *(
                        backend.measure(
                            config,
                            oracle,
                            module_path,
                            candidate_id=candidate_id,
                            variant_id=variant_id,
                            precision=precision,
                            compensation=compensation,
                            seed=seed,
                        )
                        for seed in seeds
                    )
                )
                primary = samples[0]
                if len(samples) > 1:
                    primary.stochastic_samples = [
                        {
                            "seed": seed,
                            "status": sample.status.value,
                            "latency_s": sample.latency_s,
                            "max_rel_error": sample.max_rel_error,
                            "relative_l2": sample.relative_l2,
                        }
                        for seed, sample in zip(seeds, samples, strict=False)
                    ]
                    valid_latencies = [
                        sample.latency_s for sample in samples if sample.latency_s is not None
                    ]
                    valid_rel = [
                        sample.max_rel_error
                        for sample in samples
                        if sample.max_rel_error is not None
                    ]
                    if valid_latencies:
                        primary.latency_s = statistics.median(valid_latencies)
                    if valid_rel:
                        primary.max_rel_error = statistics.mean(valid_rel)
                    if any(sample.status != Status.OK for sample in samples):
                        primary.status = Status.DIVERGED
                results.append(primary)
    return results
