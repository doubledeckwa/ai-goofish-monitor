<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getSystemStatus, updateLoginState, deleteLoginState, type SystemStatus } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { toast } from '@/components/ui/toast'

const status = ref<SystemStatus | null>(null)
const isMenuOpen = ref(false)
const isLoginDialogOpen = ref(false)
const isDeleteDialogOpen = ref(false)
const loginStateContent = ref('')
const isSaving = ref(false)
const isDeleting = ref(false)

const statusClass = computed(() => {
  if (!status.value) return 'text-gray-400'
  return status.value.login_state_file.exists ? 'text-green-600' : 'text-red-600'
})

async function fetchStatus() {
  try {
    status.value = await getSystemStatus()
    if (status.value && !status.value.login_state_file.exists) {
      closeMenu()
    }
  } catch (e) {
    console.error('Failed to fetch system status', e)
  }
}

function toggleMenu() {
  isMenuOpen.value = !isMenuOpen.value
}

function closeMenu() {
  isMenuOpen.value = false
}

function openLoginDialog() {
  isLoginDialogOpen.value = true
  closeMenu()
}

function openDeleteDialog() {
  isDeleteDialogOpen.value = true
  closeMenu()
}

function handleStatusClick() {
  if (!status.value) return
  if (!status.value.login_state_file.exists) {
    openLoginDialog()
    return
  }
  toggleMenu()
}

async function handleSaveLoginState() {
  const content = loginStateContent.value.trim()
  if (!content) {
    toast({
      title: '缺少登录内容',
      description: '请粘贴从浏览器获取的 JSON 内容。',
      variant: 'destructive',
    })
    return
  }
  isSaving.value = true
  try {
    await updateLoginState(content)
    toast({ title: '登录状态更新成功' })
    loginStateContent.value = ''
    isLoginDialogOpen.value = false
    await fetchStatus()
    window.dispatchEvent(new Event('login-state-changed'))
  } catch (e) {
    toast({
      title: '登录状态更新失败',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteLoginState() {
  isDeleting.value = true
  try {
    await deleteLoginState()
    toast({ title: '登录凭证已删除' })
    await fetchStatus()
    window.dispatchEvent(new Event('login-state-changed'))
    isDeleteDialogOpen.value = false
  } catch (e) {
    toast({
      title: '删除登录凭证失败',
      description: (e as Error).message,
      variant: 'destructive',
    })
  } finally {
    isDeleting.value = false
  }
}

onMounted(() => {
  fetchStatus()
  window.addEventListener('login-state-changed', fetchStatus)
  document.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  window.removeEventListener('login-state-changed', fetchStatus)
  document.removeEventListener('click', closeMenu)
})
</script>

<template>
  <header class="bg-white h-16 px-6 border-b border-gray-200 flex justify-between items-center flex-shrink-0 shadow-sm z-10">
    <h1 class="text-xl font-semibold text-gray-800">
      闲鱼智能监控机器人
    </h1>

    <div class="relative ml-auto text-sm font-bold flex items-center gap-1" @click.stop>
      <span class="text-gray-500 font-medium">闲鱼登录状态：</span>
      <button
        type="button"
        class="cursor-pointer flex items-center gap-1 transition-all hover:opacity-80"
        :class="statusClass"
        @click.stop="handleStatusClick"
      >
        <template v-if="!status">
          检测中...
        </template>
        <template v-else-if="status.login_state_file.exists">
          <span class="w-2 h-2 rounded-full bg-green-500 mr-1"></span>
          已登录
        </template>
        <template v-else>
          <span class="animate-pulse">！</span>闲鱼未登录（点击设置）
        </template>
      </button>

      <div
        v-if="isMenuOpen && status?.login_state_file.exists"
        class="absolute right-0 top-full mt-2 w-36 rounded-md border border-gray-200 bg-white shadow-lg py-1 z-50"
      >
        <button
          type="button"
          class="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
          @click="openLoginDialog"
        >
          手动更新
        </button>
        <button
          type="button"
          class="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="isDeleting || !status?.login_state_file.exists"
          @click="openDeleteDialog"
        >
          {{ isDeleting ? '删除中...' : '删除凭证' }}
        </button>
      </div>
    </div>
  </header>

  <Dialog v-model:open="isLoginDialogOpen">
    <DialogContent class="sm:max-w-[700px]">
      <DialogHeader>
        <DialogTitle>手动更新登录状态 (Cookie)</DialogTitle>
        <DialogDescription>
          用于在无法运行图形化浏览器的服务器上更新闲鱼登录凭证。
        </DialogDescription>
      </DialogHeader>
      <div class="space-y-4 text-sm text-gray-600">
        <div>
          <h4 class="font-medium text-gray-800 mb-2">使用 Chrome 扩展（推荐）</h4>
          <ol class="list-decimal list-inside space-y-1">
            <li>
              安装
              <a class="text-blue-600 hover:underline" href="https://chromewebstore.google.com/detail/xianyu-login-state-extrac/eidlpfjiodpigmfcahkmlenhppfklcoa" target="_blank" rel="noopener noreferrer">
                闲鱼登录状态提取扩展
              </a>
            </li>
            <li>
              打开并登录
              <a class="text-blue-600 hover:underline" href="https://www.goofish.com" target="_blank" rel="noopener noreferrer">
                闲鱼官网
              </a>
            </li>
            <li>点击扩展图标，选择“提取登录状态”，再点击“复制到剪贴板”</li>
            <li>将内容粘贴到下方文本框并保存</li>
          </ol>
        </div>
        <div class="grid gap-2">
          <Label>粘贴 JSON 内容</Label>
          <Textarea
            v-model="loginStateContent"
            class="min-h-[160px]"
            placeholder="请在此处粘贴从浏览器扩展复制的 JSON 文本..."
          />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" @click="isLoginDialogOpen = false">
          取消
        </Button>
        <Button :disabled="isSaving" @click="handleSaveLoginState">
          {{ isSaving ? '保存中...' : '保存' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <Dialog v-model:open="isDeleteDialogOpen">
    <DialogContent class="sm:max-w-[420px]">
      <DialogHeader>
        <DialogTitle>删除登录凭证</DialogTitle>
        <DialogDescription>
          删除后需要重新设置才能运行任务，确定要继续吗？
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button variant="outline" @click="isDeleteDialogOpen = false">取消</Button>
        <Button variant="destructive" :disabled="isDeleting" @click="handleDeleteLoginState">
          {{ isDeleting ? '删除中...' : '确认删除' }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
