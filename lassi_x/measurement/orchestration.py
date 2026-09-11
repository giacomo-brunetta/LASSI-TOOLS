from __future__ import annotations

import asyncio
import statistics
from typing import TYPE_CHECKING, Any

from ..types import Status
from .groq import GroqBackend
from .native import NativeBackend
from .torch import TorchBackend

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from ..config import RunConfig
    from ..execution import ExecutionContext
    from ..scheduler import PipelineScheduler
    from ..types import Measurement
    from ..validation import OracleResult
    from .common import Backend


def build_backends(
    config: RunConfig,
    execution: ExecutionContext,
    scheduler: PipelineScheduler | None = None,
) -> list[Backend[Any]]:
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
    torch_lock = (
        asyncio.Semaphore(1)
        if scheduler is None and config.measure.serialize_torch_backends
        else None
    )
    for spec in config.measure.backends:
        resource = spec.resource or execution.default_resource
        resource_slot = scheduler.resource_slot(resource) if scheduler is not None else None
        if spec.type == "torch":
            result.append(
                TorchBackend(
                    spec,
                    execution.backend(spec.resource),
                    resource,
                    semaphore=resource_slot or torch_lock,
                )
            )
        elif spec.type == "groq":
            if spec.queue_dir is not None:
                result.append(
                    GroqBackend(
                        spec,
                        resource=resource,
                        semaphore=resource_slot or asyncio.Semaphore(1),
                    )
                )
            else:
                result.append(
                    GroqBackend(
                        spec,
                        execution.backend(spec.resource),
                        resource,
                        semaphore=resource_slot or asyncio.Semaphore(1),
                    )
                )
        else:
            result.append(
                NativeBackend(
                    spec,
                    execution.backend(spec.resource),
                    resource,
                    semaphore=resource_slot or asyncio.Semaphore(1),
                )
            )
    return result


async def measure_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str]],
    backends: list[Backend[Any]],
    *,
    cells: set[tuple[str, str]] | None = None,
    on_result: Callable[[Measurement], None] | None = None,
) -> list[Measurement]:
    calls = []
    for candidate_id, variant_id, module_path, compensation in variants:
        for backend in backends:
            for precision in config.measure.precisions:
                if cells is not None and (backend.spec.name, precision) not in cells:
                    continue
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
    if on_result is None:
        return list(await asyncio.gather(*calls))
    results: list[Measurement] = []
    for call in asyncio.as_completed(calls):
        result = await call
        results.append(result)
        on_result(result)
    return results


async def _measure_compensated_cell(
    config: RunConfig,
    oracle: OracleResult,
    backend: Backend[Any],
    *,
    candidate_id: str,
    variant_id: str,
    module_path: Path,
    compensation: str,
    precision: str,
) -> Measurement:
    seeds = config.measure.stochastic_seeds if compensation == "stochastic-round" else [0]
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
        valid_latencies = [sample.latency_s for sample in samples if sample.latency_s is not None]
        valid_rel = [sample.max_rel_error for sample in samples if sample.max_rel_error is not None]
        if valid_latencies:
            primary.latency_s = statistics.median(valid_latencies)
        if valid_rel:
            primary.max_rel_error = statistics.mean(valid_rel)
        if any(sample.status != Status.OK for sample in samples):
            primary.status = Status.DIVERGED
    return primary


async def measure_compensation_variants(
    config: RunConfig,
    oracle: OracleResult,
    variants: list[tuple[str, str, Path, str, str, str]],
    backends: list[Backend[Any]],
    *,
    on_result: Callable[[Measurement], None] | None = None,
) -> list[Measurement]:
    """Broadcast portable numerical variants across every configured backend and precision.

    The target backend/precision fields are retained in the tuple for artifact compatibility,
    but no longer restrict measurement. Platform-specific compatibility branches are created
    only after this complete numerical probe.
    """
    calls = []
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
                calls.append(
                    _measure_compensated_cell(
                        config,
                        oracle,
                        backend,
                        candidate_id=candidate_id,
                        variant_id=variant_id,
                        module_path=module_path,
                        compensation=compensation,
                        precision=precision,
                    )
                )
    if on_result is None:
        return list(await asyncio.gather(*calls))
    results: list[Measurement] = []
    for call in asyncio.as_completed(calls):
        result = await call
        results.append(result)
        on_result(result)
    return results
