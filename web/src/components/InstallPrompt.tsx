import React, { useEffect, useState } from 'react'
import { isIosDevice, isStandaloneMode } from '../pwa'

interface BeforeInstallPromptEvent extends Event {
  readonly platforms: string[]
  readonly userChoice: Promise<{
    outcome: 'accepted' | 'dismissed'
    platform: string
  }>
  prompt(): Promise<void>
}

function checkInitialDismissed(): boolean {
  if (typeof window === 'undefined') return true
  if (isStandaloneMode()) return true
  try {
    return localStorage.getItem('offscript_pwa_prompt_dismissed') === 'true'
  } catch {
    return false
  }
}

export const InstallPrompt: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isDismissed, setIsDismissed] = useState<boolean>(checkInitialDismissed)
  const showIosTip = isIosDevice() && !isStandaloneMode()

  useEffect(() => {
    if (isStandaloneMode()) return

    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
      setIsDismissed(false)
    }

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
    }
  }, [])

  const handleDismiss = () => {
    setIsDismissed(true)
    try {
      localStorage.setItem('offscript_pwa_prompt_dismissed', 'true')
    } catch {
      // ignore storage errors
    }
  }

  const handleInstallClick = async () => {
    if (!deferredPrompt) return

    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice
    if (outcome === 'accepted') {
      setIsDismissed(true)
    }
    setDeferredPrompt(null)
  }

  if (isDismissed || (!deferredPrompt && !showIosTip)) {
    return null
  }

  return (
    <aside className="pwa-install-banner" aria-label="Install Offscript App">
      <div className="pwa-install-content">
        <div className="pwa-install-icon">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </div>
        <div className="pwa-install-text">
          <span className="pwa-install-title">Install Offscript</span>
          <span className="pwa-install-subtitle">
            {showIosTip ? (
              <>
                Tap <strong className="pwa-key">Share ⎋</strong> then{' '}
                <strong className="pwa-key">Add to Home Screen ⊞</strong>
              </>
            ) : (
              'Add to home screen for instant full-screen access'
            )}
          </span>
        </div>
      </div>

      <div className="pwa-install-actions">
        {deferredPrompt && (
          <button
            type="button"
            className="pwa-install-btn"
            onClick={handleInstallClick}
            aria-label="Install App"
          >
            Install
          </button>
        )}
        <button
          type="button"
          className="pwa-dismiss-btn"
          onClick={handleDismiss}
          aria-label="Dismiss install prompt"
          title="Dismiss"
        >
          ✕
        </button>
      </div>
    </aside>
  )
}
