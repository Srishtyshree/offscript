"""Single source of truth for Offscript request/response shapes.

Planned modules (see AGENTS.md B4/B5, open decision B12):
    request.py        RouteRequest {question, context?}
    responses.py      card | guard | error discriminated union
    router_output.py  tuned-model JSON (fit + route kept separate)

Ask before adding or renaming any field.
"""

from offscript_contract.health import HealthResponse

__all__ = ["HealthResponse"]
