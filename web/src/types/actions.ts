import type { FeedItem } from './feed'

/**
 * Callback type for feed item actions.
 */
export type FeedItemAction = (item: FeedItem) => void

/**
 * Shared interface for components that handle feed item actions.
 * Used by FeedCard, FeedList, useKeyboardShortcuts, and FeedPage.
 */
export interface FeedItemActions {
  onToggleStar?: FeedItemAction
  onToggleLike?: FeedItemAction
  onMarkRead?: FeedItemAction
  onToggleHide?: FeedItemAction
}
