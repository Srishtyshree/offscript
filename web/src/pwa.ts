/**
 * PWA Service Worker Registration & Installation utilities
 */

export function registerServiceWorker(): void {
  if (typeof window === 'undefined') return

  if ('serviceWorker' in navigator && import.meta.env.PROD) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch((err) => {
        // Silent fallback in development or restricted environments
        console.debug('Service Worker registration skipped:', err)
      })
    })
  }
}

export function isStandaloneMode(): boolean {
  if (typeof window === 'undefined') return false

  const isStandaloneMedia = window.matchMedia('(display-mode: standalone)').matches
  const isIosStandalone =
    'standalone' in window.navigator &&
    Boolean((window.navigator as unknown as { standalone?: boolean }).standalone)

  return isStandaloneMedia || isIosStandalone
}

export function isIosDevice(): boolean {
  if (typeof window === 'undefined') return false
  const userAgent = window.navigator.userAgent.toLowerCase()
  return /iphone|ipad|ipod/.test(userAgent)
}
