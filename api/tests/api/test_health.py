from fastapi.testclient import TestClient

from offscript_api.config import Settings, get_settings
from offscript_api.main import create_app


def _client(settings: Settings) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_health_reports_ready_without_secrets():
    secret = "sk-should-never-leak"
    client = _client(Settings(tinker_api_key=secret, tinker_model_path="tinker://x"))

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"ok", "version", "model_configured"}
    assert body["ok"] is True
    assert body["model_configured"] is True
    assert secret not in response.text


def test_health_reports_unconfigured_model():
    client = _client(Settings(tinker_api_key="", tinker_model_path=""))

    assert client.get("/health").json()["model_configured"] is False
