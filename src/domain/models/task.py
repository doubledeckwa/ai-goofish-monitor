"""
task domain model
Define task entities and their business logic
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    """Task status enum"""
    STOPPED = "stopped"
    RUNNING = "running"
    SCHEDULED = "scheduled"


class Task(BaseModel):
    """task entity"""
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
    account_state_file: Optional[str] = None
    free_shipping: bool = True
    new_publish_option: Optional[str] = None
    region: Optional[str] = None
    is_running: bool = False

    class Config:
        use_enum_values = True

    def can_start(self) -> bool:
        """Check if the task can be started"""
        return self.enabled and not self.is_running

    def can_stop(self) -> bool:
        """Check if the task can be stopped"""
        return self.is_running

    def apply_update(self, update: 'TaskUpdate') -> 'Task':
        """Apply updates and return new task instance"""
        update_data = update.dict(exclude_unset=True)
        return self.copy(update=update_data)


class TaskCreate(BaseModel):
    """create taskDTO"""
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
    account_state_file: Optional[str] = None
    free_shipping: bool = True
    new_publish_option: Optional[str] = None
    region: Optional[str] = None


class TaskUpdate(BaseModel):
    """update taskDTO"""
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
    account_state_file: Optional[str] = None
    free_shipping: Optional[bool] = None
    new_publish_option: Optional[str] = None
    region: Optional[str] = None
    is_running: Optional[bool] = None


class TaskGenerateRequest(BaseModel):
    """AIGenerate task requestDTO"""
    task_name: str
    keyword: str
    description: str
    personal_only: bool = True
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    max_pages: int = 3
    cron: Optional[str] = None
    account_state_file: Optional[str] = None
    free_shipping: bool = True
    new_publish_option: Optional[str] = None
    region: Optional[str] = None

    @validator('min_price', 'max_price', pre=True)
    def convert_price_to_str(cls, v):
        """Convert price to string, handle empty strings and numbers"""
        if v == "" or v == "null" or v == "undefined" or v is None:
            return None
        # If it is a number, convert it to a string
        if isinstance(v, (int, float)):
            return str(v)
        return v

    @validator('cron', pre=True)
    def empty_str_to_none(cls, v):
        """Convert empty string to None"""
        if v == "" or v == "null" or v == "undefined":
            return None
        return v

    @validator('account_state_file', pre=True)
    def empty_account_to_none(cls, v):
        if v == "" or v == "null" or v == "undefined":
            return None
        return v

    @validator('new_publish_option', 'region', pre=True)
    def empty_str_to_none_for_strings(cls, v):
        if v == "" or v == "null" or v == "undefined":
            return None
        return v
