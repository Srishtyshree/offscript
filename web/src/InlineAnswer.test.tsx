import { describe, it, expect } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { InlineAnswer } from './components/QuestionForm'
import type { CardResponse } from './types/route'

const render = (response: CardResponse) =>
  renderToString(
    React.createElement(InlineAnswer, {
      response,
      onOpenReport: () => {},
      onAskAnother: () => {},
    }),
  )

const card = (route: CardResponse['route'], content: CardResponse['content']): CardResponse => ({
  kind: 'card',
  fit: 'ok',
  route,
  reason: 'Test reason.',
  content,
  request_id: 'req_test',
  latency_ms: 10,
})

describe('InlineAnswer and the optional outdoor step', () => {
  it('shows no step and no report button for an AI answer without a step', () => {
    const html = render(
      card('AI', { answer: 'Multiply the dollars by the current rate.', outdoor_action: null }),
    )
    expect(html).toContain('Multiply the dollars by the current rate.')
    expect(html).not.toContain('Outdoor Action')
    expect(html).not.toContain('Report Result')
    expect(html).toContain('Ask another question')
  })

  it('shows the step and the report button when an AI answer has a step', () => {
    const html = render(
      card('AI', {
        answer: 'Light bends as it enters the water.',
        outdoor_action: 'Dip a straight stick in a bucket of water and look from the side.',
      }),
    )
    expect(html).toContain('Outdoor Action')
    expect(html).toContain('Dip a straight stick')
    expect(html).toContain('Report Result')
  })

  it('cites the source and shows the local tip on a SEARCH answer without a step', () => {
    const html = render(
      card('SEARCH', {
        search_query: 'lalbagh open republic day',
        sources: [{ title: 'Lalbagh timings', url: 'https://www.karnatakatourism.org/lalbagh' }],
        search_url: 'https://www.google.com/search?q=lalbagh',
        outdoor_action: null,
        summary: 'Open 7 AM to 6 PM on Republic Day.',
        summary_source: 1,
        local_tip: 'Mornings are calmer.',
      }),
    )
    expect(html).toContain('According to <!-- -->karnatakatourism.org')
    expect(html).toContain('Local tip: <!-- -->Mornings are calmer.')
    expect(html).not.toContain('Outdoor Action')
    expect(html).not.toContain('Report Result')
  })

  it('says so when the search results do not clearly answer', () => {
    const html = render(
      card('SEARCH', {
        search_query: 'usd inr rate today',
        sources: [{ title: 'Rates', url: 'https://example.com/rates' }],
        search_url: 'https://www.google.com/search?q=usd+inr',
        outdoor_action: null,
        summary: null,
      }),
    )
    expect(html).toContain('The results don&#x27;t clearly answer this. Check the sources below.')
    expect(html).not.toContain('According to')
  })

  it('keeps the HUMAN ask and the report button even without an outdoor step', () => {
    const html = render(
      card('HUMAN', {
        who_to_ask: 'a current hostel resident',
        suggested_question: 'What does a normal week in the hostel feel like?',
        outdoor_action: null,
      }),
    )
    expect(html).toContain('a current hostel resident')
    expect(html).toContain('What does a normal week in the hostel feel like?')
    expect(html).not.toContain('Outdoor Action')
    expect(html).toContain('Report Result')
  })
})
