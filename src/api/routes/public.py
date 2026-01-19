"""
Public API routes for marketplace
Accessible without admin authentication
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional, Set
from pydantic import BaseModel

from src.domain.models.product import ProductPublic, ProductFilter, PaginatedProducts
from src.domain.models.user import User, UserCreate, UserLogin, TokenResponse
from src.domain.models.favorite import Favorite, FavoriteCreate, FavoriteResponse
from src.services.product_service import ProductService
from src.services.user_service import UserService
from src.services.favorite_service import FavoriteService
from src.services.task_service import TaskService
from src.api.dependencies import get_task_service
from src.infrastructure.persistence.json_task_repository import JsonTaskRepository


router = APIRouter(prefix="/api/public", tags=["public"])


class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class FavoriteRequest(BaseModel):
    product_id: str
    task_name: str
    product_title: str
    price: str
    image_url: Optional[str] = None
    product_link: str


def get_optional_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Extract optional token from header"""
    if authorization and authorization.startswith("Bearer "):
        return authorization[7:]
    return None


async def get_optional_user(
    token: Optional[str] = Depends(get_optional_token)
) -> Optional[User]:
    """Get current user from optional token"""
    if not token:
        return None
    user_service = UserService()
    return await user_service.get_current_user(token)


async def get_current_user(
    token: str = Depends(get_optional_token)
) -> User:
    """Get current user from required token"""
    user_service = UserService()
    user = await user_service.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


async def get_public_task_names() -> Set[str]:
    """Get task names that are marked as public"""
    task_repo = JsonTaskRepository()
    task_service = TaskService(task_repo)
    tasks = await task_service.get_all_tasks()
    product_service = ProductService()
    return await product_service.get_public_task_names(tasks)


@router.get("/categories")
async def get_categories():
    """Get available categories (task names)"""
    product_service = ProductService()
    task_names = await product_service.get_task_names()
    public_task_names = await get_public_task_names()
    return {
        "categories": [
            {"name": name, "public": name in public_task_names}
            for name in task_names
        ]
    }


@router.get("/products", response_model=PaginatedProducts)
async def get_products(
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    task_name: Optional[str] = None,
    is_recommended: Optional[bool] = None,
    sort_by: str = "crawl_time",
    sort_order: str = "desc",
    page: int = 1,
    limit: int = 20,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Search and filter products"""
    filters = ProductFilter(
        search=search,
        min_price=min_price,
        max_price=max_price,
        task_name=task_name,
        is_recommended=is_recommended,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        limit=limit
    )

    public_task_names = await get_public_task_names()
    product_service = ProductService()

    result = await product_service.search_products(filters, public_task_names)

    if current_user:
        favorite_service = FavoriteService()
        for item in result.items:
            favorite = await favorite_service.get_favorite_by_product(
                current_user.id,
                item.id
            )
            setattr(item, 'is_favorited', favorite is not None)
    else:
        for item in result.items:
            setattr(item, 'is_favorited', False)

    return result


@router.get("/products/{product_id}", response_model=ProductPublic)
async def get_product(
    product_id: str,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get product details by ID"""
    public_task_names = await get_public_task_names()
    product_service = ProductService()

    product = await product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    task_name = getattr(product, "Task name", "")
    if task_name not in public_task_names:
        raise HTTPException(status_code=403, detail="Product not available publicly")

    if current_user:
        favorite_service = FavoriteService()
        favorite = await favorite_service.get_favorite_by_product(
            current_user.id,
            product.id
        )
        setattr(product, 'is_favorited', favorite is not None)
    else:
        setattr(product, 'is_favorited', False)

    return product


@router.post("/register", response_model=TokenResponse)
async def register(user_request: UserRegisterRequest):
    """Register new user"""
    try:
        user_create = UserCreate(
            username=user_request.username,
            email=user_request.email,
            password=user_request.password
        )
        user_service = UserService()
        return await user_service.register(user_create)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(user_request: UserLogin):
    """Login user"""
    user_service = UserService()
    result = await user_service.login(user_request)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return result


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return current_user


@router.get("/favorites", response_model=dict)
async def get_favorites(
    page: int = 1,
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get user's favorites"""
    favorite_service = FavoriteService()
    favorites, total = await favorite_service.get_user_favorites(current_user.id, page, limit)

    return {
        "items": favorites,
        "total": total,
        "page": page,
        "limit": limit
    }


@router.post("/favorites", response_model=dict)
async def add_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user)
):
    """Add product to favorites"""
    try:
        favorite_create = FavoriteCreate(**request.dict())
        favorite_service = FavoriteService()
        favorite = await favorite_service.add_favorite(favorite_create, current_user.id)
        return {"message": "Added to favorites", "favorite": favorite}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/favorites/{product_id}")
async def remove_favorite(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove product from favorites"""
    favorite_service = FavoriteService()
    success = await favorite_service.remove_favorite_by_product(current_user.id, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    return {"message": "Removed from favorites"}


@router.post("/favorites/toggle")
async def toggle_favorite(
    request: FavoriteRequest,
    current_user: User = Depends(get_current_user)
):
    """Toggle favorite (add if not exists, remove if exists)"""
    favorite_create = FavoriteCreate(**request.dict())
    favorite_service = FavoriteService()
    favorite, is_added = await favorite_service.toggle_favorite(favorite_create, current_user.id)

    return {
        "message": "Added to favorites" if is_added else "Removed from favorites",
        "is_added": is_added,
        "favorite": favorite
    }
