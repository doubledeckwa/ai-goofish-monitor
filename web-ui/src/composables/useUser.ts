import { ref, computed } from 'vue'
import type { User, UserRegisterRequest, UserLoginRequest, TokenResponse } from '@/types/user'
import {
  register as registerApi,
  login as loginApi,
  getCurrentUser as getCurrentUserApi,
  logout as logoutApi,
  getToken,
  setToken,
} from '@/api/user'

const currentUser = ref<User | null>(null)
const isLoading = ref(false)

export function useUser() {
  const isAuthenticated = computed(() => currentUser.value !== null)

  async function loadCurrentUser() {
    const token = getToken()
    if (!token) {
      currentUser.value = null
      return
    }

    try {
      isLoading.value = true
      currentUser.value = await getCurrentUserApi()
    } catch (e) {
      console.error('Failed to load current user', e)
      logout()
    } finally {
      isLoading.value = false
    }
  }

  async function register(request: UserRegisterRequest): Promise<TokenResponse> {
    const result = await registerApi(request)
    setToken(result.access_token)
    currentUser.value = result.user
    return result
  }

  async function login(request: UserLoginRequest): Promise<TokenResponse> {
    const result = await loginApi(request)
    setToken(result.access_token)
    currentUser.value = result.user
    return result
  }

  async function logout() {
    await logoutApi()
    currentUser.value = null
  }

  function checkAuth() {
    const token = getToken()
    if (token && !currentUser.value) {
      loadCurrentUser()
    }
  }

  return {
    currentUser,
    isAuthenticated,
    isLoading,
    register,
    login,
    logout,
    loadCurrentUser,
    checkAuth,
  }
}
