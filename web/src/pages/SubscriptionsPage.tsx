import { useState } from 'react'
import { useSubscriptionsQuery } from '@/hooks/useSubscriptionsQuery'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { PlusIcon, RssIcon, TrashIcon, ExclamationTriangleIcon, ClockIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { cn, formatDate } from '@/lib/utils'
import type { Subscription } from '@/types/feed'

type HealthStatus = 'healthy' | 'stale' | 'pending' | 'error'

function getHealthStatus(lastRun: string | null, createdAt: string): HealthStatus {
  if (!lastRun) {
    // If created within last 10 minutes, it's still pending first fetch
    const minutesSinceCreated = (Date.now() - new Date(createdAt).getTime()) / (1000 * 60)
    return minutesSinceCreated < 10 ? 'pending' : 'error'
  }
  const hoursSinceRun = (Date.now() - new Date(lastRun).getTime()) / (1000 * 60 * 60)
  if (hoursSinceRun < 6) return 'healthy'
  if (hoursSinceRun < 24) return 'stale'
  return 'error'
}

interface HealthIndicatorProps {
  subscription: Subscription
}

function HealthIndicator({ subscription }: HealthIndicatorProps): React.ReactElement {
  const status = getHealthStatus(subscription.last_run, subscription.created_at)

  switch (status) {
    case 'healthy':
      return (
        <span
          className="h-2 w-2 rounded-full bg-green-500"
          title="Feed is healthy - fetched recently"
        />
      )
    case 'stale':
      return (
        <span
          className="h-2 w-2 rounded-full bg-yellow-500"
          title="Feed may be stale - not fetched in the last 6 hours"
        />
      )
    case 'pending':
      return (
        <ClockIcon
          className="h-4 w-4 animate-pulse text-muted-foreground"
          title="Fetching feed for the first time..."
        />
      )
    case 'error':
      return (
        <ExclamationTriangleIcon
          className="h-4 w-4 text-red-500"
          title={subscription.last_run ? 'Feed error - not fetched in over 24 hours' : 'Feed never fetched'}
        />
      )
  }
}

export default function SubscriptionsPage(): React.ReactElement {
  const [newUrl, setNewUrl] = useState('')
  const { subscriptions, isLoading, error, addSubscription, isAdding, deleteSubscription, refetchSubscription } = useSubscriptionsQuery()

  function handleSubmit(e: React.FormEvent): void {
    e.preventDefault()
    const trimmedUrl = newUrl.trim()
    if (trimmedUrl) {
      addSubscription(trimmedUrl)
      setNewUrl('')
    }
  }

  if (isLoading && subscriptions.length === 0) {
    return <PageLoader />
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground">Subscriptions</h2>
        <p className="text-sm text-muted-foreground">
          Manage your feed sources
        </p>
      </div>

      {/* Add subscription form */}
      <form onSubmit={handleSubmit} className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row gap-2">
          <input
            type="url"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="Enter RSS feed URL..."
            className="w-full sm:flex-1 rounded-lg border border-input bg-background px-3 sm:px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            required
          />
          <Button type="submit" disabled={isAdding || !newUrl.trim()} className="flex-shrink-0">
            <PlusIcon className="mr-2 h-4 w-4" />
            Add
          </Button>
        </div>
      </form>

      {/* Error state */}
      {error && (
        <div className="mb-4 rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Subscriptions list */}
      {subscriptions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <RssIcon className="mb-4 h-12 w-12 text-muted-foreground" />
          <p className="text-lg font-medium text-foreground">No subscriptions yet</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Add an RSS feed URL above to get started
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {subscriptions.map((sub) => (
            <div
              key={sub.id}
              className={cn(
                'flex items-start sm:items-center justify-between gap-2 rounded-lg border bg-card p-3 sm:p-4',
                getHealthStatus(sub.last_run, sub.created_at) === 'error'
                  ? 'border-red-500/50'
                  : 'border-border'
              )}
            >
              <div className="flex items-start gap-2 sm:gap-3 min-w-0 flex-1">
                <div className="mt-1 sm:mt-0">
                  <HealthIndicator subscription={sub} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium text-foreground text-sm sm:text-base">
                    {sub.source_name}
                  </p>
                  <p className="truncate text-xs sm:text-sm text-muted-foreground">
                    {sub.resource_url}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDate(sub.created_at)}
                    {sub.item_count > 0 && ` · ${sub.item_count} items`}
                  </p>
                  {sub.last_error && (
                    <p className="mt-1 text-xs text-red-500 truncate" title={sub.last_error}>
                      {sub.last_error.slice(0, 60)}{sub.last_error.length > 60 ? '...' : ''}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex flex-shrink-0 items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-foreground"
                  onClick={() => refetchSubscription(sub.id)}
                  title="Refetch now"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:text-destructive"
                  onClick={() => deleteSubscription(sub.id)}
                  title="Delete"
                >
                  <TrashIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
