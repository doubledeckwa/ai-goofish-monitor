<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import SearchBar from '@/components/marketplace/SearchBar.vue'
import CategorySidebar from '@/components/marketplace/CategorySidebar.vue'
import ProductCard from '@/components/marketplace/ProductCard.vue'
import { Button } from '@/components/ui/button'
import { useMarketplace } from '@/composables/useMarketplace'
import { useUser } from '@/composables/useUser'

const route = useRoute()
const { products, categories, totalItems, isLoading, error, filters, hasMore, loadCategories, loadProducts, loadMoreProducts, updateFilters } = useMarketplace()
const { currentUser } = useUser()

onMounted(async () => {
  await loadCategories()

  const category = route.query.category as string
  if (category) {
    updateFilters({ task_name: category })
  }

  await loadProducts()
})

watch(() => route.query.category, async (newCategory) => {
  updateFilters({ task_name: newCategory ? String(newCategory) : undefined })
  await loadProducts()
})

async function handleSearch() {
  await loadProducts()
}

async function handleLoadMore() {
  await loadMoreProducts()
}

function handleFavoriteToggled() {
  loadProducts(false)
}
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="flex gap-6">
      <aside class="w-64 flex-shrink-0 hidden lg:block">
        <CategorySidebar
          :categories="categories"
          :selected-category="filters.task_name || null"
          @category-selected="(cat) => updateFilters({ task_name: cat || undefined })"
        />
      </aside>

      <div class="flex-1">
        <div class="mb-6">
          <SearchBar
            v-model="filters.search"
            @search="handleSearch"
          />
        </div>

        <div v-if="error" class="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
          {{ error.message }}
        </div>

        <div v-if="isLoading && products.length === 0" class="text-center py-12">
          <div class="text-gray-500">Loading products...</div>
        </div>

        <div v-else-if="products.length === 0" class="text-center py-12">
          <div class="text-gray-500">No products found</div>
        </div>

        <div v-else>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            <ProductCard
              v-for="product in products"
              :key="product.id"
              :product="product"
              @favorite-toggled="handleFavoriteToggled"
            />
          </div>

          <div v-if="isLoading" class="text-center py-8">
            <div class="text-gray-500">Loading more...</div>
          </div>

          <div v-else-if="hasMore" class="text-center mt-8">
            <Button @click="handleLoadMore">
              Load More
            </Button>
          </div>
        </div>

        <div v-if="totalItems > 0" class="mt-4 text-sm text-gray-600">
          Showing {{ products.length }} of {{ totalItems }} products
        </div>
      </div>
    </div>
  </div>
</template>
