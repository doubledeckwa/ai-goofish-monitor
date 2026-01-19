<script setup lang="ts">
import { computed } from 'vue'
import { Heart } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { useFavorites } from '@/composables/useFavorites'
import { useUser } from '@/composables/useUser'

const props = defineProps<{
  productId: string
  isFavorited: boolean
  size?: 'sm' | 'md' | 'lg'
}>()

const emit = defineEmits<{
  toggled: []
}>()

const { isAuthenticated } = useUser()
const { toggleProductFavorite } = useFavorites()

const buttonSize = computed(() => {
  switch (props.size) {
    case 'sm': return 'icon-sm'
    case 'lg': return 'icon-lg'
    default: return 'icon'
  }
})

const iconSize = computed(() => {
  switch (props.size) {
    case 'sm': return 16
    case 'lg': return 24
    default: return 20
  }
})

async function handleToggle() {
  if (!isAuthenticated.value) {
    return
  }

  emit('toggled')
}
</script>

<template>
  <Button
    v-if="isAuthenticated"
    :variant="isFavorited ? 'default' : 'outline'"
    :size="buttonSize"
    @click="handleToggle"
    :class="{ 'text-red-500 border-red-500 hover:bg-red-50': isFavorited }"
  >
    <Heart
      :size="iconSize"
      :class="{ 'fill-current': isFavorited }"
    />
  </Button>
</template>
