import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/shared/Button'
import { SunIcon, MoonIcon, PlusIcon, XMarkIcon, CheckIcon, KeyIcon } from '@heroicons/react/24/outline'
import { api } from '@/lib/api'
import type { UserInterest, UserInterestIn, UserSettingsIn } from '@/types/feed'
import { toast } from 'sonner'

const USER_ID = 1 // TODO: Get from auth context

function getInitialTheme(): boolean {
  if (typeof window === 'undefined') return false
  const saved = localStorage.getItem('theme')
  if (saved === 'dark') return true
  if (saved === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [isDark, setIsDark] = useState(getInitialTheme)
  const [newTopic, setNewTopic] = useState('')
  const [newWeight, setNewWeight] = useState(1.0)
  const [apiKey, setApiKey] = useState('')

  const { data: interests = [], isLoading } = useQuery({
    queryKey: ['interests', USER_ID],
    queryFn: () => api.getInterests(USER_ID),
  })

  const { data: settings } = useQuery({
    queryKey: ['settings', USER_ID],
    queryFn: () => api.getSettings(USER_ID),
  })

  const addInterestMutation = useMutation({
    mutationFn: (interest: UserInterestIn) => api.addInterest(USER_ID, interest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interests', USER_ID] })
      setNewTopic('')
      setNewWeight(1.0)
    },
  })

  const deleteInterestMutation = useMutation({
    mutationFn: (interestId: number) => api.deleteInterest(USER_ID, interestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interests', USER_ID] })
    },
  })

  const updateSettingsMutation = useMutation({
    mutationFn: (settingsIn: UserSettingsIn) => api.updateSettings(USER_ID, settingsIn),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', USER_ID] })
      setApiKey('')
      toast.success('API key saved')
    },
    onError: () => {
      toast.error('Failed to save API key')
    },
  })

  const handleAddInterest = (e: React.FormEvent): void => {
    e.preventDefault()
    if (newTopic.trim()) {
      addInterestMutation.mutate({ topic: newTopic.trim(), weight: newWeight })
    }
  }

  const handleSaveApiKey = (e: React.FormEvent): void => {
    e.preventDefault()
    updateSettingsMutation.mutate({ openai_api_key: apiKey || null })
  }

  const handleRemoveApiKey = (): void => {
    updateSettingsMutation.mutate({ openai_api_key: '' })
  }

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark)
    localStorage.setItem('theme', isDark ? 'dark' : 'light')
  }, [isDark])

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
        {/* Interests */}
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-lg font-medium text-foreground">Interests</h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Add topics you're interested in. Stories matching these topics will rank higher in your feed.
          </p>

          {/* Add interest form */}
          <form onSubmit={handleAddInterest} className="mb-4 flex gap-2">
            <input
              type="text"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              placeholder="e.g., python, rust, machine-learning"
              className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            <select
              value={newWeight}
              onChange={(e) => setNewWeight(parseFloat(e.target.value))}
              className="rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value={0.5}>Low (0.5x)</option>
              <option value={1.0}>Normal (1x)</option>
              <option value={1.5}>High (1.5x)</option>
              <option value={2.0}>Very High (2x)</option>
            </select>
            <Button
              type="submit"
              disabled={!newTopic.trim() || addInterestMutation.isPending}
              className="gap-1"
            >
              <PlusIcon className="h-4 w-4" />
              Add
            </Button>
          </form>

          {/* Interest list */}
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading interests...</p>
          ) : interests.length === 0 ? (
            <p className="text-sm text-muted-foreground">No interests added yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {interests.map((interest: UserInterest) => (
                <div
                  key={interest.id}
                  className="flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1"
                >
                  <span className="text-sm text-foreground">{interest.topic}</span>
                  <span className="text-xs text-muted-foreground">({interest.weight}x)</span>
                  <button
                    onClick={() => deleteInterestMutation.mutate(interest.id)}
                    disabled={deleteInterestMutation.isPending}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <XMarkIcon className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* API Keys */}
        <section className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-lg font-medium text-foreground">API Keys</h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Provide your own API keys for AI-powered features like summarization and intelligent ranking.
          </p>

          <div className="space-y-4">
            {/* OpenAI API Key */}
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                OpenAI API Key
              </label>
              {settings?.has_openai_key ? (
                <div className="flex items-center gap-2">
                  <div className="flex flex-1 items-center gap-2 rounded-md border border-border bg-secondary px-3 py-2">
                    <KeyIcon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Key configured</span>
                    <CheckIcon className="h-4 w-4 text-green-500" />
                  </div>
                  <Button
                    variant="secondary"
                    onClick={handleRemoveApiKey}
                    disabled={updateSettingsMutation.isPending}
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSaveApiKey} className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                  <Button
                    type="submit"
                    disabled={!apiKey.trim() || updateSettingsMutation.isPending}
                  >
                    Save
                  </Button>
                </form>
              )}
              <p className="mt-2 text-xs text-muted-foreground">
                Get your API key from{' '}
                <a
                  href="https://platform.openai.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline"
                >
                  platform.openai.com
                </a>
              </p>
            </div>
          </div>
        </section>

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
