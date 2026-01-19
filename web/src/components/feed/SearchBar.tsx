import { useState } from 'react'
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline'

const SEARCH_HINTS = [
  { label: 'is:saved', description: 'Saved items' },
  { label: 'is:liked', description: 'Liked items' },
  { label: 'is:read', description: 'Read items' },
  { label: 'is:unread', description: 'Unread items' },
  { label: 'is:hidden', description: 'Hidden items' },
  { label: 'source:name', description: 'Filter by source' },
] as const

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
}

export function SearchBar({
  value,
  onChange,
  placeholder = 'Search...',
}: SearchBarProps): React.ReactElement {
  const [showHints, setShowHints] = useState(false)

  function handleHintClick(hint: string): void {
    onChange(value ? `${value} ${hint}` : hint)
    setShowHints(false)
  }

  function handleClear(): void {
    onChange('')
  }

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setShowHints(true)}
          onBlur={() => setTimeout(() => setShowHints(false), 200)}
          placeholder={placeholder}
          className="w-full rounded-lg border border-border bg-background py-2 pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
        />
        {value && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      {showHints && !value && (
        <div className="absolute z-10 mt-1 w-full rounded-lg border border-border bg-card p-2 shadow-lg">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Search operators:</p>
          <div className="flex flex-wrap gap-1">
            {SEARCH_HINTS.map((hint) => (
              <button
                key={hint.label}
                onClick={() => handleHintClick(hint.label)}
                className="rounded bg-secondary px-2 py-1 text-xs text-foreground hover:bg-secondary/80"
                title={hint.description}
              >
                {hint.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
