import { useState } from 'react'
import { useSubscriptionsQuery } from '@/hooks/useSubscriptionsQuery'
import { PageLoader } from '@/components/shared/LoadingSpinner'
import { Button } from '@/components/shared/Button'
import { PlusIcon, RssIcon, TrashIcon } from '@heroicons/react/24/outline'
import { formatDate } from '@/lib/utils'

// TODO: Make this configurable or remove when multi-user
const DEFAULT_USER_ID = 1

export default function SubscriptionsPage() {
  const [newUrl, setNewUrl] = useState('')
  const { subscriptions, isLoading, error, addSubscription, isAdding } = useSubscriptionsQuery({
    userId: DEFAULT_USER_ID,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (newUrl.trim()) {
      addSubscription(newUrl.trim())
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
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-2">
          <input
            type="url"
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            placeholder="Enter RSS feed URL..."
            className="flex-1 rounded-lg border border-input bg-background px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            required
          />
          <Button type="submit" disabled={isAdding || !newUrl.trim()}>
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
              className="flex items-center justify-between rounded-lg border border-border bg-card p-4"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-foreground">
                  {sub.source_name}
                </p>
                <p className="truncate text-sm text-muted-foreground">
                  {sub.resource_url}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Added {formatDate(sub.created_at)}
                  {sub.last_run && ` · Last fetched ${formatDate(sub.last_run)}`}
                </p>
              </div>
              <Button variant="ghost" size="sm" className="ml-4 text-muted-foreground hover:text-destructive">
                <TrashIcon className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
