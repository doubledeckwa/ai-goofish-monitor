import { ref, computed } from 'vue'
import type { ProductPublic, ProductFilter, Category } from '@/types/product'
import { getProducts, getProductById, getCategories } from '@/api/public'

export function useMarketplace() {
  const products = ref<ProductPublic[]>([])
  const categories = ref<Category[]>([])
  const totalItems = ref(0)
  const totalPages = ref(0)
  const currentPage = ref(1)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  const filters = ref<ProductFilter>({
    search: '',
    min_price: undefined,
    max_price: undefined,
    task_name: undefined,
    is_recommended: undefined,
    sort_by: 'crawl_time',
    sort_order: 'desc',
    page: 1,
    limit: 20,
  })

  const hasMore = computed(() => currentPage.value < totalPages.value)

  async function loadCategories() {
    try {
      categories.value = await getCategories()
    } catch (e) {
      console.error('Failed to load categories', e)
    }
  }

  async function loadProducts(resetPage = true) {
    try {
      isLoading.value = true
      error.value = null

      if (resetPage) {
        filters.value.page = 1
      }

      const result = await getProducts(filters.value)

      if (resetPage) {
        products.value = result.items
      } else {
        products.value = [...products.value, ...result.items]
      }

      totalItems.value = result.total_items
      totalPages.value = result.total_pages
      currentPage.value = result.page
    } catch (e) {
      error.value = e as Error
      throw e
    } finally {
      isLoading.value = false
    }
  }

  async function loadMoreProducts() {
    if (hasMore.value && !isLoading.value) {
      filters.value.page = currentPage.value + 1
      await loadProducts(false)
    }
  }

  function updateFilters(newFilters: Partial<ProductFilter>) {
    Object.assign(filters.value, newFilters)
  }

  function resetFilters() {
    filters.value = {
      search: '',
      min_price: undefined,
      max_price: undefined,
      task_name: undefined,
      is_recommended: undefined,
      sort_by: 'crawl_time',
      sort_order: 'desc',
      page: 1,
      limit: 20,
    }
  }

  return {
    products,
    categories,
    totalItems,
    totalPages,
    currentPage,
    isLoading,
    error,
    filters,
    hasMore,
    loadCategories,
    loadProducts,
    loadMoreProducts,
    updateFilters,
    resetFilters,
  }
}

export function useProductDetail() {
  const product = ref<ProductPublic | null>(null)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  async function loadProduct(productId: string) {
    try {
      isLoading.value = true
      error.value = null
      product.value = await getProductById(productId)
    } catch (e) {
      error.value = e as Error
      throw e
    } finally {
      isLoading.value = false
    }
  }

  return {
    product,
    isLoading,
    error,
    loadProduct,
  }
}
