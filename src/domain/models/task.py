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


class TaskType(str, Enum):
    """Task type enum"""
    KEYWORD_SEARCH = "keyword_search"
    SELLER_MONITORING = "seller_monitoring"


class Task(BaseModel):
    """task entity"""
    id: Optional[int] = None
    task_name: str
    enabled: bool
    task_type: TaskType = TaskType.KEYWORD_SEARCH
    keyword: Optional[str] = None
    seller_id: Optional[str] = None
    description: Optional[str] = ""
    max_pages: int
    max_products_per_run: Optional[int] = None
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
    is_public: bool = False
    
    @validator('keyword')
    def validate_keyword_for_type(cls, v, values):
        """Validate that keyword is provided for keyword_search tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        if task_type == TaskType.KEYWORD_SEARCH and not v:
            raise ValueError('keyword is required for keyword_search tasks')
        return v
    
    @validator('seller_id')
    def validate_seller_id_for_type(cls, v, values):
        """Validate that seller_id is provided for seller_monitoring tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        print(values)
        if task_type == TaskType.SELLER_MONITORING and not v:
            raise ValueError('seller_id is required for seller_monitoring tasks')
        return v
        

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
    task_type: TaskType = TaskType.KEYWORD_SEARCH
    keyword: Optional[str] = None
    seller_id: Optional[str] = None
    description: Optional[str] = ""
    max_pages: int = 3
    max_products_per_run: Optional[int] = None
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
    is_public: bool = False
    
    @validator('keyword')
    def validate_keyword_for_type(cls, v, values):
        """Validate that keyword is provided for keyword_search tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        if task_type == TaskType.KEYWORD_SEARCH and not v:
            raise ValueError('keyword is required for keyword_search tasks')
        return v
    
    @validator('seller_id')
    def validate_seller_id_for_type(cls, v, values):
        """Validate that seller_id is provided for seller_monitoring tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        if task_type == TaskType.SELLER_MONITORING and not v:
            raise ValueError('seller_id is required for seller_monitoring tasks')
        return v


class TaskUpdate(BaseModel):
    """update taskDTO"""
    task_name: Optional[str] = None
    enabled: Optional[bool] = None
    task_type: Optional[TaskType] = None
    keyword: Optional[str] = None
    seller_id: Optional[str] = None
    description: Optional[str] = None
    max_pages: Optional[int] = None
    max_products_per_run: Optional[int] = None
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
    is_public: Optional[bool] = None


class TaskGenerateRequest(BaseModel):
    """AIGenerate task requestDTO"""
    task_name: str
    task_type: TaskType = TaskType.KEYWORD_SEARCH
    keyword: Optional[str] = None
    seller_id: Optional[str] = None
    description: str
    personal_only: bool = True
    min_price: Optional[str] = None
    max_price: Optional[str] = None
    max_pages: int = 3
    max_products_per_run: Optional[int] = None
    cron: Optional[str] = None
    account_state_file: Optional[str] = None
    free_shipping: bool = True
    new_publish_option: Optional[str] = None
    region: Optional[str] = None

    @validator('keyword')
    def validate_keyword_for_type(cls, v, values):
        """Validate that keyword is provided for keyword_search tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        if task_type == TaskType.KEYWORD_SEARCH and not v:
            raise ValueError('keyword is required for keyword_search tasks')
        return v
    
    @validator('seller_id')
    def validate_seller_id_for_type(cls, v, values):
        """Validate that seller_id is provided for seller_monitoring tasks"""
        task_type = values.get('task_type', TaskType.KEYWORD_SEARCH)
        if task_type == TaskType.SELLER_MONITORING and not v:
            raise ValueError('seller_id is required for seller_monitoring tasks')
        return v

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
