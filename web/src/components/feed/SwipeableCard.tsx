import { useRef, useState, useCallback, type ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { BookmarkIcon, XMarkIcon } from '@heroicons/react/24/solid'

interface SwipeableCardProps {
  children: ReactNode
  onSwipeLeft?: () => void
  onSwipeRight?: () => void
  leftLabel?: string
  rightLabel?: string
  disabled?: boolean
}

const SWIPE_THRESHOLD = 80
const SWIPE_MIN_DISTANCE = 30
const SWIPE_MAX_DISTANCE = 150
const SWIPE_VELOCITY_THRESHOLD = 0.5
const ACTION_INDICATOR_THRESHOLD = 30

export function SwipeableCard({
  children,
  onSwipeLeft,
  onSwipeRight,
  leftLabel = 'Hide',
  rightLabel = 'Save',
  disabled = false,
}: SwipeableCardProps): React.ReactElement {
  const containerRef = useRef<HTMLDivElement>(null)
  const [offsetX, setOffsetX] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const startX = useRef(0)
  const startTime = useRef(0)

  const handleTouchStart = useCallback(
    (e: React.TouchEvent) => {
      if (disabled || !e.touches[0]) return
      startX.current = e.touches[0].clientX
      startTime.current = Date.now()
      setIsDragging(true)
    },
    [disabled]
  )

  const handleTouchMove = useCallback(
    (e: React.TouchEvent) => {
      if (!isDragging || disabled || !e.touches[0]) return
      const diff = e.touches[0].clientX - startX.current
      const clampedDiff = Math.max(-SWIPE_MAX_DISTANCE, Math.min(SWIPE_MAX_DISTANCE, diff))
      setOffsetX(clampedDiff)
    },
    [isDragging, disabled]
  )

  const handleTouchEnd = useCallback(() => {
    if (!isDragging || disabled) return

    const elapsed = Date.now() - startTime.current
    const velocity = Math.abs(offsetX) / elapsed
    const isSwipeByDistance = Math.abs(offsetX) >= SWIPE_THRESHOLD
    const isSwipeByVelocity = Math.abs(offsetX) >= SWIPE_MIN_DISTANCE && velocity > SWIPE_VELOCITY_THRESHOLD

    if (isSwipeByDistance || isSwipeByVelocity) {
      if (offsetX < 0) {
        onSwipeLeft?.()
      } else {
        onSwipeRight?.()
      }
    }

    setOffsetX(0)
    setIsDragging(false)
  }, [isDragging, disabled, offsetX, onSwipeLeft, onSwipeRight])

  const showLeftAction = offsetX < -ACTION_INDICATOR_THRESHOLD
  const showRightAction = offsetX > ACTION_INDICATOR_THRESHOLD

  return (
    <div className="relative overflow-hidden rounded-lg">
      {/* Left action background (Hide) */}
      <div
        className={cn(
          'absolute inset-y-0 right-0 flex items-center justify-end bg-red-500 px-6 transition-opacity',
          showLeftAction ? 'opacity-100' : 'opacity-0'
        )}
        style={{ width: Math.abs(Math.min(offsetX, 0)) + 20 }}
      >
        <div className="flex flex-col items-center text-white">
          <XMarkIcon className="h-6 w-6" />
          <span className="text-xs font-medium">{leftLabel}</span>
        </div>
      </div>

      {/* Right action background (Save) */}
      <div
        className={cn(
          'absolute inset-y-0 left-0 flex items-center justify-start bg-primary px-6 transition-opacity',
          showRightAction ? 'opacity-100' : 'opacity-0'
        )}
        style={{ width: Math.max(offsetX, 0) + 20 }}
      >
        <div className="flex flex-col items-center text-primary-foreground">
          <BookmarkIcon className="h-6 w-6" />
          <span className="text-xs font-medium">{rightLabel}</span>
        </div>
      </div>

      {/* Swipeable content */}
      <div
        ref={containerRef}
        className={cn(
          'relative bg-card',
          isDragging ? '' : 'transition-transform duration-200'
        )}
        style={{ transform: `translateX(${offsetX}px)` }}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {children}
      </div>
    </div>
  )
}
