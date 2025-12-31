import { ref, onMounted, onUnmounted } from 'vue'
import * as logsApi from '@/api/logs'

export function useLogs() {
  const logs = ref('')
  const currentPos = ref(0)
  const isAutoRefresh = ref(true)
  const isLoading = ref(false)
  const error = ref<Error | null>(null)
  
  let refreshInterval: number | null = null
  const MAX_LOG_CHARS = 200_000
  const TRIM_LOG_CHARS = 150_000
  const TRIM_NOTICE = '...日志过长已截断，仅保留最新内容...'

  function appendLogs(content: string) {
    if (!content) return
    logs.value += content
    // Prevent unbounded growth that can freeze the UI.
    if (logs.value.length > MAX_LOG_CHARS) {
      const tail = logs.value.slice(-TRIM_LOG_CHARS)
      logs.value = `${TRIM_NOTICE}\n${tail}`
    }
  }

  async function fetchLogs() {
    if (isLoading.value) return
    isLoading.value = true
    try {
      const data = await logsApi.getLogs(currentPos.value)
      if (data.new_pos < currentPos.value) {
        // Log file rotated or cleared.
        logs.value = ''
      }
      if (data.new_content) {
        appendLogs(data.new_content)
      }
      currentPos.value = data.new_pos
    } catch (e) {
      if (e instanceof Error) error.value = e
    } finally {
      isLoading.value = false
    }
  }

  async function clearLogs() {
    try {
      await logsApi.clearLogs()
      logs.value = ''
      currentPos.value = 0
    } catch (e) {
      if (e instanceof Error) error.value = e
      throw e
    }
  }

  function startAutoRefresh() {
    if (refreshInterval) return
    fetchLogs() // Fetch immediately
    refreshInterval = window.setInterval(fetchLogs, 2000)
    isAutoRefresh.value = true
  }

  function stopAutoRefresh() {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
    isAutoRefresh.value = false
  }

  function toggleAutoRefresh() {
    if (isAutoRefresh.value) {
      stopAutoRefresh()
    } else {
      startAutoRefresh()
    }
  }

  onMounted(() => {
    startAutoRefresh()
  })

  onUnmounted(() => {
    stopAutoRefresh()
  })

  return {
    logs,
    isAutoRefresh,
    isLoading, // Not strictly used for polling to avoid flickering
    error,
    fetchLogs,
    clearLogs,
    toggleAutoRefresh
  }
}
