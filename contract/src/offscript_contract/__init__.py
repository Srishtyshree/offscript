"""Single source of truth for Offscript shapes shared by api/, training/ and web/.

router.py     router input cleanup, messages, RouterOutput and the strict parser
rendering.py  Qwen3 prompt rendering without PyTorch, for the backend
dataset.py    labelled example format and dataset validation

Planned (backend-led): request.py and responses.py for POST /api/route.
Ask before adding or renaming any field.
"""

from offscript_contract.health import HealthResponse

__all__ = ["HealthResponse"]
