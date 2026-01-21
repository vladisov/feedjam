import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { api } from '@/lib/api'
import type { Subscription } from '@/types/feed'

interface UseSubscriptionsQueryOptions {
  enabled?: boolean
}

interface UseSubscriptionsQueryResult {
  subscriptions: Subscription[]
  isLoading: boolean
  error: string | null
  refetch: () => void
  addSubscription: (resourceUrl: string) => void
  isAdding: boolean
  deleteSubscription: (subscriptionId: number) => void
  isDeleting: boolean
  refetchSubscription: (subscriptionId: number) => void
  isRefetching: boolean
}

export function useSubscriptionsQuery({ enabled = true }: UseSubscriptionsQueryOptions = {}): UseSubscriptionsQueryResult {
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

  const refetchSubscription = useMutation({
    mutationFn: (subscriptionId: number) => api.refetchSubscription(subscriptionId),
    onSuccess: () => {
      toast.success('Refetch triggered - check back soon')
      // Refresh the list after a short delay to show updated status
      setTimeout(() => {
        queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      }, 2000)
    },
    onError: (error: Error) => {
      toast.error(error.message || 'Failed to trigger refetch')
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
    refetchSubscription: refetchSubscription.mutate,
    isRefetching: refetchSubscription.isPending,
  }
}
