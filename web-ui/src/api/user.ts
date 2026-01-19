import type {
  User,
  UserRegisterRequest,
  UserLoginRequest,
  TokenResponse,
  Favorite,
  FavoriteRequest,
  PaginatedFavorites
} from '@/types/user'

const BASE_URL = '/api/public'

let currentToken: string | null = localStorage.getItem('user_token')

export function getToken(): string | null {
  return currentToken
}

export function setToken(token: string | null): void {
  currentToken = token
  if (token) {
    localStorage.setItem('user_token', token)
  } else {
    localStorage.removeItem('user_token')
  }
}

function getAuthHeaders(): HeadersInit {
  return currentToken
    ? { Authorization: `Bearer ${currentToken}` }
    : {}
}

export async function register(request: UserRegisterRequest): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Registration failed')
  }
  return response.json()
}

export async function login(request: UserLoginRequest): Promise<TokenResponse> {
  const response = await fetch(`${BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Login failed')
  }
  return response.json()
}

export async function getCurrentUser(): Promise<User> {
  const response = await fetch(`${BASE_URL}/me`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to fetch user')
  return response.json()
}

export async function getFavorites(
  page: number = 1,
  limit: number = 20
): Promise<PaginatedFavorites> {
  const params = new URLSearchParams({ page: String(page), limit: String(limit) })
  const response = await fetch(`${BASE_URL}/favorites?${params}`, {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to fetch favorites')
  return response.json()
}

export async function addFavorite(request: FavoriteRequest): Promise<{ message: string; favorite: Favorite }> {
  const response = await fetch(`${BASE_URL}/favorites`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to add favorite')
  }
  return response.json()
}

export async function removeFavorite(productId: string): Promise<{ message: string }> {
  const response = await fetch(`${BASE_URL}/favorites/${productId}`, {
    method: 'DELETE',
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to remove favorite')
  return response.json()
}

export async function toggleFavorite(
  request: FavoriteRequest
): Promise<{ message: string; is_added: boolean; favorite: Favorite }> {
  const response = await fetch(`${BASE_URL}/favorites/toggle`, {
    method: 'POST',
    headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!response.ok) throw new Error('Failed to toggle favorite')
  return response.json()
}

export async function logout(): Promise<void> {
  setToken(null)
}
