import type { CardResponse, SearchContent } from '../types/route'

// The site the search summary relies on, e.g. "karnatakatourism.org", or null if unknown.
export function citedSite(content: SearchContent): string | null {
  const source = content.summary_source ? content.sources[content.summary_source - 1] : undefined
  if (!source) return null
  try {
    return new URL(source.url).hostname.replace(/^www\./, '')
  } catch {
    return null
  }
}

// Whether the result has a real-world step to report back on. An AI or SEARCH answer with no
// outdoor step is complete on screen; asking the person is always the step for HUMAN.
export function hasRealWorldStep(card: CardResponse): boolean {
  return card.route === 'HUMAN' || Boolean(card.content.outdoor_action)
}
