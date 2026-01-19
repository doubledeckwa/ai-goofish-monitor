"""
Favorite service
Handles favorite business logic
"""
from typing import List, Optional
from src.domain.models.favorite import Favorite, FavoriteCreate, FavoriteResponse
from src.infrastructure.persistence.json_favorite_repository import JsonFavoriteRepository


class FavoriteService:
    """Favorite service"""

    def __init__(self, repository: Optional[JsonFavoriteRepository] = None):
        self.repository = repository or JsonFavoriteRepository()

    async def add_favorite(self, favorite_create: FavoriteCreate, user_id: int) -> Favorite:
        """Add product to favorites"""
        return await self.repository.create(favorite_create, user_id)

    async def get_user_favorites(self, user_id: int, page: int = 1, limit: int = 20) -> tuple[List[Favorite], int]:
        """Get user's favorites with pagination"""
        return await self.repository.get_by_user(user_id, page, limit)

    async def get_favorite_by_product(self, user_id: int, product_id: str) -> Optional[Favorite]:
        """Get favorite by user and product"""
        return await self.repository.get_by_user_and_product(user_id, product_id)

    async def remove_favorite(self, favorite_id: int, user_id: int) -> bool:
        """Remove favorite by ID"""
        return await self.repository.delete(favorite_id, user_id)

    async def remove_favorite_by_product(self, user_id: int, product_id: str) -> bool:
        """Remove favorite by product ID"""
        return await self.repository.delete_by_product(user_id, product_id)

    async def toggle_favorite(self, favorite_create: FavoriteCreate, user_id: int) -> tuple[Favorite, bool]:
        """
        Toggle favorite (add if not exists, remove if exists)
        Returns (favorite, is_added)
        """
        existing = await self.get_favorite_by_product(user_id, favorite_create.product_id)

        if existing:
            await self.remove_favorite_by_product(user_id, favorite_create.product_id)
            return existing, False
        else:
            new_favorite = await self.add_favorite(favorite_create, user_id)
            return new_favorite, True
