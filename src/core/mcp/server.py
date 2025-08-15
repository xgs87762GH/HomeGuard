import asyncio
import logging

from src.core.config.setting import LOGGER
from src.core.mcp.schemas import JSONRPCRequest, JSONRPCResponse, JSONRPCError
from typing import Dict, Any


class MCPServer:
    def __init__(self) -> None:
        self.adapters: Dict[str, Any] = {}

    def add_adapter(self, name: str, adapter) -> None:
        self.adapters[name] = adapter

    async def call(self, req: JSONRPCRequest) -> JSONRPCResponse:
        full_name: str = req.method
        params: Dict[str, Any] = req.params or {}

        if "." not in full_name:
            LOGGER.warning("Invalid method format: %s", full_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.invalid_request("Invalid method format"))

        adapter_name, method_name = full_name.rsplit(".", 1)

        if adapter_name not in self.adapters:
            LOGGER.warning("Adapter '%s' not found", adapter_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.method_not_found("Adapter not found"))

        method = getattr(self.adapters[adapter_name], method_name, None)
        if method is None:
            LOGGER.warning("Method '%s' not found in adapter '%s'", method_name, adapter_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.method_not_found("Method not found"))

        try:
            result = await method(**params) if asyncio.iscoroutinefunction(method) else method(**params)

            if result.get("status", "").upper() == "SUCCESS":
                LOGGER.info("✅ %s.%s executed successfully -> %s", adapter_name, method_name, result)
                return JSONRPCResponse(id=req.id, result=result.get("data"))
            else:
                return JSONRPCResponse(id=req.id,
                                       error=JSONRPCError.custom(-32000, result.get("message", "Execution failed"),
                                                                 result.get("data")))

        except Exception as exc:
            LOGGER.exception("❌ %s.%s call failed: %s", adapter_name, method_name, exc)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.internal_error(str(exc)))
