<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listAccounts, getAccount, createAccount, updateAccount, deleteAccount, type AccountItem } from '@/api/accounts'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from '@/components/ui/toast'

const accounts = ref<AccountItem[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const router = useRouter()

const isCreateDialogOpen = ref(false)
const isEditDialogOpen = ref(false)
const isDeleteDialogOpen = ref(false)

const newName = ref('')
const newContent = ref('')
const editName = ref('')
const editContent = ref('')
const deleteName = ref('')

async function fetchAccounts() {
  isLoading.value = true
  try {
    accounts.value = await listAccounts()
  } catch (e) {
    toast({ title: 'Failed to load account', description: (e as Error).message, variant: 'destructive' })
  } finally {
    isLoading.value = false
  }
}

function openCreateDialog() {
  newName.value = ''
  newContent.value = ''
  isCreateDialogOpen.value = true
}

async function openEditDialog(name: string) {
  isSaving.value = true
  try {
    const detail = await getAccount(name)
    editName.value = detail.name
    editContent.value = detail.content
    isEditDialogOpen.value = true
  } catch (e) {
    toast({ title: 'Failed to load account content', description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

function openDeleteDialog(name: string) {
  deleteName.value = name
  isDeleteDialogOpen.value = true
}

function goCreateTask(name: string) {
  router.push({ path: '/tasks', query: { account: name, create: '1' } })
}

async function handleCreateAccount() {
  if (!newName.value.trim() || !newContent.value.trim()) {
    toast({ title: 'Incomplete information', description: 'Please fill in the account name and paste it JSON content。', variant: 'destructive' })
    return
  }
  isSaving.value = true
  try {
    await createAccount({ name: newName.value.trim(), content: newContent.value.trim() })
    toast({ title: 'Account has been added' })
    isCreateDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: 'Failed to add account', description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

async function handleUpdateAccount() {
  if (!editContent.value.trim()) {
    toast({ title: 'Content cannot be empty', description: 'Please paste JSON content。', variant: 'destructive' })
    return
  }
  isSaving.value = true
  try {
    await updateAccount(editName.value, editContent.value.trim())
    toast({ title: 'Account has been updated' })
    isEditDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: 'Failed to update account', description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteAccount() {
  isSaving.value = true
  try {
    await deleteAccount(deleteName.value)
    toast({ title: 'Account has been deleted' })
    isDeleteDialogOpen.value = false
    await fetchAccounts()
  } catch (e) {
    toast({ title: 'Failed to delete account', description: (e as Error).message, variant: 'destructive' })
  } finally {
    isSaving.value = false
  }
}

onMounted(fetchAccounts)
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Xianyu account management</h1>
        <p class="text-sm text-gray-500 mt-1">use Chrome Extension to extract login status JSON，and add account here。</p>
      </div>
      <Button @click="openCreateDialog">+ Add account</Button>
    </div>

    <Card class="mb-6">
      <CardHeader>
        <CardTitle>Get XianyuCookie</CardTitle>
      </CardHeader>
      <CardContent class="text-sm text-gray-600">
        <ol class="list-decimal list-inside space-y-1">
          <li>
            Install
            <a
              class="text-blue-600 hover:underline"
              href="https://chromewebstore.google.com/detail/xianyu-login-state-extrac/eidlpfjiodpigmfcahkmlenhppfklcoa"
              target="_blank"
              rel="noopener noreferrer"
            >Xianyu login status extraction extension</a>
          </li>
          <li>
            Open and log in
            <a
              class="text-blue-600 hover:underline"
              href="https://www.goofish.com"
              target="_blank"
              rel="noopener noreferrer"
            >Xianyu official website</a>
          </li>
          <li>Click on the extension icon and select“Extract login status" and click“copy to clipboard”</li>
          <li>Return to this page, click“Add account" and paste JSON content and save</li>
          <li>If you configure multiple accounts, do not exit the Xianyu account in the current window.，You can open a new incognito window to log in and extract other accountsCookie</li>
        </ol>
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Account list</CardTitle>
        <CardDescription>The account file is saved in state/ directory, can be bound to tasks。</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account name</TableHead>
              <TableHead>status file</TableHead>
              <TableHead class="text-right">operate</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="isLoading">
              <TableCell colspan="3" class="h-20 text-center text-muted-foreground">loading...</TableCell>
            </TableRow>
            <TableRow v-else-if="accounts.length === 0">
              <TableCell colspan="3" class="h-20 text-center text-muted-foreground">No account yet</TableCell>
            </TableRow>
            <TableRow v-else v-for="account in accounts" :key="account.name">
              <TableCell class="font-medium">{{ account.name }}</TableCell>
              <TableCell class="text-sm text-gray-500">{{ account.path }}</TableCell>
              <TableCell class="text-right">
                <div class="flex justify-end gap-2">
                  <Button size="sm" variant="outline" @click="goCreateTask(account.name)">Create tasks</Button>
                  <Button size="sm" variant="outline" @click="openEditDialog(account.name)">renew</Button>
                  <Button size="sm" variant="destructive" @click="openDeleteDialog(account.name)">delete</Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </CardContent>
    </Card>

    <Dialog v-model:open="isCreateDialogOpen">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>Add Xianyu account</DialogTitle>
          <DialogDescription>Paste through Chrome Extracted by plug-in JSON content。</DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="grid gap-2">
            <Label>Account name</Label>
            <Input v-model="newName" placeholder="For example：acc_1" />
          </div>
          <div class="grid gap-2">
            <Label>JSON content</Label>
            <Textarea v-model="newContent" class="min-h-[200px]" placeholder="Please paste login status JSON..." />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isCreateDialogOpen = false">Cancel</Button>
          <Button :disabled="isSaving" @click="handleCreateAccount">
            {{ isSaving ? 'Saving...' : 'save' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isEditDialogOpen">
      <DialogContent class="sm:max-w-[700px]">
        <DialogHeader>
          <DialogTitle>Update account：{{ editName }}</DialogTitle>
          <DialogDescription>Replace the login status of an account JSON。</DialogDescription>
        </DialogHeader>
        <div class="space-y-4">
          <div class="grid gap-2">
            <Label>JSON content</Label>
            <Textarea v-model="editContent" class="min-h-[200px]" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="isEditDialogOpen = false">Cancel</Button>
          <Button :disabled="isSaving" @click="handleUpdateAccount">
            {{ isSaving ? 'Saving...' : 'save' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <Dialog v-model:open="isDeleteDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete account</DialogTitle>
          <DialogDescription>Confirm account deletion {{ deleteName }} ? This operation is irreversible。</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="isDeleteDialogOpen = false">Cancel</Button>
          <Button variant="destructive" :disabled="isSaving" @click="handleDeleteAccount">
            {{ isSaving ? 'Deleting...' : 'delete' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
