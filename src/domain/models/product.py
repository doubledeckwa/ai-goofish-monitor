"""
Product domain model for public marketplace
Define product entities and their business logic
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProductInfoPublic(BaseModel):
    """Public product information (filtered for safety)"""
    "Product title": str
    "Current selling price": str
    "Product original price": Optional[str] = None
    "Product tag": Optional[List[str]] = None
    "Shipping area": Optional[str] = None
    "Product link": str
    "Release time": Optional[str] = None
    "commodityID": str
    "Product picture list": Optional[List[str]] = None
    "Product main image link": Optional[str] = None
    "Views": Optional[str | int] = None


class SellerInfoPublic(BaseModel):
    """Public seller information (without contact details)"""
    "Seller nickname": Optional[str] = None
    "Seller avatar link": Optional[str] = None
    "Seller's personalized signature": Optional[str] = None
    "Seller is selling/Number of items sold": Optional[str] = None
    "Seller credit rating": Optional[str] = None


class ProductPublic(BaseModel):
    """Public product entity"""
    id: str = Field(..., description="Unique product identifier")
    "Crawl time": str
    "Search keywords": str
    "Task name": str
    "Product information": ProductInfoPublic
    "Seller information": SellerInfoPublic
    ai_analysis: Optional[dict] = None
    is_recommended: Optional[bool] = None

    @classmethod
    def from_jsonl_record(cls, record: dict) -> "ProductPublic":
        """Create ProductPublic from JSONL record"""
        product_info = record.get("Product information", {})
        seller_info = record.get("Seller information", {})
        ai_analysis = record.get("ai_analysis", {})

        return cls(
            id=f"{record.get('Task name', '')}_{product_info.get('commodityID', '')}",
            **record,
            "Product information": ProductInfoPublic(**product_info),
            "Seller information": SellerInfoPublic(**{
                k: v for k, v in seller_info.items()
                if k not in ["Seller phone", "Seller email", "Seller QQ", "Seller WeChat"]
            }),
            is_recommended=ai_analysis.get("is_recommended") if ai_analysis else None
        )


class ProductFilter(BaseModel):
    """Product filter criteria"""
    search: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    task_name: Optional[str] = None
    is_recommended: Optional[bool] = None
    sort_by: str = "crawl_time"
    sort_order: str = "desc"
    page: int = 1
    limit: int = 20


class PaginatedProducts(BaseModel):
    """Paginated product list response"""
    items: List[ProductPublic]
    total_items: int
    page: int
    limit: int
    total_pages: int
