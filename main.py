import asyncio

import uvicorn
from fastapi import FastAPI

from src.core.config.setting import setup_logging, load_config
from src.core.db import create_tables, async_session
from src.core.scheduler.task_scheduler import TaskEngine, TaskScheduler
from src.routers.root import router as root_router
from src.routers.task import router as task_router

setup_logging()
load_config("dev")
app = FastAPI(title="HomeGuard", description="HomeGuard API", version="0.0.1")

app.include_router(root_router)
app.include_router(task_router)


@app.on_event("startup")
async def start_scheduler():
    await create_tables()
    scheduler = TaskScheduler()
    asyncio.create_task(scheduler.poll_forever(interval=10))

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info", workers=1)
