"""Tests for route DTO contract schemas."""

import pytest
from pydantic import ValidationError

from offscript_contract.route_dto import (
    AiCardContent,
    CardResponse,
    ErrorResponse,
    GuardResponse,
    RouteRequest,
    SearchCardContent,
    SearchSource,
)
from offscript_contract.router import Fit, Route


def test_route_request_validation():
    req = RouteRequest(question="How do I join a pickup game?", context="Campus court")
    assert req.question == "How do I join a pickup game?"
    assert req.context == "Campus court"

    with pytest.raises(ValidationError):
        RouteRequest(extra_field="invalid")  # type: ignore[call-arg]


def test_card_response_ai_serialization():
    card = CardResponse(
        fit=Fit.OK,
        route=Route.AI,
        reason="Generic etiquette on joining games.",
        content=AiCardContent(
            answer="Wait for a break between games and ask if you can join next.",
            only_out_there="Whether a game is currently playing.",
            do_this="Walk up to the court side and wait for the current game to end.",
        ),
        request_id="req_123",
        latency_ms=15,
    )
    assert card.kind == "card"
    assert card.route == Route.AI
    assert card.fit == Fit.OK


def test_card_response_search_serialization():
    card = CardResponse(
        fit=Fit.OK,
        route=Route.SEARCH,
        reason="Public schedule / hours inquiry.",
        content=SearchCardContent(
            search_query="Campus court public game hours this week",
            sources=[SearchSource(title="Campus Sports", url="https://example.com/sports")],
            search_url="https://www.google.com/search?q=campus+court",
            only_out_there="Weather conditions at the court.",
            do_this="Check the court board when you arrive.",
        ),
        request_id="req_456",
        latency_ms=25,
    )
    assert card.kind == "card"
    assert card.route == Route.SEARCH
    assert len(card.content.sources) == 1


def test_guard_response_serialization():
    guard = GuardResponse(
        fit=Fit.SCOPE_NUDGE,
        reason="Trivia or screen-complete question.",
        message="Offscript is for something you want to do or find out out there.",
        request_id="req_789",
        latency_ms=10,
    )
    assert guard.kind == "guard"
    assert guard.fit == Fit.SCOPE_NUDGE
    assert guard.route is None


def test_error_response_serialization():
    err = ErrorResponse.model_validate(
        {"error": {"code": "question_empty", "message": "Please enter a question."}}
    )
    assert err.error.code == "question_empty"
    assert err.error.message == "Please enter a question."
