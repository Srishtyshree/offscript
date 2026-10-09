from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from offscript_api.config import get_settings
from offscript_api.routes import health


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Offscript API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    app.include_router(health.router)
    return app


app = create_app()
