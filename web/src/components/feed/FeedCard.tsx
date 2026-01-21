import { forwardRef } from 'react'
import {
  ArrowTopRightOnSquareIcon,
  BookmarkIcon,
  ChatBubbleLeftIcon,
  EyeIcon,
  HandThumbUpIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import {
  BookmarkIcon as BookmarkIconSolid,
  HandThumbUpIcon as HandThumbUpIconSolid,
} from '@heroicons/react/24/solid'
import { cn, formatRelativeTime, truncate } from '@/lib/utils'
import type { FeedItemActions } from '@/types/actions'
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

interface FeedCardProps extends FeedItemActions {
  item: FeedItem
  showSummary?: boolean
  isSelected?: boolean
}

export const FeedCard = forwardRef<HTMLDivElement, FeedCardProps>(function FeedCard(
  {
    item,
    showSummary = true,
    isSelected = false,
    onToggleStar,
    onToggleLike,
    onMarkRead,
    onToggleHide,
  },
  ref
) {
  const { read: isRead, star: isStarred, like: isLiked, hide: isHidden } = item.state

  function handleArticleClick(e: React.MouseEvent<HTMLAnchorElement>): void {
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
      ref={ref}
      className={cn(
        'group rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50',
        isSelected && 'sm:ring-2 sm:ring-primary sm:border-primary',
        isHidden && 'opacity-40'
      )}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <a
            href={item.article_url || '#'}
            target="_blank"
            rel="noopener noreferrer"
            className="group/link inline-flex items-start gap-1"
            onClick={handleArticleClick}
          >
            <h3 className="text-sm sm:text-base font-medium leading-snug break-words text-foreground group-hover/link:text-primary">
              {item.title}
            </h3>
            <ArrowTopRightOnSquareIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover/link:opacity-100" />
          </a>
          <p className="mt-0.5 text-xs text-muted-foreground truncate">
            {item.source_name}
            {item.created_at && <> &middot; {formatRelativeTime(item.created_at)}</>}
          </p>
        </div>

        <div className="flex flex-shrink-0 items-center gap-1">
          <ActionButton
            onClick={() => onToggleLike?.(item)}
            isActive={isLiked}
            activeColor="text-green-500"
            title="Like - more of this"
            OutlineIcon={HandThumbUpIcon}
            SolidIcon={HandThumbUpIconSolid}
          />
          <ActionButton
            onClick={() => onToggleStar?.(item)}
            isActive={isStarred}
            activeColor="text-primary"
            title="Save for later"
            OutlineIcon={BookmarkIcon}
            SolidIcon={BookmarkIconSolid}
          />
          <ActionButton
            onClick={() => onToggleHide?.(item)}
            isActive={isHidden}
            activeColor="text-muted-foreground"
            title="Dismiss"
            OutlineIcon={XMarkIcon}
            SolidIcon={XMarkIcon}
          />
        </div>
      </div>

      {showSummary && item.summary && (
        <p className="mb-3 text-sm leading-relaxed text-muted-foreground">
          {truncate(item.summary, 400)}
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
})
