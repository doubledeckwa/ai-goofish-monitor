"""
Notify client base class
Define a unified interface for notifying clients
"""
from abc import ABC, abstractmethod
from typing import Dict


class NotificationClient(ABC):
    """Notify client abstract base class"""

    def __init__(self, enabled: bool = False):
        self._enabled = enabled

    def is_enabled(self) -> bool:
        """Check if the client is enabled"""
        return self._enabled

    @abstractmethod
    async def send(self, product_data: Dict, reason: str) -> bool:
        """
        Send notification

        Args:
            product_data: Product data
            reason: Reasons for recommendation

        Returns:
            Whether sent successfully
        """
        pass

    def _format_message(self, product_data: Dict, reason: str) -> Dict[str, str]:
        """Format message content"""
        title = product_data.get('Product title', 'N/A')
        price = product_data.get('Current selling price', 'N/A')
        link = product_data.get('Product link', '#')

        return {
            'title': title,
            'price': price,
            'link': link,
            'reason': reason
        }
