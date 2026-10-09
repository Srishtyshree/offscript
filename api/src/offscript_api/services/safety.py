"""Rule-based safety and guard checks that run BEFORE the model (AGENTS.md B3 step 2).

These are the ONLY place rules are allowed. A hit returns a guard response
and the model is never called. The model is never trained on safety questions.
"""

import re

from offscript_contract.route_dto import GuardResponse
from offscript_contract.router import RouterInput

# --- Keyword lists ---------------------------------------------------------------

_EMERGENCY_KEYWORDS = [
    "suicide",
    "kill myself",
    "self-harm",
    "overdose",
    "emergency",
    "call 911",
    "call 999",
    "call 112",
    "ambulance",
]

_MEDICAL_KEYWORDS = [
    "medicine",
    "medication",
    "prescription",
    "drug dosage",
    "doctor",
    "diagnosis",
    "symptom",
    "treatment",
    "therapy",
    "medical advice",
]

_LEGAL_KEYWORDS = [
    "lawyer",
    "legal advice",
    "sue",
    "lawsuit",
    "arrest",
    "court case",
    "bail",
]

_DANGEROUS_ROUTE_KEYWORDS = [
    "dark shortcut",
    "unsafe route",
    "after dark",
    "abandoned",
    "trespass",
    "break in",
    "sneak in",
    "climb the fence",
    "restricted area",
]

_INTRUSIVE_KEYWORDS = [
    "follow them",
    "follow her",
    "follow him",
    "stalk",
    "harass",
    "woman sitting alone",
    "man sitting alone",
    "person sitting alone",
    "why she is alone",
    "why he is alone",
    "why they are alone",
    "record without",
    "film without",
    "photograph without",
    "take a picture without",
    "private property",
]

# Compiled patterns for multi-word matching
_EMERGENCY_PATTERN = re.compile(
    "|".join(re.escape(k) for k in _EMERGENCY_KEYWORDS),
    re.IGNORECASE,
)
_MEDICAL_PATTERN = re.compile(
    "|".join(re.escape(k) for k in _MEDICAL_KEYWORDS),
    re.IGNORECASE,
)
_LEGAL_PATTERN = re.compile(
    "|".join(re.escape(k) for k in _LEGAL_KEYWORDS),
    re.IGNORECASE,
)
_DANGEROUS_PATTERN = re.compile(
    "|".join(re.escape(k) for k in _DANGEROUS_ROUTE_KEYWORDS),
    re.IGNORECASE,
)
_INTRUSIVE_PATTERN = re.compile(
    "|".join(re.escape(k) for k in _INTRUSIVE_KEYWORDS),
    re.IGNORECASE,
)


# --- Public API ------------------------------------------------------------------


def check_safety(
    router_input: RouterInput,
    request_id: str,
    latency_ms: int,
) -> GuardResponse | None:
    """Return a guard response if safety rules trigger, else None.

    Checks are ordered by severity: emergency first, then medical/legal,
    then dangerous routes, then intrusive/targeting requests.
    """
    combined = f"{router_input.question} {router_input.context}"

    # Emergency / immediate safety
    if _EMERGENCY_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Emergency or immediate safety concern detected.",
            message=(
                "If you or someone nearby is in immediate danger, "
                "please call your local emergency number (911 / 999 / 112). "
                "Offscript cannot provide emergency assistance."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Medical / mental-health
    if _MEDICAL_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Medical or health question requires professional guidance.",
            message=(
                "Please consult a qualified healthcare professional for "
                "medical advice. Offscript is not a substitute for "
                "professional medical guidance."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Legal
    if _LEGAL_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Legal question requires professional counsel.",
            message=(
                "For legal questions, please consult a qualified legal "
                "professional. Offscript cannot provide legal advice."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Dangerous routes / trespass
    if _DANGEROUS_PATTERN.search(combined):
        return GuardResponse(
            fit="safety_guidance",
            reason="Potentially unsafe route or location access.",
            message=(
                "This route or location may not be safe. Please choose a "
                "well-lit, public path and never enter restricted areas "
                "without permission."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    # Intrusive / harassing / targeting
    if _INTRUSIVE_PATTERN.search(combined):
        return GuardResponse(
            fit="refusal",
            reason="Request involves intrusive or targeting behaviour.",
            message=(
                "Offscript cannot help with requests that involve following, "
                "harassing, or intruding on other people. Everyone deserves "
                "to feel safe in public spaces."
            ),
            request_id=request_id,
            latency_ms=latency_ms,
        )

    return None
