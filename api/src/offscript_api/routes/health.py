from importlib.metadata import version
from typing import Annotated

from fastapi import APIRouter, Depends

from offscript_api.config import Settings, get_settings
from offscript_contract import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        ok=True,
        version=version("offscript-api"),
        model_configured=settings.model_configured,
    )
