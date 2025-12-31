"""
任务领域模型
定义任务实体及其业务逻辑
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    STOPPED = "stopped"
    RUNNING = "running"
    SCHEDULED = "scheduled"


class Task(BaseModel):
    """任务实体"""
    id: Optional[int] = None
    task_name: str
    enabled: bool
    keyword: str
    description: Optional[str] = ""
    max_pages: int
    personal_only: bool
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    cron: Optional[str] = None
    ai_prompt_base_file: str
    ai_prompt_criteria_file: str
    is_running: bool = False

    class Config:
        use_enum_values = True

    def can_start(self) -> bool:
        """检查任务是否可以启动"""
        return self.enabled and not self.is_running

    def can_stop(self) -> bool:
        """检查任务是否可以停止"""
        return self.is_running

    def apply_update(self, update: 'TaskUpdate') -> 'Task':
        """应用更新并返回新的任务实例"""
        update_data = update.dict(exclude_unset=True)
        return self.copy(update=update_data)


class TaskCreate(BaseModel):
    """创建任务的DTO"""
    task_name: str
    enabled: bool = True
    keyword: str
    description: Optional[str] = ""
    max_pages: int = 3
    personal_only: bool = True
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    cron: Optional[str] = None
    ai_prompt_base_file: str = "prompts/base_prompt.txt"
    ai_prompt_criteria_file: str


class TaskUpdate(BaseModel):
    """更新任务的DTO"""
    task_name: Optional[str] = None
    enabled: Optional[bool] = None
    keyword: Optional[str] = None
    description: Optional[str] = None
    max_pages: Optional[int] = None
    personal_only: Optional[bool] = None
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    cron: Optional[str] = None
    ai_prompt_base_file: Optional[str] = None
    ai_prompt_criteria_file: Optional[str] = None
    is_running: Optional[bool] = None
