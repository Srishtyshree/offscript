# Data

| File | Purpose |
|---|---|
| `train.jsonl` | Training examples |
| `test_sealed.jsonl` | Sealed evaluation set. Training code must never open it, and prompts must not be tuned on it. |

- JSONL format, one example per line, matching the router output schema in `contract/`.
- Each row has two separate labels: **outing fit** and **route**. The route is null when the question doesn't fit.
- No question may appear in both files. The overlap check enforces this.
- The reference cases R01–R24 in AGENTS.md are design cases, not data for either file.
