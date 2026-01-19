import type { FeedItem } from '@/types/feed'

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
  if (filters.liked !== undefined && item.state.like !== filters.liked) {
    return false
  }
  if (filters.disliked !== undefined && item.state.dislike !== filters.disliked) {
    return false
  }
  if (filters.read !== undefined && item.state.read !== filters.read) {
    return false
  }
  if (filters.unread !== undefined && item.state.read === filters.unread) {
    return false
  }
  if (filters.saved !== undefined && item.state.star !== filters.saved) {
    return false
  }
  if (filters.hidden !== undefined && item.state.hide !== filters.hidden) {
    return false
  }
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
    if (!matchesFilters(item, parsed.filters)) {
      return false
    }

    // Exclude hidden items unless explicitly searching for them
    if (parsed.filters.hidden === undefined && item.state.hide) {
      return false
    }

    if (!matchesSources(item, parsed.sources)) {
      return false
    }

    return matchesTextTerms(item, parsed.textTerms)
  })
}
