"""
User management routes for admin
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.domain.models.user import User, UserResponse
from src.services.user_service import UserService
from src.infrastructure.persistence.json_user_repository import JsonUserRepository


router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


def get_user_service() -> UserService:
    """Get user service instance"""
    return UserService()


@router.get("", response_model=List[UserResponse])
async def get_all_users(
    user_service: UserService = Depends(get_user_service)
):
    """Get all users (admin only)"""
    users = await user_service.get_all_users()
    return [UserResponse(**user.dict()) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID (admin only)"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.dict())


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    updates: dict,
    user_service: UserService = Depends(get_user_service)
):
    """Update user (admin only)"""
    user = await user_service.update_user(user_id, **updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user.dict())


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (admin only)"""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}
