import asyncio
import logging

from src.core.config.setting import LOGGER
from src.core.mcp.schemas import JSONRPCRequest, JSONRPCResponse, JSONRPCError
from typing import Dict, Any


class MCPServer:
    def __init__(self) -> None:
        self.provider_map: Dict[str, Any] = {}

    def add_provider(self, name: str, provider) -> None:
        self.provider_map[name] = provider

    async def call(self, req: JSONRPCRequest) -> JSONRPCResponse:
        method_full_name: str = req.method
        method_params: Dict[str, Any] = req.params or {}

        if "." not in method_full_name:
            LOGGER.warning("Invalid method format: %s", method_full_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.invalid_request("Invalid method format"))

        provider_name, method_name = method_full_name.rsplit(".", 1)

        provider = self.provider_map.get(provider_name)
        if not provider:
            LOGGER.warning("Provider '%s' not found", provider_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.method_not_found("Provider not found"))

        provider_method = getattr(provider, method_name, None)
        if provider_method is None:
            LOGGER.warning("Method '%s' not found in provider '%s'", method_name, provider_name)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.method_not_found("Method not found"))

        try:
            result = await provider_method(**method_params) if asyncio.iscoroutinefunction(provider_method) else provider_method(**method_params)
            status = result.get("status", "").upper()
            if status == "SUCCESS":
                LOGGER.info("✅ %s.%s executed successfully -> %s", provider_name, method_name, result)
                return JSONRPCResponse(id=req.id, result=result.get("data"))
            else:
                return JSONRPCResponse(
                    id=req.id,
                    error=JSONRPCError.custom(-32000, result.get("message", "Execution failed"), result.get("data"))
                )
        except Exception as exc:
            LOGGER.exception("❌ %s.%s call failed: %s", provider_name, method_name, exc)
            return JSONRPCResponse(id=req.id, error=JSONRPCError.internal_error(str(exc)))
