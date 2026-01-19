"""
Product domain model for public marketplace
Define product entities and their business logic
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class ProductInfoPublic(BaseModel):
    """Public product information (filtered for safety)"""
    model_config = ConfigDict(populate_by_name=True)
    
    product_title: str = Field(alias="Product title")
    current_selling_price: str = Field(alias="Current selling price")
    product_original_price: Optional[str] = Field(None, alias="Product original price")
    product_tag: Optional[List[str]] = Field(None, alias="Product tag")
    shipping_area: Optional[str] = Field(None, alias="Shipping area")
    product_link: str = Field(alias="Product link")
    release_time: Optional[str] = Field(None, alias="Release time")
    commodityID: str
    product_picture_list: Optional[List[str]] = Field(None, alias="Product picture list")
    product_main_image_link: Optional[str] = Field(None, alias="Product main image link")
    views: Optional[str | int] = Field(None, alias="Views")


class SellerInfoPublic(BaseModel):
    """Public seller information (without contact details)"""
    model_config = ConfigDict(populate_by_name=True)
    
    seller_nickname: Optional[str] = Field(None, alias="Seller nickname")
    seller_avatar_link: Optional[str] = Field(None, alias="Seller avatar link")
    seller_personalized_signature: Optional[str] = Field(None, alias="Seller's personalized signature")
    seller_selling_count: Optional[str] = Field(None, alias="Seller is selling/Number of items sold")
    seller_credit_rating: Optional[str] = Field(None, alias="Seller credit rating")


class ProductPublic(BaseModel):
    """Public product entity"""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str = Field(..., description="Unique product identifier")
    crawl_time: str = Field(alias="Crawl time")
    search_keywords: str = Field(alias="Search keywords")
    task_name: str = Field(alias="Task name")
    product_information: ProductInfoPublic = Field(alias="Product information")
    seller_information: SellerInfoPublic = Field(alias="Seller information")
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
            crawl_time=record.get("Crawl time", ""),
            search_keywords=record.get("Search keywords", ""),
            task_name=record.get("Task name", ""),
            product_information=ProductInfoPublic(**product_info),
            seller_information=SellerInfoPublic(**{
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
