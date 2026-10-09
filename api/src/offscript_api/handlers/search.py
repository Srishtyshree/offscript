"""SEARCH route handler: web-search action/link (AGENTS.md A2, A3, B3, B9).

For finding where or when: hours, listings, events, prices, access.
Calls SerpApi when configured; returns honest web search action and search_url
without pretending a live lookup occurred if unconfigured or offline.
Returns search_limitation if search fails or returns no results.
"""

import urllib.parse

from offscript_api.clients.serpapi import (
    SerpApiClient,
    SerpApiError,
    SerpApiNotConfiguredError,
    SerpApiQuotaError,
    SerpApiTimeoutError,
)
from offscript_contract.route_dto import (
    CardResponse,
    GuardResponse,
    SearchCardContent,
    SearchSource,
)
from offscript_contract.router import Fit, Route, RouterInput


def build_search_query(question: str, context: str | None = None) -> str:
    """Construct an effective web search query from question and optional context."""
    q_clean = question.strip().rstrip("?.")
    if context and context != "none":
        ctx_clean = context.strip().rstrip("?.")
        # Combine if context not already included in question
        if ctx_clean.lower() not in q_clean.lower():
            return f"{q_clean} {ctx_clean}"
    return q_clean


def build_search_url(query: str) -> str:
    """Generate prefilled Google Search action URL."""
    encoded = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={encoded}"


async def handle_search_route(
    router_input: RouterInput,
    reason: str,
    request_id: str,
    latency_ms: int,
    serpapi_client: SerpApiClient | None = None,
) -> CardResponse | GuardResponse:
    """Handle SEARCH route with live SerpApi or honest web-search action link.

    - When SerpApi is configured: fetches top organic results.
      - If no results or error: returns search_limitation guard with prefilled search_url.
    - When SerpApi is NOT configured: returns search action with search_url and
      NO fabricated sources (honesty rule: do not pretend live lookup occurred).
    """
    search_query = build_search_query(
        router_input.question,
        router_input.context if router_input.context != "none" else None,
    )
    search_url = build_search_url(search_query)

    sources: list[SearchSource] = []

    # Attempt live SerpApi search if client is configured
    if serpapi_client is not None and serpapi_client.is_configured:
        try:
            sources = await serpapi_client.search(search_query, num_results=3)
            if not sources:
                # Evidence missing: return search_limitation per AGENTS.md B3.5
                return GuardResponse(
                    fit="search_limitation",
                    reason="No public search results found.",
                    message=(
                        "We couldn't confirm fresh public listings or hours automatically. "
                        "Check the search link directly before heading out."
                    ),
                    search_url=search_url,
                    request_id=request_id,
                    latency_ms=max(1, latency_ms),
                )
        except (SerpApiTimeoutError, SerpApiQuotaError, SerpApiError) as err:
            # Upstream search issue: return honest search_limitation with prefilled search link
            return GuardResponse(
                fit="search_limitation",
                reason=f"Search service limitation: {err}",
                message=(
                    "Public search lookup could not be completed right now. "
                    "Use the search link to check fresh details directly."
                ),
                search_url=search_url,
                request_id=request_id,
                latency_ms=max(1, latency_ms),
            )
        except SerpApiNotConfiguredError:
            sources = []

    # When no live search lookup was performed, sources is empty:
    # "do not pretend live lookup occurred" (Task A03 acceptance check)
    content = SearchCardContent(
        search_query=search_query,
        sources=sources,
        search_url=search_url,
        only_out_there="Live real-time venue crowding and weather conditions.",
        do_this="Check current schedule or hours using the search action, then head to the venue.",
    )

    return CardResponse(
        fit=Fit.OK,
        route=Route.SEARCH,
        reason=reason,
        content=content,
        request_id=request_id,
        latency_ms=max(1, latency_ms),
    )
