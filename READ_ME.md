

> pipreqs . --encoding=utf8 --force

HomeGuard/
├── app/                    # FastAPI + MCP 核心
│   ├── __init__.py
│   ├── main.py             # uvicorn 入口
│   ├── api/                # REST / MCP 路由
│   │   ├── __init__.py
│   │   ├── camera_router.py
│   │   └── health_router.py
│   ├── core/               # 全局配置、依赖、生命周期
│   │   ├── __init__.py
│   │   ├── config.py       # 所有 pydantic-settings
│   │   └── logging.py
│   └── models/             # Pydantic 请求/响应模型
│       ├── __init__.py
│       └── schemas.py
├── adapters/               # 硬件或协议适配器（关键：一个适配器一个包）
│   ├── __init__.py
│   ├── camera/
│   │   ├── __init__.py
│   │   ├── camera_tools.py # 重构后的 CameraTools
│   │   ├── camera.py       # 抽象相机接口 & Cv2Camera 实现
│   │   └── config.py       # CameraConfig
│   └── rtsp/               # 以后支持 RTSP/ONVIF
│       ├── __init__.py
│       └── rtsp_camera.py
├── services/               # 业务层（拍照/录像/定时任务）
│   ├── __init__.py
│   ├── task_service.py     # 任务表 CRUD
│   └── scheduler.py        # schedule / APScheduler
├── storage/                # 数据库 & 文件
│   ├── __init__.py
│   ├── db.py               # 创建 sqlite 连接 & 迁移
│   ├── migrations/         # alembic 或手动 sql
│   └── output/             # 照片/视频落盘目录（.gitignore）
├── tests/                  # pytest
│   ├── __init__.py
│   ├── conftest.py
│   └── test_camera.py
├── requirements.txt        # 生产依赖
├── requirements-dev.txt    # 测试/格式化/热重载
├── .env.example            # 环境变量模板
├── .gitignore
├── Dockerfile              # 可选：容器化
└── README.md