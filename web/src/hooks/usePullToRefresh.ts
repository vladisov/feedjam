import { useEffect, useRef, useState, type RefObject } from 'react'

const PULL_THRESHOLD = 80
const MAX_PULL = 120

interface UsePullToRefreshOptions {
  onRefresh: () => void
  enabled?: boolean
}

interface UsePullToRefreshReturn {
  containerRef: RefObject<HTMLDivElement | null>
  pullDistance: number
  isPulling: boolean
}

export function usePullToRefresh({
  onRefresh,
  enabled = true,
}: UsePullToRefreshOptions): UsePullToRefreshReturn {
  const containerRef = useRef<HTMLDivElement>(null)
  const [pullDistance, setPullDistance] = useState(0)
  const [isPulling, setIsPulling] = useState(false)
  const startY = useRef(0)
  const currentY = useRef(0)

  useEffect(() => {
    if (!enabled) return

    const container = containerRef.current
    if (!container) return

    function handleTouchStart(e: TouchEvent): void {
      // Only start pull if at top of page
      if (window.scrollY > 0) return
      const touch = e.touches[0]
      if (!touch) return
      startY.current = touch.clientY
      setIsPulling(true)
    }

    function handleTouchMove(e: TouchEvent): void {
      if (!isPulling || window.scrollY > 0) {
        setPullDistance(0)
        return
      }

      const touch = e.touches[0]
      if (!touch) return
      currentY.current = touch.clientY
      const diff = currentY.current - startY.current

      if (diff > 0) {
        // Apply resistance curve for more natural feel
        const distance = Math.min(diff * 0.5, MAX_PULL)
        setPullDistance(distance)

        // Prevent default scroll when pulling down
        if (distance > 10) {
          e.preventDefault()
        }
      }
    }

    function handleTouchEnd(): void {
      if (pullDistance >= PULL_THRESHOLD) {
        onRefresh()
      }
      setPullDistance(0)
      setIsPulling(false)
      startY.current = 0
      currentY.current = 0
    }

    container.addEventListener('touchstart', handleTouchStart, { passive: true })
    container.addEventListener('touchmove', handleTouchMove, { passive: false })
    container.addEventListener('touchend', handleTouchEnd, { passive: true })

    return () => {
      container.removeEventListener('touchstart', handleTouchStart)
      container.removeEventListener('touchmove', handleTouchMove)
      container.removeEventListener('touchend', handleTouchEnd)
    }
  }, [enabled, isPulling, pullDistance, onRefresh])

  return {
    containerRef,
    pullDistance,
    isPulling,
  }
}
