"""Unit tests for S11 HUMAN route handler (Task A04, S11 spec, AGENTS.md A2, A3, B3)."""

import pytest
from fastapi.testclient import TestClient

from offscript_api.handlers.human import (
    generate_human_card_content,
    handle_human_route,
    validate_human_content,
)
from offscript_api.main import app
from offscript_contract.route_dto import HumanCardContent
from offscript_contract.router import Fit, Route, RouterInput

client = TestClient(app)


# ── S11 Worked Examples & Reference Cases ───────────────────────────


def test_s11_outdoor_court_beginner():
    """R12 & S11 worked example 1: Court beginner."""
    content = generate_human_card_content(
        question="How do beginners join games at this outdoor court?",
        context="At the court",
    )
    assert "player" in content.who_to_ask.lower()
    assert "break" in content.who_to_ask.lower() or "break" in content.do_this.lower()
    assert content.suggested_question == "How do new players usually get into a game here?"
    assert len(content.suggested_question.split()) < 20
    assert "practice" in content.only_out_there.lower()


def test_s11_food_stall_returning_customers():
    """R11 & S11 worked example 2: Market stall regulars."""
    content = generate_human_card_content(
        question="What do regulars buy at this market stall?",
        context="At the food stall at the outdoor market",
    )
    assert "vendor" in content.who_to_ask.lower()
    assert "free" in content.who_to_ask.lower() or "free" in content.do_this.lower()
    assert content.suggested_question == "What do your regulars usually come back for?"
    assert len(content.suggested_question.split()) < 20
    assert "recommendation" in content.only_out_there.lower()


def test_s11_run_club_first_timer():
    """S11 worked example 3: Run club newcomer."""
    content = generate_human_card_content(
        question="I'm going to this outdoor run club meeting. What's it like for first-timers?",
        context="Campus area",
    )
    assert "member" in content.who_to_ask.lower()
    assert content.suggested_question == "What was your first run with this group like?"
    assert len(content.suggested_question.split()) < 20


def test_s11_sketching_group_meetup():
    """S11 worked example 4: Sketching group."""
    content = generate_human_card_content(
        question="I'm going to this public park art meetup. Can I join the sketching group?",
        context="In the park",
    )
    assert "organizer" in content.who_to_ask.lower()
    assert content.suggested_question == "Is it okay if I join your sketching group?"
    assert len(content.suggested_question.split()) < 20
    assert "sketch only if invited" in content.do_this.lower()


def test_s11_craft_fair_pattern_inspiration():
    """S11 worked example 5: Craft fair maker."""
    content = generate_human_card_content(
        question="Why did the maker choose this pattern?",
        context="Open-air craft fair",
    )
    assert "maker" in content.who_to_ask.lower()
    assert content.suggested_question == "What inspired this pattern?"
    assert len(content.suggested_question.split()) < 20


def test_s11_community_garden_volunteer():
    """S11 worked example 6: Community garden volunteer."""
    content = generate_human_card_content(
        question="What can a new volunteer do at this community garden?",
        context="Community garden",
    )
    assert "coordinator" in content.who_to_ask.lower()
    assert content.suggested_question == "What can a new volunteer help with today?"
    assert len(content.suggested_question.split()) < 20


def test_s11_outdoor_music_jam():
    """S11 worked example 7: Music jam newcomer."""
    content = generate_human_card_content(
        question="Can a newcomer play along at this outdoor music jam?",
        context="Outdoor jam",
    )
    assert "host" in content.who_to_ask.lower() or "organizer" in content.who_to_ask.lower()
    assert content.suggested_question == "Would it be okay if I played along?"
    assert len(content.suggested_question.split()) < 20


def test_s11_book_swap_table():
    """S11 worked example 8: Book swap table."""
    content = generate_human_card_content(
        question="What books do visitors ask for most at this book swap?",
        context="Public book-swap table",
    )
    assert "volunteer" in content.who_to_ask.lower()
    assert content.suggested_question == "Which books do visitors ask for most?"
    assert len(content.suggested_question.split()) < 20


def test_s11_campus_club_meeting_r13():
    """R13: Campus club meeting."""
    content = generate_human_card_content(
        question="What is this campus club actually like week to week?",
        context="Before club meeting",
    )
    assert "member" in content.who_to_ask.lower()
    assert content.suggested_question == "What is this club like week to week?"
    assert len(content.suggested_question.split()) < 20


def test_s11_student_eating_spots_r14():
    """R14: Student food habits."""
    content = generate_human_card_content(
        question="Where do students here actually eat between classes?",
        context="On campus",
    )
    assert "student" in content.who_to_ask.lower()
    assert len(content.suggested_question.split()) < 20


def test_s11_daylight_walking_loop_r15():
    """R15: Walking loop in daylight."""
    content = generate_human_card_content(
        question="Which walking loop do people here enjoy in daylight?",
        context="Campus area",
    )
    assert len(content.suggested_question.split()) < 20


# ── S11 Strict Constraint & Validation Tests ────────────────────────


def test_all_s11_questions_strictly_under_20_words():
    """S11 section 2: Question must be under 20 spoken words."""
    test_inputs = [
        ("How do beginners join games at this outdoor court?", "court"),
        ("What do regulars buy at this market stall?", "market"),
        ("What's it like for first-timers at this run club?", "run club"),
        ("Can I join the sketching group?", "park"),
        ("Why did the maker choose this pattern?", "craft fair"),
        ("What can a new volunteer do at this garden?", "garden"),
        ("Can a newcomer play along at this jam?", "music jam"),
        ("Which books do visitors ask for most?", "book swap"),
        ("What is this club like week to week?", "campus club"),
        ("Where do students grab food between classes?", "campus"),
        ("Which walking loop do people enjoy?", "daylight"),
        ("How do people usually join this group?", "general"),
    ]
    for q, ctx in test_inputs:
        card = generate_human_card_content(q, ctx)
        words = card.suggested_question.split()
        assert len(words) < 20, (
            f"Question exceeded 20 words ({len(words)}): {card.suggested_question}"
        )


def test_validation_raises_when_question_too_long():
    """Validator enforces S11 < 20 words constraint."""
    bad_content = HumanCardContent(
        who_to_ask="A vendor",
        suggested_question="word " * 21,  # 21 words
        only_out_there="Something",
        do_this="Go there",
    )
    with pytest.raises(ValueError, match="must be under 20 words"):
        validate_human_content(bad_content)


def test_handle_human_route_returns_card_response():
    inp = RouterInput(
        question="How do beginners join games at this court?",
        context="outdoor court",
    )
    res = handle_human_route(
        router_input=inp,
        reason="Local joining norm.",
        request_id="req_h1",
        latency_ms=10,
    )
    assert res.kind == "card"
    assert res.fit == Fit.OK
    assert res.route == Route.HUMAN
    assert res.request_id == "req_h1"
    assert res.latency_ms >= 1
    assert "player" in res.content.who_to_ask.lower()


def test_pipeline_integration_human_endpoint():
    """End-to-end endpoint verification for HUMAN route."""
    response = client.post(
        "/api/route",
        json={"question": "What do regulars buy at this market stall?", "context": "At the market"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "HUMAN"
    assert "vendor" in data["content"]["who_to_ask"].lower()
    assert data["content"]["suggested_question"] == "What do your regulars usually come back for?"
    assert len(data["content"]["suggested_question"].split()) < 20
