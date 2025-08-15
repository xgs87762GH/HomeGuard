import enum
import json

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Enum as SAEnum
)

from src.core.db import Base
from src.core.utils.time_utils import TimeUtils


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED  = "FAILED"
    RETRY   = "RETRY"

class Task(Base):
    __tablename__ = "task"

    id            = Column(Integer, primary_key=True)
    adapter_name  = Column(String(50), nullable=False)
    method_name   = Column(String(50), nullable=False)
    params_json   = Column(Text, nullable=False)   # {"a":1,"b":2}

    status        = Column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    result_json   = Column(Text)
    error_msg     = Column(Text)

    created_at = Column(DateTime(timezone= True), default=TimeUtils.now_utc())
    updated_at = Column(DateTime(timezone= True), default=TimeUtils.now_utc(), onupdate=TimeUtils.now_utc())
    started_at    = Column(DateTime(timezone= True))
    finished_at   = Column(DateTime(timezone= True))
    next_retry_at = Column(DateTime(timezone= True))
    retry_count   = Column(Integer, default=0)

    deleted_at = Column(DateTime(timezone= True), default=None)

    # 辅助属性
    @property
    def params(self):
        return json.loads(self.params_json)

    @params.setter
    def params(self, value: dict):
        self.params_json = json.dumps(value, ensure_ascii=False)

    @property
    def result(self):
        return json.loads(self.result_json) if self.result_json else None

    @result.setter
    def result(self, value):
        self.result_json = json.dumps(value, ensure_ascii=False)