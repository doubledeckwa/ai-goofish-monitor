"""
Favorite domain model
Define favorite entities and their business logic
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Favorite(BaseModel):
    """Favorite entity"""
    id: int
    user_id: int
    product_id: str
    task_name: str
    product_title: str
    price: str
    image_url: Optional[str] = None
    product_link: str
    created_at: datetime


class FavoriteCreate(BaseModel):
    """Create favorite DTO"""
    product_id: str
    task_name: str
    product_title: str
    price: str
    image_url: Optional[str] = None
    product_link: str


class FavoriteResponse(BaseModel):
    """Favorite response DTO"""
    id: int
    user_id: int
    product_id: str
    task_name: str
    product_title: str
    price: str
    image_url: Optional[str] = None
    product_link: str
    created_at: datetime
