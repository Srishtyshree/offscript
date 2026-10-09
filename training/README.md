# training/

The offline pipeline: datasets, base-model baseline, LoRA SFT on Tinker, and base-vs-tuned evaluation on the sealed set. The live app receives only the resulting checkpoint path, set as `TINKER_MODEL_PATH` on Render.

```
configs/   SFT configs (base model, rank, lr, epochs, seed)
data/      train.jsonl, test_sealed.jsonl. See data/README.md
src/       check_overlap, baseline, train, evaluate
runs/      one folder per run: config, logs, checkpoint ID, metrics (no weights)
tests/
```

Rules: AGENTS.md B6.
