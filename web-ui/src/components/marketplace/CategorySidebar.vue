<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronRight } from 'lucide-vue-next'
import type { Category } from '@/types/product'

const props = defineProps<{
  categories: Category[]
  selectedCategory?: string | null
}>()

const emit = defineEmits<{
  categorySelected: [category: string | null]
}>()

const router = useRouter()
const isExpanded = ref(true)

const publicCategories = computed(() =>
  props.categories.filter(c => c.public)
)

const allCount = computed(() => {
  const selected = props.selectedCategory
    ? props.categories.find(c => c.name === props.selectedCategory)
    : null
  return selected ? props.categories.length : props.categories.length
})

function selectCategory(category: string | null) {
  emit('categorySelected', category)

  const query = category
    ? { category }
    : {}
  router.push({ path: '/', query })
}
</script>

<template>
  <aside class="bg-white rounded-lg shadow-sm border border-gray-200">
    <button
      @click="isExpanded = !isExpanded"
      class="w-full px-4 py-3 flex items-center justify-between font-medium text-gray-900 hover:bg-gray-50 transition-colors"
    >
      <span>Categories</span>
      <ChevronRight
        :size="16"
        class="transition-transform duration-200"
        :class="{ '-rotate-90': !isExpanded }"
      />
    </button>

    <div v-show="isExpanded" class="border-t border-gray-200">
      <button
        :class="[
          'w-full px-4 py-2 text-left text-sm transition-colors flex items-center justify-between',
          selectedCategory === null
            ? 'bg-blue-50 text-blue-600 font-medium'
            : 'text-gray-700 hover:bg-gray-50'
        ]"
        @click="selectCategory(null)"
      >
        <span>All Products</span>
        <span class="text-xs text-gray-500">{{ allCount }}</span>
      </button>

      <button
        v-for="category in publicCategories"
        :key="category.name"
        :class="[
          'w-full px-4 py-2 text-left text-sm transition-colors flex items-center justify-between',
          selectedCategory === category.name
            ? 'bg-blue-50 text-blue-600 font-medium'
            : 'text-gray-700 hover:bg-gray-50'
        ]"
        @click="selectCategory(category.name)"
      >
        <span class="truncate">{{ category.name }}</span>
        <span
          v-if="!category.public"
          class="text-xs text-orange-500 font-medium"
        >
          Private
        </span>
      </button>
    </div>
  </aside>
</template>
