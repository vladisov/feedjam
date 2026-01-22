import { DevicePhoneMobileIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { useInstallPrompt } from '@/hooks/useInstallPrompt'

export function InstallPrompt(): React.ReactElement | null {
  const { canInstall, promptInstall, dismiss } = useInstallPrompt()

  if (!canInstall) return null

  return (
    <div className="fixed bottom-20 left-4 right-4 z-50 mx-auto max-w-sm animate-in slide-in-from-bottom duration-300 sm:left-auto sm:right-4">
      <div className="flex items-center gap-3 rounded-xl bg-card p-4 shadow-lg ring-1 ring-border/50">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
          <DevicePhoneMobileIcon className="h-5 w-5 text-primary" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-foreground">Install FeedJam</p>
          <p className="text-xs text-muted-foreground">Add to home screen for the best experience</p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-1">
          <button
            onClick={promptInstall}
            className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Install
          </button>
          <button
            onClick={dismiss}
            className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
