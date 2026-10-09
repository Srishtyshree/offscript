"""Guard check: an untuned call to the base model that runs after the backend's safety rules and
before the fine-tuned router. It stops questions that can't be routed as asked: an essential
detail is missing, or two separate questions are asked in one.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, TypeAdapter, field_validator, model_validator

from offscript_contract.parsing import check_text, parse_model_json
from offscript_contract.router import (
    format_user_message,
    load_prompt,
    normalize_input,
    prompt_version,
)

GUARD_PROMPT = "guard_system"
GUARD_MAX_TOKENS = 100
GUARD_MESSAGE_MAX_CHARS = 160


class GuardVerdict(StrEnum):
    OK = "ok"
    NEEDS_DETAIL = "needs_detail"
    TWO_QUESTIONS = "two_questions"


class GuardOutput(BaseModel):
    """`message` is shown to the user when the question is stopped, and is null when it is ok."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    verdict: GuardVerdict
    message: str | None

    @field_validator("message")
    @classmethod
    def _message(cls, value: str | None) -> str | None:
        if value is not None:
            check_text(value, max_chars=GUARD_MESSAGE_MAX_CHARS)
        return value

    @model_validator(mode="after")
    def _message_matches_verdict(self) -> "GuardOutput":
        if (self.verdict is GuardVerdict.OK) != (self.message is None):
            raise ValueError("message must be null when verdict is ok, and set otherwise")
        return self


GUARD_OUTPUT = TypeAdapter(GuardOutput)


def guard_prompt_version() -> str:
    return prompt_version(GUARD_PROMPT)


def build_guard_messages(question: str, context: str | None = None) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": load_prompt(GUARD_PROMPT)},
        {"role": "user", "content": format_user_message(normalize_input(question, context))},
    ]


def parse_guard_output(text: str, *, complete: bool = True) -> GuardOutput:
    return parse_model_json(text, GUARD_OUTPUT, complete=complete)
