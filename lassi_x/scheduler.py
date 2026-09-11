"""Central concurrency policy for model sessions and compute resources."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .config import SchedulerConfig

ResultT = TypeVar("ResultT")


class PipelineScheduler:
    """Own shared semaphores instead of letting stages invent concurrency."""

    def __init__(self, config: SchedulerConfig) -> None:
        self.config = config
        self.model_slots = asyncio.Semaphore(config.max_model_sessions)
        self.candidate_slots = asyncio.Semaphore(config.max_candidate_flows)
        self._resource_slots: dict[str, asyncio.Semaphore] = {}

    def resource_slot(self, resource: str) -> asyncio.Semaphore:
        """Return the one shared capacity limit for a compute resource."""

        if resource not in self._resource_slots:
            limit = self.config.resource_concurrency.get(
                resource,
                self.config.default_resource_concurrency,
            )
            self._resource_slots[resource] = asyncio.Semaphore(limit)
        return self._resource_slots[resource]

    async def run_model(self, work: Callable[[], Awaitable[ResultT]]) -> ResultT:
        """Run one persistent model session within the configured global bound."""

        async with self.model_slots:
            return await work()

    async def run_candidate(self, work: Callable[[], Awaitable[ResultT]]) -> ResultT:
        """Run one end-to-end candidate flow within the pipeline bound."""

        async with self.candidate_slots:
            return await work()
