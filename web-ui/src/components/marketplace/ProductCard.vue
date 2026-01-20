<script setup lang="ts">
import { computed } from 'vue'
import type { ProductPublic } from '@/types/product'
import { RouterLink } from 'vue-router'
import { Heart } from 'lucide-vue-next'
import { useFavorites } from '@/composables/useFavorites'
import { useUser } from '@/composables/useUser'

const props = defineProps<{
  product: ProductPublic
}>()

const emit = defineEmits<{
  favoriteToggled: []
}>()

const { isAuthenticated } = useUser()
const { toggleProductFavorite } = useFavorites()

const isFavorited = computed(() => props.product.is_favorited ?? false)

const mainImage = computed(() => {
  return props.product['Product information']['Product main image link'] ||
         props.product['Product information']['Product picture list']?.[0] ||
         '/placeholder-product.png'
})

const price = computed(() => props.product['Product information']['Current selling price'])
const title = computed(() => props.product['Product information']['Product title'])
const sellerName = computed(() => props.product['Seller information']['Seller nickname'] || 'Unknown')
const productNameForFavorite = computed(() => title.value.substring(0, 50))

async function handleFavoriteToggle(event: Event) {
  event.preventDefault()
  event.stopPropagation()

  if (!isAuthenticated.value) {
    return
  }

  try {
    await toggleProductFavorite({
      product_id: props.product.id,
      task_name: props.product['Task name'],
      product_title: productNameForFavorite.value,
      price: price.value,
      image_url: mainImage.value,
      product_link: props.product['Product information']['Product link'],
    })

    emit('favoriteToggled')
  } catch (e) {
    console.error('Failed to toggle favorite', e)
  }
}
</script>

<template>
  <RouterLink
    :to="`/products/${product.id}`"
    class="group bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden border border-gray-200"
  >
    <div class="relative aspect-square overflow-hidden bg-gray-100">
      <img
        :src="mainImage"
        :alt="title"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
      <button
        v-if="isAuthenticated"
        @click="handleFavoriteToggle"
        class="absolute top-2 right-2 p-2 rounded-full bg-white/90 hover:bg-white transition-colors shadow-sm"
        :class="{ 'text-red-500': isFavorited, 'text-gray-600': !isFavorited }"
      >
        <Heart :class="{ 'fill-current': isFavorited }" :size="20" />
      </button>
      <span
        v-if="product.is_recommended"
        class="absolute top-2 left-2 px-2 py-1 bg-green-500 text-white text-xs font-medium rounded"
      >
        Recommended
      </span>
    </div>

    <div class="p-4">
      <h3 class="font-medium text-gray-900 line-clamp-2 mb-2 min-h-[2.5rem]">
        {{ title }}
      </h3>
      <p class="text-lg font-bold text-gray-900 mb-2">
        {{ price }}
      </p>
      <div class="flex items-center justify-between text-sm text-gray-600">
        <span class="truncate flex-1 mr-2">{{ sellerName }}</span>
        <span class="text-xs text-gray-500 whitespace-nowrap">
          {{ product['Task name'] }}
        </span>
      </div>
    </div>
  </RouterLink>
</template>
