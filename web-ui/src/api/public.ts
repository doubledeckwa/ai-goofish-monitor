import type { PaginatedProducts, ProductPublic, ProductFilter, Category } from '@/types/product'

const BASE_URL = '/api/public'

export async function getCategories(): Promise<Category[]> {
  const response = await fetch(`${BASE_URL}/categories`)
  if (!response.ok) throw new Error('Failed to fetch categories')
  const data = await response.json()
  return data.categories
}

export async function getProducts(filters: ProductFilter = {}): Promise<PaginatedProducts> {
  const params = new URLSearchParams()

  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      params.append(key, String(value))
    }
  })

  const url = `${BASE_URL}/products${params.toString() ? '?' + params.toString() : ''}`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Failed to fetch products')
  return response.json()
}

export async function getProductById(productId: string): Promise<ProductPublic> {
  const response = await fetch(`${BASE_URL}/products/${productId}`)
  if (!response.ok) throw new Error('Product not found')
  return response.json()
}
