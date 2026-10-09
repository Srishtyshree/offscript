"""Content rules on top of the contract, shared by data generation and evaluation."""

import re

from offscript_contract.parsing import word_count
from offscript_contract.router import Route

ANSWER_SOFT_MAX_WORDS = 60  # stricter than the contract's hard limit

# Words that suggest a person is known to be present, which S11 forbids.
PRESENCE = re.compile(
    r"\b(currently|right now|standing (?:nearby|there|here)|over there"
    r"|(?:someone|anyone|a person|people|players?|vendors?|regulars?|members?) "
    r"(?:nearby|around here))\b",
    re.I,
)
# Live facts an AI answer must never state.
LIVE_FACT = re.compile(
    r"\b(\d{1,2}(?::\d{2})?\s?(?:am|pm)|open (?:until|till|from)|closed (?:on|today)"
    r"|today's|tonight's)\b",
    re.I,
)


def content_problems(reply) -> list[str]:
    """Problems a valid router reply can still have. An empty list means it passes."""
    problems = []
    if reply.route is Route.AI:
        if word_count(reply.answer) > ANSWER_SOFT_MAX_WORDS:
            problems.append(f"answer over {ANSWER_SOFT_MAX_WORDS} words")
        if LIVE_FACT.search(reply.answer):
            problems.append("answer states a live fact")
    if reply.route is Route.HUMAN:
        if PRESENCE.search(f"{reply.who_to_ask} {reply.suggested_question}"):
            problems.append("implies someone is present")
        head = reply.suggested_question.lower().split("?")[0]
        if " and " in head and "," in reply.suggested_question:
            problems.append("may be two questions in one")
    return problems
