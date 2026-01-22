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
        <MagnifyingGlassIcon className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setShowHints(true)}
          onBlur={() => setTimeout(() => setShowHints(false), 200)}
          placeholder={placeholder}
          className="h-10 w-full rounded-xl bg-secondary/50 pl-10 pr-10 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:bg-card focus:outline-none focus:ring-1 focus:ring-border"
        />
        {value && (
          <button
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 rounded-full p-0.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      {showHints && !value && (
        <div className="absolute z-10 mt-2 w-full rounded-xl bg-card p-3 shadow-lg ring-1 ring-border/50">
          <p className="mb-2 text-xs font-medium text-muted-foreground">Search operators</p>
          <div className="flex flex-wrap gap-1.5">
            {SEARCH_HINTS.map((hint) => (
              <button
                key={hint.label}
                onClick={() => handleHintClick(hint.label)}
                className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:bg-secondary/80"
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
