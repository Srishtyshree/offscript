# Data

| File | Purpose | Written by |
|---|---|---|
| `train.jsonl` | Training examples, converted from the team's training dataset | Training data author |
| `test_sealed.jsonl` | Sealed evaluation set (30–50 rows). Training code must never open it, and prompts must not be tuned on it. | A **different** teammate, kept separate from the training data |
| `train_annotations.jsonl` | Earlier draft in the old format. **Not used**; removed when the team's dataset arrives. | — |

## Row format

One JSON object per line ([JSONL](https://jsonlines.org/)), defined by `LabelledExample` in `contract/src/offscript_contract/dataset.py`. Each row has the question, the route, a reason, and **only that route's fields**:

```json
{"id": "t001", "question": "Why does bread go stale?", "context": "", "route": "AI", "reason": "How bread ages is stable kitchen science.", "answer": "Its starch slowly recrystallises and pushes water out, so the crumb turns firm and dry."}
{"id": "t002", "question": "Is the planetarium open on Monday?", "context": "Bengaluru", "route": "SEARCH", "reason": "Opening days change, so a current listing is needed.", "search_query": "Bengaluru planetarium opening hours Monday"}
{"id": "t003", "question": "Where do people usually cast from on this pier?", "context": "on the pier now", "route": "HUMAN", "reason": "Regular anglers here know the spots that work.", "who_to_ask": "a regular angler on the pier", "suggested_question": "Where do you usually like to cast from here?"}
```

| Field | Rule |
|---|---|
| `id` | Unique in the file; letters, digits, `-` and `_` only |
| `question` | 1–300 characters, one line, no leading/trailing or double spaces |
| `context` | `""` when there is none (never `"none"`), otherwise up to 200 characters, same rules |
| `route` | `AI`, `SEARCH` or `HUMAN` |
| `reason` | One plain sentence, at most 160 characters |
| `answer` (AI only) | About 50 words, at most 70; plain sentences or short bullet lines |
| `search_query` (SEARCH only) | One line, at most 200 characters |
| `who_to_ask` (HUMAN only) | One type of person, never a named or "present" individual; at most 80 characters |
| `suggested_question` (HUMAN only) | One natural question ending in "?", about 25 words, at most 30 |

Safety and refusal questions are **not** included: backend rules catch them before the model. Questions the guard check would stop (missing essential detail, two questions in one) are not router training rows either.

## Check a file before committing

```bash
uv run python -m offscript_contract.dataset training/data/train.jsonl
```

It prints the valid row count per route and every problem with its line number, and exits non-zero if anything is wrong.

## Rules

- No question may appear in both files, even reworded. A check enforces this before training.
- The reference cases in AGENTS.md (A7) and the worked examples in the team's spec documents are design examples, not data for either file.
- Every row is reviewed by a person, even if an LLM drafted it.
