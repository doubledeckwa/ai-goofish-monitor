<script setup lang="ts">
import { computed, ref } from 'vue'
import { useResults } from '@/composables/useResults'
import ResultsFilterBar from '@/components/results/ResultsFilterBar.vue'
import ResultsGrid from '@/components/results/ResultsGrid.vue'
import { Button } from '@/components/ui/button'
import { toast } from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

const {
  files,
  selectedFile,
  results,
  filters,
  isLoading,
  error,
  refreshResults,
  deleteSelectedFile,
  fileOptions,
  isFileOptionsReady,
} = useResults()

const isDeleteDialogOpen = ref(false)

const selectedTaskLabel = computed(() => {
  if (!selectedFile.value || fileOptions.value.length === 0) return null
  const match = fileOptions.value.find((option) => option.value === selectedFile.value)
  if (!match) return null
  const label = match.label.replace(/^Task name：/, '').trim()
  return label || null
})

const deleteConfirmText = computed(() => {
  return selectedTaskLabel.value
    ? `Confirm deletion task results「${selectedTaskLabel.value}」? This operation is irreversible。`
    : 'Are you sure you want to delete this task result? This operation is irreversible。'
})

function openDeleteDialog() {
  if (!selectedFile.value) {
    toast({
      title: 'There are no results to delete yet.',
      variant: 'destructive',
    })
    return
  }
  isDeleteDialogOpen.value = true
}

async function handleDeleteResults() {
  if (!selectedFile.value) return
  try {
    await deleteSelectedFile(selectedFile.value)
    toast({ title: 'Result deleted' })
  } catch (e) {
    toast({
      title: 'Deletion result failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">
      View results
    </h1>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">something went wrong!</strong>
      <span class="block sm:inline">{{ error.message }}</span>
    </div>

    <ResultsFilterBar
      :files="files"
      :file-options="fileOptions"
      :is-ready="isFileOptionsReady"
      v-model:selectedFile="selectedFile"
      v-model:recommendedOnly="filters.recommended_only"
      v-model:sortBy="filters.sort_by"
      v-model:sortOrder="filters.sort_order"
      :is-loading="isLoading"
      @refresh="refreshResults"
      @delete="openDeleteDialog"
    />

    <ResultsGrid :results="results" :is-loading="isLoading" />

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>Delete task results</DialogTitle>
          <DialogDescription>
            {{ deleteConfirmText }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">Cancel</Button>
          <Button variant="destructive" :disabled="isLoading" @click="handleDeleteResults">
            Confirm deletion
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
