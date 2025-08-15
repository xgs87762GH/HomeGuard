# src/core/config/settings.py
from __future__ import annotations

import logging
import logging.config
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field

YAML_PATH = Path(__file__).resolve().parents[3] / "configs" / "config.yml"

# ---------------- 数据模型 ----------------
class DatabaseConfig(BaseModel):
    driver: str
    host: str | None = None
    port: int | None = None
    database: str
    username: str | None = None
    password: str | None = None
    echo: bool = False
    pool_pre_ping: bool = True

    @property
    def url(self) -> str:
        if self.driver.startswith("sqlite"):
            return f"{self.driver}:///{self.database}"
        user_pass = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.driver}://{user_pass}{self.host}:{self.port}/{self.database}"

class LoggingConfig(BaseModel):
    root_level: str = "INFO"
    file_level: str = "DEBUG"
    console: bool = True
    log_dir: str = "{system_tmp}/logs/{app_name}"

class AppConfig(BaseModel):
    name: str = "HomeGuard"
    env: str = "dev"

class GlobalConfig(BaseModel):
    app: AppConfig
    database: Dict[str, DatabaseConfig]  # key = env
    logging: LoggingConfig

def project_root() -> Path:
    """
    Locate the project root by searching upward for any of the following marker files:
    - .git
    - pyproject.toml
    - requirements.txt
    Falls back to the current working directory if none are found.
    """
    marker_files = {".git", "pyproject.toml", "requirements.txt"}
    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents):
        if any((parent / marker).exists() for marker in marker_files):
            LOGGER.debug("Project root detected at: %s", parent)
            return parent
    LOGGER.warning("No project-root marker files found; using cwd as fallback: %s", cwd)
    return cwd


# ---------------- 单例加载 ----------------
_config: GlobalConfig | None = None

@lru_cache
def load_config(env: str | None = None) -> GlobalConfig:
    env = env or os.getenv("ENVIRONMENT", "dev")
    raw = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))

    # 解析数据库块
    db_raw = raw["database"]
    db_map = {}
    for k, v in db_raw.items():
        # 支持 !ENV 语法
        if isinstance(v.get("password"), str) and v["password"].startswith("!ENV"):
            key = v["password"][5:].strip().lstrip("$").lstrip("{").rstrip("}")
            v["password"] = os.getenv(key, "")
        db_map[k] = DatabaseConfig(**v)

    raw["database"] = db_map
    return GlobalConfig(**raw)

# ---------------- 日志初始化 ----------------
def setup_logging() -> None:
    cfg = load_config()
    log_dir = Path(
        cfg.logging.log_dir.format(
            system_tmp=tempfile.gettempdir() if os.name == "nt" else "/tmp",
            app_name=cfg.app.name,
        )
    )
    log_dir.mkdir(parents=True, exist_ok=True)

    handlers = {
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": cfg.logging.file_level,
            "formatter": "verbose",
            "filename": log_dir / f"{cfg.app.name}.log",
            "when": "midnight",
            "interval": 1,
            "backupCount": 30,
            "encoding": "utf-8",
        }
    }
    if cfg.logging.console:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "level": cfg.logging.root_level,
            "formatter": "simple",
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {"format": "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d | %(message)s"},
                "verbose": {"format": "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d | %(message)s"},
            },
            "handlers": handlers,
            "root": {"level": cfg.logging.root_level, "handlers": list(handlers.keys())},
        }
    )

# ---------------- 全局对象 ----------------
CFG = load_config()
LOGGER = logging.getLogger(CFG.app.name)