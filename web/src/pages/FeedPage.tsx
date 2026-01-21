import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { useKeyboardShortcuts } from '@/hooks/useKeyboardShortcuts'
import { FeedList } from '@/components/feed/FeedList'
import { SearchBar } from '@/components/feed/SearchBar'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { KeyboardShortcutsHelp } from '@/components/shared/KeyboardShortcutsHelp'
import { ArrowPathIcon, Bars3BottomLeftIcon, SparklesIcon, QuestionMarkCircleIcon, ChevronUpDownIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { applySearch, parseSearchQuery, requiresServerSearch, toSearchParams } from '@/lib/search'
import type { FeedItem, SearchResultItem } from '@/types/feed'

type FeedTab = 'feed' | 'digest'
type SortOption = 'newest' | 'oldest' | 'score' | 'points' | 'source'

const PAGE_SIZE = 20

const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' },
  { value: 'score', label: 'Top Score' },
  { value: 'points', label: 'Most Points' },
  { value: 'source', label: 'Source A-Z' },
]

function getStoredString(key: string, defaultValue: string): string {
  if (typeof window === 'undefined') return defaultValue
  return localStorage.getItem(key) ?? defaultValue
}

function getStoredBoolean(key: string, defaultValue: boolean): boolean {
  if (typeof window === 'undefined') return defaultValue
  const stored = localStorage.getItem(key)
  if (stored === null) return defaultValue
  return stored !== 'false'
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
  const [sortOption, setSortOption] = useState<SortOption>(() => getStoredString('feedSortOption', 'newest') as SortOption)
  const [activeTab, setActiveTab] = useState<FeedTab>('feed')
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE)
  const [localUpdates, setLocalUpdates] = useState<Record<number, Partial<FeedItem['state']>>>({})
  const { items: rawItems, isLoading, error, refetch } = useFeedQuery()
  const loadMoreRef = useRef<HTMLDivElement>(null)
  const prevRawItemsRef = useRef(rawItems)

  // Clear local updates when feed data changes (on refetch)
  useEffect(() => {
    if (rawItems !== prevRawItemsRef.current && rawItems.length > 0) {
      setLocalUpdates({})
      prevRawItemsRef.current = rawItems
    }
  }, [rawItems])

  // Apply local state updates to items, filtering out server-hidden items without local updates
  const items = useMemo(() => {
    return rawItems
      .filter((item) => !item.state.hide || localUpdates[item.id])
      .map((item) => {
        const updates = localUpdates[item.id]
        return updates ? { ...item, state: { ...item.state, ...updates } } : item
      })
  }, [rawItems, localUpdates])

  // Digest query - load upfront for instant tab switching
  const digestQuery = useQuery({
    queryKey: ['digest'],
    queryFn: () => api.getDigest(),
  })

  // Parse search query to check if server search is needed
  const parsedSearch = useMemo(() => parseSearchQuery(searchQuery), [searchQuery])
  const needsServerSearch = useMemo(() => requiresServerSearch(parsedSearch), [parsedSearch])
  const searchParams = useMemo(() => toSearchParams(parsedSearch), [parsedSearch])

  // Server-side search (only enabled when state filters are used on Feed tab)
  const serverSearch = useQuery({
    queryKey: ['search', searchParams],
    queryFn: () => api.searchItems(searchParams),
    enabled: needsServerSearch && activeTab === 'feed',
  })

  function updateItemState(itemId: number, updates: Partial<FeedItem['state']>): void {
    setLocalUpdates((prev) => ({
      ...prev,
      [itemId]: { ...prev[itemId], ...updates },
    }))
  }

  function handleToggleLike(item: FeedItem): void {
    updateItemState(item.id, { like: !item.state.like, hide: false })
    api.toggleLike(item.feed_item_id)
  }

  function handleToggleStar(item: FeedItem): void {
    updateItemState(item.id, { star: !item.state.star })
    api.toggleStar(item.feed_item_id)
  }

  function handleMarkRead(item: FeedItem): void {
    api.markRead(item.feed_item_id)
  }

  function handleToggleHide(item: FeedItem): void {
    updateItemState(item.id, { hide: !item.state.hide, like: false })
    api.toggleHide(item.feed_item_id)
  }

  // Get filtered items based on active tab (needed for keyboard shortcuts)
  const filteredItems = useMemo(() => {
    let result: FeedItem[]
    if (activeTab === 'digest') {
      result = applySearch(digestQuery.data ?? [], searchQuery)
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

  const visibleItems = useMemo(() => filteredItems.slice(0, visibleCount), [filteredItems, visibleCount])

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
    onMarkRead: handleMarkRead,
    onToggleHide: handleToggleHide,
    onRefresh: () => refetch(),
    enabled: true,
  })

  const totalCount = useMemo(() => items.filter((item) => !item.state.hide).length, [items])

  function toggleShowSummaries(): void {
    const newValue = !showSummaries
    setShowSummaries(newValue)
    localStorage.setItem('feedShowSummaries', String(newValue))
  }

  const isSearching = needsServerSearch && activeTab === 'feed' && serverSearch.isLoading

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
      {/* Tabs + Actions */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex">
          <TabButton isActive={activeTab === 'feed'} onClick={() => setActiveTab('feed')}>
            Feed
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
        </div>
      </div>

      {/* Search and Sort */}
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

      {/* Feed list */}
      <FeedList
        items={visibleItems}
        showSummaries={showSummaries}
        selectedIndex={selectedIndex}
        onToggleStar={handleToggleStar}
        onToggleLike={handleToggleLike}
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
