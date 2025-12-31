<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useLogs } from '@/composables/useLogs'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Card, CardContent } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast'

const { logs, isAutoRefresh, clearLogs, toggleAutoRefresh, fetchLogs } = useLogs()
const logContainer = ref<HTMLElement | null>(null)
const autoScroll = ref(true)
const isClearDialogOpen = ref(false)

// Auto-scroll logic
watch(logs, async () => {
  if (autoScroll.value) {
    await nextTick()
    scrollToBottom()
  }
})

function scrollToBottom() {
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}

function openClearDialog() {
  isClearDialogOpen.value = true
}

async function handleClearLogs() {
  try {
    await clearLogs()
    toast({ title: '日志已清空' })
  } catch (e) {
    toast({
      title: '清空日志失败',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isClearDialogOpen.value = false
  }
}
</script>

<template>
  <div class="h-[calc(100vh-100px)] flex flex-col">
    <div class="flex justify-between items-center mb-4">
      <h1 class="text-2xl font-bold text-gray-800">运行日志</h1>
      
      <div class="flex items-center gap-4">
        <Button variant="outline" size="sm" @click="fetchLogs">
          刷新
        </Button>

        <div class="flex items-center space-x-2">
          <Switch id="auto-refresh" :model-value="isAutoRefresh" @update:model-value="toggleAutoRefresh" />
          <Label for="auto-refresh">自动刷新</Label>
        </div>

        <div class="flex items-center space-x-2">
          <Switch id="auto-scroll" v-model="autoScroll" />
          <Label for="auto-scroll">自动滚动</Label>
        </div>

        <Button variant="destructive" size="sm" @click="openClearDialog">
          清空日志
        </Button>
      </div>
    </div>

    <Card class="flex-1 overflow-hidden flex flex-col">
      <CardContent class="flex-1 p-0 relative">
        <pre
          ref="logContainer"
          class="absolute inset-0 p-4 bg-gray-950 text-gray-100 font-mono text-sm overflow-auto whitespace-pre-wrap break-all"
        >{{ logs }}</pre>
      </CardContent>
    </Card>

    <Dialog v-model:open="isClearDialogOpen">
      <DialogContent class="sm:max-w-[420px]">
        <DialogHeader>
          <DialogTitle>清空运行日志</DialogTitle>
          <DialogDescription>
            此操作不可恢复，确定要清空所有日志吗？
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isClearDialogOpen = false">取消</Button>
          <Button variant="destructive" @click="handleClearLogs">确认清空</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
