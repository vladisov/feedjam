import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { CheckIcon } from '@heroicons/react/24/outline'

import { Button } from '@/components/shared/Button'
import { INTEREST_TOPICS, SUGGESTED_FEEDS, type SuggestedFeed } from '@/config/onboarding'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'

const STEPS = [1, 2, 3] as const
type Step = (typeof STEPS)[number]

export default function OnboardingPage() {
  const [step, setStep] = useState<Step>(1)
  const [selectedFeeds, setSelectedFeeds] = useState<string[]>([])
  const [selectedInterests, setSelectedInterests] = useState<string[]>([])
  const [error, setError] = useState<string | null>(null)

  const navigate = useNavigate()
  const { refreshUser } = useAuth()

  const batchSubscribeMutation = useMutation({
    mutationFn: (urls: string[]) => api.batchSubscribe(urls),
  })

  const saveInterestsMutation = useMutation({
    mutationFn: (interests: { topic: string; weight: number }[]) => api.replaceInterests(interests),
  })

  const completeOnboardingMutation = useMutation({
    mutationFn: () => api.completeOnboarding(),
  })

  function toggleSelection<T>(setter: React.Dispatch<React.SetStateAction<T[]>>, item: T): void {
    setter((prev) => (prev.includes(item) ? prev.filter((i) => i !== item) : [...prev, item]))
  }

  function toggleFeed(url: string): void {
    toggleSelection(setSelectedFeeds, url)
  }

  function toggleInterest(topic: string): void {
    toggleSelection(setSelectedInterests, topic)
  }

  async function handleFinish(): Promise<void> {
    setError(null)

    try {
      if (selectedFeeds.length > 0) {
        await batchSubscribeMutation.mutateAsync(selectedFeeds)
      }

      if (selectedInterests.length > 0) {
        const interests = selectedInterests.map((topic) => ({ topic, weight: 1.0 }))
        await saveInterestsMutation.mutateAsync(interests)
      }

      await completeOnboardingMutation.mutateAsync()
      await refreshUser()
      navigate('/', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    }
  }

  const isLoading =
    batchSubscribeMutation.isPending ||
    saveInterestsMutation.isPending ||
    completeOnboardingMutation.isPending

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-2xl space-y-8">
        <div className="flex items-center justify-center gap-2">
          {STEPS.map((s) => (
            <div
              key={s}
              className={`h-2 w-12 rounded-full transition-colors ${
                s <= step ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {error && (
          <div className="rounded-lg bg-destructive/10 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        {/* Step 1: Welcome */}
        {step === 1 && (
          <div className="space-y-6 text-center">
            <h1 className="text-4xl font-bold text-foreground">Welcome to FeedJam</h1>
            <p className="text-lg text-muted-foreground">
              Your personal feed aggregator. Let's set up your feeds.
            </p>
            <Button size="lg" onClick={() => setStep(2)} className="mt-8">
              Get Started
            </Button>
          </div>
        )}

        {/* Step 2: Pick Feeds */}
        {step === 2 && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-foreground">Pick some feeds to follow</h2>
              <p className="mt-2 text-muted-foreground">
                Select at least one feed to get started. You can add more later.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              {SUGGESTED_FEEDS.map((feed: SuggestedFeed) => {
                const isSelected = selectedFeeds.includes(feed.url)
                return (
                  <button
                    key={feed.url}
                    onClick={() => toggleFeed(feed.url)}
                    className={`flex items-center gap-3 rounded-lg border p-4 text-left transition-colors ${
                      isSelected
                        ? 'border-primary bg-primary/10'
                        : 'border-border bg-card hover:border-muted-foreground'
                    }`}
                  >
                    <span className="text-2xl">{feed.icon}</span>
                    <span className="flex-1 font-medium text-foreground">{feed.name}</span>
                    {isSelected && <CheckIcon className="h-5 w-5 text-primary" />}
                  </button>
                )
              })}
            </div>

            <div className="flex justify-between pt-4">
              <Button variant="ghost" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={() => setStep(3)} disabled={selectedFeeds.length === 0}>
                Continue
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Pick Interests */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-foreground">What topics interest you?</h2>
              <p className="mt-2 text-muted-foreground">
                Select topics to personalize your feed ranking. This is optional.
              </p>
            </div>

            <div className="flex flex-wrap justify-center gap-2">
              {INTEREST_TOPICS.map((topic) => {
                const isSelected = selectedInterests.includes(topic)
                return (
                  <button
                    key={topic}
                    onClick={() => toggleInterest(topic)}
                    className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                      isSelected
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                    }`}
                  >
                    {topic}
                  </button>
                )
              })}
            </div>

            <div className="flex justify-between pt-4">
              <Button variant="ghost" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button onClick={handleFinish} disabled={isLoading}>
                {isLoading ? 'Setting up...' : 'Finish Setup'}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
