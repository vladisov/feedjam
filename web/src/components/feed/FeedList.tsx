import { FeedCard } from './FeedCard'
import type { FeedItem } from '@/types/feed'

interface FeedListProps {
  items: FeedItem[]
  showSummaries?: boolean
  onToggleStar?: (item: FeedItem) => void
  onToggleLike?: (item: FeedItem) => void
  onToggleDislike?: (item: FeedItem) => void
  onMarkRead?: (item: FeedItem) => void
  onToggleHide?: (item: FeedItem) => void
}

export function FeedList({
  items,
  showSummaries = true,
  onToggleStar,
  onToggleLike,
  onToggleDislike,
  onMarkRead,
  onToggleHide,
}: FeedListProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-medium text-foreground">No items in your feed</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Add some subscriptions to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <FeedCard
          key={item.id}
          item={item}
          showSummary={showSummaries}
          onToggleStar={onToggleStar}
          onToggleLike={onToggleLike}
          onToggleDislike={onToggleDislike}
          onMarkRead={onMarkRead}
          onToggleHide={onToggleHide}
        />
      ))}
    </div>
  )
}
