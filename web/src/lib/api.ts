import type {
  UserFeed,
  FeedItem,
  DigestItem,
  Subscription,
  UserInterest,
  UserInterestIn,
  UserSettings,
  UserSettingsIn,
  InboxAddress,
  SearchResultItem,
  SearchParams,
  AuthUser,
  TokenResponse,
  LoginCredentials,
  RegisterCredentials,
} from '@/types/feed'

const API_URL = import.meta.env.VITE_API_URL || '/api'

// Token storage keys
const ACCESS_TOKEN_KEY = 'feedjam_access_token'
const REFRESH_TOKEN_KEY = 'feedjam_refresh_token'

// Token management
export const tokenStorage = {
  getAccessToken: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (access: string, refresh: string): void => {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  clearTokens: (): void => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

// Build headers with auth token
function getAuthHeaders(): HeadersInit {
  const token = tokenStorage.getAccessToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// Auth error event - AuthContext listens for this to trigger logout
export const AUTH_ERROR_EVENT = 'feedjam:auth_error'

function dispatchAuthError() {
  window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT))
}

// Handle response with auto-refresh on 401
async function handleResponse<T>(response: Response, retryFn?: () => Promise<T>): Promise<T> {
  // 403 = no token (HTTPBearer returns this when header missing)
  if (response.status === 403 && retryFn) {
    // No token present, trigger auth error immediately
    tokenStorage.clearTokens()
    dispatchAuthError()
    throw new Error('Please log in to continue.')
  }

  // 401 = invalid/expired token
  if (response.status === 401 && retryFn) {
    // Try to refresh token
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      return retryFn()
    }
    // Refresh failed, clear tokens and notify AuthContext
    tokenStorage.clearTokens()
    dispatchAuthError()
    throw new Error('Session expired. Please log in again.')
  }

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || `HTTP error ${response.status}`)
  }
  return response.json()
}

// Refresh access token using refresh token
async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = tokenStorage.getRefreshToken()
  if (!refreshToken) return false

  try {
    const response = await fetch(`${API_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    if (!response.ok) return false

    const data: TokenResponse = await response.json()
    tokenStorage.setTokens(data.access_token, data.refresh_token)
    return true
  } catch {
    return false
  }
}

function post<T>(url: string): Promise<T> {
  const doFetch = () =>
    fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
    }).then((res) => handleResponse<T>(res, doFetch))
  return doFetch()
}

function postJson<T>(url: string, body: unknown): Promise<T> {
  const doFetch = () =>
    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify(body),
    }).then((res) => handleResponse<T>(res, doFetch))
  return doFetch()
}

function putJson<T>(url: string, body: unknown): Promise<T> {
  const doFetch = () =>
    fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify(body),
    }).then((res) => handleResponse<T>(res, doFetch))
  return doFetch()
}

function del<T>(url: string): Promise<T> {
  const doFetch = () =>
    fetch(url, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    }).then((res) => handleResponse<T>(res, doFetch))
  return doFetch()
}

function get<T>(url: string): Promise<T> {
  const doFetch = () =>
    fetch(url, {
      headers: getAuthHeaders(),
    }).then((res) => handleResponse<T>(res, doFetch))
  return doFetch()
}

async function authRequest(
  endpoint: string,
  body: LoginCredentials | RegisterCredentials,
  fallbackError: string
): Promise<TokenResponse> {
  const response = await fetch(`${API_URL}/auth/${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    // Try to parse JSON error from backend
    try {
      const errorData = await response.json()
      throw new Error(errorData.message || fallbackError)
    } catch {
      throw new Error(fallbackError)
    }
  }
  const data: TokenResponse = await response.json()
  tokenStorage.setTokens(data.access_token, data.refresh_token)
  return data
}

export const api = {
  login: (credentials: LoginCredentials): Promise<TokenResponse> =>
    authRequest('login', credentials, 'Login failed'),

  register: (credentials: RegisterCredentials): Promise<TokenResponse> =>
    authRequest('register', credentials, 'Registration failed'),

  getMe: (): Promise<AuthUser> =>
    get(`${API_URL}/auth/me`),

  logout: (): void => {
    tokenStorage.clearTokens()
  },

  // Feed (authenticated - no userId needed)
  getFeed: (): Promise<UserFeed> =>
    get(`${API_URL}/feed`),

  getDigest: async (): Promise<FeedItem[]> => {
    const items = await get<DigestItem[]>(`${API_URL}/feed/digest`)
    return items.map((item): FeedItem => ({
      id: item.feed_item_id,
      feed_item_id: item.feed_item_id,
      title: item.title,
      summary: item.summary,
      description: item.description,
      source_name: item.source_name,
      article_url: item.article_url,
      comments_url: item.comments_url,
      points: item.points,
      views: item.views,
      rank_score: item.rank_score,
      state: { id: 0, ...item.state },
      created_at: item.created_at,
      updated_at: null,
    }))
  },

  markRead: (itemId: number): Promise<void> =>
    post(`${API_URL}/feed/mark-read/${itemId}`),

  toggleLike: (itemId: number): Promise<{ liked: boolean }> =>
    post(`${API_URL}/feed/items/${itemId}/like`),

  toggleDislike: (itemId: number): Promise<{ disliked: boolean }> =>
    post(`${API_URL}/feed/items/${itemId}/dislike`),

  toggleStar: (itemId: number): Promise<{ starred: boolean }> =>
    post(`${API_URL}/feed/items/${itemId}/star`),

  toggleHide: (itemId: number): Promise<{ hidden: boolean }> =>
    post(`${API_URL}/feed/items/${itemId}/hide`),

  hideRead: (): Promise<{ hidden_count: number }> =>
    post(`${API_URL}/feed/hide-read`),

  markAllRead: (): Promise<{ read_count: number }> =>
    post(`${API_URL}/feed/mark-all-read`),

  searchItems: (params: SearchParams): Promise<SearchResultItem[]> => {
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
    return get(`${API_URL}/feed/search?${searchParams.toString()}`)
  },

  // Subscriptions (authenticated)
  getSubscriptions: (): Promise<Subscription[]> =>
    get(`${API_URL}/subscriptions`),

  addSubscription: (resourceUrl: string): Promise<Subscription> =>
    postJson(`${API_URL}/subscriptions`, { resource_url: resourceUrl }),

  deleteSubscription: (subscriptionId: number): Promise<void> =>
    del(`${API_URL}/subscriptions/${subscriptionId}`),

  // Interests (authenticated via /users/me)
  getInterests: (): Promise<UserInterest[]> =>
    get(`${API_URL}/users/me/interests`),

  replaceInterests: (interests: UserInterestIn[]): Promise<UserInterest[]> =>
    putJson(`${API_URL}/users/me/interests`, { interests }),

  addInterest: (interest: UserInterestIn): Promise<UserInterest> =>
    postJson(`${API_URL}/users/me/interests`, interest),

  deleteInterest: (interestId: number): Promise<void> =>
    del(`${API_URL}/users/me/interests/${interestId}`),

  // Settings (authenticated via /users/me)
  getSettings: (): Promise<UserSettings> =>
    get(`${API_URL}/users/me/settings`),

  updateSettings: (settings: UserSettingsIn): Promise<UserSettings> =>
    putJson(`${API_URL}/users/me/settings`, settings),

  // Inbox (authenticated via /users/me)
  getInbox: (): Promise<InboxAddress> =>
    get(`${API_URL}/users/me/inbox`),

  regenerateInbox: (): Promise<InboxAddress> =>
    post(`${API_URL}/users/me/inbox/regenerate`),
}
