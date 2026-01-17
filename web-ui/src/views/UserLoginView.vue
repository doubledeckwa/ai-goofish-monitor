<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useUser } from '@/composables/useUser'
import type { UserLoginRequest } from '@/types/user'

const router = useRouter()
const route = useRoute()
const { login, isAuthenticated, isLoading } = useUser()

if (isAuthenticated.value) {
  router.push('/')
}

const form = ref<UserLoginRequest>({
  username: '',
  password: '',
})

const error = ref<string | null>(null)

async function handleSubmit() {
  try {
    error.value = null
    await login(form.value)

    const redirect = route.query.redirect as string
    router.push(redirect || '/')
  } catch (e) {
    error.value = 'Invalid username or password'
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center p-4">
    <Card class="w-full max-w-md">
      <CardHeader>
        <CardTitle class="text-2xl">Login</CardTitle>
        <CardDescription>
          Enter your credentials to access your account
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
              placeholder="Enter your username"
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
              placeholder="Enter your password"
              required
              :disabled="isLoading"
            />
          </div>

          <Button type="submit" class="w-full" :disabled="isLoading">
            {{ isLoading ? 'Logging in...' : 'Login' }}
          </Button>

          <div class="text-center text-sm text-gray-600">
            Don't have an account?
            <RouterLink to="/user/register" class="text-blue-600 hover:text-blue-800 font-medium">
              Register
            </RouterLink>
          </div>
        </form>

        <div class="mt-6 pt-6 border-t">
          <RouterLink to="/admin/login" class="text-sm text-gray-600 hover:text-gray-900">
            Admin Login
          </RouterLink>
        </div>
      </CardContent>
    </Card>
  </div>
</template>
