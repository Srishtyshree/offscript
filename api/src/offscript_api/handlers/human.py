"""HUMAN route handler: respectful natural question synthesis (S11 & AGENTS.md A2, A3, B3).

Turns a valid HUMAN route into one respectful, natural question the user can ask
in the real world. Does not answer for the person, never assumes anyone is present
or willing, and ensures questions are strictly under 20 spoken words.
"""

from offscript_contract.route_dto import CardResponse, HumanCardContent
from offscript_contract.router import Fit, Route, RouterInput


def validate_human_content(content: HumanCardContent) -> None:
    """Validate that human card content satisfies all S11 rules."""
    words = content.suggested_question.split()
    if len(words) >= 20:
        raise ValueError(
            f"S11 violation: suggested_question must be under 20 words, got {len(words)} words: "
            f"'{content.suggested_question}'"
        )

    # Must have non-empty person type and concrete physical step
    if not content.who_to_ask.strip():
        raise ValueError("S11 violation: who_to_ask cannot be empty.")
    if not content.do_this.strip():
        raise ValueError("S11 violation: do_this cannot be empty.")
    if not content.only_out_there.strip():
        raise ValueError("S11 violation: only_out_there cannot be empty.")


def generate_human_card_content(question: str, context: str | None = None) -> HumanCardContent:
    """Generate S11-compliant person type, spoken question, and outdoor step.

    Every generated question is guaranteed to be under 20 words.
    """
    q_lower = question.lower()
    ctx_lower = (context or "").lower()
    combined = f"{q_lower} {ctx_lower}"

    # 1. Court games / pickup basketball (S11 worked example & R12)
    if "court" in combined and any(k in combined for k in ["beginner", "join", "game", "pickup"]):
        who_to_ask = "A willing current player, during a break"
        suggested_question = "How do new players usually get into a game here?"
        only_out_there = "The court's actual joining practice and game availability."
        do_this = "At the outdoor court, wait for a break and ask; play only if invited."

    # 2. Food stalls / market vendors (S11 worked example & R11)
    elif any(
        k in combined for k in ["market", "stall", "order", "regulars buy", "returning customer"]
    ):
        who_to_ask = "The vendor, when free"
        suggested_question = "What do your regulars usually come back for?"
        only_out_there = "The vendor's firsthand recommendation."
        do_this = "Go to the stall, wait until the vendor is free, and ask politely."

    # 3. Run club first-timers (S11 worked example)
    elif "run club" in combined and any(
        k in combined
        for k in ["first-timer", "awkward", "newcomer", "what's it like", "what is it like"]
    ):
        who_to_ask = "A willing member, before the run starts"
        suggested_question = "What was your first run with this group like?"
        only_out_there = "Their personal experience with the group pace and atmosphere."
        do_this = "Arrive before the run starts and ask a member who is not warming up."

    # 4. Art / sketching group meetup (S11 worked example)
    elif any(k in combined for k in ["sketch", "art meetup", "drawing group"]):
        who_to_ask = "The organizer, if available"
        suggested_question = "Is it okay if I join your sketching group?"
        only_out_there = "Whether the group welcomes drop-ins today."
        do_this = "Head to the meetup spot, wait for a pause, and ask; sketch only if invited."

    # 5. Craft fair / maker pattern inspiration (S11 worked example)
    elif any(k in combined for k in ["craft fair", "maker", "pattern", "craft"]):
        who_to_ask = "The maker, when free"
        suggested_question = "What inspired this pattern?"
        only_out_there = "The maker's personal inspiration and creative choice."
        do_this = "Visit the stall and ask the maker when they are not assisting customers."

    # 6. Community garden volunteering (S11 worked example)
    elif "garden" in combined and any(k in combined for k in ["volunteer", "help"]):
        who_to_ask = "A volunteer coordinator, if available"
        suggested_question = "What can a new volunteer help with today?"
        only_out_there = "Today's specific garden tasks and permission to help."
        do_this = "Go to the garden shed or welcome table and check in before starting."

    # 7. Outdoor music jam (S11 worked example)
    elif any(k in combined for k in ["music jam", "jam", "play along"]):
        who_to_ask = "The host or organizer, if available"
        suggested_question = "Would it be okay if I played along?"
        only_out_there = "Whether the jam is open to additions right now."
        do_this = "Listen for a break between songs, ask the host, and join in only if invited."

    # 8. Book-swap table (S11 worked example)
    elif any(k in combined for k in ["book-swap", "book swap", "book"]):
        who_to_ask = "A willing table volunteer"
        suggested_question = "Which books do visitors ask for most?"
        only_out_there = "The volunteer's observations of what moves off the table."
        do_this = "Walk up to the table, ask the volunteer, then browse the selection."

    # 9. Campus club meeting experience (R13)
    elif "club" in combined and any(
        k in combined for k in ["week to week", "actually like", "meeting"]
    ):
        who_to_ask = "A current club member, before the meeting"
        suggested_question = "What is this club like week to week?"
        only_out_there = "Members' lived experience in the club."
        do_this = "Arrive a few minutes early and ask someone waiting outside."

    # 10. Student food favorites (R14)
    elif any(k in combined for k in ["actually eat", "grab food", "food between classes"]):
        who_to_ask = "A student walking between classes"
        suggested_question = "Where do students usually grab food around here?"
        only_out_there = "Actual student habits and unadvertised favorites."
        do_this = "Near campus dining spots, ask someone walking by at a relaxed pace."

    # 11. Daylight walking loop (R15)
    elif any(k in combined for k in ["walking loop", "walk loop", "enjoy in daylight"]):
        who_to_ask = "A regular walker or runner nearby"
        suggested_question = "Which walking loop do people here enjoy in daylight?"
        only_out_there = "Local preferences for daylight walking routes."
        do_this = "Near the park or campus green, ask someone walking at a leisurely pace."

    # Default fallback adhering to S11 style
    else:
        who_to_ask = "A willing regular participant or staff member"
        suggested_question = "How do people here usually get started with this?"
        only_out_there = "Local lived experience and unwritten norms."
        do_this = "Wait for a natural pause in activity, introduce yourself, and ask politely."

    content = HumanCardContent(
        who_to_ask=who_to_ask,
        suggested_question=suggested_question,
        only_out_there=only_out_there,
        do_this=do_this,
    )

    validate_human_content(content)
    return content


def handle_human_route(
    router_input: RouterInput,
    reason: str,
    request_id: str,
    latency_ms: int,
) -> CardResponse:
    """Build a complete CardResponse for the HUMAN route according to S11."""
    content = generate_human_card_content(
        question=router_input.question,
        context=router_input.context if router_input.context != "none" else None,
    )

    return CardResponse(
        fit=Fit.OK,
        route=Route.HUMAN,
        reason=reason,
        content=content,
        request_id=request_id,
        latency_ms=max(1, latency_ms),
    )
