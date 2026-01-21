import { useEffect, useCallback, useState, useMemo } from 'react'
import type { FeedItemActions } from '@/types/actions'
import type { FeedItem } from '@/types/feed'

function isEditableElement(target: EventTarget | null): boolean {
  if (!target || !(target instanceof HTMLElement)) return false
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target.isContentEditable
  )
}

interface UseKeyboardShortcutsOptions extends FeedItemActions {
  items: FeedItem[]
  onRefresh?: () => void
  enabled?: boolean
}

interface UseKeyboardShortcutsReturn {
  selectedIndex: number
  setSelectedIndex: (index: number) => void
  showHelp: boolean
  setShowHelp: (show: boolean) => void
}

export function useKeyboardShortcuts({
  items,
  onToggleStar,
  onToggleLike,
  onMarkRead,
  onToggleHide,
  onRefresh,
  enabled = true,
}: UseKeyboardShortcutsOptions): UseKeyboardShortcutsReturn {
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [showHelp, setShowHelp] = useState(false)

  const selectedItem = items[selectedIndex] ?? null

  const openArticle = useCallback(() => {
    if (selectedItem?.article_url) {
      window.open(selectedItem.article_url, '_blank', 'noopener,noreferrer')
      onMarkRead?.(selectedItem)
    }
  }, [selectedItem, onMarkRead])

  const openComments = useCallback(() => {
    if (selectedItem?.comments_url) {
      window.open(selectedItem.comments_url, '_blank', 'noopener,noreferrer')
    }
  }, [selectedItem])

  const keyActions = useMemo(() => {
    const moveDown = () => setSelectedIndex((prev) => Math.min(prev + 1, items.length - 1))
    const moveUp = () => setSelectedIndex((prev) => Math.max(prev - 1, 0))

    return new Map<string, () => void>([
      ['j', moveDown],
      ['ArrowDown', moveDown],
      ['k', moveUp],
      ['ArrowUp', moveUp],
      ['o', openArticle],
      ['Enter', openArticle],
      ['c', openComments],
      ['s', () => selectedItem && onToggleStar?.(selectedItem)],
      ['l', () => selectedItem && onToggleLike?.(selectedItem)],
      ['h', () => selectedItem && onToggleHide?.(selectedItem)],
      ['r', () => onRefresh?.()],
      ['?', () => setShowHelp((prev) => !prev)],
      ['Escape', () => setShowHelp(false)],
    ])
  }, [
    items.length,
    selectedItem,
    openArticle,
    openComments,
    onToggleStar,
    onToggleLike,
    onMarkRead,
    onToggleHide,
    onRefresh,
  ])

  useEffect(() => {
    if (!enabled) return

    function handleKeyDown(e: KeyboardEvent): void {
      if (isEditableElement(e.target)) return
      if (e.ctrlKey || e.metaKey || e.altKey) return

      const action = keyActions.get(e.key)
      if (action) {
        e.preventDefault()
        action()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [enabled, keyActions])

  // Keep selection in bounds when items change
  useEffect(() => {
    if (selectedIndex >= items.length && items.length > 0) {
      setSelectedIndex(items.length - 1)
    }
  }, [items.length, selectedIndex])

  return {
    selectedIndex,
    setSelectedIndex,
    showHelp,
    setShowHelp,
  }
}
