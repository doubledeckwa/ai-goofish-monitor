export interface User {
  id: number
  username: string
  email: string
  role: 'user' | 'admin'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface UserRegisterRequest {
  username: string
  email: string
  password: string
}

export interface UserLoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Favorite {
  id: number
  user_id: number
  product_id: string
  task_name: string
  product_title: string
  price: string
  image_url?: string
  product_link: string
  created_at: string
}

export interface FavoriteRequest {
  product_id: string
  task_name: string
  product_title: string
  price: string
  image_url?: string
  product_link: string
}

export interface PaginatedFavorites {
  items: Favorite[]
  total: number
  page: number
  limit: number
}
