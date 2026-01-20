<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { User, LogOut, Heart } from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { useUser } from '@/composables/useUser'

const { currentUser, isAuthenticated, logout } = useUser()

function handleLogout() {
  logout()
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex flex-col">
    <header class="bg-white border-b border-gray-200 shadow-sm">
      <div class="container mx-auto px-4 h-16 flex items-center justify-between">
        <RouterLink to="/" class="flex items-center gap-2">
          <span class="text-xl font-bold text-gray-900">Marketplace</span>
        </RouterLink>

        <div class="flex items-center gap-4">
          <RouterLink to="/favorites" v-if="isAuthenticated">
            <Button variant="ghost" size="icon">
              <Heart :size="20" />
            </Button>
          </RouterLink>

          <div v-if="isAuthenticated" class="flex items-center gap-2">
            <span class="text-sm text-gray-600">{{ currentUser?.username }}</span>
            <Button variant="ghost" size="icon" @click="handleLogout">
              <LogOut :size="20" />
            </Button>
          </div>

          <RouterLink to="/user/login" v-else>
            <Button>
              <User class="mr-2" :size="18" />
              Login
            </Button>
          </RouterLink>
        </div>
      </div>
    </header>

    <main class="flex-grow">
      <slot />
    </main>

    <footer class="bg-white border-t border-gray-200 py-6">
      <div class="container mx-auto px-4 text-center text-sm text-gray-600">
        <p>&copy; 2026 Marketplace. All rights reserved.</p>
        <RouterLink to="/admin/login" class="text-blue-600 hover:text-blue-800 ml-4">
          Admin
        </RouterLink>
      </div>
    </footer>
  </div>
</template>
