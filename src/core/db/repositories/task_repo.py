# src/core/db/repositories/task_repo.py
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.models.task import Task, TaskStatus
from src.core.utils.time_utils import TimeUtils


class TaskRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # region 基础 CRUD ---------------------------------------------------------
    async def create(self, **kwargs) -> Task:
        task = Task(**kwargs)
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get(self, task_id: int) -> Optional[Task]:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.deleted_at.is_(None)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, task_id: int, **kwargs) -> Optional[Task]:
        task = await self.get(task_id)
        if not task:
            return None
        for k, v in kwargs.items():
            setattr(task, k, v)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def delete(self, task_id: int) -> bool:
        task = await self.get(task_id)
        if not task:
            return False
        task.deleted_at = TimeUtils.now_utc()
        await self.session.commit()
        return True

    # endregion

    # region 业务查询 ----------------------------------------------------------
    async def list_by_pending(self, limit: int = None) -> List[Task]:
        """
        返回所有待处理的任务：
        1. status = PENDING 且未被软删除
        2. status = RETRY 且 next_retry_at <= 当前 UTC 时间 且未被软删除
        """
        now_utc = TimeUtils.now_utc()
        stmt = (
            select(Task)
            .where(
                (
                        (Task.status == TaskStatus.PENDING) &
                        Task.deleted_at.is_(None)
                )
                |
                (
                        (Task.status == TaskStatus.RETRY) &
                        Task.next_retry_at.is_not(None)
                        # &
                        # (Task.next_retry_at <= now_utc) &
                        # Task.deleted_at.is_(None)
                )
            )
            .limit(limit)
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
