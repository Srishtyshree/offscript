"""Router contract shared by training and the backend.

One definition of the router's input (cleanup, limits, messages), its output (RouterOutput)
and how raw model text is parsed. Training, evaluation, the live API and the mock router
all go through these functions, so they cannot drift apart.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from functools import cache
from hashlib import sha256
from importlib.resources import files
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator

BASE_MODEL = "Qwen/Qwen3.5-9B"
RENDERER_NAME = "qwen3_5_disable_thinking"
TEMPERATURE = 0.0
MAX_TOKENS = 150
STOP_TOKEN = "<|im_end|>"  # noqa: S105 (a chat marker, not a secret)

QUESTION_MAX = 300
CONTEXT_MAX = 200
REASON_MAX = 160
NO_CONTEXT = "none"


class Fit(StrEnum):
    OK = "ok"
    SCOPE_NUDGE = "scope_nudge"
    CONTEXT_REQUEST = "context_request"
    SPLIT_REQUEST = "split_request"


class Route(StrEnum):
    AI = "AI"
    SEARCH = "SEARCH"
    HUMAN = "HUMAN"


class RouterOutput(BaseModel):
    """The tuned model's whole answer. `route` is set exactly when `fit` is ok."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fit: Fit
    route: Route | None
    reason: str

    @field_validator("reason")
    @classmethod
    def _one_clean_line(cls, reason: str) -> str:
        if not reason or reason != reason.strip():
            raise ValueError("reason must be non-empty with no leading or trailing spaces")
        if any(unicodedata.category(ch) == "Cc" for ch in reason):
            raise ValueError("reason must be a single line without control characters")
        if len(reason) > REASON_MAX:
            raise ValueError(f"reason must be at most {REASON_MAX} characters")
        return reason

    @model_validator(mode="after")
    def _route_matches_fit(self) -> "RouterOutput":
        if (self.fit is Fit.OK) != (self.route is not None):
            raise ValueError("route must be set when fit is ok, and null otherwise")
        return self

    def to_target_json(self) -> str:
        """Canonical training answer: compact, fixed key order, characters kept as written."""
        payload = {"fit": self.fit.value, "route": self.route, "reason": self.reason}
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


# --- Input -----------------------------------------------------------------------------


class InputError(ValueError):
    """User input the router must never see. `code` is stable for the API's 422 response."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RouterInput:
    question: str
    context: str  # NO_CONTEXT when the user gave none


# Strings the Qwen3.5 tokenizer treats as control tokens. The cookbook renderer encodes them as
# real control tokens even inside user text, so they are removed before any rendering.
CONTROL_TOKEN_PATTERN = re.compile(
    r"<\|[^<>|\s]{1,40}\|>|</?(?:think|tool_call|tool_response)>|<tts_[a-z_]{1,30}>"
)


def clean_text(text: str) -> str:
    """NFC-normalise, remove control-token strings and control characters, and collapse all
    whitespace to single spaces.

    Collapsing newlines also stops a user from faking a second "Context:" line.
    """
    text = unicodedata.normalize("NFC", text)
    text = CONTROL_TOKEN_PATTERN.sub(" ", text)
    text = "".join(ch for ch in text if ch.isspace() or unicodedata.category(ch) != "Cc")
    return " ".join(text.split())


def normalize_input(question: str, context: str | None = None) -> RouterInput:
    """Clean question and context, then enforce limits on the cleaned text."""
    question = clean_text(question)
    context = clean_text(context or "")
    if not question:
        raise InputError("question_empty", "Please enter a question.")
    if len(question) > QUESTION_MAX:
        raise InputError("question_too_long", f"Keep the question under {QUESTION_MAX} characters.")
    if len(context) > CONTEXT_MAX:
        raise InputError("context_too_long", f"Keep the context under {CONTEXT_MAX} characters.")
    return RouterInput(question=question, context=context or NO_CONTEXT)


def format_user_message(router_input: RouterInput) -> str:
    return f"Question: {router_input.question}\nContext: {router_input.context}"


@cache
def load_system_prompt() -> str:
    return files("offscript_contract").joinpath("prompts/router_system.md").read_text("utf-8")


@cache
def router_prompt_version() -> str:
    """Short hash of the system prompt. A checkpoint is only valid with the prompt it was
    trained on, so this travels with every checkpoint handover."""
    return sha256(load_system_prompt().encode("utf-8")).hexdigest()[:12]


def build_router_messages(question: str, context: str | None = None) -> list[dict[str, str]]:
    router_input = normalize_input(question, context)
    return [
        {"role": "system", "content": load_system_prompt()},
        {"role": "user", "content": format_user_message(router_input)},
    ]


# --- Output ----------------------------------------------------------------------------


class RouterOutputError(ValueError):
    """Raw model text that is not a valid RouterOutput. Never repaired, never retried."""

    CODES = (
        "empty",
        "not_json",
        "extra_text",
        "duplicate_keys",
        "schema",
        "inconsistent",
        "truncated",
    )

    def __init__(self, code: str, message: str):
        assert code in self.CODES, code
        super().__init__(message)
        self.code = code


class _DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise _DuplicateKeyError(keys)
    return dict(pairs)


_DECODER = json.JSONDecoder(object_pairs_hook=_reject_duplicate_keys)


def parse_router_output(text: str, *, complete: bool = True) -> RouterOutput:
    """Parse raw model text strictly: exactly one JSON object, optional surrounding whitespace.

    `complete=False` means generation stopped at the token limit instead of the stop token,
    so any failure is reported as `truncated`.
    """
    stripped = text.strip()
    if not stripped:
        raise RouterOutputError("truncated" if not complete else "empty", "model returned nothing")

    def fail(code: str, message: str) -> RouterOutputError:
        return RouterOutputError("truncated" if not complete else code, message)

    if not stripped.startswith("{"):
        code = "extra_text" if "{" in stripped else "not_json"
        raise fail(code, "reply does not start with a JSON object")
    try:
        data, end = _DECODER.raw_decode(stripped)
    except _DuplicateKeyError as error:
        raise fail("duplicate_keys", f"duplicate keys in {error.args[0]}") from None
    except json.JSONDecodeError as error:
        code = "not_json" if stripped.endswith("}") else "truncated"
        raise fail(code, f"invalid JSON: {error.msg}") from None
    if stripped[end:].strip():
        raise fail("extra_text", "text after the JSON object")
    if not isinstance(data, dict):
        raise fail("schema", "reply is not a JSON object")

    try:
        return RouterOutput.model_validate(data)
    except ValidationError as error:
        # Field-level problems carry a location; the fit/route rule is model-level (loc ()).
        problems = error.errors()
        code = "inconsistent" if all(problem["loc"] == () for problem in problems) else "schema"
        raise fail(code, "; ".join(problem["msg"] for problem in problems)) from None
