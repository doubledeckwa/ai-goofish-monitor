"""
FastAPI dependency injection
Provides creation and management of service instances
"""
from fastapi import Depends
from src.services.task_service import TaskService
from src.services.notification_service import NotificationService
from src.services.ai_service import AIAnalysisService
from src.services.process_service import ProcessService
from src.infrastructure.persistence.json_task_repository import JsonTaskRepository
from src.infrastructure.external.ai_client import AIClient
from src.infrastructure.external.notification_clients.ntfy_client import NtfyClient
from src.infrastructure.external.notification_clients.bark_client import BarkClient
from src.infrastructure.external.notification_clients.telegram_client import TelegramClient
from src.infrastructure.config.settings import notification_settings


# overall situation ProcessService instance (will be in app.py Medium settings）
_process_service_instance = None


def set_process_service(service: ProcessService):
    """Set global ProcessService Example"""
    global _process_service_instance
    _process_service_instance = service


# Service dependency injection
def get_task_service() -> TaskService:
    """Get task management service instance"""
    repository = JsonTaskRepository()
    return TaskService(repository)


def get_notification_service() -> NotificationService:
    """Get notification service instance"""
    clients = [
        NtfyClient(notification_settings.ntfy_topic_url),
        BarkClient(notification_settings.bark_url),
        TelegramClient(
            notification_settings.telegram_bot_token,
            notification_settings.telegram_chat_id
        )
    ]
    return NotificationService(clients)


def get_ai_service() -> AIAnalysisService:
    """getAIAnalysis service instance"""
    ai_client = AIClient()
    return AIAnalysisService(ai_client)


def get_process_service() -> ProcessService:
    """Get the process management service instance"""
    if _process_service_instance is None:
        raise RuntimeError("ProcessService not initialized")
    return _process_service_instance
