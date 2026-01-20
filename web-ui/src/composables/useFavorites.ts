import type { Favorite, FavoriteRequest, PaginatedFavorites } from '@/types/user'
import { addFavorite, removeFavorite, toggleFavorite, getFavorites } from '@/api/user'
import { useUser } from './useUser'

export function useFavorites() {
  const { currentUser } = useUser()

  async function addToFavorite(request: FavoriteRequest): Promise<Favorite> {
    const result = await addFavorite(request)
    return result.favorite
  }

  async function removeFromFavorite(productId: string): Promise<void> {
    await removeFavorite(productId)
  }

  async function toggleProductFavorite(
    request: FavoriteRequest
  ): Promise<{ isFavorited: boolean; favorite?: Favorite }> {
    if (!currentUser.value) {
      throw new Error('User must be logged in')
    }

    const result = await toggleFavorite(request)
    return {
      isFavorited: result.is_added,
      favorite: result.favorite,
    }
  }

  async function loadFavorites(
    page: number = 1,
    limit: number = 20
  ): Promise<PaginatedFavorites> {
    return getFavorites(page, limit)
  }

  return {
    addToFavorite,
    removeFromFavorite,
    toggleProductFavorite,
    loadFavorites,
  }
}
