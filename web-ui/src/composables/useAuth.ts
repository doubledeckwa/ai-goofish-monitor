import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

// Global State
const username = ref<string | null>(localStorage.getItem('auth_username'))
const credentials = ref<string | null>(localStorage.getItem('auth_credentials')) // Base64 encoded 'user:pass'

export function useAuth() {
  const router = useRouter()

  const isAuthenticated = computed(() => !!credentials.value)

  function setCredentials(user: string, pass: string) {
    const encoded = btoa(`${user}:${pass}`)
    username.value = user
    credentials.value = encoded
    
    localStorage.setItem('auth_username', user)
    localStorage.setItem('auth_credentials', encoded)
  }

  function logout() {
    username.value = null
    credentials.value = null
    localStorage.removeItem('auth_username')
    localStorage.removeItem('auth_credentials')
    
    // Redirect to login if using router
    if (router) {
      router.push('/login')
    } else {
      window.location.href = '/login'
    }
  }

  async function login(user: string, pass: string): Promise<boolean> {
    const encoded = btoa(`${user}:${pass}`)
    
    try {
      const response = await fetch('/auth/status', {
        headers: {
          'Authorization': `Basic ${encoded}`
        }
      })

      if (response.ok) {
        setCredentials(user, pass)
        return true
      } else {
        return false
      }
    } catch (e) {
      console.error('Login error', e)
      return false
    }
  }

  return {
    username,
    credentials,
    isAuthenticated,
    login,
    logout
  }
}
