"""
notification service
Unified management of all notification channels
"""
import asyncio
from typing import Dict, List
from src.infrastructure.external.notification_clients.base import NotificationClient


class NotificationService:
    """notification service"""

    def __init__(self, clients: List[NotificationClient]):
        self.clients = [client for client in clients if client.is_enabled()]

    async def send_notification(self, product_data: Dict, reason: str) -> Dict[str, bool]:
        """
        Send notifications to all enabled channels

        Args:
            product_data: Product data
            reason: Reasons for recommendation

        Returns:
            Send results across channels
        """
        if not self.clients:
            print("Warning: No notification service is configured")
            return {}

        # Send to all channels concurrently
        tasks = [client.send(product_data, reason) for client in self.clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Statistical results
        result_dict = {}
        for i, result in enumerate(results):
            client_name = self.clients[i].__class__.__name__
            result_dict[client_name] = result if not isinstance(result, Exception) else False

        return result_dict
