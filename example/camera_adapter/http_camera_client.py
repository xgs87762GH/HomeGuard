# https_mcp_client.py
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import httpx
from openai import AsyncOpenAI

from src.core.config.setting import LOGGER, GlobalConfig

CFG = GlobalConfig.load()

logging.getLogger("httpx").setLevel(logging.WARNING)

OPENAI_MODEL = CFG.ai.openai["model"]
OPENAI_KEY = CFG.ai.openai["api_key"]
HTTPS_MCP_URL = "http://192.168.110.126:8001/invoke"

client = AsyncOpenAI(api_key=OPENAI_KEY, base_url=os.getenv("OPENAI_BASE_URL"))

# ---------- 读取 schema ----------
BASE_DIR = Path(__file__).resolve().parent
FUNC_FILE = BASE_DIR / "schemas" / "camera_functions.json"
SCHEMA_FILE = BASE_DIR / "schemas" / "camera_schema.json"

FUNCTIONS = json.loads(FUNC_FILE.read_text(encoding="utf-8"))
SCHEMA_DIC = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def build_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": fn["name"],
                "description": fn["description"],
                "parameters": SCHEMA_DIC["definitions"][fn["parameters"]["$ref"].split("/")[-1]]
            }
        }
        for fn in FUNCTIONS
    ]


# ---------- 调用 MCP ----------
async def call_mcp(fn_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": f"camera.{fn_name}",
        "params": args
    }
    async with httpx.AsyncClient(timeout=10) as http:
        resp = await http.post(HTTPS_MCP_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("error"):
            raise RuntimeError(data["error"])
        return data["result"]


# ---------- 主流程 ----------
async def chat_with_camera(prompt: str) -> str:
    tools = build_tools()
    messages = [{"role": "user", "content": prompt}]
    logging.info("👤 用户: %s", prompt)

    while True:
        try:
            completion = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
            assistant_msg = completion.choices[0].message
            messages.append(assistant_msg)

            if not assistant_msg.tool_calls:
                break

            for call in assistant_msg.tool_calls:
                func_name = call.function.name
                func_args = json.loads(call.function.arguments)
                result = await call_mcp(func_name, func_args)
                # logging.info("🤖 %s -> %s", func_name, result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result),
                })
                # logging.info("✅ %s -> %s", func_name, result)
        except Exception:
            LOGGER.exception("❌ 调用失败")
            break

    return assistant_msg.content


# ---------- CLI ----------
async def main():
    try:
        reply = await chat_with_camera("帮我拍摄一张照片")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("再拍一张")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("再拍一张，文件名为photo.jpg")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("再拍一张")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("录制视频")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("录制5秒的视频")
        LOGGER.info("🤖AI智能体: %s \n", reply)

        reply = await chat_with_camera("再录制一个")
        LOGGER.info("🤖AI智能体: %s \n", reply)
    except Exception as e:
        print("发生错误，请检查网络或服务器：", e)


if __name__ == "__main__":
    asyncio.run(main())
