<script setup lang="ts">
import { ref, watchEffect } from 'vue'
import type { Task, TaskGenerateRequest } from '@/types/task.d.ts'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Textarea } from '@/components/ui/textarea'
import { toast } from '@/components/ui/toast'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

type FormMode = 'create' | 'edit'
type EmittedData = TaskGenerateRequest | Partial<Task>

const props = defineProps<{
  mode: FormMode
  initialData?: Task | null
  accountOptions?: { name: string; path: string }[]
  defaultAccount?: string
}>()

const emit = defineEmits<{
  (e: 'submit', data: EmittedData): void
}>()

const form = ref<EmittedData>({})

// Initialize form based on mode and initialData
  watchEffect(() => {
   if (props.mode === 'edit' && props.initialData) {
     form.value = {
       ...props.initialData,
       task_type: props.initialData.task_type || 'keyword_search',
       keyword: props.initialData.keyword || '',
       seller_id: props.initialData.seller_id || '',
       max_products_per_run: props.initialData.max_products_per_run || undefined,
       account_state_file: props.initialData.account_state_file || '',
       free_shipping: props.initialData.free_shipping ?? true,
       new_publish_option: props.initialData.new_publish_option || '__none__',
       region: props.initialData.region || '',
       is_public: props.initialData.is_public ?? false,
     }
   } else {
     form.value = {
       task_name: '',
       task_type: 'keyword_search',
       keyword: '',
       seller_id: '',
       description: '',
       max_pages: 3,
       max_products_per_run: undefined,
       personal_only: true,
       min_price: undefined,
       max_price: undefined,
       cron: '',
       account_state_file: props.defaultAccount || '',
       free_shipping: true,
       new_publish_option: '__none__',
       region: '',
       is_public: false,
     }
   }
 })

function handleSubmit() {
  // Basic validation
  if (!form.value.task_name || !form.value.description) {
    toast({
      title: 'Incomplete information',
      description: 'Task name and detailed requirements cannot be empty。',
      variant: 'destructive',
    })
    return
  }
  
  // Task type specific validation
  if (form.value.task_type === 'seller_monitoring' && !form.value.seller_id) {
    toast({
      title: 'Seller ID required',
      description: 'Please enter the seller ID for monitoring。',
      variant: 'destructive',
    })
    return
  }
  
  if (form.value.task_type === 'keyword_search' && !form.value.keyword) {
    toast({
      title: 'Keyword required',
      description: 'Please enter search keyword。',
      variant: 'destructive',
    })
    return
  }

  // Filter out fields that shouldn't be sent in update requests
  const { id, is_running, ...submitData } = form.value as any
  if (submitData.account_state_file === '') {
    submitData.account_state_file = null
  }
  if (typeof submitData.region === 'string') {
    const normalized = submitData.region
      .trim()
      .split('/')
      .map((part: string) => part.trim().replace(/(Province|city)$/u, ''))
      .filter((part: string) => part.length > 0)
      .join('/')
    submitData.region = normalized
  }
  if (submitData.new_publish_option === '__none__') {
    submitData.new_publish_option = ''
  }
  emit('submit', submitData)
}
</script>

<template>
  <form id="task-form" @submit.prevent="handleSubmit">
    <div class="grid gap-6 py-4">
      <div class="grid grid-cols-4 items-center gap-4">
        <Label for="task-name" class="text-right">Task name</Label>
        <Input id="task-name" v-model="form.task_name" class="col-span-3" placeholder="Example: Sony A7M4 camera" required />
      </div>
      
      <div class="grid grid-cols-4 items-center gap-4">
        <Label class="text-right">Task type</Label>
        <div class="col-span-3">
          <Select v-model="form.task_type">
            <SelectTrigger>
              <SelectValue placeholder="Select task type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="keyword_search">Search by keyword</SelectItem>
              <SelectItem value="seller_monitoring">Monitor seller</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <div v-if="form.task_type === 'keyword_search'" class="grid grid-cols-4 items-center gap-4">
        <Label for="keyword" class="text-right">Search keywords</Label>
        <Input id="keyword" v-model="form.keyword" class="col-span-3" placeholder="For example：a7m4" />
      </div>
      
      <div v-if="form.task_type === 'seller_monitoring'" class="grid grid-cols-4 items-center gap-4">
        <Label for="seller-id" class="text-right">Seller ID</Label>
        <Input 
          id="seller-id" 
          v-model="form.seller_id" 
          class="col-span-3" 
          placeholder="Example: 1234567890" 
        />
      </div>
      
      <div v-if="form.task_type === 'seller_monitoring'" class="grid grid-cols-4 items-center gap-4">
        <Label for="max-products" class="text-right">Max products per run</Label>
        <div class="col-span-3 space-y-2">
          <Input 
            id="max-products" 
            v-model.number="form.max_products_per_run" 
            type="number"
            placeholder="Leave empty for unlimited (e.g., 10)" 
          />
          <p class="text-xs text-gray-500">Limit how many new products to analyze per run. Useful for sellers with many products.</p>
        </div>
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label for="description" class="text-right">Detailed requirements</Label>
        <Textarea
          id="description"
          v-model="form.description"
          class="col-span-3"
          placeholder="Please describe your purchase needs in detail in natural language，AIAnalysis criteria will be generated based on this description..."
          required
        />
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label class="text-right">price range</Label>
        <div class="col-span-3 flex items-center gap-2">
          <Input type="number" v-model="form.min_price as any" placeholder="lowest price" />
          <span>-</span>
          <Input type="number" v-model="form.max_price as any" placeholder="highest price" />
        </div>
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label for="max-pages" class="text-right">Number of search pages</Label>
        <Input id="max-pages" v-model.number="form.max_pages" type="number" class="col-span-3" />
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label for="cron" class="text-right">Timing rules</Label>
        <Input id="cron" v-model="form.cron as any" class="col-span-3" placeholder="point hour day moon week (For example: 0 8 * * *)" />
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label class="text-right">Bind account</Label>
        <div class="col-span-3">
          <Select v-model="form.account_state_file">
            <SelectTrigger>
              <SelectValue placeholder="Not bound (automatically selected）" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">Not bound (automatically selected）</SelectItem>
              <SelectItem v-for="account in accountOptions || []" :key="account.path" :value="account.path">
                {{ account.name }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label for="personal-only" class="text-right">Only individual sellers</Label>
        <Switch id="personal-only" v-model="form.personal_only" />
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label class="text-right">Is it free shipping?</Label>
        <Switch v-model="form.free_shipping" />
      </div>
      <div class="grid grid-cols-4 items-center gap-4">
        <Label class="text-right">New release scope</Label>
        <div class="col-span-3">
          <Select v-model="form.new_publish_option as any">
            <SelectTrigger>
              <SelectValue placeholder="No filtering (default）" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">No filtering (default）</SelectItem>
              <SelectItem value="up to date">up to date</SelectItem>
              <SelectItem value="1within days">1within days</SelectItem>
              <SelectItem value="3within days">3within days</SelectItem>
              <SelectItem value="7within days">7within days</SelectItem>
              <SelectItem value="14within days">14within days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
       <div class="grid grid-cols-4 items-center gap-4">
         <Label class="text-right">Area filter(Leave blank by default)</Label>
         <div class="col-span-3 space-y-1">
           <Input
             v-model="form.region as any"
             placeholder="For example： Zhejiang/Hangzhou/Binjiang District or Zhejiang/Hangzhou/All Hangzhou or Shanghai/Xuhui District"
           />
           <p class="text-xs text-gray-500">Regional filtering will result in a small number of products that meet the conditions</p>
         </div>
       </div>
       <div class="grid grid-cols-4 items-center gap-4">
         <Label class="text-right">Publish to marketplace</Label>
         <div class="col-span-3 flex items-center gap-2">
           <Switch v-model="form.is_public" />
           <p class="text-sm text-gray-600">Show products from this task on public marketplace</p>
         </div>
       </div>
     </div>
   </form>
 </template>
