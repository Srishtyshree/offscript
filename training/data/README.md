# Data

| File | Purpose | Written by |
|---|---|---|
| `train.jsonl` | Training examples (120–150 rows) | Training data author, from the labelling guide |
| `test_sealed.jsonl` | Sealed evaluation set (30–50 rows). Training code must never open it, and prompts must not be tuned on it. | A **different** teammate, before the training data exists |

## Annotation file (what reviewers edit)

`train_annotations.jsonl` follows the labelling guide's annotation record, plus two fields for non-fit rows and review:

```json
{"id": "t001", "question": "...", "context": "", "outdoor_goal_fit": true, "route": "AI", "guard": null, "reason": "...", "physical_step": "...", "review_status": "draft", "origin": "kept AI01"}
{"id": "t125", "question": "Why is the sky blue?", "context": "", "outdoor_goal_fit": false, "route": null, "guard": "scope_nudge", "reason": "...", "physical_step": null, "review_status": "draft", "origin": "new: guard"}
```

- `route` is set for outings; `guard` (`scope_nudge`, `context_request`, `split_request`) is set when there is no route, labelled from the guide's reference decisions.
- `review_status` becomes `agreed` only after the reviewer checks the row. Only `agreed` rows are converted into `train.jsonl` for training.
- `physical_step` is for review and later card work; the router is not trained on it.

## Row format

One JSON object per line ([JSONL](https://jsonlines.org/)), defined by `LabelledExample` in `contract/src/offscript_contract/dataset.py`:

```json
{"id": "t001", "question": "What do regulars buy at this stall?", "context": "at the outdoor market", "fit": "ok", "route": "HUMAN", "reason": "Regulars know what is good here; no page captures it."}
{"id": "t002", "question": "What is photosynthesis?", "context": "", "fit": "scope_nudge", "route": null, "reason": "This is fully answered on a screen and needs no outing."}
```

| Field | Rule |
|---|---|
| `id` | Unique in the file; letters, digits, `-` and `_` only (e.g. `t001` for train, `s001` for sealed) |
| `question` | 1–300 characters, one line, no leading/trailing or double spaces |
| `context` | `""` when there is none (never `"none"`), otherwise up to 200 characters, same cleanliness rules |
| `fit` | `ok`, `scope_nudge`, `context_request` or `split_request` |
| `route` | `AI`, `SEARCH` or `HUMAN` when `fit` is `ok`; `null` otherwise |
| `reason` | One plain sentence, at most 160 characters, written for the person asking |

Safety and refusal questions (medical, legal, emergencies, dangerous routes, targeting people) are **not** labelled here: backend rules catch them before the model.

## Check a file before committing

```bash
uv run python -m offscript_contract.dataset training/data/train.jsonl
```

It prints the valid row count per category and every problem with its line number, and exits non-zero if anything is wrong.

## Rules

- No question may appear in both files, even reworded. A check enforces this before training.
- The reference cases R01–R24 in AGENTS.md are design examples, not data for either file.
- Every row is reviewed by a person, even if an LLM drafted it.
