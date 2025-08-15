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
        # self.adapters: dict[str, BaseAdapter] = {}
        self.server = MCPServer()
        self._load_all()
        self.task_repo = TaskRepository(session)

    async def execute(self, task_id: int) -> None:
        """
        Public interface: Execute a single task
        Called by TaskScheduler, CLI, and unit tests.
        """
        task = await self.task_repo.get(task_id)
        if task.status != TaskStatus.PENDING and not (
                task.status == TaskStatus.RETRY and task.retry_count <= 3):
            return

        await self.task_repo.update(task.id, status=TaskStatus.RUNNING, started_at=TimeUtils.now_utc())

        # Structure JSON-RPC request
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
            else:
                task.result = resp.result
                task.status = TaskStatus.SUCCESS
        except Exception as e:
            task.error_msg = str(e)
            task.retry_count += 1
            if task.retry_count >= 3:
                task.status = TaskStatus.FAILED
            else:
                task.status = TaskStatus.RETRY
                task.next_retry_at = TimeUtils.now_utc() + datetime.timedelta(minutes=task.retry_count)
        task.finished_at = TimeUtils.now_utc()
        await self.task_repo.update(task_id, **task.__dict__)

    def _load_all(self):
        from src.adapter import get_all_adapters
        for adapter in get_all_adapters():
            # self.adapters[adapter.name] = adapter
            self.server.add_adapter(adapter.name, adapter)


class TaskScheduler:
    def __init__(self):
        self.engine_factory = lambda session: TaskEngine(session)
        self.repo_factory = lambda session: TaskRepository(session)

    async def poll_once(self, limit: int = 10):
        LOGGER.info("Polling DB for pending tasks...")
        async with async_session() as session:
            repo = self.repo_factory(session)
            tasks = await repo.list_by_pending(limit)

        # Create a brand-new session for every task
        for task in tasks:
            asyncio.create_task(self._execute_task(task.id))

    async def _execute_task(self, task_id: int):
        async with async_session() as session:
            engine = self.engine_factory(session)
            await engine.execute(task_id)

    async def poll_forever(self, interval: int = 5) -> None:
        """Poll the database every `interval` seconds and run pending tasks."""
        while True:
            await self.poll_once()
            await asyncio.sleep(interval)
