import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { UserFeed } from '@/types/feed'

const STALE_TIME = 2 * 60 * 1000 // 2 minutes
const REFETCH_INTERVAL = 5 * 60 * 1000 // 5 minutes

interface UseFeedQueryOptions {
  userId: number
  enabled?: boolean
}

export function useFeedQuery({ userId, enabled = true }: UseFeedQueryOptions) {
  const {
    data: feed,
    isLoading,
    error,
    refetch,
  } = useQuery<UserFeed, Error>({
    queryKey: ['feed', userId],
    queryFn: () => api.getFeed(userId),
    staleTime: STALE_TIME,
    refetchOnWindowFocus: true,
    refetchInterval: REFETCH_INTERVAL,
    enabled,
  })

  const items = feed?.user_feed_items || []

  return {
    feed,
    items,
    isLoading,
    error: error?.message || null,
    refetch,
  }
}
