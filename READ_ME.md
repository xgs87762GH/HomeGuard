# HomeGuard 项目架构

## 🏗️ 架构模式

### 核心架构图

```mermaid
graph TB
    subgraph "应用层"
        APP[main.py]
        API[routers/]
    end
    
    subgraph "核心层"
        CORE[core/]
        CONFIG[config/]
        DB[db/]
        SCHED[scheduler/]
    end
    
    subgraph "功能层 - Provider模式"
        AUTO[自动发现系统]
        BASE[BaseProvider]
        CAM[CameraProvider]
        OTHER[其他Provider...]
    end
    
    APP --> API
    APP --> CORE
    API --> AUTO
    AUTO --> BASE
    BASE --> CAM
    BASE --> OTHER
    CORE --> CONFIG
    CORE --> DB
    CORE --> SCHED
```

### Provider 自动发现模式

```mermaid
flowchart LR
    A[扫描目录] --> B[文件过滤]
    B --> C[自动导入]
    C --> D[类发现]
    D --> E[实例化]
    E --> F[自动注册]
    
    style A fill:#e3f2fd
    style F fill:#c8e6c9
```

## 📁 项目结构

```
HomeGuard/
├── main.py                    # 入口
├── configs/config.yml         # 配置
├── src/
│   ├── core/                  # 核心模块
│   │   ├── config/           # 配置管理
│   │   ├── db/               # 数据库层
│   │   ├── scheduler/        # 任务调度
│   │   └── utils/            # 工具函数
│   ├── providers/            # 🔑 Provider模式
│   │   ├── __init__.py       # 自动发现系统
│   │   ├── base_provider.py  # 基类
│   │   └── camera/           # 相机模块
│   └── routers/              # API路由
└── example/                   # 示例代码
```

## 🎯 设计模式

### 1. Provider 模式
- **自动发现**: 零配置加载新模块
- **插件化**: 继承 `BaseProvider` 即可
- **配置驱动**: YAML 控制启用状态

### 2. 仓储模式
- **数据抽象**: `repositories/` 层
- **模型分离**: `models/` 定义
- **统一接口**: 标准数据访问

### 3. 分层架构
- **应用层**: 程序入口和路由
- **核心层**: 基础服务和工具
- **功能层**: 业务模块 (Provider)

## 🚀 核心特性

```mermaid
graph LR
    A[零配置] --> B[自动发现]
    B --> C[插件化]
    C --> D[异步支持]
    D --> E[配置驱动]
    
    style A fill:#fff3e0
    style E fill:#e8f5e8
```

- ✅ **零配置扩展**: 新 Provider 自动加载
- ✅ **异步优先**: 支持高并发
- ✅ **模块化**: 功能独立封装
- ✅ **容错设计**: 单模块失败不影响整体

## 📋 当前实现

- **Camera Provider**: 拍照、录像、参数控制
- **Task System**: 任务调度和管理
- **MCP Protocol**: 协议服务支持
- **Config Management**: YAML 配置系统