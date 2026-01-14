<script setup lang="ts">
import { ref } from 'vue'
import type { ResultItem } from '@/types/result.d.ts'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface Props {
  item: ResultItem
}

const props = defineProps<Props>()

const info = props.item.Product information
const seller = props.item.Seller information
const ai = props.item.ai_analysis

const isRecommended = ai?.is_recommended === true
const recommendationText = isRecommended ? 'recommend' : (ai?.is_recommended === false ? 'Not recommended' : 'To be determined')

const imageUrl = info.Product picture list?.[0] || info.Product main image link || ''
const crawlTime = props.item.Crawl time
  ? new Date(props.item.Crawl time).toLocaleString('sv-SE')
  : 'unknown'
const publishTime = info.Release time || 'unknown'

const expanded = ref(false)
</script>

<template>
  <Card class="flex flex-col h-full">
    <CardHeader>
      <div class="aspect-[4/3] bg-gray-100 rounded-t-lg overflow-hidden -mt-6 -mx-6">
        <a :href="info.Product link" target="_blank" rel="noopener noreferrer">
          <img
            :src="imageUrl"
            :alt="info.Product title"
            class="w-full h-full object-cover transition-transform hover:scale-105"
            loading="lazy"
          />
        </a>
      </div>
      <CardTitle class="pt-4">
        <a :href="info.Product link" target="_blank" rel="noopener noreferrer" class="hover:text-blue-600 line-clamp-2">
          {{ info.Product title }}
        </a>
      </CardTitle>
      <CardDescription class="text-xl font-bold text-red-600 !mt-2">
        {{ info.Current selling price }}
      </CardDescription>
    </CardHeader>
    <CardContent class="flex-grow">
      <div
        :class="[
          'p-3 rounded-md text-sm',
          isRecommended ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        ]"
      >
        <p class="font-semibold" :class="[isRecommended ? 'text-green-800' : 'text-red-800']">
          AIsuggestion: {{ recommendationText }}
        </p>
        <p class="mt-1 text-gray-600" :class="{ 'line-clamp-3': !expanded }">
          reason: {{ ai?.reason || 'none' }}
        </p>
        <button
          v-if="ai?.reason"
          @click="expanded = !expanded"
          class="mt-1 text-xs text-blue-600 hover:underline"
        >
          {{ expanded ? 'close' : 'Expand' }}
        </button>
      </div>
    </CardContent>
    <CardFooter class="text-xs text-gray-500 flex items-center justify-between gap-2">
      <div class="space-y-1">
        <span class="block">seller: {{ seller.Seller nickname || info.Seller nickname || 'unknown' }}</span>
        <span class="block">Posted in: {{ publishTime }}</span>
        <span class="block">Fetched from: {{ crawlTime }}</span>
      </div>
      <a
        :href="info.Product link"
        target="_blank"
        rel="noopener noreferrer"
        class="text-blue-600 hover:underline text-sm"
      >
        check the details
      </a>
    </CardFooter>
  </Card>
</template>
