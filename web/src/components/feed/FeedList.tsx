import { useEffect, useRef } from 'react'
import { FeedCard } from './FeedCard'
import type { FeedItemActions } from '@/types/actions'
import type { FeedItem } from '@/types/feed'

interface FeedListProps extends FeedItemActions {
  items: FeedItem[]
  showSummaries?: boolean
  selectedIndex?: number
}

export function FeedList({
  items,
  showSummaries = true,
  selectedIndex = -1,
  onToggleStar,
  onToggleLike,
  onToggleDislike,
  onMarkRead,
  onToggleHide,
}: FeedListProps): React.ReactElement {
  const selectedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (selectedIndex >= 0 && selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [selectedIndex])

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
      {items.map((item, index) => (
        <FeedCard
          key={item.id}
          ref={index === selectedIndex ? selectedRef : null}
          item={item}
          showSummary={showSummaries}
          isSelected={index === selectedIndex}
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
