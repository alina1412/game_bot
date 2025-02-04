import asyncio
import typing
from asyncio import Future, Task

# from service.config import logger

if typing.TYPE_CHECKING:
    from fastapi import FastAPI

    # from service.vk_api.accessor import VkApiAccessor


class Poller:
    def __init__(self, app: "FastAPI") -> None:
        self.app = app
        self.is_running = False
        self.poll_task: Task | None = None

    @property
    def logger(self):
        return self.app.config.logger

    @property
    def vk_api(self):
        return self.app.storage.vk_api

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            self.logger.exception(
                "poller stopped with exception", exc_info=result.exception()
            )
            self.is_running = False  # my, needed?
        if self.is_running:
            self.start()

    def start(self) -> None:
        self.is_running = True

        self.poll_task = asyncio.create_task(self.poll())
        self.poll_task.add_done_callback(self._done_callback)

    async def stop(self) -> None:
        self.is_running = False

        await self.poll_task

    async def poll(self) -> None:
        while self.is_running:
            if self.vk_api.server:
                await self.vk_api.poll()
            else:
                await asyncio.sleep(1)
