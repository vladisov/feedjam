import type {
  UserFeed,
  Subscription,
  UserInterest,
  UserInterestIn,
  UserSettings,
  UserSettingsIn,
  SearchResultItem,
  SearchParams,
} from '@/types/feed'

const API_URL = import.meta.env.VITE_API_URL || '/api'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `HTTP error ${response.status}`)
  }
  return response.json()
}

function post<T>(url: string): Promise<T> {
  return fetch(url, { method: 'POST' }).then((res) => handleResponse<T>(res))
}

function postJson<T>(url: string, body: unknown): Promise<T> {
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((res) => handleResponse<T>(res))
}

function putJson<T>(url: string, body: unknown): Promise<T> {
  return fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then((res) => handleResponse<T>(res))
}

function del<T>(url: string): Promise<T> {
  return fetch(url, { method: 'DELETE' }).then((res) => handleResponse<T>(res))
}

function get<T>(url: string): Promise<T> {
  return fetch(url).then((res) => handleResponse<T>(res))
}

export const api = {
  // Feed
  getFeed: (userId: number): Promise<UserFeed> =>
    get(`${API_URL}/feed/${userId}`),

  markRead: (userId: number, itemId: number): Promise<void> =>
    post(`${API_URL}/feed/${userId}/mark-read/${itemId}`),

  toggleLike: (userId: number, itemId: number): Promise<{ liked: boolean }> =>
    post(`${API_URL}/feed/${userId}/items/${itemId}/like`),

  toggleDislike: (userId: number, itemId: number): Promise<{ disliked: boolean }> =>
    post(`${API_URL}/feed/${userId}/items/${itemId}/dislike`),

  toggleStar: (userId: number, itemId: number): Promise<{ starred: boolean }> =>
    post(`${API_URL}/feed/${userId}/items/${itemId}/star`),

  toggleHide: (userId: number, itemId: number): Promise<{ hidden: boolean }> =>
    post(`${API_URL}/feed/${userId}/items/${itemId}/hide`),

  hideRead: (userId: number): Promise<{ hidden_count: number }> =>
    post(`${API_URL}/feed/${userId}/hide-read`),

  markAllRead: (userId: number): Promise<{ read_count: number }> =>
    post(`${API_URL}/feed/${userId}/mark-all-read`),

  searchItems: (userId: number, params: SearchParams): Promise<SearchResultItem[]> => {
    const searchParams = new URLSearchParams()
    if (params.liked !== undefined) searchParams.set('liked', String(params.liked))
    if (params.disliked !== undefined) searchParams.set('disliked', String(params.disliked))
    if (params.starred !== undefined) searchParams.set('starred', String(params.starred))
    if (params.read !== undefined) searchParams.set('read', String(params.read))
    if (params.hidden !== undefined) searchParams.set('hidden', String(params.hidden))
    if (params.text) searchParams.set('text', params.text)
    if (params.source) searchParams.set('source', params.source)
    if (params.limit) searchParams.set('limit', String(params.limit))
    if (params.offset) searchParams.set('offset', String(params.offset))
    return get(`${API_URL}/feed/${userId}/search?${searchParams.toString()}`)
  },

  // Subscriptions
  getSubscriptions: (userId: number): Promise<Subscription[]> =>
    get(`${API_URL}/subscriptions?user_id=${userId}`),

  addSubscription: (resourceUrl: string, userId: number): Promise<Subscription> =>
    postJson(`${API_URL}/subscriptions`, { resource_url: resourceUrl, user_id: userId }),

  deleteSubscription: (subscriptionId: number): Promise<void> =>
    del(`${API_URL}/subscriptions/${subscriptionId}`),

  // Interests
  getInterests: (userId: number): Promise<UserInterest[]> =>
    get(`${API_URL}/users/${userId}/interests`),

  replaceInterests: (userId: number, interests: UserInterestIn[]): Promise<UserInterest[]> =>
    putJson(`${API_URL}/users/${userId}/interests`, { interests }),

  addInterest: (userId: number, interest: UserInterestIn): Promise<UserInterest> =>
    postJson(`${API_URL}/users/${userId}/interests`, interest),

  deleteInterest: (userId: number, interestId: number): Promise<void> =>
    del(`${API_URL}/users/${userId}/interests/${interestId}`),

  // Settings
  getSettings: (userId: number): Promise<UserSettings> =>
    get(`${API_URL}/users/${userId}/settings`),

  updateSettings: (userId: number, settings: UserSettingsIn): Promise<UserSettings> =>
    putJson(`${API_URL}/users/${userId}/settings`, settings),
}
