import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Subscription } from '@/types/feed'
import { toast } from 'sonner'

interface UseSubscriptionsQueryOptions {
  userId: number
  enabled?: boolean
}

export function useSubscriptionsQuery({ userId, enabled = true }: UseSubscriptionsQueryOptions) {
  const queryClient = useQueryClient()

  const {
    data: subscriptions,
    isLoading,
    error,
    refetch,
  } = useQuery<Subscription[], Error>({
    queryKey: ['subscriptions', userId],
    queryFn: () => api.getSubscriptions(userId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled,
  })

  const addSubscription = useMutation({
    mutationFn: (resourceUrl: string) => api.addSubscription(resourceUrl, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions', userId] })
      toast.success('Subscription added')
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add subscription')
    },
  })

  return {
    subscriptions: subscriptions || [],
    isLoading,
    error: error?.message || null,
    refetch,
    addSubscription: addSubscription.mutate,
    isAdding: addSubscription.isPending,
  }
}
