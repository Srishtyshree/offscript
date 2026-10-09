"""POST /api/route endpoint implementation."""

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from offscript_api.clients.serpapi import SerpApiClient
from offscript_api.config import Settings, get_settings
from offscript_api.services.pipeline import run_pipeline
from offscript_contract.route_dto import ErrorResponse, RouteRequest, RouteResponseUnion
from offscript_contract.router import InputError, normalize_input

router = APIRouter()


def get_serpapi_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> SerpApiClient | None:
    """Dependency that provides a SerpApiClient instance if configured, or None."""
    if settings.serpapi_api_key:
        return SerpApiClient(api_key=settings.serpapi_api_key)
    return None


@router.post(
    "/api/route",
    response_model=RouteResponseUnion,
    responses={
        422: {"model": ErrorResponse, "description": "Input validation error"},
    },
)
async def route_request(
    payload: RouteRequest,
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    serpapi_client: Annotated[SerpApiClient | None, Depends(get_serpapi_client)] = None,
) -> Any:
    """Classify and return a card or guard response for user question."""
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    # Step 1: Validate input
    try:
        norm_input = normalize_input(question=payload.question, context=payload.context)
    except InputError as err:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"error": {"code": err.code, "message": str(err)}},
        )

    # Steps 2–7: Safety → Router → Handler → Card
    return await run_pipeline(
        norm_input,
        request_id=request_id,
        settings=settings,
        serpapi_client=serpapi_client,
    )
