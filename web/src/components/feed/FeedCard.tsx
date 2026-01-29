import { forwardRef } from 'react'
import {
  BookmarkIcon,
  HeartIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import {
  BookmarkIcon as BookmarkIconSolid,
  HeartIcon as HeartIconSolid,
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
  pulse?: boolean
}

function ActionButton({
  onClick,
  isActive,
  activeColor,
  title,
  OutlineIcon,
  SolidIcon,
  pulse,
}: ActionButtonProps): React.ReactElement {
  const Icon = isActive ? SolidIcon : OutlineIcon
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex-shrink-0 rounded-full p-2.5 transition-all hover:bg-secondary/80 active:scale-95',
        isActive ? activeColor : 'text-muted-foreground hover:text-foreground'
      )}
      title={title}
    >
      <Icon className={cn(
        'h-5 w-5 transition-transform',
        pulse && isActive && 'animate-heartbeat'
      )} />
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
        'group rounded-xl bg-card p-4 sm:p-5 shadow-sm ring-1 ring-border/50 transition-all duration-200 hover:shadow-md hover:ring-border',
        isSelected && 'sm:ring-1 sm:ring-primary/50 sm:bg-primary/5',
        isHidden && 'opacity-40'
      )}
    >
      {/* Title + Actions */}
      <div className="flex items-start justify-between gap-2">
        <a
          href={item.article_url || '#'}
          target="_blank"
          rel="noopener noreferrer"
          className="group/link min-w-0 flex-1"
          onClick={handleArticleClick}
        >
          <h3 className="text-[15px] sm:text-base font-semibold leading-snug tracking-tight text-foreground transition-colors group-hover/link:text-primary">
            {item.title}
          </h3>
        </a>
        <div className="flex flex-shrink-0 items-center -mr-1.5 -mt-1">
          <ActionButton
            onClick={() => onToggleLike?.(item)}
            isActive={isLiked}
            activeColor="text-red-600"
            title="Love - more of this"
            OutlineIcon={HeartIcon}
            SolidIcon={HeartIconSolid}
            pulse={isLiked}
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

      {/* Source + Time */}
      <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
        <span className="font-medium text-foreground/60">{item.source_name}</span>
        {(item.published || item.created_at) && (
          <>
            <span>·</span>
            <span>{formatRelativeTime(item.published ?? item.created_at)}</span>
          </>
        )}
      </div>

      {/* Summary */}
      {showSummary && item.summary && (
        <p className="mt-3 text-[13px] leading-6 text-foreground/70">
          {truncate(item.summary, 400)}
        </p>
      )}

      {/* Footer: points + comments */}
      {(item.points != null && item.points > 0) || item.comments_url ? (
        <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
          {item.points != null && item.points > 0 && (
            <span>
              <span className="font-medium text-foreground/70">{item.points}</span> points
            </span>
          )}
          {item.comments_url && (
            <a
              href={item.comments_url}
              target="_blank"
              rel="noopener noreferrer"
              className="transition-colors hover:text-foreground"
            >
              comments
            </a>
          )}
        </div>
      ) : null}
    </article>
  )
})
