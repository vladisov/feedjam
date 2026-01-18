import { useState, useEffect } from 'react'
import { Button } from '@/components/shared/Button'
import { SunIcon, MoonIcon } from '@heroicons/react/24/outline'

export default function SettingsPage() {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return document.documentElement.classList.contains('dark')
    }
    return false
  })

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  // Initialize theme from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark') {
      setIsDark(true)
    } else if (saved === 'light') {
      setIsDark(false)
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setIsDark(true)
    }
  }, [])

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-foreground">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Customize your feed reader
        </p>
      </div>

      {/* Settings sections */}
      <div className="space-y-6">
        {/* Appearance */}
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-lg font-medium text-foreground">Appearance</h3>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-foreground">Theme</p>
              <p className="text-sm text-muted-foreground">
                Choose between light and dark mode
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => setIsDark(!isDark)}
              className="gap-2"
            >
              {isDark ? (
                <>
                  <SunIcon className="h-4 w-4" />
                  Light
                </>
              ) : (
                <>
                  <MoonIcon className="h-4 w-4" />
                  Dark
                </>
              )}
            </Button>
          </div>
        </section>

        {/* About */}
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-lg font-medium text-foreground">About</h3>
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>
              <span className="font-medium text-foreground">FeedJam</span> - Personal feed aggregator
            </p>
            <p>
              Built with FastAPI, React, and TanStack Query
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
