<script setup lang="ts">
import { ref, watch } from 'vue'
import { Search, X, Filter } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  search: []
}>()

const searchQuery = ref(props.modelValue)

watch(searchQuery, (newValue) => {
  emit('update:modelValue', newValue)
})

watch(() => props.modelValue, (newValue) => {
  searchQuery.value = newValue
})

function handleSearch() {
  emit('search')
}

function clearSearch() {
  searchQuery.value = ''
  emit('update:modelValue', '')
  emit('search')
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    handleSearch()
  }
}
</script>

<template>
  <div class="flex gap-2">
    <div class="relative flex-1">
      <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" :size="20" />
      <Input
        v-model="searchQuery"
        placeholder="Search products..."
        class="pl-10"
        @keydown="handleKeydown"
      />
      <Button
        v-if="searchQuery"
        variant="ghost"
        size="icon"
        class="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
        @click="clearSearch"
      >
        <X :size="16" />
      </Button>
    </div>
    <Button @click="handleSearch">
      <Filter class="mr-2" :size="16" />
      Search
    </Button>
  </div>
</template>
