# src/core/db/base_async.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.core.config.setting import CFG  # Reuse singleton from setting.py
from src.core.db.base import Base
from src.core.db.models import task

# ---------------- Configuration ----------------
db_cfg = CFG.database[CFG.app.env]  # e.g. dev / prod

engine = create_async_engine(
    db_cfg.url,
    echo=db_cfg.echo,
    pool_pre_ping=db_cfg.pool_pre_ping,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
)

# ---------------- Table Creation Utility ----------------
async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
