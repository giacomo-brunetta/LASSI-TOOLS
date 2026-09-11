from __future__ import annotations

import asyncio

from lassi_x.config import SchedulerConfig
from lassi_x.scheduler import PipelineScheduler


def test_scheduler_enforces_shared_model_and_resource_capacity() -> None:
    scheduler = PipelineScheduler(
        SchedulerConfig(
            max_model_sessions=2,
            resource_concurrency={"accelerator": 2},
        )
    )
    model_release = asyncio.Event()
    resource_release = asyncio.Event()
    model_active = 0
    resource_active = 0
    model_maximum = 0
    resource_maximum = 0

    async def model_work() -> None:
        nonlocal model_active, model_maximum
        model_active += 1
        model_maximum = max(model_maximum, model_active)
        await model_release.wait()
        model_active -= 1

    async def resource_work() -> None:
        nonlocal resource_active, resource_maximum
        async with scheduler.resource_slot("accelerator"):
            resource_active += 1
            resource_maximum = max(resource_maximum, resource_active)
            await resource_release.wait()
            resource_active -= 1

    async def exercise() -> None:
        model_tasks = [asyncio.create_task(scheduler.run_model(model_work)) for _ in range(4)]
        resource_tasks = [asyncio.create_task(resource_work()) for _ in range(4)]
        for _ in range(20):
            if model_active == 2 and resource_active == 2:
                break
            await asyncio.sleep(0)
        assert model_active == 2
        assert resource_active == 2
        model_release.set()
        resource_release.set()
        await asyncio.gather(*model_tasks, *resource_tasks)

    asyncio.run(exercise())
    assert model_maximum == 2
    assert resource_maximum == 2
    assert scheduler.resource_slot("accelerator") is scheduler.resource_slot("accelerator")
