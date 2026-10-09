"""Single source of truth for Offscript shapes shared by api/, training/ and web/.

router.py     router input cleanup, messages, RouterOutput and the strict parser
route_dto.py  request and response DTO schemas for POST /api/route
rendering.py  Qwen3 prompt rendering without PyTorch, for the backend
dataset.py    labelled example format and dataset validation
"""

from offscript_contract.health import HealthResponse
from offscript_contract.route_dto import (
    AiCardContent,
    CardResponse,
    ErrorDetail,
    ErrorResponse,
    GuardResponse,
    HumanCardContent,
    RouteRequest,
    RouteResponseUnion,
    SearchCardContent,
    SearchSource,
)

__all__ = [
    "HealthResponse",
    "RouteRequest",
    "CardResponse",
    "GuardResponse",
    "ErrorDetail",
    "ErrorResponse",
    "AiCardContent",
    "SearchCardContent",
    "HumanCardContent",
    "SearchSource",
    "RouteResponseUnion",
]
