import { FeedCard } from './FeedCard'
import type { FeedItem } from '@/types/feed'

interface FeedListProps {
  items: FeedItem[]
  onToggleStar?: (item: FeedItem) => void
}

export function FeedList({ items, onToggleStar }: FeedListProps) {
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
        <FeedCard key={item.id} item={item} onToggleStar={onToggleStar} />
      ))}
    </div>
  )
}
