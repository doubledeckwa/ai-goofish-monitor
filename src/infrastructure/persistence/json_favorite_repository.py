"""
JSON-based favorite repository
Handles favorite persistence in data/favorites.json
"""
import json
import os
from typing import Optional, List
from datetime import datetime
from src.domain.models.favorite import Favorite, FavoriteCreate


class JsonFavoriteRepository:
    """JSON-based favorite repository"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.favorites_file = os.path.join(data_dir, "favorites.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.favorites_file):
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_favorites(self) -> List[dict]:
        """Load favorites from file"""
        try:
            with open(self.favorites_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_favorites(self, favorites: List[dict]):
        """Save favorites to file"""
        with open(self.favorites_file, 'w', encoding='utf-8') as f:
            json.dump(favorites, f, ensure_ascii=False, indent=2)

    def _get_next_id(self, favorites: List[dict]) -> int:
        """Get next favorite ID"""
        if not favorites:
            return 1
        return max(f['id'] for f in favorites) + 1

    async def create(self, favorite_create: FavoriteCreate, user_id: int) -> Favorite:
        """Create new favorite"""
        favorites = self._load_favorites()

        if any(
            f['user_id'] == user_id and f['product_id'] == favorite_create.product_id
            for f in favorites
        ):
            raise ValueError("Product already in favorites")

        favorite_dict = {
            "id": self._get_next_id(favorites),
            "user_id": user_id,
            **favorite_create.dict(),
            "created_at": datetime.now().isoformat()
        }

        favorites.append(favorite_dict)
        self._save_favorites(favorites)

        return Favorite(**favorite_dict)

    async def get_by_id(self, favorite_id: int) -> Optional[Favorite]:
        """Get favorite by ID"""
        favorites = self._load_favorites()
        for favorite_dict in favorites:
            if favorite_dict['id'] == favorite_id:
                return Favorite(**favorite_dict)
        return None

    async def get_by_user(self, user_id: int, page: int = 1, limit: int = 20) -> tuple[List[Favorite], int]:
        """Get favorites by user with pagination"""
        favorites = self._load_favorites()
        user_favorites = [
            Favorite(**f) for f in favorites if f['user_id'] == user_id
        ]

        total = len(user_favorites)
        start = (page - 1) * limit
        end = start + limit
        paginated = user_favorites[start:end]

        return paginated, total

    async def get_by_user_and_product(self, user_id: int, product_id: str) -> Optional[Favorite]:
        """Get favorite by user and product"""
        favorites = self._load_favorites()
        for favorite_dict in favorites:
            if favorite_dict['user_id'] == user_id and favorite_dict['product_id'] == product_id:
                return Favorite(**favorite_dict)
        return None

    async def delete(self, favorite_id: int, user_id: int) -> bool:
        """Delete favorite"""
        favorites = self._load_favorites()
        original_len = len(favorites)
        favorites = [
            f for f in favorites
            if not (f['id'] == favorite_id and f['user_id'] == user_id)
        ]
        if len(favorites) < original_len:
            self._save_favorites(favorites)
            return True
        return False

    async def delete_by_product(self, user_id: int, product_id: str) -> bool:
        """Delete favorite by user and product"""
        favorites = self._load_favorites()
        original_len = len(favorites)
        favorites = [
            f for f in favorites
            if not (f['user_id'] == user_id and f['product_id'] == product_id)
        ]
        if len(favorites) < original_len:
            self._save_favorites(favorites)
            return True
        return False
