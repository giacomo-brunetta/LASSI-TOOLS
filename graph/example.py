import asyncio
from concurrent.futures import ThreadPoolExecutor

from academy.agent import action
from academy.agent import Agent
from academy.handle import Handle

from academy.agent import Agent, action
from academy.exchange import LocalExchangeFactory
from academy.logging.recommended import recommended_logging
from academy.manager import Manager, logger


class Lowerer(Agent):
    @action
    async def lower(self, text: str) -> str:
        return text.lower()


class Reverser(Agent):
    @action
    async def reverse(self, text: str) -> str:
        return text[::-1]
    
class Coordinator(Agent):
    def __init__(
        self,
        lowerer: Handle[Lowerer],
        reverser: Handle[Reverser],
    ) -> None:
        super().__init__()
        self.lowerer = lowerer
        self.reverser = reverser

    @action
    async def process(self, text: str) -> str:
        text = await self.lowerer.lower(text)
        text = await self.reverser.reverse(text)
        return text


async def main() -> None:

    async with await Manager.from_exchange_factory(
        factory=LocalExchangeFactory(),
        executors=ThreadPoolExecutor(),
        log_config=recommended_logging(),
    ) as manager:
        lowerer = await manager.launch(Lowerer)
        reverser = await manager.launch(Reverser)
        coordinator = await manager.launch(
            Coordinator,
            args=(lowerer, reverser),
        )

        text = 'DEADBEEF'
        expected = 'feebdaed'

        logger.info('Invoking process("%s") on %s', text, coordinator.agent_id)
        result = await coordinator.process(text)
        assert result == expected
        logger.info('Received result: "%s"', result)

if __name__ == '__main__':
    asyncio.run(main())