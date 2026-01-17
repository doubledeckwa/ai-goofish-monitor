"""
JSON-based user repository
Handles user persistence in data/users.json
"""
import json
import os
from typing import Optional, List
from datetime import datetime
from src.domain.models.user import User, UserCreate, UserResponse, UserRole


class JsonUserRepository:
    """JSON-based user repository"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.users_file = os.path.join(data_dir, "users.json")
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _load_users(self) -> List[dict]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _save_users(self, users: List[dict]):
        """Save users to file"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

    def _get_next_id(self, users: List[dict]) -> int:
        """Get next user ID"""
        if not users:
            return 1
        return max(u['id'] for u in users) + 1

    async def create(self, user_create: UserCreate, password_hash: str) -> User:
        """Create new user"""
        users = self._load_users()

        if any(u['username'] == user_create.username for u in users):
            raise ValueError("Username already exists")
        if any(u['email'] == user_create.email for u in users):
            raise ValueError("Email already exists")

        user_dict = {
            "id": self._get_next_id(users),
            "username": user_create.username,
            "email": user_create.email,
            "password_hash": password_hash,
            "role": UserRole.USER,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        users.append(user_dict)
        self._save_users(users)

        return User(**user_dict)

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        users = self._load_users()
        for user_dict in users:
            if user_dict['id'] == user_id:
                return User(**user_dict)
        return None

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        users = self._load_users()
        for user_dict in users:
            if user_dict['username'] == username:
                return User(**user_dict)
        return None

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = self._load_users()
        for user_dict in users:
            if user_dict['email'] == email:
                return User(**user_dict)
        return None

    async def get_all(self) -> List[User]:
        """Get all users"""
        users = self._load_users()
        return [User(**u) for u in users]

    async def update(self, user_id: int, **updates) -> Optional[User]:
        """Update user"""
        users = self._load_users()
        for i, user_dict in enumerate(users):
            if user_dict['id'] == user_id:
                updates['updated_at'] = datetime.now().isoformat()
                users[i].update(updates)
                self._save_users(users)
                return User(**users[i])
        return None

    async def delete(self, user_id: int) -> bool:
        """Delete user"""
        users = self._load_users()
        original_len = len(users)
        users = [u for u in users if u['id'] != user_id]
        if len(users) < original_len:
            self._save_users(users)
            return True
        return False
