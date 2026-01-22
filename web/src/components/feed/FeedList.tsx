import { useEffect, useRef } from 'react'
import { useWindowVirtualizer } from '@tanstack/react-virtual'
import { NewspaperIcon } from '@heroicons/react/24/outline'
import { FeedCard } from './FeedCard'
import { EmptyState } from '@/components/shared/EmptyState'
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
  const listRef = useRef<HTMLDivElement>(null)

  const virtualizer = useWindowVirtualizer({
    count: items.length,
    estimateSize: () => (showSummaries ? 180 : 100),
    overscan: 5,
    scrollMargin: listRef.current?.offsetTop ?? 0,
  })

  const virtualItems = virtualizer.getVirtualItems()

  // Scroll to selected item when using keyboard navigation
  useEffect(() => {
    if (isKeyboardMode && selectedIndex >= 0) {
      virtualizer.scrollToIndex(selectedIndex, { align: 'center', behavior: 'smooth' })
    }
  }, [isKeyboardMode, selectedIndex, virtualizer])

  if (items.length === 0) {
    return (
      <EmptyState
        icon={<NewspaperIcon />}
        title="No items yet"
        description="Add some subscriptions to get started"
        className="py-20"
      />
    )
  }

  return (
    <div ref={listRef}>
      <div
        className="relative w-full"
        style={{ height: virtualizer.getTotalSize() }}
      >
        {virtualItems.map((virtualItem) => {
          const item = items[virtualItem.index]
          if (!item) return null
          return (
            <div
              key={item.id}
              data-index={virtualItem.index}
              ref={virtualizer.measureElement}
              className="absolute left-0 top-0 w-full pb-4"
              style={{ transform: `translateY(${virtualItem.start - virtualizer.options.scrollMargin}px)` }}
            >
              <FeedCard
                item={item}
                showSummary={showSummaries}
                isSelected={isKeyboardMode && virtualItem.index === selectedIndex}
                onToggleStar={onToggleStar}
                onToggleLike={onToggleLike}
                onMarkRead={onMarkRead}
                onToggleHide={onToggleHide}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
