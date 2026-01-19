"""
Bark Notify client
"""
import asyncio
import requests
from typing import Dict
from .base import NotificationClient


class BarkClient(NotificationClient):
    """Bark Notify client"""

    def __init__(self, bark_url: str = None):
        super().__init__(enabled=bool(bark_url))
        self.bark_url = bark_url

    async def send(self, product_data: Dict, reason: str) -> bool:
        """send Bark notify"""
        if not self.is_enabled():
            return False

        try:
            msg_data = self._format_message(product_data, reason)

            bark_payload = {
                "title": f"🚨 New recommendations! {msg_data['title'][:30]}...",
                "body": f"price: {msg_data['price']}\nreason: {msg_data['reason']}",
                "url": msg_data['link'],
                "level": "timeSensitive",
                "group": "Xianyu monitoring"
            }

            # Add product main image
            main_image = product_data.get('Product main image link')
            if not main_image:
                image_list = product_data.get('Product picture list', [])
                if image_list:
                    main_image = image_list[0]

            if main_image:
                bark_payload['icon'] = main_image

            headers = {"Content-Type": "application/json; charset=utf-8"}
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    self.bark_url,
                    json=bark_payload,
                    headers=headers,
                    timeout=10
                )
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Bark Notification failed to send: {e}")
            return False
