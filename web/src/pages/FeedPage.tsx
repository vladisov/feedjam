import { useState, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { FeedList } from '@/components/feed/FeedList'
import { SearchBar } from '@/components/feed/SearchBar'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { ArrowPathIcon, Bars3BottomLeftIcon, EyeSlashIcon, CheckIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { applySearch, parseSearchQuery, requiresServerSearch, toSearchParams } from '@/lib/search'
import type { FeedItem, SearchResultItem } from '@/types/feed'

function useFeedItemMutation(
  mutationFn: (item: FeedItem) => Promise<unknown>
): (item: FeedItem) => void {
  const queryClient = useQueryClient()
  const mutation = useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
  })
  return mutation.mutate
}

function getInitialShowSummaries(): boolean {
  if (typeof window === 'undefined') return true
  return localStorage.getItem('feedShowSummaries') !== 'false'
}

function toFeedItem(item: SearchResultItem): FeedItem {
  return {
    id: item.id,
    feed_item_id: item.feed_item_id,
    title: item.title,
    summary: item.summary,
    description: item.description,
    source_name: item.source_name,
    article_url: item.article_url,
    comments_url: item.comments_url,
    points: item.points,
    views: item.views,
    rank_score: 0,
    state: { id: 0, ...item.state },
    created_at: item.created_at,
    updated_at: item.updated_at,
  }
}

export default function FeedPage(): React.ReactElement {
  const [searchQuery, setSearchQuery] = useState('')
  const [showSummaries, setShowSummaries] = useState(getInitialShowSummaries)
  const { items, isLoading, error, refetch } = useFeedQuery()

  const queryClient = useQueryClient()

  // Parse search query to check if server search is needed
  const parsedSearch = useMemo(() => parseSearchQuery(searchQuery), [searchQuery])
  const needsServerSearch = useMemo(() => requiresServerSearch(parsedSearch), [parsedSearch])
  const searchParams = useMemo(() => toSearchParams(parsedSearch), [parsedSearch])

  // Server-side search (only enabled when state filters are used)
  const serverSearch = useQuery({
    queryKey: ['search', searchParams],
    queryFn: () => api.searchItems(searchParams),
    enabled: needsServerSearch,
  })

  const handleToggleLike = useFeedItemMutation((item) =>
    api.toggleLike(item.id)
  )
  const handleToggleDislike = useFeedItemMutation((item) =>
    api.toggleDislike(item.id)
  )
  const handleToggleStar = useFeedItemMutation((item) =>
    api.toggleStar(item.id)
  )
  const handleMarkRead = useFeedItemMutation((item) =>
    api.markRead(item.id)
  )
  const handleToggleHide = useFeedItemMutation((item) =>
    api.toggleHide(item.id)
  )

  const hideReadMutation = useMutation({
    mutationFn: () => api.hideRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
  })

  const markAllReadMutation = useMutation({
    mutationFn: () => api.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed'] })
    },
  })

  // Get filtered items: server search results or client-side filtered
  const filteredItems = useMemo(() => {
    if (needsServerSearch) {
      return (serverSearch.data ?? []).map(toFeedItem)
    }
    return applySearch(items, searchQuery)
  }, [needsServerSearch, serverSearch.data, items, searchQuery])

  // Counts for action buttons (based on visible non-hidden items)
  const { readCount, unreadCount } = useMemo(() => {
    const visible = items.filter((item) => !item.state.hide)
    return {
      readCount: visible.filter((item) => item.state.read).length,
      unreadCount: visible.filter((item) => !item.state.read).length,
    }
  }, [items])

  function toggleShowSummaries(): void {
    const newValue = !showSummaries
    setShowSummaries(newValue)
    localStorage.setItem('feedShowSummaries', String(newValue))
  }

  const isSearching = needsServerSearch && serverSearch.isLoading

  if ((isLoading && items.length === 0) || isSearching) {
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
