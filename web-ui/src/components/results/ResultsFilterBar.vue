<script setup lang="ts">
import { computed } from 'vue'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

interface FileOption {
  value: string
  label: string
}

interface Props {
  files: string[]
  fileOptions?: FileOption[]
  selectedFile: string | null
  recommendedOnly: boolean
  sortBy: 'crawl_time' | 'publish_time' | 'price'
  sortOrder: 'asc' | 'desc'
  isLoading: boolean
  isReady: boolean
}

const props = defineProps<Props>()

const options = computed(() => {
  if (!props.isReady) {
    return []
  }
  if (props.fileOptions && props.fileOptions.length > 0) {
    return props.fileOptions
  }
  return props.files.map((file) => ({ value: file, label: file }))
})

const selectedLabel = computed(() => {
  if (!props.isReady) return 'Load task name...'
  if (options.value.length === 0) return 'No results yet, please run the task first'
  if (!props.selectedFile) return 'Please select task results'
  const match = options.value.find((option) => option.value === props.selectedFile)
  return match ? match.label : 'Task name: Unnamed'
})

const labelClass = computed(() => {
  const classes = ['transition-opacity', 'duration-200']
  if (!props.isReady || !props.selectedFile || options.value.length === 0) {
    classes.push('text-muted-foreground')
  }
  classes.push(props.isReady ? 'opacity-100' : 'opacity-70')
  return classes.join(' ')
})

const isSelectDisabled = computed(() => !props.isReady || options.value.length === 0)

const emit = defineEmits<{
  (e: 'update:selectedFile', value: string): void
  (e: 'update:recommendedOnly', value: boolean): void
  (e: 'update:sortBy', value: 'crawl_time' | 'publish_time' | 'price'): void
  (e: 'update:sortOrder', value: 'asc' | 'desc'): void
  (e: 'refresh'): void
  (e: 'delete'): void
}>()
</script>

<template>
  <div class="flex flex-wrap gap-4 items-center mb-6 p-4 bg-gray-50 rounded-lg border">
    <Select
      :model-value="props.selectedFile || undefined"
      @update:model-value="(value) => emit('update:selectedFile', value as string)"
    >
      <SelectTrigger class="w-[280px]" :disabled="isSelectDisabled">
        <span :class="labelClass">
          {{ selectedLabel }}
        </span>
      </SelectTrigger>
      <SelectContent>
        <SelectItem v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </SelectItem>
      </SelectContent>
    </Select>

    <Select
      :model-value="props.sortBy"
      @update:model-value="(value) => emit('update:sortBy', value as any)"
    >
      <SelectTrigger class="w-[180px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="crawl_time">By crawl time</SelectItem>
        <SelectItem value="publish_time">by release time</SelectItem>
        <SelectItem value="price">by price</SelectItem>
      </SelectContent>
    </Select>

    <Select
      :model-value="props.sortOrder"
      @update:model-value="(value) => emit('update:sortOrder', value as any)"
    >
      <SelectTrigger class="w-[120px]">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="desc">descending order</SelectItem>
        <SelectItem value="asc">Ascending order</SelectItem>
      </SelectContent>
    </Select>

    <div class="flex items-center space-x-2">
      <Checkbox
        id="recommended-only"
        :model-value="props.recommendedOnly"
        @update:modelValue="(value) => emit('update:recommendedOnly', value === true)"
      />
      <Label for="recommended-only" class="cursor-pointer">Just watchAIrecommend</Label>
    </div>

    <Button @click="emit('refresh')" :disabled="props.isLoading">
      refresh
    </Button>

    <Button
      variant="destructive"
      @click="emit('delete')"
      :disabled="props.isLoading || !props.selectedFile"
    >
      Delete results
    </Button>
  </div>
</template>
