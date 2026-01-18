import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { FeedList } from '@/components/feed/FeedList'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { ArrowPathIcon, BookmarkIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import type { FeedItem } from '@/types/feed'
import { cn } from '@/lib/utils'

// TODO: Make this configurable or remove when multi-user
const DEFAULT_USER_ID = 1

type FeedTab = 'all' | 'saved'

function useFeedItemMutation(
  mutationFn: (item: FeedItem) => Promise<unknown>
): (item: FeedItem) => void {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed', DEFAULT_USER_ID] })
    },
  })
  return mutation.mutate
}

export default function FeedPage() {
  const [activeTab, setActiveTab] = useState<FeedTab>('all')
  const { items, isLoading, error, refetch } = useFeedQuery({
    userId: DEFAULT_USER_ID,
  })

  const handleToggleLike = useFeedItemMutation((item) =>
    api.toggleLike(DEFAULT_USER_ID, item.id)
  )
  const handleToggleDislike = useFeedItemMutation((item) =>
    api.toggleDislike(DEFAULT_USER_ID, item.id)
  )
  const handleToggleStar = useFeedItemMutation((item) =>
    api.toggleStar(DEFAULT_USER_ID, item.id)
  )

  const filteredItems = useMemo(() => {
    if (activeTab === 'saved') {
      return items.filter((item) => item.state.star)
    }
    return items
  }, [items, activeTab])

  const savedCount = useMemo(() => items.filter((item) => item.state.star).length, [items])

  if (isLoading && items.length === 0) {
    return <PageLoader />
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-medium text-destructive">Error loading feed</p>
        <p className="mt-1 text-sm text-muted-foreground">{error}</p>
        <Button onClick={() => refetch()} className="mt-4" variant="secondary">
          Try again
        </Button>
      </div>
    )
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Your Feed</h2>
          <p className="text-sm text-muted-foreground">
            {filteredItems.length} items
          </p>
        </div>
        <Button
          onClick={() => refetch()}
          variant="ghost"
          size="sm"
          className="gap-2"
        >
          <ArrowPathIcon className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b border-border">
        <button
          onClick={() => setActiveTab('all')}
          className={cn(
            'px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'all'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          All
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={cn(
            'flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-colors',
            activeTab === 'saved'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          )}
        >
          <BookmarkIcon className="h-4 w-4" />
          Saved
          {savedCount > 0 && (
            <span className="rounded-full bg-secondary px-1.5 py-0.5 text-xs">
              {savedCount}
            </span>
          )}
        </button>
      </div>

      {/* Feed list */}
      <FeedList
        items={filteredItems}
        onToggleStar={handleToggleStar}
        onToggleLike={handleToggleLike}
        onToggleDislike={handleToggleDislike}
      />
    </div>
  )
}
