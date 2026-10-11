import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderToString } from 'react-dom/server'
import React from 'react'
import { InstallPrompt } from './components/InstallPrompt'
import { isIosDevice, isStandaloneMode } from './pwa'

describe('PWA Integration & Installation Prompt', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders null when dismissed or standalone', () => {
    // In server-side rendering or default initial dismissed state, renders null
    const html = renderToString(React.createElement(InstallPrompt))
    expect(html).toBe('')
  })

  it('isStandaloneMode returns false when window is undefined or display-mode is not standalone', () => {
    expect(isStandaloneMode()).toBe(false)
  })

  it('isIosDevice handles non-iOS user agents', () => {
    expect(isIosDevice()).toBe(false)
  })
})
