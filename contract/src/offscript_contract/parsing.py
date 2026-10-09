"""Strict parsing and field rules shared by every model reply (router, guard check, search summary).

A reply must be exactly one JSON object with optional surrounding whitespace. Nothing is
repaired: invalid text becomes a ModelOutputError with a stable code, and is never retried.
"""

import json
import unicodedata
from typing import Any, TypeVar

from pydantic import TypeAdapter, ValidationError

T = TypeVar("T")


class ModelOutputError(ValueError):
    """Raw model text that is not a valid reply."""

    CODES = ("empty", "not_json", "extra_text", "duplicate_keys", "schema", "truncated")

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


def parse_model_json(text: str, adapter: TypeAdapter[T], *, complete: bool = True) -> T:
    """Parse one JSON object and validate it with `adapter`.

    `complete=False` means generation stopped at the token limit instead of the stop token,
    so any failure is reported as `truncated`.
    """

    def fail(code: str, message: str) -> ModelOutputError:
        return ModelOutputError(code if complete else "truncated", message)

    stripped = text.strip()
    if not stripped:
        raise fail("empty", "model returned nothing")
    if not stripped.startswith("{"):
        raise fail("extra_text" if "{" in stripped else "not_json", "reply is not a JSON object")
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
        return adapter.validate_python(data)
    except ValidationError as error:
        raise fail("schema", "; ".join(problem["msg"] for problem in error.errors())) from None


def word_count(text: str) -> int:
    return len(text.split())


def check_text(value: str, *, max_chars: int, max_words: int | None = None, multiline=False):
    """Validate one model-written text field; raise ValueError with a readable reason."""
    if not value or value != value.strip():
        raise ValueError("must be non-empty with no leading or trailing spaces")
    allowed = {"\n"} if multiline else set()
    if any(unicodedata.category(ch) == "Cc" and ch not in allowed for ch in value):
        raise ValueError("must be a single line without control characters")
    if len(value) > max_chars:
        raise ValueError(f"must be at most {max_chars} characters")
    if max_words is not None and word_count(value) > max_words:
        raise ValueError(f"must be at most {max_words} words")
    return value
