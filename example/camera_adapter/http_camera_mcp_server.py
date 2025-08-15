import uvicorn
from fastapi import FastAPI

from src.adapter import get_all_adapters
from src.core.config.setting import LOGGER, GlobalConfig
from src.core.mcp.server import MCPServer, JSONRPCResponse, JSONRPCRequest

# ---------- FastAPI ----------
mcp = MCPServer()
CFG = GlobalConfig.load()
app = FastAPI(title="MCP-HTTP")

@app.post("/invoke", response_model=JSONRPCResponse)
async def invoke(req: JSONRPCRequest):
    LOGGER.info("RPC request: %s", req)
    return await mcp.call(req)

# ---------- 生命周期 ----------
@app.on_event("startup")
async def startup_event():
    """在应用启动时一次性注册 adapter"""
    adapters = get_all_adapters()
    for adapter in adapters:
        mcp.add_adapter(adapter.name, adapter)
    LOGGER.info("✅ Registered adapters: %s", list(mcp.adapters.keys()))

# ---------- 启动 ----------
if __name__ == "__main__":
    uvicorn.run(
        "http_camera_mcp_server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        access_log=True,
        use_colors=True
    )