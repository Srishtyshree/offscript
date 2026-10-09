"""Mock router service for Task A01 (development and test mode).

Generates realistic dummy AI, SEARCH, HUMAN, and Guard responses without requiring live API keys.
"""

import time
import uuid

from offscript_contract.route_dto import (
    AiCardContent,
    CardResponse,
    GuardResponse,
    HumanCardContent,
    RouteResponseUnion,
    SearchCardContent,
)
from offscript_contract.router import Fit, Route, RouterInput


def handle_mock_route(
    router_input: RouterInput,
    request_id: str | None = None,
) -> RouteResponseUnion:
    """Return realistic mock response for input."""
    req_id = request_id or f"mock_{uuid.uuid4().hex[:12]}"
    start_time = time.perf_counter()

    q_lower = router_input.question.lower()

    # Rule 1: Safety & Refusal checks
    if any(k in q_lower for k in ["woman sitting alone", "harass", "stalk", "private property"]):
        latency = int((time.perf_counter() - start_time) * 1000)
        return GuardResponse(
            fit="refusal",
            reason="Safety rule: intrusive or harassing request.",
            message=(
                "Offscript cannot fulfill requests that involve intrusive, "
                "harassing, or targeting behavior."
            ),
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    if any(k in q_lower for k in ["shortcut", "dark", "unsafe", "medicine", "doctor", "emergency"]):
        latency = int((time.perf_counter() - start_time) * 1000)
        return GuardResponse(
            fit="safety_guidance",
            reason="Safety guidance rule triggered for safety or health risk.",
            message=(
                "Please seek professional advice or emergency services for "
                "medical, safety, or legal concerns."
            ),
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    # Rule 2: Guard states (Scope Nudge & Context Request)
    if "photosynthesis" in q_lower or "who won" in q_lower or "highest rating" in q_lower:
        latency = int((time.perf_counter() - start_time) * 1000)
        return GuardResponse(
            fit=Fit.SCOPE_NUDGE,
            reason="Trivia or screen-complete request.",
            message=(
                "Offscript is for something you want to do or find out out there. "
                "What are you heading out to try, see, or ask?"
            ),
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    is_missing_ctx = router_input.context == "none"
    is_location_q = "near me" in q_lower or "open" in q_lower
    if is_missing_ctx and is_location_q and "campus" not in q_lower:
        latency = int((time.perf_counter() - start_time) * 1000)
        return GuardResponse(
            fit=Fit.CONTEXT_REQUEST,
            reason="Promising goal, missing location context.",
            message="Which area or place will you be near?",
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    # Rule 3: HUMAN route
    human_keywords = ["regular", "buy", "like week to week", "actually eat", "loop"]
    if any(k in q_lower for k in human_keywords):
        latency = int((time.perf_counter() - start_time) * 1000)
        return CardResponse(
            fit=Fit.OK,
            route=Route.HUMAN,
            reason="Lived or tacit knowledge from a plausible person nearby.",
            content=HumanCardContent(
                who_to_ask="A regular vendor or customer",
                suggested_question="What do you usually recommend ordering here?",
                only_out_there="Tacit experience and personal recommendations.",
                do_this="Step up to the counter and ask the vendor when it's quiet.",
            ),
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    # Rule 4: SEARCH route
    search_keywords = ["where", "when", "hours", "meeting", "free entry", "workshop", "open today"]
    if any(k in q_lower for k in search_keywords):
        latency = int((time.perf_counter() - start_time) * 1000)
        encoded_q = router_input.question.replace(" ", "+")
        return CardResponse(
            fit=Fit.OK,
            route=Route.SEARCH,
            reason="Fresh public fact requirement (schedule/hours/listings).",
            content=SearchCardContent(
                search_query=router_input.question,
                sources=[],
                search_url=f"https://www.google.com/search?q={encoded_q}",
                only_out_there="Live real-time venue crowding and weather.",
                do_this="Head to the location listed in the schedule.",
            ),
            request_id=req_id,
            latency_ms=max(1, latency),
        )

    # Rule 5: Default AI route (Know-how)
    latency = int((time.perf_counter() - start_time) * 1000)
    return CardResponse(
        fit=Fit.OK,
        route=Route.AI,
        reason="Stable practical know-how for trying or joining something.",
        content=AiCardContent(
            answer=(
                "Wait for a pause between games, approach politely, and ask if "
                "you can join the next round."
            ),
            only_out_there="Whether a game is currently playing right now.",
            do_this="Walk up to the court side and wait for the current game to pause.",
        ),
        request_id=req_id,
        latency_ms=max(1, latency),
    )
