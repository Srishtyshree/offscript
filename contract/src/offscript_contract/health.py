from pydantic import BaseModel


class HealthResponse(BaseModel):
    """GET /health. Never add config values, paths or keys here."""

    ok: bool
    version: str
    model_configured: bool
