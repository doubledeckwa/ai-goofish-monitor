import type { PaginatedProducts, ProductPublic, ProductFilter, Category } from '@/types/product'
import { getToken } from './user'

const BASE_URL = '/api/public'

function getAuthHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function getCategories(): Promise<Category[]> {
  const response = await fetch(`${BASE_URL}/categories`, {
    headers: getAuthHeaders(),
  })
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
  const response = await fetch(url, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to fetch products')
  return response.json()
}

export async function getProductById(productId: string): Promise<ProductPublic> {
  const response = await fetch(`${BASE_URL}/products/${productId}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Product not found')
  return response.json()
}
