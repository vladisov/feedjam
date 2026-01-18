import {
  ChatBubbleLeftIcon,
  ArrowTopRightOnSquareIcon,
  StarIcon,
  EyeIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
} from '@heroicons/react/24/outline'
import {
  StarIcon as StarIconSolid,
  HandThumbUpIcon as HandThumbUpIconSolid,
  HandThumbDownIcon as HandThumbDownIconSolid,
} from '@heroicons/react/24/solid'
import { cn, formatRelativeTime, truncate } from '@/lib/utils'
import type { FeedItem } from '@/types/feed'

interface FeedCardProps {
  item: FeedItem
  onToggleStar?: (item: FeedItem) => void
  onToggleLike?: (item: FeedItem) => void
  onToggleDislike?: (item: FeedItem) => void
}

export function FeedCard({ item, onToggleStar, onToggleLike, onToggleDislike }: FeedCardProps) {
  const isRead = item.state.read
  const isStarred = item.state.star
  const isLiked = item.state.like
  const isDisliked = item.state.dislike

  return (
    <article
      className={cn(
        'group rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50',
        isRead && 'opacity-60'
      )}
    >
      {/* Header */}
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex-1">
          <a
            href={item.article_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="group/link inline-flex items-start gap-1"
          >
            <h3
              className={cn(
                'text-base font-medium leading-snug',
                isRead ? 'text-feed-read' : 'text-foreground',
                'group-hover/link:text-feed-unread'
              )}
            >
              {item.title}
            </h3>
            <ArrowTopRightOnSquareIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover/link:opacity-100" />
          </a>
          <p className="mt-0.5 text-xs text-muted-foreground">
            {item.source_name} &middot; {formatRelativeTime(item.created_at)}
          </p>
        </div>

        <div className="flex items-center gap-1">
          <button
            onClick={() => onToggleLike?.(item)}
            className={cn(
              'flex-shrink-0 rounded p-1 transition-colors hover:bg-secondary',
              isLiked ? 'text-green-500' : 'text-muted-foreground hover:text-green-500'
            )}
            title="Like - stories from this source will rank higher"
          >
            {isLiked ? (
              <HandThumbUpIconSolid className="h-5 w-5" />
            ) : (
              <HandThumbUpIcon className="h-5 w-5" />
            )}
          </button>

          <button
            onClick={() => onToggleDislike?.(item)}
            className={cn(
              'flex-shrink-0 rounded p-1 transition-colors hover:bg-secondary',
              isDisliked ? 'text-red-500' : 'text-muted-foreground hover:text-red-500'
            )}
            title="Dislike - stories from this source will rank lower"
          >
            {isDisliked ? (
              <HandThumbDownIconSolid className="h-5 w-5" />
            ) : (
              <HandThumbDownIcon className="h-5 w-5" />
            )}
          </button>

          <button
            onClick={() => onToggleStar?.(item)}
            className="flex-shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-feed-starred"
          >
            {isStarred ? (
              <StarIconSolid className="h-5 w-5 text-feed-starred" />
            ) : (
              <StarIcon className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Summary */}
      {item.summary && (
        <p className="mb-3 text-sm leading-relaxed text-muted-foreground">
          {truncate(item.summary, 200)}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        {item.points !== null && item.points > 0 && (
          <span className="flex items-center gap-1">
            <span className="font-medium text-foreground">{item.points}</span> points
          </span>
        )}

        {item.views !== null && item.views > 0 && (
          <span className="flex items-center gap-1">
            <EyeIcon className="h-3.5 w-3.5" />
            {item.views.toLocaleString()}
          </span>
        )}

        {item.comments_url && (
          <a
            href={item.comments_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 transition-colors hover:text-foreground"
          >
            <ChatBubbleLeftIcon className="h-3.5 w-3.5" />
            comments
          </a>
        )}
      </div>
    </article>
  )
}
