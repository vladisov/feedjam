import {
  ChatBubbleLeftIcon,
  ArrowTopRightOnSquareIcon,
  BookmarkIcon,
  EyeIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import {
  BookmarkIcon as BookmarkIconSolid,
  HandThumbUpIcon as HandThumbUpIconSolid,
  HandThumbDownIcon as HandThumbDownIconSolid,
} from '@heroicons/react/24/solid'
import { cn, formatRelativeTime, truncate } from '@/lib/utils'
import type { FeedItem } from '@/types/feed'

interface ActionButtonProps {
  onClick?: () => void
  isActive: boolean
  activeColor: string
  title: string
  OutlineIcon: React.ComponentType<{ className?: string }>
  SolidIcon: React.ComponentType<{ className?: string }>
}

function ActionButton({
  onClick,
  isActive,
  activeColor,
  title,
  OutlineIcon,
  SolidIcon,
}: ActionButtonProps): React.ReactElement {
  const Icon = isActive ? SolidIcon : OutlineIcon
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex-shrink-0 rounded p-1 transition-colors hover:bg-secondary',
        isActive ? activeColor : 'text-muted-foreground'
      )}
      title={title}
    >
      <Icon className={cn('h-5 w-5', isActive && activeColor)} />
    </button>
  )
}

interface FeedCardProps {
  item: FeedItem
  showSummary?: boolean
  onToggleStar?: (item: FeedItem) => void
  onToggleLike?: (item: FeedItem) => void
  onToggleDislike?: (item: FeedItem) => void
  onMarkRead?: (item: FeedItem) => void
  onToggleHide?: (item: FeedItem) => void
}

export function FeedCard({
  item,
  showSummary = true,
  onToggleStar,
  onToggleLike,
  onToggleDislike,
  onMarkRead,
  onToggleHide,
}: FeedCardProps) {
  const { read: isRead, star: isStarred, like: isLiked, dislike: isDisliked } = item.state

  const handleArticleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    if (item.article_url) {
      window.open(item.article_url, '_blank', 'noopener,noreferrer')
    }
    if (!isRead) {
      onMarkRead?.(item)
    }
  }

  return (
    <article
      className={cn(
        'group rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50',
        isRead && 'opacity-60'
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="flex-1">
          <a
            href={item.article_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="group/link inline-flex items-start gap-1"
            onClick={handleArticleClick}
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
          <ActionButton
            onClick={() => onToggleLike?.(item)}
            isActive={isLiked}
            activeColor="text-green-500"
            title="Like - stories from this source will rank higher"
            OutlineIcon={HandThumbUpIcon}
            SolidIcon={HandThumbUpIconSolid}
          />
          <ActionButton
            onClick={() => onToggleDislike?.(item)}
            isActive={isDisliked}
            activeColor="text-red-500"
            title="Dislike - stories from this source will rank lower"
            OutlineIcon={HandThumbDownIcon}
            SolidIcon={HandThumbDownIconSolid}
          />
          <ActionButton
            onClick={() => onToggleStar?.(item)}
            isActive={isStarred}
            activeColor="text-primary"
            title="Save for later"
            OutlineIcon={BookmarkIcon}
            SolidIcon={BookmarkIconSolid}
          />
          <button
            onClick={() => onToggleHide?.(item)}
            className="flex-shrink-0 rounded p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            title="Hide"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {showSummary && item.summary && (
        <p className="mb-3 text-sm leading-relaxed text-muted-foreground">
          {truncate(item.summary, 200)}
        </p>
      )}

      <div className="flex items-center gap-4 text-xs text-muted-foreground">
        {item.points != null && item.points > 0 && (
          <span className="flex items-center gap-1">
            <span className="font-medium text-foreground">{item.points}</span> points
          </span>
        )}
        {item.views != null && item.views > 0 && (
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
