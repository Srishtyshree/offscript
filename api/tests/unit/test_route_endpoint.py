"""Unit tests for POST /api/route endpoint (Task A01)."""

from fastapi.testclient import TestClient

from offscript_api.main import app

client = TestClient(app)


def test_post_route_ai_response():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a casual pickup game at the court?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "AI"
    assert "answer" in data["content"]
    assert "do_this" in data["content"]
    assert "only_out_there" in data["content"]
    assert "request_id" in data
    assert isinstance(data["latency_ms"], int)


def test_post_route_search_response():
    response = client.post(
        "/api/route",
        json={"question": "Where is a public run club meeting near campus this week?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "SEARCH"
    assert "search_query" in data["content"]
    assert "sources" in data["content"]
    assert "search_url" in data["content"]
    # Unconfigured / mock: sources is empty, does not pretend live lookup occurred
    assert data["content"]["sources"] == []


def test_post_route_search_injected_serpapi_sources():
    from offscript_api.clients.serpapi import SerpApiClient
    from offscript_api.routes.route import get_serpapi_client
    from offscript_contract.route_dto import SearchSource

    class FakeSerpApiClient(SerpApiClient):
        def __init__(self):
            super().__init__(api_key="test-key")

        async def search(self, query: str, num_results: int = 3) -> list[SearchSource]:
            return [SearchSource(title="Campus Running Hub", url="https://example.com/running")]

    app.dependency_overrides[get_serpapi_client] = lambda: FakeSerpApiClient()
    try:
        response = client.post(
            "/api/route",
            json={"question": "Where is a public run club meeting near campus this week?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "card"
        assert data["route"] == "SEARCH"
        assert len(data["content"]["sources"]) == 1
        assert data["content"]["sources"][0]["title"] == "Campus Running Hub"
    finally:
        app.dependency_overrides.pop(get_serpapi_client, None)


def test_post_route_search_injected_serpapi_failure_returns_search_limitation():
    from offscript_api.clients.serpapi import SerpApiClient, SerpApiTimeoutError
    from offscript_api.routes.route import get_serpapi_client

    class FailingSerpApiClient(SerpApiClient):
        def __init__(self):
            super().__init__(api_key="test-key")

        async def search(self, query: str, num_results: int = 3) -> list:
            raise SerpApiTimeoutError("Timeout")

    app.dependency_overrides[get_serpapi_client] = lambda: FailingSerpApiClient()
    try:
        response = client.post(
            "/api/route",
            json={"question": "Where is a public run club meeting near campus this week?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["kind"] == "guard"
        assert data["fit"] == "search_limitation"
        assert "search_url" in data
        assert data["search_url"] is not None
    finally:
        app.dependency_overrides.pop(get_serpapi_client, None)


def test_post_route_human_response():
    response = client.post(
        "/api/route",
        json={"question": "What do regulars buy at this market stall?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["fit"] == "ok"
    assert data["route"] == "HUMAN"
    assert "who_to_ask" in data["content"]
    assert "suggested_question" in data["content"]


def test_post_route_guard_scope_nudge():
    response = client.post(
        "/api/route",
        json={"question": "What is photosynthesis?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "scope_nudge"
    assert data["route"] is None
    assert "message" in data


def test_post_route_validation_error_empty_question():
    response = client.post(
        "/api/route",
        json={"question": ""},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "question_empty"
    assert "message" in data["error"]


def test_post_route_validation_error_too_long():
    response = client.post(
        "/api/route",
        json={"question": "a" * 301},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "question_too_long"


def test_post_route_guard_context_request():
    response = client.post(
        "/api/route",
        json={"question": "I want to visit a park today. Which is open near me?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "context_request"


def test_post_route_guard_split_request():
    response = client.post(
        "/api/route",
        json={"question": "How do I join a game, and where is one tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "split_request"


def test_post_route_guard_safety_guidance():
    response = client.post(
        "/api/route",
        json={"question": "Is the dark shortcut behind the station safe to try tonight?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "safety_guidance"


def test_post_route_guard_refusal():
    response = client.post(
        "/api/route",
        json={"question": "Ask the woman sitting alone why she is alone."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "guard"
    assert data["fit"] == "refusal"


def test_post_route_canonical_human_college_club():
    response = client.post(
        "/api/route",
        json={"question": "What is this college club actually like before I go to its meeting?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "HUMAN"


def test_post_route_canonical_ai_birdwatching():
    response = client.post(
        "/api/route",
        json={"question": "How can I start birdwatching in the park?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["kind"] == "card"
    assert data["route"] == "AI"
