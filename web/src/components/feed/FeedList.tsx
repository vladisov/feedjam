import { useEffect, useRef } from 'react'
import { FeedCard } from './FeedCard'
import type { FeedItemActions } from '@/types/actions'
import type { FeedItem } from '@/types/feed'

interface FeedListProps extends FeedItemActions {
  items: FeedItem[]
  showSummaries?: boolean
  selectedIndex?: number
  isKeyboardMode?: boolean
}

export function FeedList({
  items,
  showSummaries = true,
  selectedIndex = -1,
  isKeyboardMode = false,
  onToggleStar,
  onToggleLike,
  onMarkRead,
  onToggleHide,
}: FeedListProps): React.ReactElement {
  const selectedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isKeyboardMode && selectedIndex >= 0 && selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }, [isKeyboardMode, selectedIndex])

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="rounded-full bg-secondary p-4 mb-4">
          <svg className="h-8 w-8 text-muted-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
          </svg>
        </div>
        <p className="text-lg font-semibold text-foreground">No items yet</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Add some subscriptions to get started
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <FeedCard
          key={item.id}
          ref={index === selectedIndex ? selectedRef : null}
          item={item}
          showSummary={showSummaries}
          isSelected={isKeyboardMode && index === selectedIndex}
          onToggleStar={onToggleStar}
          onToggleLike={onToggleLike}
          onMarkRead={onMarkRead}
          onToggleHide={onToggleHide}
        />
      ))}
    </div>
  )
}
