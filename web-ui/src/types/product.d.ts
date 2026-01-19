export interface ProductInfoPublic {
  "Product title": string
  "Current selling price": string
  "Product original price"?: string
  "Product tag"?: string[]
  "Shipping area"?: string
  "Product link": string
  "Release time"?: string
  "commodityID": string
  "Product picture list"?: string[]
  "Product main image link"?: string
  "Views"?: string | number
}

export interface SellerInfoPublic {
  "Seller nickname"?: string
  "Seller avatar link"?: string
  "Seller's personalized signature"?: string
  "Seller is selling/Number of items sold"?: string
  "Seller credit rating"?: string
}

export interface ProductPublic {
  id: string
  "Crawl time": string
  "Search keywords": string
  "Task name": string
  "Product information": ProductInfoPublic
  "Seller information": SellerInfoPublic
  ai_analysis?: any
  is_recommended?: boolean | null
  is_favorited?: boolean
}

export interface ProductFilter {
  search?: string
  min_price?: number
  max_price?: number
  task_name?: string
  is_recommended?: boolean
  sort_by?: string
  sort_order?: string
  page?: number
  limit?: number
}

export interface PaginatedProducts {
  items: ProductPublic[]
  total_items: number
  page: number
  limit: number
  total_pages: number
}

export interface Category {
  name: string
  public: boolean
}
