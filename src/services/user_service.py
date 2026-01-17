"""
User service
Handles user business logic including authentication and token generation
"""
import hashlib
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt

from src.domain.models.user import User, UserCreate, UserLogin, UserResponse, TokenResponse, UserRole
from src.infrastructure.persistence.json_user_repository import JsonUserRepository


class UserService:
    """User service"""

    SECRET_KEY = "your-secret-key-change-in-production"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS = 24

    def __init__(self, repository: Optional[JsonUserRepository] = None):
        self.repository = repository or JsonUserRepository()

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self._hash_password(plain_password) == hashed_password

    def _create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.ACCESS_TOKEN_EXPIRE_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def _decode_token(self, token: str) -> Optional[dict]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None

    async def register(self, user_create: UserCreate) -> TokenResponse:
        """Register new user"""
        password_hash = self._hash_password(user_create.password)

        user = await self.repository.create(user_create, password_hash)

        access_token = self._create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        })

        return TokenResponse(
            access_token=access_token,
            user=UserResponse(**user.dict())
        )

    async def login(self, user_login: UserLogin) -> Optional[TokenResponse]:
        """Login user"""
        user = await self.repository.get_by_username(user_login.username)

        if not user:
            return None
        if not user.is_active:
            return None
        if not self._verify_password(user_login.password, user.password_hash):
            return None

        access_token = self._create_access_token({
            "sub": user.username,
            "user_id": user.id,
            "role": user.role
        })

        return TokenResponse(
            access_token=access_token,
            user=UserResponse(**user.dict())
        )

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        payload = self._decode_token(token)
        if payload is None:
            return None

        user_id = payload.get("user_id")
        if user_id is None:
            return None

        return await self.repository.get_by_id(user_id)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.repository.get_by_id(user_id)

    async def get_all_users(self) -> list[User]:
        """Get all users"""
        return await self.repository.get_all()

    async def update_user(self, user_id: int, **updates) -> Optional[User]:
        """Update user"""
        if 'password' in updates:
            updates['password_hash'] = self._hash_password(updates['password'])
            del updates['password']
        return await self.repository.update(user_id, **updates)

    async def delete_user(self, user_id: int) -> bool:
        """Delete user"""
        return await self.repository.delete(user_id)
