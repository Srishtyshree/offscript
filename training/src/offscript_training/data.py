"""Loading the training and sealed files, the train/test overlap check, and chat conversions.

uv run python -m offscript_training.data        # check both files before any run
"""

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

from offscript_contract.dataset import LabelledExample, SealedExample, validate_dataset
from offscript_contract.router import build_router_messages

TRAIN_FILE = Path("training/data/train.jsonl")
SEALED_FILE = Path("training/data/test_sealed.jsonl")
NEAR_DUPLICATE = 0.6


def refuse_sealed(path: Path) -> None:
    """Training code calls this on every input path: the sealed set must never be trained on."""
    if Path(path).name.startswith("test_sealed"):
        raise SystemExit(f"Refusing to use the sealed test set for training: {path}")


def load_train(path: Path = TRAIN_FILE) -> list[LabelledExample]:
    refuse_sealed(path)
    report = validate_dataset(path, LabelledExample)
    if report.errors:
        raise SystemExit("\n".join([f"{path} is invalid:", *report.errors]))
    return report.examples


def load_eval_rows(path: Path) -> list[dict]:
    """Rows to evaluate: question, context, gold route, kind (outdoor or general)."""
    rows = []
    for line in Path(path).read_text("utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "kind" in row:
            row = SealedExample.model_validate(row).model_dump(mode="json")
        rows.append(
            {
                "id": row["id"],
                "question": row["question"],
                "context": row["context"],
                "route": row["route"],
                "kind": row.get("kind", "outdoor"),
            }
        )
    return rows


def to_conversation(example: LabelledExample) -> dict:
    """One training example in the cookbook's chat format: prompt messages + target reply."""
    messages = build_router_messages(example.question, example.context)
    return {"messages": [*messages, {"role": "assistant", "content": example.target_json}]}


def _norm(text: str) -> str:
    return re.sub(r"[^a-z ]", "", text.lower())


def overlaps(train: list[dict], sealed: list[dict], threshold: float = NEAR_DUPLICATE):
    """Pairs of (similarity, train id, sealed id) at or above the threshold."""
    hits = []
    for a in train:
        for b in sealed:
            score = SequenceMatcher(None, _norm(a["question"]), _norm(b["question"])).ratio()
            if score >= threshold:
                hits.append((round(score, 2), a["id"], b["id"]))
    return sorted(hits, reverse=True)


def main() -> int:
    train = validate_dataset(TRAIN_FILE, LabelledExample)
    sealed = validate_dataset(SEALED_FILE, SealedExample)
    failed = False
    for name, report in (("train", train), ("sealed", sealed)):
        counts = ", ".join(f"{k} {v}" for k, v in sorted(report.counts.items()))
        print(f"{name}: {len(report.examples)} valid rows ({counts})")
        for error in report.errors:
            print(f"  {error}")
        failed |= bool(report.errors)
    rows = lambda report: [e.model_dump() for e in report.examples]  # noqa: E731
    hits = overlaps(rows(train), rows(sealed))
    print(f"train/sealed overlap (similarity >= {NEAR_DUPLICATE}): {hits or 'none'}")
    return 1 if failed or hits else 0


if __name__ == "__main__":
    sys.exit(main())
