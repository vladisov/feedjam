import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { Subscription } from '@/types/feed'
import { toast } from 'sonner'

interface UseSubscriptionsQueryOptions {
  enabled?: boolean
}

export function useSubscriptionsQuery({ enabled = true }: UseSubscriptionsQueryOptions = {}) {
  const queryClient = useQueryClient()

  const {
    data: subscriptions,
    isLoading,
    error,
    refetch,
  } = useQuery<Subscription[], Error>({
    queryKey: ['subscriptions'],
    queryFn: () => api.getSubscriptions(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    enabled,
  })

  const addSubscription = useMutation({
    mutationFn: (resourceUrl: string) => api.addSubscription(resourceUrl),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      toast.success('Subscription added')
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to add subscription')
    },
  })

  const deleteSubscription = useMutation({
    mutationFn: (subscriptionId: number) => api.deleteSubscription(subscriptionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      toast.success('Subscription removed')
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to remove subscription')
    },
  })

  return {
    subscriptions: subscriptions || [],
    isLoading,
    error: error?.message || null,
    refetch,
    addSubscription: addSubscription.mutate,
    isAdding: addSubscription.isPending,
    deleteSubscription: deleteSubscription.mutate,
    isDeleting: deleteSubscription.isPending,
  }
}
