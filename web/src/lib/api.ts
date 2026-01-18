import type { UserFeed, Subscription } from '@/types/feed'

const API_URL = import.meta.env.VITE_API_URL || '/api'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `HTTP error ${response.status}`)
  }
  return response.json()
}

export const api = {
  // Feed
  getFeed: (userId: number): Promise<UserFeed> =>
    fetch(`${API_URL}/feed/${userId}`).then((res) => handleResponse<UserFeed>(res)),

  markRead: (userId: number, itemId: number): Promise<void> =>
    fetch(`${API_URL}/feed/${userId}/items/${itemId}/read`, {
      method: 'POST',
    }).then((res) => handleResponse<void>(res)),

  // Subscriptions
  getSubscriptions: (userId: number): Promise<Subscription[]> =>
    fetch(`${API_URL}/subscriptions?user_id=${userId}`).then((res) =>
      handleResponse<Subscription[]>(res)
    ),

  addSubscription: (resourceUrl: string, userId: number): Promise<Subscription> =>
    fetch(`${API_URL}/subscribe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_url: resourceUrl, user_id: userId }),
    }).then((res) => handleResponse<Subscription>(res)),
}
