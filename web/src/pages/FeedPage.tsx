import { useState, useMemo } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { FeedList } from '@/components/feed/FeedList'
import { SearchBar } from '@/components/feed/SearchBar'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { ArrowPathIcon, Bars3BottomLeftIcon, EyeSlashIcon, CheckIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { applySearch } from '@/lib/search'
import type { FeedItem } from '@/types/feed'

// TODO: Make this configurable or remove when multi-user
const DEFAULT_USER_ID = 1

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

export default function FeedPage(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('')
  const [showSummaries, setShowSummaries] = useState(getInitialShowSummaries)
  const { items, isLoading, error, refetch } = useFeedQuery({
    userId: DEFAULT_USER_ID,
  })

  const queryClient = useQueryClient()

  const handleToggleLike = useFeedItemMutation((item) =>
    api.toggleLike(DEFAULT_USER_ID, item.id)
  )
  const handleToggleDislike = useFeedItemMutation((item) =>
    api.toggleDislike(DEFAULT_USER_ID, item.id)
  )
  const handleToggleStar = useFeedItemMutation((item) =>
    api.toggleStar(DEFAULT_USER_ID, item.id)
  )
  const handleMarkRead = useFeedItemMutation((item) =>
    api.markRead(DEFAULT_USER_ID, item.id)
  )
  const handleToggleHide = useFeedItemMutation((item) =>
    api.toggleHide(DEFAULT_USER_ID, item.id)
  )

  const hideReadMutation = useMutation({
    mutationFn: () => api.hideRead(DEFAULT_USER_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed', DEFAULT_USER_ID] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => api.markAllRead(DEFAULT_USER_ID),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed', DEFAULT_USER_ID] })
    },
  })

  // Apply search/filter to items
  const filteredItems = useMemo(() => applySearch(items, searchQuery), [items, searchQuery])

  // Counts for action buttons (based on visible non-hidden items)
  const visibleItems = useMemo(() => items.filter((item) => !item.state.hide), [items])
  const readCount = useMemo(() => visibleItems.filter((item) => item.state.read).length, [visibleItems])
  const unreadCount = useMemo(() => visibleItems.filter((item) => !item.state.read).length, [visibleItems])

  function toggleShowSummaries(): void {
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
          {unreadCount > 0 && (
            <Button
              onClick={() => markAllReadMutation.mutate()}
              variant="ghost"
              size="sm"
              className="gap-2"
              disabled={markAllReadMutation.isPending}
              title="Mark all items as read"
            >
              <CheckIcon className="h-4 w-4" />
              Mark all read
            </Button>
          )}
          {readCount > 0 && (
            <Button
              onClick={() => hideReadMutation.mutate()}
              variant="ghost"
              size="sm"
              className="gap-2"
              disabled={hideReadMutation.isPending}
              title="Hide all read items"
            >
              <EyeSlashIcon className="h-4 w-4" />
              Hide read ({readCount})
            </Button>
          )}
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

      {/* Search */}
      <div className="mb-4">
        <SearchBar value={searchQuery} onChange={setSearchQuery} />
      </div>

      {/* Feed list */}
      <FeedList
        items={filteredItems}
        showSummaries={showSummaries}
        onToggleStar={handleToggleStar}
        onToggleLike={handleToggleLike}
        onToggleDislike={handleToggleDislike}
        onMarkRead={handleMarkRead}
        onToggleHide={handleToggleHide}
      />
    </div>
  )
}
