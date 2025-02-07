import asyncio
import typing
from asyncio import Future, Task

if typing.TYPE_CHECKING:
    from fastapi import FastAPI


class Worker:
    def __init__(self, app: "FastAPI") -> None:
        self.app = app
        self.is_running = False
        self.work_task: Task | None = None

    @property
    def logger(self):
        return self.app.config.logger

    @property
    def queue(self):
        return self.app.storage.que

    def start(self) -> None:
        self.is_running = True
        self.work_task = asyncio.create_task(self.queue.receive_from_queue())
        self.work_task.add_done_callback(self._done_callback)

    async def stop(self) -> None:
        self.is_running = False
        # if self.work_task:
        #     self.work_task.cancel()
        if self.work_task:
            await self.work_task

    def _done_callback(self, result: Future) -> None:
        if result.exception():
            self.logger.exception(
                "worker had exception", exc_info=result.exception()
            )
            self.is_running = False  # my, needed?
        if self.is_running:
            self.start()
