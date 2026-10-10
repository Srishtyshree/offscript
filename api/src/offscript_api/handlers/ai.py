"""AI route handler: brief answer path for practical know-how (AGENTS.md A2, A3, B3).

Stable practical know-how for trying, noticing or joining something.
Never guesses live hours, availability, or local facts.
"""

from offscript_contract.route_dto import AiCardContent, CardResponse
from offscript_contract.router import Fit, Route, RouterInput


def generate_ai_card_content(question: str, context: str | None = None) -> AiCardContent:
    """Generate concise know-how answer, physical step, and outdoor distinction.

    Maintains the 60-word concise card limit per AGENTS.md A3.
    """
    q_lower = question.lower()

    court_keywords = ["casual game", "pickup game", "court", "how should i ask", "join a game"]
    if any(k in q_lower for k in court_keywords):
        answer = (
            "Wait for a pause between games, approach politely, and ask if you can "
            "call next round. Most courts run next-game rules."
        )
        outdoor_action = "Walk up to the court side and wait for the current game to pause."

    elif any(k in q_lower for k in ["birdwatch", "bird watching", "bird"]):
        answer = (
            "Focus on tree canopies and water margins. Move slowly, pause every few "
            "paces, and listen for rustling before scanning with your eyes."
        )
        outdoor_action = "Head to the tree line or water edge and stay still for three minutes."

    elif any(k in q_lower for k in ["soil", "garden", "water", "plant"]):
        answer = (
            "Push your finger two inches into the soil. If it feels dry and warm, "
            "it needs water; if cool and damp, leave it."
        )
        outdoor_action = "Walk over to a garden bed and test the soil with your index finger."

    elif any(k in q_lower for k in ["sketch", "drawing", "paint"]):
        answer = (
            "Pick a single distinct subject with simple shadows. Sketch rough bounding "
            "shapes in light lines before committing to dark contours."
        )
        outdoor_action = "Find a bench facing an interesting subject and sketch its basic outline."

    elif any(k in q_lower for k in ["run club", "running club", "group run"]):
        answer = (
            "Arrive ten minutes early and look for the person holding a clipboard "
            "or giving announcements. Introduce yourself as a newcomer."
        )
        outdoor_action = "Head to the meeting point ten minutes before start time."

    else:
        # Default practical know-how pattern
        answer = (
            "Approach at a natural break in activity, introduce yourself with a single "
            "clear question, and observe the group rhythm first."
        )
        outdoor_action = "Walk up to the area and observe for two minutes before stepping in."

    return AiCardContent(
        answer=answer,
        outdoor_action=outdoor_action,
    )


def handle_ai_route(
    router_input: RouterInput,
    reason: str,
    request_id: str,
    latency_ms: int,
) -> CardResponse:
    """Build a complete CardResponse for the AI route."""
    content = generate_ai_card_content(
        question=router_input.question,
        context=router_input.context if router_input.context != "none" else None,
    )

    return CardResponse(
        fit=Fit.OK,
        route=Route.AI,
        reason=reason,
        content=content,
        request_id=request_id,
        latency_ms=max(1, latency_ms),
    )
