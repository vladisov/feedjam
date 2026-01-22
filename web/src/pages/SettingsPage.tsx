import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/shared/Button';
import {
  SunIcon,
  MoonIcon,
  PlusIcon,
  XMarkIcon,
  CheckIcon,
  KeyIcon,
  ClipboardIcon,
  ArrowPathIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline';
import { api } from '@/lib/api';
import type {
  UserInterest,
  UserInterestIn,
  UserSettingsIn,
} from '@/types/feed';
import { toast } from 'sonner';

function getInitialTheme(): boolean {
  if (typeof window === 'undefined') return false;
  const saved = localStorage.getItem('theme');
  if (saved === 'dark') return true;
  if (saved === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [isDark, setIsDark] = useState(getInitialTheme);
  const [newTopic, setNewTopic] = useState('');
  const [newWeight, setNewWeight] = useState(1.0);
  const [apiKey, setApiKey] = useState('');

  const { data: interests = [], isLoading } = useQuery({
    queryKey: ['interests'],
    queryFn: () => api.getInterests(),
  });

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: () => api.getSettings(),
  });

  const { data: inbox } = useQuery({
    queryKey: ['inbox'],
    queryFn: () => api.getInbox(),
  });

  const addInterestMutation = useMutation({
    mutationFn: (interest: UserInterestIn) => api.addInterest(interest),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interests'] });
      setNewTopic('');
      setNewWeight(1.0);
    },
  });

  const deleteInterestMutation = useMutation({
    mutationFn: (interestId: number) => api.deleteInterest(interestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['interests'] });
    },
  });

  const updateSettingsMutation = useMutation({
    mutationFn: (settingsIn: UserSettingsIn) => api.updateSettings(settingsIn),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setApiKey('');
      toast.success('API key saved');
    },
    onError: () => {
      toast.error('Failed to save API key');
    },
  });

  const regenerateInboxMutation = useMutation({
    mutationFn: () => api.regenerateInbox(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox'] });
      toast.success('Inbox address regenerated');
    },
    onError: () => {
      toast.error('Failed to regenerate inbox address');
    },
  });

  const handleAddInterest = (e: React.FormEvent): void => {
    e.preventDefault();
    if (newTopic.trim()) {
      addInterestMutation.mutate({ topic: newTopic.trim(), weight: newWeight });
    }
  };

  const handleSaveApiKey = (e: React.FormEvent): void => {
    e.preventDefault();
    updateSettingsMutation.mutate({ openai_api_key: apiKey || null });
  };

  const handleRemoveApiKey = (): void => {
    updateSettingsMutation.mutate({ openai_api_key: '' });
  };

  const handleCopyInbox = (): void => {
    if (!inbox?.inbox_address) return;

    navigator.clipboard
      .writeText(inbox.inbox_address)
      .then(() => toast.success('Copied to clipboard'))
      .catch(() => toast.error('Failed to copy to clipboard'));
  };

  const handleRegenerateInbox = (): void => {
    if (confirm('Are you sure? The old address will stop working.')) {
      regenerateInboxMutation.mutate();
    }
  };

  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDark);
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  }, [isDark]);

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
      <div className="space-y-4 sm:space-y-6">
        {/* Interests */}
        <section className="rounded-xl bg-card p-4 sm:p-6 shadow-sm ring-1 ring-border/50">
          <h3 className="mb-4 text-lg font-medium text-foreground">
            Interests
          </h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Add topics you're interested in. Stories matching these topics will
            rank higher in your feed.
          </p>

          {/* Add interest form */}
          <form
            onSubmit={handleAddInterest}
            className="mb-4 space-y-2 sm:space-y-0 sm:flex sm:gap-2"
          >
            <input
              type="text"
              value={newTopic}
              onChange={(e) => setNewTopic(e.target.value)}
              placeholder="e.g., python, rust, machine-learning"
              className="h-10 w-full sm:flex-1 rounded-xl bg-secondary/50 px-4 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:bg-card focus:outline-none focus:ring-1 focus:ring-border"
            />
            <div className="flex gap-2">
              <select
                value={newWeight}
                onChange={(e) => setNewWeight(parseFloat(e.target.value))}
                className="h-10 flex-1 sm:flex-none rounded-xl bg-secondary/50 px-3 text-sm text-foreground transition-all focus:bg-card focus:outline-none focus:ring-1 focus:ring-border"
              >
                <option value={0.5}>Low</option>
                <option value={1.0}>Normal</option>
                <option value={1.5}>High</option>
                <option value={2.0}>Very High</option>
              </select>
              <Button
                type="submit"
                disabled={!newTopic.trim() || addInterestMutation.isPending}
                className="gap-1"
              >
                <PlusIcon className="h-4 w-4" />
                <span className="hidden sm:inline">Add</span>
              </Button>
            </div>
          </form>

          {/* Interest list */}
          {isLoading ? (
            <p className="text-sm text-muted-foreground">
              Loading interests...
            </p>
          ) : interests.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No interests added yet.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {interests.map((interest: UserInterest) => (
                <div
                  key={interest.id}
                  className="flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1"
                >
                  <span className="text-sm text-foreground">
                    {interest.topic}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    ({interest.weight}x)
                  </span>
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

        {/* Email Inbox */}
        <section className="rounded-xl bg-card p-4 sm:p-6 shadow-sm ring-1 ring-border/50">
          <h3 className="mb-4 text-lg font-medium text-foreground">
            Email Inbox
          </h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Subscribe to newsletters using this address. Emails will appear in
            your feed.
          </p>

          {inbox?.inbox_address ? (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-2">
                <div className="flex min-w-0 flex-1 items-center gap-2 rounded-md border border-border bg-secondary px-3 py-2">
                  <EnvelopeIcon className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                  <code className="flex-1 truncate text-sm text-foreground">
                    {inbox.inbox_address}
                  </code>
                </div>
                <Button
                  variant="secondary"
                  onClick={handleCopyInbox}
                  className="gap-1 flex-shrink-0"
                >
                  <ClipboardIcon className="h-4 w-4" />
                  Copy
                </Button>
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:justify-between">
                <p className="text-xs text-muted-foreground">
                  Regenerating will invalidate the old address.
                </p>
                <Button
                  variant="secondary"
                  onClick={handleRegenerateInbox}
                  disabled={regenerateInboxMutation.isPending}
                  className="gap-1 flex-shrink-0"
                >
                  <ArrowPathIcon className="h-4 w-4" />
                  Regenerate
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Loading inbox address...
            </p>
          )}
        </section>

        {/* API Keys */}
        <section className="rounded-xl bg-card p-4 sm:p-6 shadow-sm ring-1 ring-border/50">
          <h3 className="mb-4 text-lg font-medium text-foreground">API Keys</h3>
          <p className="mb-4 text-sm text-muted-foreground">
            Provide your own API keys for AI-powered features like summarization
            and intelligent ranking.
          </p>

          <div className="space-y-4">
            {/* OpenAI API Key */}
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                OpenAI API Key
              </label>
              {settings?.has_openai_key ? (
                <div className="flex flex-col sm:flex-row gap-2">
                  <div className="flex flex-1 items-center gap-2 rounded-md border border-border bg-secondary px-3 py-2">
                    <KeyIcon className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      Key configured
                    </span>
                    <CheckIcon className="h-4 w-4 flex-shrink-0 text-green-500" />
                  </div>
                  <Button
                    variant="secondary"
                    onClick={handleRemoveApiKey}
                    disabled={updateSettingsMutation.isPending}
                    className="flex-shrink-0"
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <form
                  onSubmit={handleSaveApiKey}
                  className="flex flex-col sm:flex-row gap-2"
                >
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="sk-..."
                    className="h-10 w-full sm:flex-1 rounded-xl bg-secondary/50 px-4 text-sm text-foreground placeholder:text-muted-foreground transition-all focus:bg-card focus:outline-none focus:ring-1 focus:ring-border"
                  />
                  <Button
                    type="submit"
                    disabled={
                      !apiKey.trim() || updateSettingsMutation.isPending
                    }
                    className="flex-shrink-0"
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
        <section className="rounded-xl bg-card p-4 sm:p-6 shadow-sm ring-1 ring-border/50">
          <h3 className="mb-4 text-lg font-medium text-foreground">
            Appearance
          </h3>
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
      </div>
    </div>
  );
}
