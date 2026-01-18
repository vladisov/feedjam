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
  state: FeedItemState
  created_at: string
  updated_at: string
}

export interface FeedItemState {
  id: number
  read: boolean
  star: boolean
  like: boolean
  dislike: boolean
  hide: boolean
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
}

