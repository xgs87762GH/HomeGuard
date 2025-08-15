from fastapi import APIRouter, HTTPException

from src.core.db import async_session
from src.core.db.models.task import TaskStatus
from src.core.db.repositories.task_repo import TaskRepository
from src.core.mcp.schemas import JSONRPCRequest, JSONRPCResponse
from src.core.config.setting import LOGGER

router = APIRouter(tags=["Invoke"])


@router.post("/invoke", response_model=JSONRPCResponse)
async def invoke(req: JSONRPCRequest):
    """
    Receive JSON-RPC request → Create task → Immediately return task_id
    """
    LOGGER.info("RPC request: %s", req)

    # Split adapter.method
    try:
        adapter, method = req.method.split(".", 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="method format should be adapter.method")

    async with async_session() as session:
        repo = TaskRepository(session)
        task = await repo.create(
            adapter_name=adapter,
            method_name=method,
            params=req.params or {},
            status=TaskStatus.PENDING,
        )

    return JSONRPCResponse(id=req.id, result={"task_id": task.id, "status": task.status})
