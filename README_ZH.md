# HomeGuard · AI 摄像头小助手  
**FastAPI + MCP 服务器**  |  **一句中文即可拍照 / 录像 / 调参**

> 把摄像头变成 AI 的小跟班：对着大模型说一句“拍张照”，立刻咔嚓！  
> 支持 OpenAI、Claude、本地模型，通过 MCP 协议即插即用。

---

## 🚀 30 秒上手

```bash
git clone https://github.com/xgs87762GH/HomeGuard.git
cd HomeGuard
pip install -r requirements.txt
python main.py            # http://localhost:8001/docs
```

MCP 客户端（Cursor、Claude Desktop 等）填写地址  
`http://localhost:8001/mcp`，即可中文对话：

> “帮我拍张自拍。”  
> “录 15 秒视频。”  
> “亮度高一点，分辨率 1920×1080。”

---

## 📦 MCP 工具速查

| 工具名 | 中文示例 | 自动生成文件名 |
|---|---|---|
| **take_photo** | “拍张照” | ✅ |
| **record_video** | “录 15 秒” | ✅ |
| **set_camera_parameters** | “提高亮度” | — |

参数见 `camera_schema.json`，留空文件名即 **时间戳自动命名**。

---

## 🗂️ 项目结构

```
HomeGuard
├── main.py                 # FastAPI 入口 + 生命周期
├── configs/config.yml      # 配置 + 环境变量覆盖
├── src
│   ├── adapter/camera      # OpenCV 驱动 + MCP 适配器
│   ├── core/config         # pydantic-settings 配置加载
│   ├── routers             # REST & MCP 路由
│   ├── db                  # 异步 SQLite + 模型
│   └── scheduler           # 后台任务调度
├── data/homeguard.db       # 任务与元数据
└── output/YYYY/MM/DD/      # 媒体文件按日期归档
```

---

## ⚙️ 配置示例

`configs/config.yml`

```yaml
app:
  env: dev                 # dev | prod
ai:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o-mini
database:
  dev:
    driver: mysql+asyncmy
    host: 192.168.110.126
    port: 3306
    database: homeguard
```

支持环境变量覆盖：`APP__AI__OPENAI__API_KEY=sk-xxx`

---

## 🛠️ 开发调试

```bash
uvicorn main:app --reload --port 8001
pytest tests/             # 即将上线
```

---

## 📄 开源协议

MIT © 2025 [HomeGuard 团队](https://github.com/xgs87762GH/HomeGuard)