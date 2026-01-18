import type { UserFeed, Subscription, UserInterest, UserInterestIn } from '@/types/feed'

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

  toggleLike: (userId: number, itemId: number): Promise<{ liked: boolean }> =>
    fetch(`${API_URL}/feed/${userId}/items/${itemId}/like`, {
      method: 'POST',
    }).then((res) => handleResponse<{ liked: boolean }>(res)),

  toggleDislike: (userId: number, itemId: number): Promise<{ disliked: boolean }> =>
    fetch(`${API_URL}/feed/${userId}/items/${itemId}/dislike`, {
      method: 'POST',
    }).then((res) => handleResponse<{ disliked: boolean }>(res)),

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

  // Interests
  getInterests: (userId: number): Promise<UserInterest[]> =>
    fetch(`${API_URL}/users/${userId}/interests`).then((res) =>
      handleResponse<UserInterest[]>(res)
    ),

  replaceInterests: (userId: number, interests: UserInterestIn[]): Promise<UserInterest[]> =>
    fetch(`${API_URL}/users/${userId}/interests`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ interests }),
    }).then((res) => handleResponse<UserInterest[]>(res)),

  addInterest: (userId: number, interest: UserInterestIn): Promise<UserInterest> =>
    fetch(`${API_URL}/users/${userId}/interests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(interest),
    }).then((res) => handleResponse<UserInterest>(res)),

  deleteInterest: (userId: number, interestId: number): Promise<void> =>
    fetch(`${API_URL}/users/${userId}/interests/${interestId}`, {
      method: 'DELETE',
    }).then((res) => handleResponse<void>(res)),
}
