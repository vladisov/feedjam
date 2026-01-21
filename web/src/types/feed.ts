export interface FeedItem {
  id: number
  feed_item_id: number
  title: string
  summary: string | null
  description: string | null
  source_name: string
  article_url: string | null
  comments_url: string | null
  points: number | null
  views: number | null
  rank_score: number
  state: FeedItemState
  created_at: string | null
  updated_at: string | null
}

/** Base state flags shared across feed items */
export interface ItemStateFlags {
  read: boolean
  star: boolean
  like: boolean
  dislike: boolean
  hide: boolean
}

export interface FeedItemState extends ItemStateFlags {
  id: number
}

export interface UserFeed {
  id: number
  user_id: number
  is_active: boolean
  user_feed_items: FeedItem[]
  created_at: string
  updated_at: string
}

export interface Subscription {
  id: number
  user_id: number
  source_id: number
  source_name: string
  resource_url: string
  is_active: boolean
  created_at: string
  last_run: string | null
  last_error: string | null
  item_count: number
}

export interface FeedPreviewItem {
  title: string
  link: string
  published: string | null
  description: string | null
}

export interface FeedPreview {
  source_type: string
  source_name: string
  item_count: number
  items: FeedPreviewItem[]
  error: string | null
}

export interface UserInterest {
  id: number
  user_id: number
  topic: string
  weight: number
  created_at: string
  updated_at: string
}

export interface UserInterestIn {
  topic: string
  weight: number
}

export interface UserSettings {
  has_openai_key: boolean
}

export interface UserSettingsIn {
  openai_api_key?: string | null
}

export interface InboxAddress {
  inbox_address: string
  email_token: string
}

/** Search results use the base state flags (no id) */
export type SearchResultState = ItemStateFlags

export interface SearchResultItem {
  id: number
  feed_item_id: number
  title: string
  link: string
  source_name: string
  description: string | null
  article_url: string | null
  comments_url: string | null
  points: number | null
  views: number | null
  summary: string | null
  published: string | null
  created_at: string
  updated_at: string
  state: SearchResultState
}

/** API response shape for digest items */
export interface DigestItem {
  feed_item_id: number
  user_id: number
  title: string
  source_name: string
  state: ItemStateFlags
  description: string
  article_url: string | null
  comments_url: string | null
  points: number | null
  views: number | null
  summary: string | null
  rank_score: number
  created_at: string | null
}

export interface SearchParams {
  liked?: boolean
  disliked?: boolean
  starred?: boolean
  read?: boolean
  hidden?: boolean
  text?: string
  source?: string
  limit?: number
  offset?: number
}

// Auth types
export interface AuthUser {
  id: number
  email: string
  handle: string
  is_active: boolean
  is_verified: boolean
  created_at: string
  onboarding_completed: boolean
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterCredentials {
  email: string
  password: string
}

