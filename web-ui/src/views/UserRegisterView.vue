<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useUser } from '@/composables/useUser'
import type { UserRegisterRequest } from '@/types/user'

const router = useRouter()
const { register, isAuthenticated, isLoading } = useUser()

if (isAuthenticated.value) {
  router.push('/')
}

const form = ref<UserRegisterRequest>({
  username: '',
  email: '',
  password: '',
})

const error = ref<string | null>(null)

async function handleSubmit() {
  try {
    error.value = null
    await register(form.value)
    router.push('/')
  } catch (e) {
    error.value = (e as Error).message
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center p-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">Register</CardTitle>
        <CardDescription>
          Create a new account to save your favorites
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div v-if="error" class="bg-red-100 text-red-700 p-3 rounded-lg text-sm">
            {{ error }}
          </div>

          <div class="space-y-2">
            <Label for="username">Username</Label>
            <Input
              id="username"
              v-model="form.username"
              placeholder="Choose a username"
              required
              minlength="3"
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="form.email"
              type="email"
              placeholder="Enter your email"
              required
              :disabled="isLoading"
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              placeholder="Choose a password"
              required
              minlength="6"
              :disabled="isLoading"
            />
          </div>

          <Button type="submit" class="w-full" :disabled="isLoading">
            {{ isLoading ? 'Creating account...' : 'Register' }}
          </Button>

          <div class="text-center text-sm text-gray-600">
            Already have an account?
            <RouterLink to="/user/login" class="text-blue-600 hover:text-blue-800 font-medium">
              Login
            </RouterLink>
          </div>
        </form>
      </CardContent>
    </Card>
  </div>
</template>
