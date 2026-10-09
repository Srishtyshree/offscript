"""Unit tests for AI and SEARCH action handlers (Task A03, AGENTS.md A2, A3, B3, B9)."""

import asyncio

from offscript_api.clients.serpapi import SerpApiClient, SerpApiTimeoutError
from offscript_api.handlers.ai import generate_ai_card_content, handle_ai_route
from offscript_api.handlers.search import build_search_query, build_search_url, handle_search_route
from offscript_contract.route_dto import SearchSource
from offscript_contract.router import Fit, Route, RouterInput

# ── AI Handler Tests ────────────────────────────────────────────────


def test_ai_handler_pickup_game():
    inp = RouterInput(question="How do I join a casual pickup game at the court?", context="none")
    card = handle_ai_route(inp, reason="Stable know-how.", request_id="req_1", latency_ms=10)

    assert card.fit == Fit.OK
    assert card.route == Route.AI
    assert "pause" in card.content.answer.lower()
    assert len(card.content.do_this) > 0
    assert len(card.content.only_out_there) > 0


def test_ai_handler_birdwatching():
    content = generate_ai_card_content("How do I start birdwatching in the park?")
    assert "tree" in content.answer.lower() or "canop" in content.answer.lower()
    assert "still" in content.do_this.lower()


def test_ai_handler_gardening_soil():
    content = generate_ai_card_content("How can I tell if garden soil needs water?")
    assert "finger" in content.answer.lower()
    assert "test" in content.do_this.lower() or "walk" in content.do_this.lower()


def test_ai_handler_concise_under_limits():
    content = generate_ai_card_content("How do I sketch outdoors?")
    word_count = len(content.answer.split())
    assert word_count < 60  # Under 60 words per AGENTS.md A3


# ── SEARCH Handler Tests (Task A03 Honesty & Web Search Action) ─────


def test_build_search_query_with_context():
    q = build_search_query("Is the museum open today?", context="downtown")
    assert "downtown" in q
    assert not q.endswith("?")


def test_build_search_url():
    url = build_search_url("campus run club meeting")
    assert "https://www.google.com/search?q=" in url
    assert "campus+run+club" in url


def test_search_handler_without_live_client_does_not_pretend_lookup():
    """Honesty rule: sources is empty when ungrounded; prefilled search_url provided."""

    async def _test():
        inp = RouterInput(
            question="Where is a public run club meeting near campus this week?",
            context="campus",
        )
        result = await handle_search_route(
            router_input=inp,
            reason="Fresh public listings required.",
            request_id="req_search_1",
            latency_ms=12,
            serpapi_client=None,
        )

        assert result.kind == "card"
        assert result.fit == Fit.OK
        assert result.route == Route.SEARCH
        assert result.content.sources == []  # Honest: do not fabricate fake sources!
        assert "google.com/search" in result.content.search_url
        assert len(result.content.do_this) > 0

    asyncio.run(_test())


def test_search_handler_with_live_sources():
    """When SerpApi succeeds, sources are returned in the CardResponse."""

    async def _test():
        class FakeSerpApiClient(SerpApiClient):
            def __init__(self):
                super().__init__(api_key="fake-key")

            async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
                return [
                    SearchSource(title="Campus Run Club Official", url="https://runclub.edu"),
                    SearchSource(title="Weekend Morning Runs", url="https://cityruns.org"),
                ]

        inp = RouterInput(question="Where is a public run club meeting?", context="none")
        result = await handle_search_route(
            router_input=inp,
            reason="Listing needed.",
            request_id="req_search_2",
            latency_ms=25,
            serpapi_client=FakeSerpApiClient(),
        )

        assert result.kind == "card"
        assert result.route == Route.SEARCH
        assert len(result.content.sources) == 2
        assert result.content.sources[0].title == "Campus Run Club Official"

    asyncio.run(_test())


def test_search_handler_returns_search_limitation_on_failure():
    """If SerpApi fails, return search_limitation guard with prefilled search_url."""

    async def _test():
        class FailingSerpApiClient(SerpApiClient):
            def __init__(self):
                super().__init__(api_key="fake-key")

            async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
                raise SerpApiTimeoutError("Search timed out")

        inp = RouterInput(question="When is the outdoor court open today?", context="none")
        result = await handle_search_route(
            router_input=inp,
            reason="Listing needed.",
            request_id="req_search_3",
            latency_ms=50,
            serpapi_client=FailingSerpApiClient(),
        )

        assert result.kind == "guard"
        assert result.fit == "search_limitation"
        assert result.route is None
        assert result.search_url is not None
        assert "google.com/search" in result.search_url

    asyncio.run(_test())


def test_search_handler_returns_search_limitation_when_no_sources():
    """If SerpApi finds 0 results, return search_limitation guard with prefilled search_url."""

    async def _test():
        class EmptySerpApiClient(SerpApiClient):
            def __init__(self):
                super().__init__(api_key="fake-key")

            async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
                return []

        inp = RouterInput(question="Is the rare obscure garden open today?", context="none")
        result = await handle_search_route(
            router_input=inp,
            reason="Listing needed.",
            request_id="req_search_4",
            latency_ms=30,
            serpapi_client=EmptySerpApiClient(),
        )

        assert result.kind == "guard"
        assert result.fit == "search_limitation"
        assert result.search_url is not None

    asyncio.run(_test())
