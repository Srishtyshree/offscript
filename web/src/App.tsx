import { useEffect, useState } from 'react'
import { fetchHealth, type HealthResponse } from './api/health'

// Scaffold only: shows real backend readiness. Replaced by the app state machine (src/app/).
type Status =
  | { state: 'checking' }
  | { state: 'up'; health: HealthResponse }
  | { state: 'down'; message: string }

function App() {
  const [status, setStatus] = useState<Status>({ state: 'checking' })

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((health) => setStatus({ state: 'up', health }))
      .catch((error: unknown) => {
        if (controller.signal.aborted) return
        setStatus({
          state: 'down',
          message: error instanceof Error ? error.message : 'Unknown error',
        })
      })
    return () => controller.abort()
  }, [])

  return (
    <main>
      <h1>Offscript</h1>
      <p aria-live="polite">
        {status.state === 'checking' && 'Checking API…'}
        {status.state === 'up' &&
          `API ok (v${status.health.version}) · model ${status.health.model_configured ? 'configured' : 'not configured'}`}
        {status.state === 'down' && `API unreachable: ${status.message}`}
      </p>
    </main>
  )
}

export default App
