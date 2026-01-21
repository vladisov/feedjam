export interface SuggestedFeed {
  name: string
  url: string
  icon: string
}

export const SUGGESTED_FEEDS: SuggestedFeed[] = [
  { name: 'Hacker News', url: 'https://hnrss.org/best', icon: '🔶' },
  { name: 'Lobsters', url: 'https://lobste.rs/rss', icon: '🦞' },
  { name: 'TechCrunch', url: 'https://techcrunch.com/feed/', icon: '📱' },
  { name: 'The Verge', url: 'https://www.theverge.com/rss/index.xml', icon: '🔷' },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/index', icon: '🚀' },
  { name: 'MIT Tech Review', url: 'https://www.technologyreview.com/feed/', icon: '🎓' },
]

export const INTEREST_TOPICS = [
  'AI/ML',
  'Startups',
  'Web Dev',
  'Mobile',
  'DevOps',
  'Security',
  'Design',
  'Open Source',
  'Crypto',
  'Science',
  'Business',
  'Gaming',
  'Hardware',
  'Programming',
]
