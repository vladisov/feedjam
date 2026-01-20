import { useState, useMemo, useEffect, useRef, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { FeedList } from '@/components/feed/FeedList'
import { SearchBar } from '@/components/feed/SearchBar'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { KeyboardShortcutsHelp } from '@/components/shared/KeyboardShortcutsHelp'
import { ArrowPathIcon, Bars3BottomLeftIcon, EyeSlashIcon, CheckIcon, SparklesIcon, QuestionMarkCircleIcon, ChevronUpDownIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { applySearch, parseSearchQuery, requiresServerSearch, toSearchParams } from '@/lib/search'
import type { FeedItem, SearchResultItem } from '@/types/feed'

type FeedTab = 'all' | 'digest'
type SortOption = 'newest' | 'oldest' | 'score' | 'points' | 'source'

const PAGE_SIZE = 20

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'score', label: 'Top Score' },
  { value: 'points', label: 'Most Points' },
  { value: 'source', label: 'Source A-Z' },
]

function getStoredValue<T extends string>(key: string, defaultValue: T): T {
  if (typeof window === 'undefined') return defaultValue
  return (localStorage.getItem(key) as T) ?? defaultValue
}

function getDateValue(item: FeedItem): number {
  return item.created_at ? new Date(item.created_at).getTime() : 0
}

function sortItems(items: FeedItem[], sortBy: SortOption): FeedItem[] {
  const sorted = [...items]
  switch (sortBy) {
    case 'newest':
      return sorted.sort((a, b) => getDateValue(b) - getDateValue(a))
    case 'oldest':
      return sorted.sort((a, b) => getDateValue(a) - getDateValue(b))
    case 'score':
      return sorted.sort((a, b) => (b.rank_score ?? 0) - (a.rank_score ?? 0))
    case 'points':
      return sorted.sort((a, b) => (b.points ?? 0) - (a.points ?? 0))
    case 'source':
      return sorted.sort((a, b) => a.source_name.localeCompare(b.source_name))
    default:
      return sorted
  }
}

interface TabButtonProps {
  isActive: boolean
  onClick: () => void
  children: React.ReactNode
}

function TabButton({ isActive, onClick, children }: TabButtonProps): React.ReactElement {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex items-center gap-1.5 px-4 py-2 text-sm font-medium transition-colors',
        isActive
          ? 'border-b-2 border-primary text-foreground'
          : 'text-muted-foreground hover:text-foreground'
      )}
    >
      {children}
    </button>
  )
}

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

function getStoredBoolean(key: string, defaultValue: boolean): boolean {
  if (typeof window === 'undefined') return defaultValue
  const stored = localStorage.getItem(key)
  if (stored === null) return defaultValue
  return stored !== 'false'
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
  const [showSummaries, setShowSummaries] = useState(() => getStoredBoolean('feedShowSummaries', true))
  const [sortOption, setSortOption] = useState<SortOption>(() => getStoredValue('feedSortOption', 'newest'))
  const [activeTab, setActiveTab] = useState<FeedTab>('all')
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  const { items, isLoading, error, refetch } = useFeedQuery()
  const loadMoreRef = useRef<HTMLDivElement>(null)

  const queryClient = useQueryClient()

  // Digest query
  const digestQuery = useQuery({
    queryKey: ['digest'],
    queryFn: () => api.getDigest(),
    enabled: activeTab === 'digest',
  })

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

  // Get filtered items based on active tab (needed for keyboard shortcuts)
  const filteredItems = useMemo(() => {
    let result: FeedItem[]
    if (activeTab === 'digest') {
      result = digestQuery.data ?? []
    } else if (needsServerSearch) {
      result = (serverSearch.data ?? []).map(toFeedItem)
    } else {
      result = applySearch(items, searchQuery)
    }
    // Apply sorting (skip for digest as it's already ranked)
    return activeTab === 'digest' ? result : sortItems(result, sortOption)
  }, [activeTab, digestQuery.data, needsServerSearch, serverSearch.data, items, searchQuery, sortOption])

  function handleSortChange(newSort: SortOption): void {
    setSortOption(newSort)
    localStorage.setItem('feedSortOption', newSort)
    setVisibleCount(PAGE_SIZE) // Reset pagination on sort change
  }

  // Paginated items for display
  const visibleItems = useMemo(() => {
    return filteredItems.slice(0, visibleCount)
  }, [filteredItems, visibleCount])

  const hasMore = visibleCount < filteredItems.length

  // Load more when scrolling to bottom
  const loadMore = useCallback(() => {
    if (hasMore) {
      setVisibleCount((prev) => Math.min(prev + PAGE_SIZE, filteredItems.length))
    }
  }, [hasMore, filteredItems.length])

  // Intersection observer for infinite scroll
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && hasMore) {
          loadMore()
        }
      },
      { threshold: 0.1 }
    )

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current)
    }

    return () => observer.disconnect()
  }, [hasMore, loadMore])

  // Reset pagination when filters change
  useEffect(() => {
    setVisibleCount(PAGE_SIZE)
  }, [searchQuery, activeTab])

  // Keyboard shortcuts (use visible items for navigation)
  const { selectedIndex, showHelp, setShowHelp } = useKeyboardShortcuts({
    items: visibleItems,
    onToggleStar: handleToggleStar,
    onToggleLike: handleToggleLike,
    onToggleDislike: handleToggleDislike,
    onMarkRead: handleMarkRead,
    onToggleHide: handleToggleHide,
    onRefresh: () => refetch(),
    enabled: true,
  })

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
  const isLoadingDigest = activeTab === 'digest' && digestQuery.isLoading

  if ((isLoading && items.length === 0) || isSearching || isLoadingDigest) {
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
          <h2 className="text-2xl font-bold text-foreground">
            {activeTab === 'digest' ? "Today's Digest" : 'Your Feed'}
          </h2>
          <p className="text-sm text-muted-foreground">
            {activeTab === 'digest'
              ? 'Top 5 items from the last 24 hours'
              : hasMore
                ? `Showing ${visibleItems.length} of ${filteredItems.length} items`
                : `${filteredItems.length} items`}
          </p>
        </div>
        <div className="flex items-center gap-1">
          {activeTab === 'all' && unreadCount > 0 && (
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
          {activeTab === 'all' && readCount > 0 && (
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

      {/* Tabs */}
      <div className="mb-4 flex gap-1 border-b border-border">
        <TabButton isActive={activeTab === 'all'} onClick={() => setActiveTab('all')}>
          All
        </TabButton>
        <TabButton isActive={activeTab === 'digest'} onClick={() => setActiveTab('digest')}>
          <SparklesIcon className="h-4 w-4" />
          Digest
        </TabButton>
      </div>

      {/* Search and Sort (only show for All tab) */}
      {activeTab === 'all' && (
        <div className="mb-4 flex gap-2">
          <div className="flex-1">
            <SearchBar value={searchQuery} onChange={setSearchQuery} />
          </div>
          <div className="relative">
            <select
              value={sortOption}
              onChange={(e) => handleSortChange(e.target.value as SortOption)}
              className="h-10 appearance-none rounded-lg border border-border bg-card pl-3 pr-8 text-sm text-foreground transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronUpDownIcon className="pointer-events-none absolute right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>
        </div>
      )}

      {/* Feed list */}
      <FeedList
        items={visibleItems}
        showSummaries={showSummaries}
        selectedIndex={selectedIndex}
        onToggleStar={handleToggleStar}
        onToggleLike={handleToggleLike}
        onToggleDislike={handleToggleDislike}
        onMarkRead={handleMarkRead}
        onToggleHide={handleToggleHide}
      />

      {/* Infinite scroll trigger */}
      {hasMore && (
        <div ref={loadMoreRef} className="flex justify-center py-8">
          <span className="text-sm text-muted-foreground">Loading more...</span>
        </div>
      )}

      {/* Keyboard shortcuts help */}
      <KeyboardShortcutsHelp isOpen={showHelp} onClose={() => setShowHelp(false)} />

      {/* Keyboard shortcut hint */}
      <button
        onClick={() => setShowHelp(true)}
        className="fixed bottom-4 right-4 flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-muted-foreground shadow-md transition-colors hover:bg-secondary/80 hover:text-foreground"
        title="Keyboard shortcuts (?)"
      >
        <QuestionMarkCircleIcon className="h-5 w-5" />
      </button>
    </div>
  )
}
