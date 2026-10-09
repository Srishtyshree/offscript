# training/

The offline pipeline. The live app receives only the resulting checkpoint path, set as `TINKER_MODEL_PATH` on Render.

| Step | Command | Script |
|---|---|---|
| Generate training fields from S06 | `python -m offscript_training.generate` | `generate.py` (+ `prompts/generate_fields.md`) |
| Check both data files, no overlap | `make check-data` | `data.py` |
| Baseline on the sealed set | `make baseline` | `evaluate.py --base` |
| Fine-tune (LoRA) | `make train RUN=sft-v1` | `train.py` |
| Evaluate the tuned checkpoint | `make evaluate RUN=sft-v1 MODEL_PATH=tinker://…` | `evaluate.py --model-path` |
| Compare base vs tuned | `make report RUN=sft-v1` | `report.py` → `training/runs/REPORT.md` |

```
data/      s06_source, train_candidates, review_corrections, train, test_sealed (see data/README.md)
src/       generate, content_rules, data, train, evaluate, metrics, report, smoke_test
runs/      one folder per run: run_config.json, config.json, metrics.jsonl, checkpoints.jsonl,
           run_summary.json, logs.log (no weights); eval/ with raw_outputs.jsonl + metrics.json
tests/
```

Rules: AGENTS.md B6. Training code refuses the sealed test set; only `evaluate.py` reads it.
