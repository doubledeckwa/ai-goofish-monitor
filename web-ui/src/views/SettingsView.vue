<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useSettings } from '@/composables/useSettings'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { toast } from '@/components/ui/toast'
import { getPromptContent, listPrompts, updatePrompt } from '@/api/prompts'

const {
  notificationSettings,
  aiSettings,
  rotationSettings,
  systemStatus,
  isLoading,
  isSaving,
  isReady,
  error,
  refreshStatus,
  saveNotificationSettings,
  saveAiSettings,
  saveRotationSettings,
  testAiConnection
} = useSettings()

const activeTab = ref('ai')
const route = useRoute()
const validTabs = new Set(['notifications', 'ai', 'rotation', 'status', 'prompts'])

const promptFiles = ref<string[]>([])
const selectedPrompt = ref<string | null>(null)
const promptContent = ref('')
const isPromptLoading = ref(false)
const isPromptSaving = ref(false)
const promptError = ref<string | null>(null)

function notifySuccess(title: string, description?: string) {
  toast({ title, description })
}

function notifyError(title: string, description?: string) {
  toast({ title, description, variant: 'destructive' })
}

async function handleSaveNotifications() {
  try {
    await saveNotificationSettings()
    notifySuccess('Notification settings saved')
  } catch (e) {
    notifyError('Failed to save notification settings', (e as Error).message)
  }
}

async function handleSaveAi() {
  try {
    await saveAiSettings()
    notifySuccess('AI Settings saved')
  } catch (e) {
    notifyError('AI Failed to save settings', (e as Error).message)
  }
}

async function handleSaveRotation() {
  try {
    await saveRotationSettings()
    notifySuccess('Rotation settings saved')
  } catch (e) {
    notifyError('Failed to save rotation settings', (e as Error).message)
  }
}

async function handleTestAi() {
  try {
    const res = await testAiConnection()
    notifySuccess('AI Connection test completed', res.message)
  } catch (e) {
    notifyError('AI Connection test failed', (e as Error).message)
  }
}

async function fetchPrompts() {
  isPromptLoading.value = true
  promptError.value = null
  try {
    const files = await listPrompts()
    promptFiles.value = files

    if (selectedPrompt.value && files.includes(selectedPrompt.value)) {
      return
    }

    const lastSelected = localStorage.getItem('lastSelectedPrompt')
    if (lastSelected && files.includes(lastSelected)) {
      selectedPrompt.value = lastSelected
      return
    }

    selectedPrompt.value = files[0] || null
  } catch (e) {
    promptError.value = (e as Error).message || 'load Prompt List failed'
  } finally {
    isPromptLoading.value = false
  }
}

async function handleSavePrompt() {
  if (!selectedPrompt.value) {
    notifyError('Please select Prompt document')
    return
  }
  isPromptSaving.value = true
  try {
    const res = await updatePrompt(selectedPrompt.value, promptContent.value)
    notifySuccess('Prompt Saved successfully', res.message)
  } catch (e) {
    notifyError('Prompt Save failed', (e as Error).message)
  } finally {
    isPromptSaving.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'prompts') {
    fetchPrompts()
  }
})

watch(
  () => route.query.tab,
  (tab) => {
    if (typeof tab === 'string' && validTabs.has(tab)) {
      activeTab.value = tab
    }
  },
  { immediate: true }
)

watch(selectedPrompt, async (value) => {
  if (!value) {
    promptContent.value = ''
    return
  }
  localStorage.setItem('lastSelectedPrompt', value)
  isPromptLoading.value = true
  promptError.value = null
  try {
    const data = await getPromptContent(value)
    promptContent.value = data.content
  } catch (e) {
    promptError.value = (e as Error).message || 'load Prompt Content failed'
  } finally {
    isPromptLoading.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-800 mb-6">System settings</h1>
    
    <div v-if="error" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4">
      {{ error.message }}
    </div>

    <Tabs v-model="activeTab" class="w-full">
      <TabsList class="mb-4">
        <TabsTrigger value="ai">AI Model</TabsTrigger>
        <TabsTrigger value="rotation">IP rotation</TabsTrigger>
        <TabsTrigger value="notifications">Push notification</TabsTrigger>
        <TabsTrigger value="status">System status</TabsTrigger>
        <TabsTrigger value="prompts">Prompt manage</TabsTrigger>
      </TabsList>

      <!-- AI Tab -->
      <TabsContent value="ai">
        <Card>
          <CardHeader>
            <CardTitle>AI Model settings</CardTitle>
            <CardDescription>Configuring large language models for product analysis。</CardDescription>
          </CardHeader>
          <CardContent v-if="isReady" class="space-y-4">
            <div class="grid gap-2">
              <Label>API Base URL</Label>
              <Input v-model="aiSettings.OPENAI_BASE_URL" placeholder="https://api.openai.com/v1" />
            </div>
            <div class="grid gap-2">
              <Label>API Key</Label>
              <Input
                v-model="aiSettings.OPENAI_API_KEY"
                type="password"
                placeholder="Leave blank to indicate no changes"
              />
              <p class="text-xs text-gray-500">
                {{ systemStatus?.env_file.openai_api_key_set ? 'configured' : 'Not configured' }}，Not echoed for security reasons。
              </p>
            </div>
            <div class="grid gap-2">
              <Label>Model name</Label>
              <Input v-model="aiSettings.OPENAI_MODEL_NAME" placeholder="gpt-3.5-turbo" />
            </div>
            <div class="grid gap-2">
              <Label>proxy address (Optional)</Label>
              <Input v-model="aiSettings.PROXY_URL" placeholder="http://127.0.0.1:7890" />
            </div>
          </CardContent>
          <CardContent v-else class="py-8 text-sm text-gray-500">
            Loading AI Configuration...
          </CardContent>
          <CardFooter v-if="isReady" class="flex gap-2">
            <Button variant="outline" @click="handleTestAi" :disabled="isSaving">test connection</Button>
            <Button @click="handleSaveAi" :disabled="isSaving">save AI set up</Button>
          </CardFooter>
        </Card>
      </TabsContent>

      <!-- Rotation Tab -->
      <TabsContent value="rotation">
        <Card>
          <CardHeader>
            <CardTitle>IP Agent rotation</CardTitle>
            <CardDescription>Configure agent pool and rotation strategy。</CardDescription>
          </CardHeader>
          <CardContent v-if="isReady" class="space-y-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium">Agent rotation</h3>
                <p class="text-sm text-gray-500">Use proxy pool IP rotation。</p>
              </div>
              <Switch v-model:checked="rotationSettings.PROXY_ROTATION_ENABLED" />
            </div>
            <div class="grid gap-2">
              <Label>rotation mode</Label>
              <Select v-model="rotationSettings.PROXY_ROTATION_MODE">
                <SelectTrigger>
                  <SelectValue placeholder="Please select rotation mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="per_task">Fixed by task</SelectItem>
                  <SelectItem value="on_failure">Rotate after failure</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="grid gap-2">
              <Label>proxy pool (comma separated)</Label>
              <Textarea
                v-model="rotationSettings.PROXY_POOL"
                class="min-h-[120px]"
                placeholder="http://127.0.0.1:7890,socks5://127.0.0.1:1080"
              />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="grid gap-2">
                <Label>Retry limit</Label>
                <Input v-model.number="rotationSettings.PROXY_ROTATION_RETRY_LIMIT" type="number" min="1" />
              </div>
              <div class="grid gap-2">
                <Label>blacklist TTL (Second)</Label>
                <Input v-model.number="rotationSettings.PROXY_BLACKLIST_TTL" type="number" min="0" />
              </div>
            </div>
          </CardContent>
          <CardContent v-else class="py-8 text-sm text-gray-500">
            Loading rotation configuration...
          </CardContent>
          <CardFooter v-if="isReady" class="flex gap-2">
            <Button @click="handleSaveRotation" :disabled="isSaving">Save rotation settings</Button>
          </CardFooter>
        </Card>
      </TabsContent>

      <!-- Notifications Tab -->
      <TabsContent value="notifications">
        <Card>
          <CardHeader>
            <CardTitle>Notification push settings</CardTitle>
            <CardDescription>Configure the message push channel after the crawler task is completed。</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div class="grid gap-2">
              <Label>Bark URL (iOS)</Label>
              <Input v-model="notificationSettings.BARK_URL" placeholder="https://api.day.app/YOUR_KEY/" />
            </div>
            <div class="grid gap-2">
              <Label>Ntfy Topic URL</Label>
              <Input v-model="notificationSettings.NTFY_TOPIC_URL" placeholder="https://ntfy.sh/topic" />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="grid gap-2">
                <Label>Gotify URL</Label>
                <Input v-model="notificationSettings.GOTIFY_URL" placeholder="https://gotify.example.com" />
              </div>
              <div class="grid gap-2">
                <Label>Gotify Token</Label>
                <Input v-model="notificationSettings.GOTIFY_TOKEN" placeholder="Token" />
              </div>
            </div>
            <div class="grid gap-2">
              <Label>Enterprise WeChat Bot URL</Label>
              <Input v-model="notificationSettings.WX_BOT_URL" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..." />
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div class="grid gap-2">
                <Label>Telegram Bot Token</Label>
                <Input v-model="notificationSettings.TELEGRAM_BOT_TOKEN" />
              </div>
              <div class="grid gap-2">
                <Label>Telegram Chat ID</Label>
                <Input v-model="notificationSettings.TELEGRAM_CHAT_ID" />
              </div>
            </div>
            <div class="border-t pt-4 space-y-4">
              <div class="grid gap-2">
                <Label>Universal Webhook URL</Label>
                <Input v-model="notificationSettings.WEBHOOK_URL" placeholder="https://your-webhook-url.com/endpoint" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div class="grid gap-2">
                  <Label>Webhook method</Label>
                  <Select
                    :model-value="notificationSettings.WEBHOOK_METHOD || 'POST'"
                    @update:model-value="(value) => notificationSettings.WEBHOOK_METHOD = value as string"
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="POST">POST</SelectItem>
                      <SelectItem value="GET">GET</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div class="grid gap-2">
                  <Label>Webhook Content type</Label>
                  <Select
                    :model-value="notificationSettings.WEBHOOK_CONTENT_TYPE || 'JSON'"
                    @update:model-value="(value) => notificationSettings.WEBHOOK_CONTENT_TYPE = value as string"
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="JSON">JSON</SelectItem>
                      <SelectItem value="FORM">FORM</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div class="grid gap-2">
                <Label>Webhook Request header (JSON)</Label>
                <Textarea v-model="notificationSettings.WEBHOOK_HEADERS" placeholder='For example: {"Authorization": "Bearer token"}' />
              </div>
              <div class="grid gap-2">
                <Label>Webhook Query parameter (JSON)</Label>
                <Textarea v-model="notificationSettings.WEBHOOK_QUERY_PARAMETERS" placeholder='For example: {"param1": "value1"}' />
              </div>
              <div class="grid gap-2">
                <Label>Webhook Body (Support variables)</Label>
                <Textarea v-model="notificationSettings.WEBHOOK_BODY" placeholder='For example: {"message": "${content}"}' />
              </div>
            </div>
             <div class="flex items-center space-x-2 mt-2">
              <Switch id="pcurl" v-model="notificationSettings.PCURL_TO_MOBILE" />
              <Label for="pcurl">Convert product links to mobile links</Label>
            </div>
          </CardContent>
          <CardFooter>
            <Button @click="handleSaveNotifications" :disabled="isSaving">Save notification settings</Button>
          </CardFooter>
        </Card>
      </TabsContent>

      <!-- Status Tab -->
      <TabsContent value="status">
        <Card>
          <CardHeader>
            <CardTitle>System running status</CardTitle>
            <div class="flex justify-end">
                <Button variant="outline" size="sm" @click="refreshStatus" :disabled="isLoading">refresh status</Button>
            </div>
          </CardHeader>
          <CardContent>
            <div v-if="systemStatus" class="space-y-6">
              <!-- Scraper Process Status -->
              <div class="flex items-center justify-between border-b pb-4">
                <div>
                  <h3 class="font-medium">crawler process</h3>
                  <p class="text-sm text-gray-500">Is there any task currently executing the crawl?</p>
                </div>
                <span :class="systemStatus.scraper_running ? 'text-green-600 font-bold bg-green-50 px-3 py-1 rounded-full' : 'text-gray-500 bg-gray-100 px-3 py-1 rounded-full'">
                  {{ systemStatus.scraper_running ? 'Running' : 'idle' }}
                </span>
              </div>

              <!-- Env Config Status -->
              <div>
                <div class="flex items-center justify-between mb-4">
                    <div>
                        <h3 class="font-medium">Environment variable configuration</h3>
                        <p class="text-sm text-gray-500">examine .env Key items in the configuration file</p>
                    </div>
                    <span :class="systemStatus.env_file.exists ? 'text-green-600 font-bold bg-green-50 px-3 py-1 rounded-full' : 'text-red-600 font-bold bg-red-50 px-3 py-1 rounded-full'">
                        {{ systemStatus.env_file.exists ? 'Loaded' : 'Missing' }}
                    </span>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="p-3 border rounded-lg" :class="systemStatus.env_file.openai_api_key_set ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-sm">OpenAI API Key</span>
                            <span class="text-xs font-bold" :class="systemStatus.env_file.openai_api_key_set ? 'text-green-700' : 'text-yellow-700'">
                                {{ systemStatus.env_file.openai_api_key_set ? 'configured' : 'Not configured' }}
                            </span>
                        </div>
                    </div>
                    
                    <div class="p-3 border rounded-lg" :class="(systemStatus.env_file.ntfy_topic_url_set || systemStatus.env_file.gotify_url_set || systemStatus.env_file.bark_url_set) ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'">
                         <div class="flex justify-between items-center">
                            <span class="font-medium text-sm">notification channel</span>
                             <span class="text-xs font-bold" :class="(systemStatus.env_file.ntfy_topic_url_set || systemStatus.env_file.gotify_url_set || systemStatus.env_file.bark_url_set) ? 'text-green-700' : 'text-gray-500'">
                                {{ (systemStatus.env_file.ntfy_topic_url_set || systemStatus.env_file.gotify_url_set || systemStatus.env_file.bark_url_set) ? 'configured' : 'Not configured' }}
                            </span>
                        </div>
                         <div class="text-xs text-gray-500 mt-1">
                            {{ [
                                systemStatus.env_file.ntfy_topic_url_set ? 'Ntfy' : '',
                                systemStatus.env_file.gotify_url_set ? 'Gotify' : '',
                                systemStatus.env_file.bark_url_set ? 'Bark' : ''
                            ].filter(Boolean).join(', ') || 'none' }}
                        </div>
                    </div>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-gray-500">
                Getting system status...
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <!-- Prompt Tab -->
      <TabsContent value="prompts">
        <Card>
          <CardHeader>
            <CardTitle>Prompt manage</CardTitle>
            <CardDescription>Online editing prompts under the directory Prompt document。</CardDescription>
          </CardHeader>
          <CardContent class="space-y-4">
            <div v-if="promptError" class="bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded">
              {{ promptError }}
            </div>

            <div class="grid gap-2">
              <Label>choose Prompt document</Label>
              <Select
                :model-value="selectedPrompt || undefined"
                @update:model-value="(value) => selectedPrompt = value as string"
              >
                <SelectTrigger>
                  <SelectValue placeholder="Please select one Prompt document..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem v-for="file in promptFiles" :key="file" :value="file">
                    {{ file }}
                  </SelectItem>
                </SelectContent>
              </Select>
              <p v-if="!promptFiles.length && !isPromptLoading" class="text-sm text-gray-500">
                not found Prompt document。
              </p>
            </div>

            <div class="grid gap-2">
              <Label>Prompt content</Label>
              <Textarea
                v-model="promptContent"
                class="min-h-[240px]"
                :disabled="!selectedPrompt || isPromptLoading"
                placeholder="Please select one Prompt file for editing..."
              />
            </div>
          </CardContent>
          <CardFooter>
            <Button :disabled="isPromptSaving || !selectedPrompt" @click="handleSavePrompt">
              {{ isPromptSaving ? 'Saving...' : 'Save changes' }}
            </Button>
          </CardFooter>
        </Card>
      </TabsContent>
    </Tabs>
  </div>
</template>
