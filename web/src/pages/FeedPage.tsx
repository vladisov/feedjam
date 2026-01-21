import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { FeedList } from '@/components/feed/FeedList'
import { SearchBar } from '@/components/feed/SearchBar'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { KeyboardShortcutsHelp } from '@/components/shared/KeyboardShortcutsHelp'
import { ArrowPathIcon, Bars3BottomLeftIcon, EyeSlashIcon, CheckIcon, SparklesIcon, QuestionMarkCircleIcon, ChevronUpDownIcon, EllipsisVerticalIcon } from '@heroicons/react/24/outline'
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

function getStored<T>(key: string, defaultValue: T, parse?: (v: string) => T): T {
  if (typeof window === 'undefined') return defaultValue
  const stored = localStorage.getItem(key)
  if (stored === null) return defaultValue
  return parse ? parse(stored) : (stored as unknown as T)
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

function useInvalidateAll() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['feed'] })
    queryClient.invalidateQueries({ queryKey: ['search'] })
    queryClient.invalidateQueries({ queryKey: ['digest'] })
  }
}

function useFeedItemMutation(
  mutationFn: (item: FeedItem) => Promise<unknown>
): (item: FeedItem) => void {
  const invalidateAll = useInvalidateAll()
  const mutation = useMutation({
    mutationFn,
    onSuccess: invalidateAll,
  })
  return mutation.mutate
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
  const [showSummaries, setShowSummaries] = useState(() => getStored('feedShowSummaries', true, (v) => v !== 'false'))
  const [sortOption, setSortOption] = useState<SortOption>(() => getStored('feedSortOption', 'newest' as SortOption))
  const [activeTab, setActiveTab] = useState<FeedTab>('all')
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  const [menuOpen, setMenuOpen] = useState(false)
  const { items, isLoading, error, refetch } = useFeedQuery()
  const loadMoreRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
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
    api.toggleLike(item.feed_item_id)
  )
  const handleToggleDislike = useFeedItemMutation((item) =>
    api.toggleDislike(item.feed_item_id)
  )
  const handleToggleStar = useFeedItemMutation((item) =>
    api.toggleStar(item.feed_item_id)
  )
  const handleMarkRead = useFeedItemMutation((item) =>
    api.markRead(item.feed_item_id)
  )
  const handleToggleHide = useFeedItemMutation((item) =>
    api.toggleHide(item.feed_item_id)
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

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    if (menuOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [menuOpen])

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
  const { totalCount, readCount, unreadCount } = useMemo(() => {
    const visible = items.filter((item) => !item.state.hide)
    const read = visible.filter((item) => item.state.read).length
    return {
      totalCount: visible.length,
      readCount: read,
      unreadCount: visible.length - read,
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
      {/* Tabs + Actions */}
      <div className="mb-4 flex items-center justify-between border-b border-border">
        <div className="flex">
          <TabButton isActive={activeTab === 'all'} onClick={() => setActiveTab('all')}>
            All
            <span className="ml-1.5 text-xs text-muted-foreground">{totalCount}</span>
          </TabButton>
          <TabButton isActive={activeTab === 'digest'} onClick={() => setActiveTab('digest')}>
            <SparklesIcon className="h-4 w-4" />
            Digest
          </TabButton>
        </div>
        <div className="flex items-center gap-1">
          <Button
            onClick={toggleShowSummaries}
            variant="ghost"
            size="sm"
            className={cn('gap-1.5', !showSummaries && 'text-muted-foreground')}
            title={showSummaries ? 'Hide summaries' : 'Show summaries'}
          >
            <Bars3BottomLeftIcon className="h-4 w-4" />
          </Button>
          <Button
            onClick={() => refetch()}
            variant="ghost"
            size="sm"
            title="Refresh"
          >
            <ArrowPathIcon className="h-4 w-4" />
          </Button>
          {activeTab === 'all' && (unreadCount > 0 || readCount > 0) && (
            <div ref={menuRef} className="relative">
              <Button
                onClick={() => setMenuOpen(!menuOpen)}
                variant="ghost"
                size="sm"
                title="More actions"
              >
                <EllipsisVerticalIcon className="h-4 w-4" />
              </Button>
              {menuOpen && (
                <div className="absolute right-0 top-full z-10 mt-1 w-48 rounded-lg border border-border bg-card py-1 shadow-lg">
                  {unreadCount > 0 && (
                    <button
                      onClick={() => {
                        markAllReadMutation.mutate()
                        setMenuOpen(false)
                      }}
                      disabled={markAllReadMutation.isPending}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent disabled:opacity-50"
                    >
                      <CheckIcon className="h-4 w-4" />
                      Mark all as read ({unreadCount})
                    </button>
                  )}
                  {readCount > 0 && (
                    <button
                      onClick={() => {
                        hideReadMutation.mutate()
                        setMenuOpen(false)
                      }}
                      disabled={hideReadMutation.isPending}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-accent disabled:opacity-50"
                    >
                      <EyeSlashIcon className="h-4 w-4" />
                      Hide read items ({readCount})
                    </button>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Search and Sort (only show for All tab) */}
      {activeTab === 'all' && (
        <div className="mb-4 flex gap-2">
          <div className="min-w-0 flex-1">
            <SearchBar value={searchQuery} onChange={setSearchQuery} />
          </div>
          <div className="relative flex-shrink-0">
            <select
              value={sortOption}
              onChange={(e) => handleSortChange(e.target.value as SortOption)}
              className="h-10 appearance-none rounded-lg border border-border bg-card pl-2 pr-7 sm:pl-3 sm:pr-8 text-sm text-foreground transition-colors hover:bg-accent focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <ChevronUpDownIcon className="pointer-events-none absolute right-1.5 sm:right-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
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
