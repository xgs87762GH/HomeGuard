from typing import Dict, Any

from pydantic import BaseModel


class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Any = None
    @staticmethod
    def parse_error(msg: str = "Parse error") -> "JSONRPCError":
        return JSONRPCError(code=-32700, message=msg)

    @staticmethod
    def invalid_request(msg: str = "Invalid Request") -> "JSONRPCError":
        return JSONRPCError(code=-32600, message=msg)

    @staticmethod
    def method_not_found(msg: str = "Method not found") -> "JSONRPCError":
        return JSONRPCError(code=-32601, message=msg)

    @staticmethod
    def invalid_params(msg: str = "Invalid params") -> "JSONRPCError":
        return JSONRPCError(code=-32602, message=msg)

    @staticmethod
    def internal_error(msg: str = "Internal error") -> "JSONRPCError":
        return JSONRPCError(code=-32603, message=msg)

    @staticmethod
    def custom(code: int, msg: str, data: Any = None) -> "JSONRPCError":
        return JSONRPCError(code=code, message=msg, data=data)

# ---------- 数据模型 ----------
class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str = "camera.take_photo"
    params: Dict[str, Any]


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: str | int | None
    result: Any = None
    error: JSONRPCError | None = None
