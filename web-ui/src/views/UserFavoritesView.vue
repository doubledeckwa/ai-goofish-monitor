<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, ExternalLink } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import ProductCard from '@/components/marketplace/ProductCard.vue'
import { useFavorites } from '@/composables/useFavorites'
import { useUser } from '@/composables/useUser'

const router = useRouter()
const { isAuthenticated } = useUser()

if (!isAuthenticated.value) {
  router.push('/user/login')
}

const { loadFavorites, removeFromFavorite } = useFavorites()

const favorites = ref<any[]>([])
const total = ref(0)
const currentPage = ref(1)
const isLoading = ref(false)
const error = ref<Error | null>(null)

async function loadFavoritesData() {
  try {
    isLoading.value = true
    error.value = null
    const result = await loadFavorites(currentPage.value, 20)
    favorites.value = result.items
    total.value = result.total
  } catch (e) {
    error.value = e as Error
  } finally {
    isLoading.value = false
  }
}

function convertFavoriteToPublic(fav: any) {
  return {
    id: fav.product_id,
    'Crawl time': fav.created_at,
    'Search keywords': '',
    'Task name': fav.task_name,
    'Product information': {
      'Product title': fav.product_title,
      'Current selling price': fav.price,
      'Product main image link': fav.image_url,
      'Product link': fav.product_link,
      commodityID: fav.product_id,
    },
    'Seller information': {},
    is_favorited: true,
  }
}

async function handleRemoveFavorite(productId: string) {
  try {
    await removeFromFavorite(productId)
    await loadFavoritesData()
  } catch (e) {
    console.error('Failed to remove favorite', e)
  }
}

function openProductLink(link: string) {
  window.open(link, '_blank')
}

onMounted(async () => {
  await loadFavoritesData()
})
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">My Favorites</h1>
      <p class="text-gray-600">{{ total }} items saved</p>
    </div>

    <div v-if="error" class="bg-red-100 text-red-700 p-4 rounded-lg mb-4">
      {{ error.message }}
    </div>

    <div v-if="isLoading && favorites.length === 0" class="text-center py-12">
      <div class="text-gray-500">Loading favorites...</div>
    </div>

    <div v-else-if="favorites.length === 0" class="text-center py-12">
      <Heart :size="48" class="mx-auto text-gray-300 mb-4" />
      <p class="text-gray-500 mb-4">No favorites yet</p>
      <Button @click="router.push('/')">
        Browse Products
      </Button>
    </div>

    <div v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div v-for="favorite in favorites" :key="favorite.id" class="relative">
          <ProductCard
            :product="convertFavoriteToPublic(favorite)"
            @favorite-toggled="loadFavoritesData"
          />
          <div class="flex gap-2 mt-2">
            <Button
              variant="outline"
              size="sm"
              class="flex-1"
              @click="openProductLink(favorite.product_link)"
            >
              <ExternalLink :size="16" class="mr-1" />
              View
            </Button>
            <Button
              variant="destructive"
              size="sm"
              @click="handleRemoveFavorite(favorite.product_id)"
            >
              Remove
            </Button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
