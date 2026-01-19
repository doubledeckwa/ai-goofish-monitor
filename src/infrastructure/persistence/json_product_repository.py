"""
JSON-based product repository
Handles products from JSONL files with public API support
"""
import os
import json
import glob
from typing import List, Optional, Dict, Set
from src.domain.models.product import ProductPublic, ProductFilter, PaginatedProducts
from src.domain.models.task import Task


class JsonProductRepository:
    """JSON-based product repository"""

    def __init__(self, jsonl_dir: str = "jsonl"):
        self.jsonl_dir = jsonl_dir

    async def get_all_jsonl_files(self) -> List[str]:
        """Get all JSONL files"""
        if not os.path.isdir(self.jsonl_dir):
            return []
        return [f for f in os.listdir(self.jsonl_dir) if f.endswith(".jsonl")]

    async def get_task_names(self) -> List[str]:
        """Get unique task names from JSONL files"""
        files = await self.get_all_jsonl_files()
        task_names = set()
        for filename in files:
            task_name = filename.replace('_full_data.jsonl', '').replace('.jsonl', '')
            if task_name:
                task_names.add(task_name)
        return sorted(list(task_names))

    async def load_products_from_file(self, filename: str, task_name: Optional[str] = None) -> List[dict]:
        """Load products from a JSONL file"""
        filepath = os.path.join(self.jsonl_dir, filename)
        if not os.path.exists(filepath):
            return []

        products = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record:
                        products.append(record)
                except json.JSONDecodeError:
                    continue
        return products

    async def load_all_products(self) -> List[dict]:
        """Load all products from all JSONL files"""
        all_products = []
        files = await self.get_all_jsonl_files()

        for filename in files:
            products = await self.load_products_from_file(filename)
            all_products.extend(products)

        return all_products

    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string to float"""
        if not price_str:
            return None
        try:
            cleaned = price_str.replace('¥', '').replace(',', '').strip()
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _filter_products(self, products: List[dict], filters: ProductFilter) -> List[dict]:
        """Apply filters to products"""
        filtered = products

        if filters.search:
            search_lower = filters.search.lower()
            filtered = [
                p for p in filtered
                if search_lower in p.get('Product information', {}).get('Product title', '').lower()
                or search_lower in p.get('Task name', '').lower()
            ]

        if filters.min_price is not None or filters.max_price is not None:
            filtered = [
                p for p in filtered
                if self._should_include_price(
                    p.get('Product information', {}).get('Current selling price', ''),
                    filters.min_price,
                    filters.max_price
                )
            ]

        if filters.task_name:
            filtered = [
                p for p in filtered
                if p.get('Task name', '') == filters.task_name
            ]

        if filters.is_recommended is not None:
            filtered = [
                p for p in filtered
                if p.get('ai_analysis', {}).get('is_recommended') == filters.is_recommended
            ]

        return filtered

    def _should_include_price(self, price_str: str, min_price: Optional[float], max_price: Optional[float]) -> bool:
        """Check if price falls within range"""
        price = self._parse_price(price_str)
        if price is None:
            return True
        if min_price is not None and price < min_price:
            return False
        if max_price is not None and price > max_price:
            return False
        return True

    def _sort_products(self, products: List[dict], sort_by: str, sort_order: str) -> List[dict]:
        """Sort products"""
        reverse = sort_order == 'desc'

        if sort_by == 'price':
            def price_key(p):
                price = self._parse_price(p.get('Product information', {}).get('Current selling price', ''))
                return price if price is not None else 0.0
            products.sort(key=price_key, reverse=reverse)
        elif sort_by == 'publish_time':
            def time_key(p):
                return p.get('Product information', {}).get('Release time', '')
            products.sort(key=time_key, reverse=reverse)
        else:
            def crawl_key(p):
                return p.get('Crawl time', '')
            products.sort(key=crawl_key, reverse=reverse)

        return products

    async def search(self, filters: ProductFilter, public_task_names: Set[str]) -> PaginatedProducts:
        """Search products with filters"""
        all_products = await self.load_all_products()

        filtered_products = self._filter_products(all_products, filters)
        sorted_products = self._sort_products(filtered_products, filters.sort_by, filters.sort_order)

        total_items = len(sorted_products)
        total_pages = (total_items + filters.limit - 1) // filters.limit

        start = (filters.page - 1) * filters.limit
        end = start + filters.limit
        paginated_products = sorted_products[start:end]

        public_products = [
            ProductPublic.from_jsonl_record(p) for p in paginated_products
            if p.get('Task name') in public_task_names
        ]

        return PaginatedProducts(
            items=public_products,
            total_items=total_items,
            page=filters.page,
            limit=filters.limit,
            total_pages=total_pages
        )

    async def get_by_id(self, product_id: str) -> Optional[ProductPublic]:
        """Get product by ID"""
        all_products = await self.load_all_products()

        for product in all_products:
            if f"{product.get('Task name', '')}_{product.get('Product information', {}).get('commodityID', '')}" == product_id:
                return ProductPublic.from_jsonl_record(product)

        return None
