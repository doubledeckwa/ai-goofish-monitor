"""
Ntfy Notify client
"""
import asyncio
import requests
from typing import Dict
from .base import NotificationClient


class NtfyClient(NotificationClient):
    """Ntfy Notify client"""

    def __init__(self, topic_url: str = None):
        super().__init__(enabled=bool(topic_url))
        self.topic_url = topic_url

    async def send(self, product_data: Dict, reason: str) -> bool:
        """send Ntfy notify"""
        if not self.is_enabled():
            return False

        try:
            msg_data = self._format_message(product_data, reason)
            message = f"price: {msg_data['price']}\nreason: {msg_data['reason']}\nLink: {msg_data['link']}"
            title = f"🚨 New recommendations! {msg_data['title'][:30]}..."

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.topic_url,
                    data=message.encode('utf-8'),
                    headers={
                        "Title": title.encode('utf-8'),
                        "Priority": "urgent",
                        "Tags": "bell,vibration"
                    },
                    timeout=10
                )
            )
            return True
        except Exception as e:
            print(f"Ntfy Notification failed to send: {e}")
            return False
