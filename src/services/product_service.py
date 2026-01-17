"""
Product service
Handles product business logic for public marketplace
"""
from typing import List, Set, Optional
from src.domain.models.product import ProductPublic, ProductFilter, PaginatedProducts
from src.infrastructure.persistence.json_product_repository import JsonProductRepository
from src.domain.models.task import Task


class ProductService:
    """Product service"""

    def __init__(self, repository: Optional[JsonProductRepository] = None):
        self.repository = repository or JsonProductRepository()

    async def get_task_names(self) -> List[str]:
        """Get all available task names (categories)"""
        return await self.repository.get_task_names()

    async def search_products(
        self,
        filters: ProductFilter,
        public_task_names: Set[str]
    ) -> PaginatedProducts:
        """Search products with filters"""
        return await self.repository.search(filters, public_task_names)

    async def get_product_by_id(self, product_id: str) -> Optional[ProductPublic]:
        """Get product by ID"""
        return await self.repository.get_by_id(product_id)

    async def get_public_task_names(self, tasks: List[Task]) -> Set[str]:
        """Get task names that are marked as public"""
        return {task.task_name for task in tasks if getattr(task, 'is_public', False)}
