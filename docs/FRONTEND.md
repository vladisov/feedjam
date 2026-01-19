# Feedjam Frontend Guidelines

## Tech Stack
- React 19 with TypeScript 5.8
- Vite 6 for build tooling
- React Router 7 for routing
- TanStack Query 5 for data fetching
- Tailwind CSS 4 for styling
- Headless UI + Heroicons for components

## Project Structure
```
web/src/
├── components/
│   ├── feed/           # Feed-specific components
│   └── shared/         # Reusable UI components
├── pages/              # Route page components
├── hooks/              # Custom React hooks (queries, utilities)
├── api/                # API client
├── types/              # TypeScript type definitions
├── utils/              # Helper functions
├── App.tsx             # Root component with routing
├── main.tsx            # Entry point with providers
└── index.css           # Global styles and theme
```

## Export Conventions
- **Pages**: Default exports (for lazy loading compatibility)
- **Components**: Named exports

```tsx
// pages/FeedPage.tsx
export default function FeedPage() { ... }

// components/shared/Button.tsx
export function Button({ ... }: ButtonProps) { ... }
```

## Data Fetching Pattern

### Query Hook Structure
```tsx
// hooks/useFeedQuery.ts

// Constants at module level
const STALE_TIME = 2 * 60 * 1000      // 2 minutes
const REFETCH_INTERVAL = 5 * 60 * 1000 // 5 minutes

export function useFeedQuery(userId: number) {
  const query = useQuery({
    queryKey: ['feed', userId],
    queryFn: () => api.getFeed(userId),
    staleTime: STALE_TIME,
    refetchInterval: REFETCH_INTERVAL,
    enabled: !!userId,
  })

  // Return simplified interface
  return {
    items: query.data ?? [],           // Derived with default
    isLoading: query.isLoading,
    error: query.error?.message || null, // Normalized error
    refetch: query.refetch,
  }
}
```

### Mutations with Toast Notifications
```tsx
export function useSubscriptionsQuery() {
  const queryClient = useQueryClient()

  const addSubscription = useMutation({
    mutationFn: api.createSubscription,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscriptions'] })
      toast.success('Subscription added')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to add subscription')
    },
  })

  return {
    // ... query data
    addSubscription: addSubscription.mutate,  // Expose mutate function
    isAdding: addSubscription.isPending,
  }
}
```

### Query Key Conventions
- Single entity: `['users', userId]`
- List: `['subscriptions']`
- Filtered list: `['feed', userId]`

## Component Patterns

### Props Interface
Always use `interface` for props:
```tsx
interface UserCardProps {
  user: User
  onEdit?: (id: number) => void
}

export function UserCard({ user, onEdit }: UserCardProps) {
  return (...)
}
```

### forwardRef for Reusable Components
```tsx
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', children, ...props }, ref) => {
    return (
      <button ref={ref} className={...} {...props}>
        {children}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

### Button Variants and Sizes
```tsx
// Variants
variant: 'primary' | 'secondary' | 'ghost' | 'destructive'

// Sizes
size: 'sm' | 'md' | 'lg'
// sm: h-8 px-3 text-sm
// md: h-10 px-4
// lg: h-12 px-6 text-lg
```

## Page Layout Pattern

### Standard Page Structure
```tsx
export default function FeedPage() {
  const { items, isLoading, error, refetch } = useFeedQuery(userId)

  // Loading state (only on initial load)
  if (isLoading && items.length === 0) {
    return <LoadingSpinner />
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <p className="text-lg font-medium text-destructive">Error loading feed</p>
        <p className="text-sm text-muted-foreground">{error}</p>
        <Button onClick={() => refetch()} className="mt-4">Try again</Button>
      </div>
    )
  }

  // Empty state
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <NewspaperIcon className="mb-4 h-12 w-12 text-muted-foreground" />
        <p className="text-lg font-medium">No items yet</p>
        <p className="text-sm text-muted-foreground">Subscribe to sources to see items here</p>
      </div>
    )
  }

  // Content
  return (
    <div>
      {/* Page header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Your Feed</h2>
          <p className="text-sm text-muted-foreground">{items.length} items</p>
        </div>
        {/* Optional action buttons */}
      </div>

      {/* Page content */}
      <div>...</div>
    </div>
  )
}
```

## Theming System (Tailwind 4 + CSS Variables)

### Color Variables
Defined in `index.css`:
```css
:root {
  --background: 0 0% 100%;
  --foreground: 240 10% 3.9%;
  --primary: 240 5.9% 10%;
  --primary-foreground: 0 0% 98%;
  --muted: 240 4.8% 95.9%;
  --muted-foreground: 240 3.8% 46.1%;
  --destructive: 0 84.2% 60.2%;
  /* ... */
}

.dark {
  --background: 240 10% 3.9%;
  --foreground: 0 0% 98%;
  /* ... */
}
```

### Using Theme Colors
```tsx
// Use semantic color names
<p className="text-muted-foreground">Secondary text</p>
<button className="bg-primary text-primary-foreground">Action</button>
<span className="text-destructive">Error message</span>

// Feed-specific colors
<div className="bg-feed-unread">Unread item</div>
```

### Adding New Colors
1. Add CSS variable in `index.css` (both light and dark)
2. Add to Tailwind theme in `@theme inline` block
3. Use with `bg-[color]` or `text-[color]`

## Responsive Design

### Mobile Breakpoints
- `sm`: 640px (tablets)
- `md`: 768px (small laptops)
- `lg`: 1024px (desktops)

### Icon-Only Mobile Navigation
```tsx
const navItems = [
  { to: '/', label: 'Feed', icon: NewspaperIcon },
  { to: '/subscriptions', label: 'Subscriptions', icon: RssIcon },
]

// Hide label on mobile, show on sm+
<NavLink to={item.to}>
  <item.icon className="h-5 w-5" />
  <span className="hidden sm:inline">{item.label}</span>
</NavLink>
```

## Form Handling

### Simple Form Pattern
```tsx
const [newUrl, setNewUrl] = useState('')

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  if (newUrl.trim()) {
    addSubscription(newUrl.trim())
    setNewUrl('')  // Clear after submission
  }
}

return (
  <form onSubmit={handleSubmit} className="flex gap-2">
    <input
      value={newUrl}
      onChange={(e) => setNewUrl(e.target.value)}
      placeholder="Enter feed URL"
      className="flex-1 rounded-lg border px-3 py-2"
    />
    <Button type="submit" disabled={isAdding}>
      {isAdding ? 'Adding...' : 'Add'}
    </Button>
  </form>
)
```

## API Client

### Structure
```tsx
// api/api.ts
const API_URL = import.meta.env.VITE_API_URL || '/api'

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.text()
    throw new Error(error || `HTTP error ${response.status}`)
  }
  return response.json()
}

export const api = {
  getFeed: (userId: number) =>
    fetch(`${API_URL}/feeds/${userId}`).then(handleResponse<FeedItem[]>),

  createSubscription: (url: string) =>
    fetch(`${API_URL}/subscriptions/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    }).then(handleResponse<Subscription>),
}
```

### Environment Variables
```bash
# .env.local (for local dev outside Docker)
VITE_API_URL=http://localhost:8001

# In Docker, uses /api proxy (default)
```

## Utility Functions

### Date/Time Formatting
```tsx
// utils/format.ts
export function formatDate(date: Date | string): string {
  return new Date(date).toLocaleDateString()  // MM/DD/YYYY
}

export function formatRelativeTime(date: Date | string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000)

  if (seconds < 60) return 'just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`
  return `${Math.floor(seconds / 86400)}d ago`
}
```

### Conditional Classes
```tsx
import { clsx } from 'clsx'

<div className={clsx(
  'p-4 rounded-lg',
  isRead && 'opacity-60',
  isSelected && 'ring-2 ring-primary'
)}>
```

## Routing

### Route Setup
```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<FeedPage />} />
          <Route path="/subscriptions" element={<SubscriptionsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

### Navigation Links
```tsx
import { NavLink } from 'react-router-dom'

<NavLink
  to="/"
  className={({ isActive }) => clsx(
    'flex items-center gap-2 px-3 py-2 rounded-lg',
    isActive ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
  )}
>
  Feed
</NavLink>
```

## Search

Client-side search with operators in `lib/search.ts`:
- `is:liked`, `is:read`, `is:saved`, `is:hidden` - filter by state
- `source:name` - filter by source
- `"phrase"` - exact match
- Free text searches title/summary

Example: `is:liked source:hackernews rust`

## State Management

- **Server state**: TanStack Query (caching, refetching, mutations)
- **Local UI state**: React useState/useReducer
- **Form state**: Controlled inputs with useState
- **No Redux** - TanStack Query handles most needs

## Code Style

### TypeScript
- Strict mode enabled
- Use `interface` for object shapes
- Use `type` for unions/aliases
- Explicit return types on exported functions

### ESLint Rules
- React hooks rules enforced
- No unused variables/parameters
- React Refresh warnings for HMR compatibility
