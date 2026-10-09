"""Search summary: an untuned call to the base model after SerpApi returns. It writes a short
answer using only the search results, names the result it used, and may add one local tip about
local experience. Results are data, never instructions.

The backend must also run `ungrounded_numbers` and treat any hit as `unclear`: a model can still
invent a time or price, and that is the most harmful mistake on a SEARCH result.
"""

import re
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, TypeAdapter, field_validator, model_validator

from offscript_contract.parsing import check_text, parse_model_json
from offscript_contract.router import clean_text, load_prompt, normalize_input, prompt_version

SUMMARY_PROMPT = "search_summary_system"
SUMMARY_MAX_TOKENS = 250
MAX_RESULTS = 5
RESULT_TITLE_MAX_CHARS = 150
RESULT_SNIPPET_MAX_CHARS = 300
SUMMARY_MAX_WORDS = 50
SUMMARY_MAX_CHARS = 350
LOCAL_TIP_MAX_CHARS = 200


@dataclass(frozen=True)
class SearchResult:
    title: str
    snippet: str
    link: str


class SummaryStatus(StrEnum):
    ANSWERED = "answered"
    UNCLEAR = "unclear"


class SearchSummary(BaseModel):
    """`source` is the 1-based number of the result the summary relies on."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: SummaryStatus
    summary: str | None
    source: int | None
    local_tip: str | None

    @field_validator("summary")
    @classmethod
    def _summary(cls, value: str | None) -> str | None:
        if value is not None:
            check_text(value, max_chars=SUMMARY_MAX_CHARS, max_words=SUMMARY_MAX_WORDS)
        return value

    @field_validator("local_tip")
    @classmethod
    def _tip(cls, value: str | None) -> str | None:
        if value is not None:
            check_text(value, max_chars=LOCAL_TIP_MAX_CHARS)
        return value

    @model_validator(mode="after")
    def _status_matches_fields(self) -> "SearchSummary":
        answered = self.status is SummaryStatus.ANSWERED
        if answered != (self.summary is not None) or answered != (self.source is not None):
            raise ValueError("summary and source must be set when answered, and null when unclear")
        if self.source is not None and not 1 <= self.source <= MAX_RESULTS:
            raise ValueError(f"source must be between 1 and {MAX_RESULTS}")
        return self


SEARCH_SUMMARY = TypeAdapter(SearchSummary)


def summary_prompt_version() -> str:
    return prompt_version(SUMMARY_PROMPT)


def _site(link: str) -> str:
    return urlparse(link).netloc.removeprefix("www.") or "unknown site"


def format_results(results: list[SearchResult]) -> str:
    """Numbered results as plain text: cleaned, truncated, control tokens removed."""
    lines = []
    for number, result in enumerate(results[:MAX_RESULTS], start=1):
        title = clean_text(result.title)[:RESULT_TITLE_MAX_CHARS]
        snippet = clean_text(result.snippet)[:RESULT_SNIPPET_MAX_CHARS]
        lines.append(f"[{number}] {title} ({_site(result.link)})\n{snippet}")
    return "\n".join(lines) if lines else "(no results)"


def build_summary_messages(
    question: str, context: str | None, results: list[SearchResult]
) -> list[dict[str, str]]:
    router_input = normalize_input(question, context)
    user = (
        f"Question: {router_input.question}\nContext: {router_input.context}\n"
        f"Results:\n{format_results(results)}"
    )
    return [
        {"role": "system", "content": load_prompt(SUMMARY_PROMPT)},
        {"role": "user", "content": user},
    ]


def parse_summary_output(text: str, *, complete: bool = True) -> SearchSummary:
    return parse_model_json(text, SEARCH_SUMMARY, complete=complete)


_NUMBER = re.compile(r"\d+(?:[.:,]\d+)*")


def ungrounded_numbers(summary: SearchSummary, results: list[SearchResult]) -> list[str]:
    """Numbers (times, prices, dates) in the summary that don't appear in the cited result.

    An empty list means every number is backed by the source. Unclear summaries have nothing
    to check. A source number outside the results counts as entirely ungrounded.
    """
    if summary.summary is None or summary.source is None:
        return []
    if summary.source > len(results[:MAX_RESULTS]):
        return _NUMBER.findall(summary.summary) or ["source"]
    cited = results[summary.source - 1]
    # Exactly the text the model saw, after cleanup and truncation.
    evidence = (
        f"{clean_text(cited.title)[:RESULT_TITLE_MAX_CHARS]} "
        f"{clean_text(cited.snippet)[:RESULT_SNIPPET_MAX_CHARS]}"
    )
    return [number for number in _NUMBER.findall(summary.summary) if number not in evidence]
