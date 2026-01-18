import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useFeedQuery } from '@/hooks/useFeedQuery'
import { FeedList } from '@/components/feed/FeedList'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { ArrowPathIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import type { FeedItem } from '@/types/feed'

// TODO: Make this configurable or remove when multi-user
const DEFAULT_USER_ID = 1

export default function FeedPage() {
  const queryClient = useQueryClient()
  const { items, isLoading, error, refetch } = useFeedQuery({
    userId: DEFAULT_USER_ID,
  })

  const likeMutation = useMutation({
    mutationFn: (item: FeedItem) => api.toggleLike(DEFAULT_USER_ID, item.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed', DEFAULT_USER_ID] })
    },
  })

  const dislikeMutation = useMutation({
    mutationFn: (item: FeedItem) => api.toggleDislike(DEFAULT_USER_ID, item.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feed', DEFAULT_USER_ID] })
    },
  })

  const handleToggleLike = (item: FeedItem) => {
    likeMutation.mutate(item)
  }

  const handleToggleDislike = (item: FeedItem) => {
    dislikeMutation.mutate(item)
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
            {items.length} items
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

      {/* Feed list */}
      <FeedList
        items={items}
        onToggleLike={handleToggleLike}
        onToggleDislike={handleToggleDislike}
      />
    </div>
  )
}
