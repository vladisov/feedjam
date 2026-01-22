import { XMarkIcon } from '@heroicons/react/24/outline'

interface KeyboardShortcutsHelpProps {
  isOpen: boolean
  onClose: () => void
}

interface ShortcutEntry {
  key: string
  description: string
}

const SHORTCUTS: ShortcutEntry[] = [
  { key: 'j / ↓', description: 'Next item' },
  { key: 'k / ↑', description: 'Previous item' },
  { key: 'o / Enter', description: 'Open article' },
  { key: 'c', description: 'Open comments' },
  { key: 'l', description: 'Love (more of this)' },
  { key: 'h', description: 'Dismiss' },
  { key: 's', description: 'Save for later' },
  { key: 'r', description: 'Refresh feed' },
  { key: '?', description: 'Toggle this help' },
  { key: 'Esc', description: 'Close help' },
]

export function KeyboardShortcutsHelp({ isOpen, onClose }: KeyboardShortcutsHelpProps): React.ReactElement | null {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 animate-fade-in" onClick={onClose}>
      <div
        className="w-full max-w-sm rounded-xl border border-border bg-card p-6 shadow-lg animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">Keyboard Shortcuts</h2>
          <button
            onClick={onClose}
            className="rounded p-1 text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="space-y-2">
          {SHORTCUTS.map(({ key, description }) => (
            <div key={key} className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{description}</span>
              <kbd className="rounded bg-secondary px-2 py-1 font-mono text-xs text-foreground">
                {key}
              </kbd>
            </div>
          ))}
        </div>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          Press <kbd className="rounded bg-secondary px-1.5 py-0.5 font-mono">?</kbd> anytime to toggle
        </p>
      </div>
    </div>
  )
}
