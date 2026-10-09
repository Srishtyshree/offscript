"""Format and validation for labelled router examples (training data and the sealed test set).

Check a file before committing it:

    uv run python -m offscript_contract.dataset training/data/train.jsonl
"""

import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from offscript_contract.router import (
    NO_CONTEXT,
    Fit,
    InputError,
    Route,
    RouterInput,
    RouterOutput,
    normalize_input,
)


class LabelledExample(BaseModel):
    """One JSONL row. `context` is "" when there is none. Text must already be clean,
    so every file stores questions exactly as the model will see them."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,40}$")
    question: str
    context: str
    fit: Fit
    route: Route | None
    reason: str

    @model_validator(mode="after")
    def _clean_and_consistent(self) -> "LabelledExample":
        try:
            cleaned = normalize_input(self.question, self.context)
        except InputError as error:
            raise ValueError(str(error)) from None
        if cleaned.question != self.question:
            raise ValueError("question has extra spaces, line breaks or control characters")
        if self.context and cleaned.context != self.context:
            raise ValueError("context has extra spaces, line breaks or control characters")
        if self.context.lower() == NO_CONTEXT:
            raise ValueError('leave context as "" instead of writing "none"')
        RouterOutput(fit=self.fit, route=self.route, reason=self.reason)
        return self

    @property
    def router_input(self) -> RouterInput:
        return normalize_input(self.question, self.context)

    @property
    def label(self) -> RouterOutput:
        return RouterOutput(fit=self.fit, route=self.route, reason=self.reason)

    @property
    def category(self) -> str:
        """AI, SEARCH or HUMAN for outings; the fit value otherwise."""
        return self.route.value if self.route else self.fit.value


@dataclass
class DatasetReport:
    examples: list[LabelledExample] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def counts(self) -> Counter[str]:
        return Counter(example.category for example in self.examples)


def validate_dataset(path: str | Path) -> DatasetReport:
    """Check every line; report each problem with its line number. Never stops early."""
    report = DatasetReport()
    seen_ids: dict[str, int] = {}
    seen_questions: dict[str, int] = {}
    for number, line in enumerate(Path(path).read_text("utf-8").splitlines(), start=1):
        if not line.strip():
            report.errors.append(f"line {number}: blank line")
            continue
        try:
            example = LabelledExample.model_validate(json.loads(line))
        except json.JSONDecodeError as error:
            report.errors.append(f"line {number}: not valid JSON ({error.msg})")
            continue
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(str(part) for part in problem['loc']) or 'row'}: {problem['msg']}"
                for problem in error.errors()
            )
            report.errors.append(f"line {number}: {details}")
            continue
        if example.id in seen_ids:
            report.errors.append(
                f"line {number}: id {example.id!r} repeats line {seen_ids[example.id]}"
            )
        seen_ids.setdefault(example.id, number)
        key = example.question.casefold()
        if key in seen_questions:
            report.errors.append(f"line {number}: question repeats line {seen_questions[key]}")
        seen_questions.setdefault(key, number)
        report.examples.append(example)
    return report


def main(paths: list[str]) -> int:
    failed = False
    for path in paths:
        report = validate_dataset(path)
        counts = ", ".join(f"{name} {count}" for name, count in sorted(report.counts.items()))
        print(f"{path}: {len(report.examples)} valid rows ({counts or 'none'})")
        for error in report.errors:
            print(f"  {error}")
        failed = failed or bool(report.errors)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
