"""
Task storage layer
Responsible for the persistence operation of task data
"""
from typing import List, Optional
from abc import ABC, abstractmethod
import json
import aiofiles
from src.domain.models.task import Task


class TaskRepository(ABC):
    """Task storage interface"""

    @abstractmethod
    async def find_all(self) -> List[Task]:
        """Get all tasks"""
        pass

    @abstractmethod
    async def find_by_id(self, task_id: int) -> Optional[Task]:
        """according toIDGet tasks"""
        pass

    @abstractmethod
    async def save(self, task: Task) -> Task:
        """Save task (create or update）"""
        pass

    @abstractmethod
    async def delete(self, task_id: int) -> bool:
        """Delete task"""
        pass
