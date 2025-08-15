from __future__ import annotations

import logging
import logging.config
import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------- 数据模型 ----------
class AppConfig(BaseModel):
    name: str = "HomeGuard"
    env: str = "dev"


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


class AIConfig(BaseModel):
    openai: Dict[str, str] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    root_level: str = "INFO"
    file_level: str = "DEBUG"
    console: bool = True
    log_dir: str = "{system_tmp}/logs/{app_name}"


class GlobalConfig(BaseSettings):
    model_config = SettingsConfigDict(
        # 允许用 APP__LOGGING__ROOT_LEVEL 这种形式覆盖
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    database: Dict[str, DatabaseConfig] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # ---------------- 动态属性 ----------------
    @property
    def active_db(self) -> DatabaseConfig:
        """根据当前环境返回对应的 database 配置"""
        env = self.app.env
        return self.database[env]

    @property
    def log_dir_path(self) -> Path:
        """渲染 log_dir 模板"""
        system_tmp = tempfile.gettempdir() if os.name == "nt" else "/tmp"
        return Path(
            self.logging.log_dir.format(
                system_tmp=system_tmp,
                app_name=self.app.name,
            )
        )

    # ---------------- 工厂方法 ----------------
    @classmethod
    @lru_cache
    def load(cls, yaml_path: Path | None = None) -> "GlobalConfig":
        """单例加载，带缓存"""
        yaml_path = yaml_path or Path(__file__).resolve().parents[3] / "configs" / "config.yml"
        with yaml_path.open("rt", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        return cls(**raw)


# ---------- 日志初始化 ----------
def setup_logging(cfg: GlobalConfig) -> None:
    cfg.log_dir_path.mkdir(parents=True, exist_ok=True)

    handlers = {
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": cfg.logging.file_level,
            "formatter": "verbose",
            "filename": cfg.log_dir_path / f"{cfg.app.name}.log",
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


# ---------- 辅助函数 ----------
def project_root() -> Path:
    """
    向上查找 .git / pyproject.toml / requirements.txt 中的任意一个，
    找不到就回退到当前工作目录。
    """
    marker_files = {".git", "pyproject.toml", "requirements.txt"}
    cwd = Path.cwd()
    for parent in (cwd, *cwd.parents):
        if any((parent / marker).exists() for marker in marker_files):
            return parent
    return cwd


# ---------- 全局单例 ----------
CFG = GlobalConfig.load()
setup_logging(CFG)
LOGGER = logging.getLogger(CFG.app.name)
