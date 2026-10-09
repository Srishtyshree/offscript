import type { RouteResponse } from '../types/route'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export async function submitRouteRequest(
  question: string,
  context?: string,
  signal?: AbortSignal,
): Promise<RouteResponse> {
  const response = await fetch(`${API_BASE_URL}/api/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      context: context && context.trim() ? context.trim() : undefined,
    }),
    signal,
  })

  const data = await response.json()

  if (!response.ok) {
    const errorMsg = data?.error?.message || `Error ${response.status}: Request failed`
    throw new Error(errorMsg)
  }

  return data as RouteResponse
}
