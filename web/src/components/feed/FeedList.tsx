import { useEffect, useRef, useState } from 'react'
import { FeedCard } from './FeedCard'
import { SwipeableCard } from './SwipeableCard'
import type { FeedItemActions } from '@/types/actions'
import type { FeedItem } from '@/types/feed'

function useIsTouchDevice(): boolean {
  const [isTouch, setIsTouch] = useState(false)

  useEffect(() => {
    setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0)
  }, [])

  return isTouch
}

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
  const isTouchDevice = useIsTouchDevice()

  // Scroll selected item into view
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

  function renderItem(item: FeedItem, index: number): React.ReactElement {
    const isSelected = index === selectedIndex
    const card = (
      <FeedCard
        ref={isSelected ? selectedRef : null}
        item={item}
        showSummary={showSummaries}
        isSelected={isSelected}
        onToggleStar={onToggleStar}
        onToggleLike={onToggleLike}
        onToggleDislike={onToggleDislike}
        onMarkRead={onMarkRead}
        onToggleHide={onToggleHide}
      />
    )

    if (isTouchDevice) {
      return (
        <SwipeableCard
          key={item.id}
          onSwipeLeft={() => onToggleHide?.(item)}
          onSwipeRight={() => onToggleStar?.(item)}
        >
          {card}
        </SwipeableCard>
      )
    }

    return <div key={item.id}>{card}</div>
  }

  return (
    <div className="space-y-3">
      {items.map(renderItem)}
    </div>
  )
}
