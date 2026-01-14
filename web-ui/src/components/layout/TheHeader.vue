<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'

const router = useRouter()

function goAccounts() {
  router.push('/accounts')
}
</script>

<template>
  <header class="bg-white h-16 px-6 border-b border-gray-200 flex justify-between items-center flex-shrink-0 shadow-sm z-10">
    <h1 class="text-xl font-semibold text-gray-800">
      Xianyu intelligent monitoring robot
    </h1>
    <div class="ml-auto">
      <Button variant="outline" size="sm" @click="goAccounts">Xianyu account management</Button>
    </div>
  </header>
</template>
