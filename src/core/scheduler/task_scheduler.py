import asyncio
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config.setting import LOGGER
from src.core.db import async_session
from src.core.db.models.task import TaskStatus
from src.core.db.repositories.task_repo import TaskRepository
from src.core.mcp.schemas import JSONRPCRequest, JSONRPCResponse
from src.core.mcp.server import MCPServer
from src.core.utils.time_utils import TimeUtils


class TaskEngine:
    def __init__(self, session: AsyncSession):
        self.server = MCPServer()
        self._register_providers()
        self.task_repo = TaskRepository(session)

    async def execute(self, task_id: int) -> None:
        """
        执行单个任务（供调度器、CLI、单元测试调用）
        """
        task = await self.task_repo.get(task_id)
        if not self._should_execute(task):
            return

        await self.task_repo.update(task.id, status=TaskStatus.RUNNING, started_at=TimeUtils.now_utc())

        req = JSONRPCRequest(
            jsonrpc="2.0",
            id=str(task.id),
            method=f"{task.adapter_name}.{task.method_name}",
            params=task.params
        )

        try:
            resp: JSONRPCResponse = await self.server.call(req=req)
            if resp.error:
                raise RuntimeError(resp.error)
            task.result = resp.result
            task.status = TaskStatus.SUCCESS
        except Exception as exc:
            task.error_msg = str(exc)
            task.retry_count += 1
            if task.retry_count >= 3:
                task.status = TaskStatus.FAILED
            else:
                task.status = TaskStatus.RETRY
                task.next_retry_at = TimeUtils.now_utc() + datetime.timedelta(minutes=task.retry_count)
        finally:
            task.finished_at = TimeUtils.now_utc()
            await self.task_repo.update(task_id, **task.__dict__)

    def _should_execute(self, task) -> bool:
        return (
            task.status == TaskStatus.PENDING or
            (task.status == TaskStatus.RETRY and task.retry_count <= 3)
        )

    def _register_providers(self):
        from src.providers import get_all_providers
        for provider in get_all_providers():
            self.server.add_provider(provider.name, provider)


class TaskScheduler:
    def __init__(self):
        self.create_engine = lambda session: TaskEngine(session)
        self.create_repo = lambda session: TaskRepository(session)

    async def poll_once(self, limit: int = 10):
        LOGGER.info("Polling DB for pending tasks...")
        async with async_session() as session:
            repo = self.create_repo(session)
            tasks = await repo.list_by_pending(limit)

        for task in tasks:
            asyncio.create_task(self._run_task(task.id))

    async def _run_task(self, task_id: int):
        async with async_session() as session:
            engine = self.create_engine(session)
            await engine.execute(task_id)

    async def poll_forever(self, interval: int = 5) -> None:
        """每隔 interval 秒轮询数据库并执行待处理任务"""
        while True:
            await self.poll_once()
            await asyncio.sleep(interval)
