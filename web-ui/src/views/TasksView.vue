<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTasks } from '@/composables/useTasks'
import type { Task, TaskGenerateRequest, TaskUpdate } from '@/types/task.d.ts'
import TasksTable from '@/components/tasks/TasksTable.vue'
import TaskForm from '@/components/tasks/TaskForm.vue'
import { listAccounts, type AccountItem } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'

const {
  tasks,
  isLoading,
  error,
  removeTask,
  createTask,
  updateTask,
  startTask,
  stopTask,
  stoppingTaskIds,
} = useTasks()

// State for dialogs
const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)
const isCriteriaDialogOpen = ref(false)
const isSubmitting = ref(false)
const selectedTask = ref<Task | null>(null)
const criteriaTask = ref<Task | null>(null)
const criteriaDescription = ref('')
const isCriteriaSubmitting = ref(false)
const isDeleteDialogOpen = ref(false)
const taskToDeleteId = ref<number | null>(null)
const accountOptions = ref<AccountItem[]>([])
const defaultAccountPath = ref<string>('')
const route = useRoute()

const taskToDelete = computed(() => {
  if (taskToDeleteId.value === null) return null
  return tasks.value.find((task) => task.id === taskToDeleteId.value) || null
})

function handleDeleteTask(taskId: number) {
  taskToDeleteId.value = taskId
  isDeleteDialogOpen.value = true
}

async function handleConfirmDeleteTask() {
  if (!taskToDelete.value) {
    toast({ title: 'The task to be deleted was not found', variant: 'destructive' })
    isDeleteDialogOpen.value = false
    return
  }
  try {
    await removeTask(taskToDelete.value.id)
    toast({ title: 'Task deleted' })
  } catch (e) {
    toast({
      title: 'Delete task failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleteDialogOpen.value = false
    taskToDeleteId.value = null
  }
}

function handleEditTask(task: Task) {
  selectedTask.value = task
  isEditDialogOpen.value = true
}

async function handleCreateTask(data: TaskGenerateRequest) {
  isSubmitting.value = true
  try {
    await createTask(data)
    isCreateDialogOpen.value = false
  }
  catch (e) {
    toast({
      title: 'Failed to create task',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
  finally {
    isSubmitting.value = false
  }
}

async function handleUpdateTask(data: TaskUpdate) {
  if (!selectedTask.value) return
  isSubmitting.value = true
  try {
    await updateTask(selectedTask.value.id, data)
    isEditDialogOpen.value = false
  }
  catch (e) {
    toast({
      title: 'Update task failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
  finally {
    isSubmitting.value = false
  }
}

function handleOpenCriteriaDialog(task: Task) {
  criteriaTask.value = task
  criteriaDescription.value = task.description || ''
  isCriteriaDialogOpen.value = true
}

async function handleRefreshCriteria() {
  if (!criteriaTask.value) return
  if (!criteriaDescription.value.trim()) {
    toast({
      title: 'Detailed requirements cannot be empty',
      description: 'Please fill in new detailed requirements。',
      variant: 'destructive',
    })
    return
  }

  isCriteriaSubmitting.value = true
  try {
    await updateTask(criteriaTask.value.id, { description: criteriaDescription.value })
    isCriteriaDialogOpen.value = false
  } catch (e) {
    toast({
      title: 'Regeneration failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isCriteriaSubmitting.value = false
  }
}

async function handleStartTask(taskId: number) {
  try {
    await startTask(taskId)
  } catch (e) {
    toast({
      title: 'Failed to start task',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function handleStopTask(taskId: number) {
  try {
    await stopTask(taskId)
  } catch (e) {
    toast({
      title: 'Stop task failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function handleToggleEnabled(task: Task, enabled: boolean) {
  const previous = task.enabled
  task.enabled = enabled
  try {
    await updateTask(task.id, { enabled })
  } catch (e) {
    task.enabled = previous
    toast({
      title: 'Update status failed',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

async function fetchAccountOptions() {
  try {
    accountOptions.value = await listAccounts()
  } catch (e) {
    toast({
      title: 'Failed to load account list',
      description: (e as Error).message,
      variant: 'destructive',
    })
  }
}

onMounted(fetchAccountOptions)

function resolveAccountPath(accountName: string) {
  const match = accountOptions.value.find((account) => account.name === accountName)
  return match ? match.path : ''
}

watch(
  () => [route.query.account, route.query.create, accountOptions.value],
  () => {
    const accountName = typeof route.query.account === 'string' ? route.query.account : ''
    if (accountName) {
      defaultAccountPath.value = resolveAccountPath(accountName)
    } else {
      defaultAccountPath.value = ''
    }
    if (route.query.create === '1') {
      isCreateDialogOpen.value = true
    }
  },
  { immediate: true }
)
</script>

<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-gray-800">
        task management
      </h1>

      <!-- Create Task Dialog -->
      <Dialog v-model:open="isCreateDialogOpen">
        <DialogTrigger as-child>
          <Button>+ Create new task</Button>
        </DialogTrigger>
        <DialogContent class="sm:max-w-[640px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create a new monitoring task (AIdrive)</DialogTitle>
            <DialogDescription>
              Please fill in the task details。AIwill be based on your "detailed needs"”Automatically generate analysis standards。
            </DialogDescription>
          </DialogHeader>
          <TaskForm
            mode="create"
            :account-options="accountOptions"
            :default-account="defaultAccountPath"
            @submit="(data) => handleCreateTask(data as TaskGenerateRequest)"
          />
          <DialogFooter>
            <Button type="submit" form="task-form" :disabled="isSubmitting">
              {{ isSubmitting ? 'Creating...' : 'Create tasks' }}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>

    <!-- Edit Task Dialog -->
    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent class="sm:max-w-[640px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit task: {{ selectedTask?.task_name }}</DialogTitle>
        </DialogHeader>
        <TaskForm
          v-if="selectedTask"
          mode="edit"
          :initial-data="selectedTask"
          :account-options="accountOptions"
          @submit="(data) => handleUpdateTask(data as TaskUpdate)"
        />
        <DialogFooter>
          <Button type="submit" form="task-form" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving...' : 'Save changes' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- Refresh Criteria Dialog -->
    <Dialog v-model:open="isCriteriaDialogOpen">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Regenerate AI standard</DialogTitle>
          <DialogDescription>
            It will be regenerated after modifying the detailed requirements. AI Analytical standards。
          </DialogDescription>
        </DialogHeader>
        <div class="grid gap-3">
          <label class="text-sm font-medium text-gray-700">Detailed requirements</label>
          <Textarea
            v-model="criteriaDescription"
            class="min-h-[140px]"
            placeholder="Please describe your purchase needs in detail in natural language，AIAnalysis criteria will be generated based on this description..."
          />
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isCriteriaDialogOpen = false">
            Cancel
          </Button>
          <Button :disabled="isCriteriaSubmitting" @click="handleRefreshCriteria">
            {{ isCriteriaSubmitting ? 'Generating...' : 'Regenerate' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
      <strong class="font-bold">something went wrong!</strong>
      <span class="block sm:inline">{{ error.message }}</span>
    </div>

    <TasksTable
      :tasks="tasks"
      :is-loading="isLoading"
      :stopping-ids="stoppingTaskIds"
      @delete-task="handleDeleteTask"
      @edit-task="handleEditTask"
      @run-task="handleStartTask"
      @stop-task="handleStopTask"
      @refresh-criteria="handleOpenCriteriaDialog"
      @toggle-enabled="handleToggleEnabled"
    />

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>Delete task</DialogTitle>
          <DialogDescription>
            {{ taskToDelete ? `Confirm to delete task「${taskToDelete.task_name}」? This operation is irreversible。` : 'Are you sure you want to delete this task? This operation is irreversible。' }}
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">Cancel</Button>
          <Button variant="destructive" @click="handleConfirmDeleteTask">Confirm deletion</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
