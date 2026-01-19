"""
User domain model
Define user entities and their business logic
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime


class UserRole(str, Enum):
    """User role enum"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """User entity"""
    id: int
    username: str
    email: EmailStr
    password_hash: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class UserCreate(BaseModel):
    """Create user DTO"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)


class UserLogin(BaseModel):
    """User login DTO"""
    username: str
    password: str


class UserUpdate(BaseModel):
    """Update user DTO"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response DTO (without password)"""
    id: int
    username: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
