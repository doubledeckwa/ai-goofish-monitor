<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, ExternalLink, User } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import FavoriteButton from '@/components/marketplace/FavoriteButton.vue'
import { useProductDetail } from '@/composables/useMarketplace'

const route = useRoute()
const router = useRouter()
const { product, isLoading, error, loadProduct } = useProductDetail()

const productId = computed(() => route.params.id as string)

const mainImage = computed(() => {
  return product.value?.['Product information']['Product main image link'] ||
         product.value?.['Product information']['Product picture list']?.[0] ||
         '/placeholder-product.png'
})

const images = computed(() => {
  return product.value?.['Product information']['Product picture list'] || [mainImage.value]
})

const price = computed(() => product.value?.['Product information']['Current selling price'])
const originalPrice = computed(() => product.value?.['Product information']['Product original price'])
const title = computed(() => product.value?.['Product information']['Product title'])
const productLink = computed(() => product.value?.['Product information']['Product link'])
const publishTime = computed(() => product.value?.['Product information']['Release time'])
const views = computed(() => product.value?.['Product information']['Views'])

const sellerInfo = computed(() => {
  if (!product.value) return null
  const seller = product.value['Seller information']
  return {
    nickname: seller['Seller nickname'],
    avatar: seller['Seller avatar link'],
    signature: seller["Seller's personalized signature"],
    rating: seller['Seller credit rating'],
    itemsSold: seller['Seller is selling/Number of items sold'],
  }
})

onMounted(async () => {
  await loadProduct(productId.value)
})

function goBack() {
  router.back()
}

function handleFavoriteToggle() {
  if (!product.value) return
  product.value.is_favorited = !product.value.is_favorited
}

async function openOriginalLink() {
  if (productLink.value) {
    window.open(productLink.value, '_blank')
  }
}
</script>

<template>
  <div class="container mx-auto px-4 py-8">
    <Button variant="ghost" @click="goBack" class="mb-6">
      <ArrowLeft class="mr-2" :size="18" />
      Back
    </Button>

    <div v-if="isLoading" class="text-center py-12">
      <div class="text-gray-500">Loading product...</div>
    </div>

    <div v-else-if="error" class="bg-red-100 text-red-700 p-4 rounded-lg">
      {{ error.message }}
    </div>

    <div v-else-if="product" class="grid lg:grid-cols-2 gap-8">
      <div>
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-4">
          <img
            :src="mainImage"
            :alt="title"
            class="w-full aspect-square object-cover"
          />
        </div>

        <div v-if="images.length > 1" class="grid grid-cols-4 gap-2">
          <img
            v-for="(img, idx) in images"
            :key="idx"
            :src="img"
            :alt="title"
            class="rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
          />
        </div>
      </div>

      <div>
        <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-4">
          <h1 class="text-2xl font-bold text-gray-900 mb-4">
            {{ title }}
          </h1>

          <div class="flex items-center gap-4 mb-4">
            <span class="text-3xl font-bold text-gray-900">
              {{ price }}
            </span>
            <span v-if="originalPrice" class="text-lg text-gray-500 line-through">
              {{ originalPrice }}
            </span>
          </div>

          <div class="flex gap-2 mb-4">
            <Badge v-if="publishTime" variant="secondary">
              {{ publishTime }}
            </Badge>
            <Badge v-if="views" variant="outline">
              {{ views }} views
            </Badge>
          </div>

          <div class="flex gap-3 mb-4">
            <Button size="lg" class="flex-1" @click="openOriginalLink">
              <ExternalLink class="mr-2" :size="18" />
              View on Goofish
            </Button>
            <FavoriteButton
              :product-id="product.id"
              :is-favorited="product.is_favorited ?? false"
              size="lg"
              @toggled="handleFavoriteToggle"
            />
          </div>
        </div>

        <div v-if="sellerInfo" class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <User :size="20" />
            Seller Information
          </h2>
          <div class="space-y-3">
            <div class="flex items-center gap-3">
              <img
                v-if="sellerInfo.avatar"
                :src="sellerInfo.avatar"
                :alt="sellerInfo.nickname"
                class="w-12 h-12 rounded-full"
              />
              <div>
                <div class="font-medium text-gray-900">
                  {{ sellerInfo.nickname }}
                </div>
                <div v-if="sellerInfo.rating" class="text-sm text-gray-600">
                  Rating: {{ sellerInfo.rating }}
                </div>
              </div>
            </div>
            <p v-if="sellerInfo.signature" class="text-sm text-gray-600">
              {{ sellerInfo.signature }}
            </p>
            <p v-if="sellerInfo.itemsSold" class="text-sm text-gray-600">
              {{ sellerInfo.itemsSold }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
