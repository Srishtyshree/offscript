import './LandingPage.css'

interface LandingPageProps {
  onStart: () => void
}

export function LandingPage({ onStart }: LandingPageProps) {
  return (
    <section className="landing-page" aria-labelledby="landing-title">
      <div className="brand-logo" aria-label="Offscript">
        <div className="brand-icon" aria-hidden="true">
          <span>O</span>
        </div>
        <span className="brand-title">Offscript</span>
      </div>
      <h1 id="landing-title">AI that knows when to get you off the screen.</h1>
      <p>Ask anything. Get a useful answer and a next step into the real world when it matters.</p>
      <button className="submit-btn" type="button" onClick={onStart}>
        Hop onto it →
      </button>
    </section>
  )
}
