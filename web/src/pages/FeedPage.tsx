import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { FeedList } from '@/components/feed/FeedList'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { ArrowPathIcon, BookmarkIcon, Bars3BottomLeftIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import type { FeedItem } from '@/types/feed'

// TODO: Make this configurable or remove when multi-user
const DEFAULT_USER_ID = 1

type FeedTab = 'all' | 'saved'

const TAB_BASE_STYLES = 'px-4 py-2 text-sm font-medium transition-colors'
const TAB_ACTIVE_STYLES = 'border-b-2 border-primary text-primary'
const TAB_INACTIVE_STYLES = 'text-muted-foreground hover:text-foreground'

function getTabStyles(isActive: boolean): string {
  return cn(TAB_BASE_STYLES, isActive ? TAB_ACTIVE_STYLES : TAB_INACTIVE_STYLES)
}

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

function getInitialShowSummaries(): boolean {
  if (typeof window === 'undefined') return true
  return localStorage.getItem('feedShowSummaries') !== 'false'
}

export default function FeedPage() {
  const [activeTab, setActiveTab] = useState<FeedTab>('all')
  const [showSummaries, setShowSummaries] = useState(getInitialShowSummaries)
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

  const filteredItems = useMemo(
    () => (activeTab === 'saved' ? items.filter((item) => item.state.star) : items),
    [items, activeTab]
  )

  const savedCount = useMemo(() => items.filter((item) => item.state.star).length, [items])

  const toggleShowSummaries = () => {
    const newValue = !showSummaries
    setShowSummaries(newValue)
    localStorage.setItem('feedShowSummaries', String(newValue))
  }

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
        <div className="flex items-center gap-1">
          <Button
            onClick={toggleShowSummaries}
            variant="ghost"
            size="sm"
            className={cn('gap-2', !showSummaries && 'text-muted-foreground')}
            title={showSummaries ? 'Hide summaries' : 'Show summaries'}
          >
            <Bars3BottomLeftIcon className="h-4 w-4" />
          </Button>
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
      </div>

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b border-border">
        <button onClick={() => setActiveTab('all')} className={getTabStyles(activeTab === 'all')}>
          All
        </button>
        <button
          onClick={() => setActiveTab('saved')}
          className={cn(getTabStyles(activeTab === 'saved'), 'flex items-center gap-1.5')}
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
        showSummaries={showSummaries}
        onToggleStar={handleToggleStar}
        onToggleLike={handleToggleLike}
        onToggleDislike={handleToggleDislike}
      />
    </div>
  )
}
