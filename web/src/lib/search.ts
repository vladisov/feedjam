import type { FeedItem, SearchParams } from '@/types/feed'

export interface SearchFilters {
  liked?: boolean
  disliked?: boolean
  read?: boolean
  unread?: boolean
  saved?: boolean
  hidden?: boolean
}

export interface ParsedSearch {
  textTerms: string[]
  filters: SearchFilters
  sources: string[]
}

/**
 * Check if the search query requires a server-side search.
 * Server search is needed when state filters (is:liked, is:read, etc.) are used,
 * as these need to search historical data beyond the active feed.
 */
export function requiresServerSearch(parsed: ParsedSearch): boolean {
  return Object.keys(parsed.filters).length > 0
}

/**
 * Convert ParsedSearch to API SearchParams.
 */
export function toSearchParams(parsed: ParsedSearch): SearchParams {
  const params: SearchParams = {}

  if (parsed.filters.liked) params.liked = true
  if (parsed.filters.disliked) params.disliked = true
  if (parsed.filters.read) params.read = true
  if (parsed.filters.unread) params.read = false // unread = read:false
  if (parsed.filters.saved) params.starred = true
  if (parsed.filters.hidden) params.hidden = true

  if (parsed.textTerms.length > 0) {
    params.text = parsed.textTerms.join(' ')
  }

  if (parsed.sources.length > 0) {
    params.source = parsed.sources[0] // API only supports one source filter
  }

  return params
}

const IS_FILTERS = ['liked', 'disliked', 'read', 'unread', 'saved', 'hidden'] as const

function removeQuotes(str: string): string {
  return str.replace(/^"|"$/g, '')
}

export function parseSearchQuery(query: string): ParsedSearch {
  const result: ParsedSearch = {
    textTerms: [],
    filters: {},
    sources: [],
  }

  const trimmed = query.trim()
  if (!trimmed) {
    return result
  }

  const tokens = trimmed.match(/(?:[^\s"]+|"[^"]*")+/g) ?? []

  for (const token of tokens) {
    const lowerToken = token.toLowerCase()

    if (lowerToken.startsWith('is:')) {
      const filter = lowerToken.slice(3) as (typeof IS_FILTERS)[number]
      if (IS_FILTERS.includes(filter)) {
        result.filters[filter] = true
      }
      continue
    }

    if (lowerToken.startsWith('source:')) {
      const source = removeQuotes(token.slice(7))
      if (source) {
        result.sources.push(source.toLowerCase())
      }
      continue
    }

    const term = removeQuotes(token)
    if (term) {
      result.textTerms.push(term.toLowerCase())
    }
  }

  return result
}

function matchesFilters(item: FeedItem, filters: SearchFilters): boolean {
  if (filters.liked && !item.state.like) return false
  if (filters.disliked && !item.state.dislike) return false
  if (filters.read && !item.state.read) return false
  if (filters.unread && item.state.read) return false
  if (filters.saved && !item.state.star) return false
  if (filters.hidden && !item.state.hide) return false
  return true
}

function matchesSources(item: FeedItem, sources: string[]): boolean {
  if (sources.length === 0) {
    return true
  }
  const itemSource = (item.source_name ?? '').toLowerCase()
  return sources.some((s) => itemSource.includes(s) || s.includes(itemSource))
}

function matchesTextTerms(item: FeedItem, terms: string[]): boolean {
  if (terms.length === 0) {
    return true
  }
  const searchText = `${item.title} ${item.summary ?? ''} ${item.description ?? ''}`.toLowerCase()
  return terms.every((term) => searchText.includes(term))
}

export function applySearch(items: FeedItem[], query: string): FeedItem[] {
  const parsed = parseSearchQuery(query)
  const hasFilters = Object.keys(parsed.filters).length > 0
  const hasSearch = parsed.textTerms.length > 0 || parsed.sources.length > 0

  if (!hasFilters && !hasSearch) {
    return items.filter((item) => !item.state.hide)
  }

  return items.filter((item) => {
    // Exclude hidden items unless explicitly searching for them
    if (!parsed.filters.hidden && item.state.hide) return false

    return (
      matchesFilters(item, parsed.filters) &&
      matchesSources(item, parsed.sources) &&
      matchesTextTerms(item, parsed.textTerms)
    )
  })
}
