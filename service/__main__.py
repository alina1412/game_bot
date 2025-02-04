import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from service.config import Storage, get_config, logger
from service.db_setup.db_connector import DbConnector
from service.endpoints.data_handlers import api_router as data_routes
from service.endpoints.put_handlers import api_router as put_routes
from service.endpoints.update_handlers import api_router as upd_routes


async def task_main():
    while True:
        ...
        await asyncio.sleep(5)


class BackgroundTask:
    async def long_running_task(self):
        logger.info("started long_running_task")
        # poll_task = asyncio.create_task(task_main())
        # await asyncio.sleep(5)
        # await poll_task


bgtask = BackgroundTask()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load
    await asyncio.sleep(1)
    await app.db.connect()
    await app.storage.que.connect()
    await app.storage.vk_api.connect()
    # task = asyncio.create_task(bgtask.long_running_task())
    yield
    await app.storage.vk_api.disconnect()
    await app.storage.que.disconnect()
    await app.db.disconnect()

    # # # Clean up
    # task.cancel()
    # try:
    #     await task
    # except asyncio.CancelledError:
    #     logger.error("lifespan(): long_running_task is cancelled now")


app = FastAPI(lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="api for a game bot",
        version="2.5.0",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        },
        "apiKey": {
            "type": "apiKey",
            "name": "client_secret",
            "in": "header",
            "scheme": "apiKey",
        },
    }
    openapi_schema["security"] = [
        {"bearerAuth": ["read", "write"], "apiKey": ["read", "write"]}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.include_router(put_routes)
app.include_router(upd_routes)
app.include_router(data_routes)
app.openapi = custom_openapi
app.config = get_config()
app.storage = Storage(app)
app.db = DbConnector(app)

if __name__ == "__main__":
    uvicorn.run(
        "service.__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["service"],
    )
