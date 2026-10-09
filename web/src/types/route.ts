export type Fit =
  | 'ok'
  | 'scope_nudge'
  | 'context_request'
  | 'split_request'
  | 'safety_guidance'
  | 'refusal'
  | 'search_limitation'

export type Route = 'AI' | 'SEARCH' | 'HUMAN'

export interface SearchSource {
  title: string
  url: string
}

export interface AiContent {
  answer: string
  only_out_there: string
  do_this: string
}

export interface SearchContent {
  search_query: string
  sources: SearchSource[]
  search_url: string
  only_out_there: string
  do_this: string
}

export interface HumanContent {
  who_to_ask: string
  suggested_question: string
  only_out_there: string
  do_this: string
}

export interface CardResponse {
  kind: 'card'
  fit: 'ok'
  route: Route
  reason: string
  content: AiContent | SearchContent | HumanContent
  request_id: string
  latency_ms: number
}

export interface GuardResponse {
  kind: 'guard'
  fit: Fit
  route: null
  reason: string
  message: string
  suggested_question?: string
  search_url?: string
  request_id: string
  latency_ms: number
}

export interface ErrorResponse {
  error: {
    code: string
    message: string
  }
}

export type RouteResponse = CardResponse | GuardResponse
