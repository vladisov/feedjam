import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  NewspaperIcon,
  RssIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from './Button'

const navItems = [
  { to: '/', label: 'Feed', icon: NewspaperIcon },
  { to: '/subscriptions', label: 'Subscriptions', icon: RssIcon },
  { to: '/settings', label: 'Settings', icon: Cog6ToothIcon },
]

export function MainLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/50 bg-background/80 backdrop-blur-xl backdrop-saturate-150">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between gap-2 px-4 sm:px-6">
          <h1 className="flex-shrink-0 text-lg sm:text-xl font-bold tracking-tight text-foreground">FeedJam</h1>
          <div className="flex items-center gap-2 sm:gap-4 overflow-hidden">
            <nav className="flex items-center gap-1">
              {navItems.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center gap-1.5 rounded-xl px-2.5 sm:px-3 py-2 text-sm font-medium transition-all',
                      isActive
                        ? 'bg-secondary text-foreground shadow-sm'
                        : 'text-muted-foreground hover:bg-secondary/50 hover:text-foreground'
                    )
                  }
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span className="hidden sm:inline">{label}</span>
                </NavLink>
              ))}
            </nav>
            <div className="flex flex-shrink-0 items-center gap-2">
              <span className="hidden text-sm text-muted-foreground md:inline truncate max-w-[150px]">
                {user?.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleLogout}
                className="gap-1.5 px-2 text-muted-foreground hover:text-foreground"
              >
                <ArrowRightOnRectangleIcon className="h-4 w-4" />
                <span className="hidden sm:inline">Logout</span>
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-4xl px-4 sm:px-6 py-6">
        <Outlet />
      </main>
    </div>
  )
}
