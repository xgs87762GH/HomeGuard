import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.core.config.setting import GlobalConfig, LOGGER
from src.core.db import create_tables
from src.core.scheduler.task_scheduler import TaskScheduler
from src.routers.root import router as root_router
from src.routers.task import router as task_router

CFG = GlobalConfig.load()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------- Startup ----------
    await create_tables()
    scheduler = TaskScheduler()
    poll_task = asyncio.create_task(scheduler.poll_forever(interval=10))
    LOGGER.info("Task scheduler started in background")
    yield  # FastAPI starts receiving requests
    # ---------- Shutdown ----------
    poll_task.cancel()
    await poll_task  # Wait for the task to actually finish
    LOGGER.info("Task scheduler stopped")


app = FastAPI(
    title="HomeGuard",
    description="HomeGuard API",
    version="0.0.1",
    lifespan=lifespan  # Using lifespan hook
)
app.include_router(root_router)
app.include_router(task_router)

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8001, log_level="info", workers=1)
