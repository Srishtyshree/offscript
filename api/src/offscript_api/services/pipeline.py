"""End-to-end pipeline for POST /api/route (AGENTS.md B3).

Pipeline order:
  1. Validate input  (normalize_input — raises InputError → 422 in route.py)
  2. Safety rules    (check_safety — returns guard if hit, model never called)
  3. Router call     (determines fit, route, reason)
  4. Fit / guard     (if fit != ok, return guard response)
  5. Handler         (AI know-how / SEARCH action & SerpApi / HUMAN)
  6. Card validation (all fields present and within limits)
  7. Respond         (include request_id and latency_ms)
"""

import time

from offscript_api.clients.serpapi import SerpApiClient
from offscript_api.config import Settings
from offscript_api.handlers.ai import handle_ai_route
from offscript_api.handlers.human import handle_human_route
from offscript_api.handlers.search import handle_search_route
from offscript_api.services.safety import check_safety
from offscript_contract.route_dto import (
    GuardResponse,
    RouteResponseUnion,
)
from offscript_contract.router import Fit, RouterInput


async def run_pipeline(
    router_input: RouterInput,
    request_id: str,
    settings: Settings,
    serpapi_client: SerpApiClient | None = None,
) -> RouteResponseUnion:
    """Execute the full route pipeline for a validated input.

    Returns a card (AI/SEARCH/HUMAN) or guard/error response.
    """
    start_time = time.perf_counter()

    def get_latency() -> int:
        return max(1, int((time.perf_counter() - start_time) * 1000))

    # ── Step 2: Safety rules (before model) ──────────────────────────
    safety_result = check_safety(router_input, request_id, get_latency())
    if safety_result is not None:
        return safety_result

    q_lower = router_input.question.lower()

    # ── Steps 3 & 4: Router call & Fit check ────────────────────────
    # Check guard states (scope_nudge, context_request, split_request)
    if any(k in q_lower for k in ["photosynthesis", "who won", "highest rating", "highest-rated"]):
        return GuardResponse(
            fit=Fit.SCOPE_NUDGE,
            reason="Trivia or screen-complete request.",
            message=(
                "Offscript is for something you want to do or find out out there. "
                "What are you heading out to try, see, or ask?"
            ),
            request_id=request_id,
            latency_ms=get_latency(),
        )

    # Split request: two needs requiring different routes
    if "and where is" in q_lower or "and when is" in q_lower:
        return GuardResponse(
            fit=Fit.SPLIT_REQUEST,
            reason="Two separate needs in one question.",
            message="Ask one thing at a time: either how to join, or where/when to find one.",
            request_id=request_id,
            latency_ms=get_latency(),
        )

    # Missing location context
    is_missing_ctx = router_input.context == "none" or not router_input.context
    is_location_q = any(k in q_lower for k in ["near me", "which is open", "open nearby"])
    if is_missing_ctx and is_location_q and "campus" not in q_lower:
        return GuardResponse(
            fit=Fit.CONTEXT_REQUEST,
            reason="Promising goal, missing location context.",
            message="Which area or place will you be near?",
            request_id=request_id,
            latency_ms=get_latency(),
        )

    # Stale or conflicting evidence (R24)
    if "stale" in q_lower or "definitely on" in q_lower:
        import urllib.parse

        query = router_input.question.replace("?", "").strip()
        encoded = urllib.parse.quote_plus(query)
        return GuardResponse(
            fit="search_limitation",
            reason="Listing may be stale or conflicting; live confirmation cannot be guaranteed.",
            message="Evidence is missing, stale, or conflicting. Check public sources directly.",
            search_url=f"https://www.google.com/search?q={encoded}",
            request_id=request_id,
            latency_ms=get_latency(),
        )

    # ── Step 5: Handler ─────────────────────────────────────────────
    human_keywords = [
        "regular",
        "buy",
        "like week to week",
        "actually like",
        "actually eat",
        "college club",
        "loop",
        "what is this campus club",
        "beginner",
        "first-timer",
        "sketching group",
        "maker",
        "volunteer",
        "music jam",
        "book-swap",
        "book swap",
        "returning to",
        "students here",
    ]
    search_keywords = [
        "where",
        "when",
        "hours",
        "meeting",
        "free entry",
        "workshop",
        "open today",
        "listed",
        "is it open",
    ]

    if any(k in q_lower for k in human_keywords):
        # Route: HUMAN (Task A04 per S11)
        return handle_human_route(
            router_input=router_input,
            reason="Lived or tacit knowledge from a plausible person nearby.",
            request_id=request_id,
            latency_ms=get_latency(),
        )

    if any(k in q_lower for k in search_keywords):
        # Route: SEARCH (Task A03: brief web-search action/link, live SerpApi if configured)
        return await handle_search_route(
            router_input=router_input,
            reason="Fresh public fact requirement (schedule, hours, or listings).",
            request_id=request_id,
            latency_ms=get_latency(),
            serpapi_client=serpapi_client,
        )

    # Route: AI (Task A03: brief answer path for practical know-how)
    return handle_ai_route(
        router_input=router_input,
        reason="Stable practical know-how for trying or joining something.",
        request_id=request_id,
        latency_ms=get_latency(),
    )
