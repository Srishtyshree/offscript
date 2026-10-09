# Architecture

Only JSON from the tuned model that passes validation reaches the user. Training runs offline, and the live app receives only a checkpoint path.

```
web (React) ──POST /api/route──► api (FastAPI on Render)
                                  validate → safety rules → router (Tinker | mock*)
                                  → fit/guard → handler [AI | SEARCH→SerpApi | HUMAN]
                                  → card validation → contract-validated JSON ──► web

contract/  Pydantic models → JSON Schema → TS types; fixtures; router prompt
           used by api (runtime), training (dataset/eval schema), web (generated types)

training/ (offline)  datasets → baseline → LoRA SFT → eval → checkpoint path → Render env
```

\* Mock router: local development only (`OFFSCRIPT_MODE=mock`), labelled MOCK in the UI, never in production.

| Component | Folder | Notes |
|---|---|---|
| Web app | `web/` | One page, state machine, pocket mode works offline |
| API | `api/` | Pipeline steps in `pipeline/`, route handlers in `handlers/`, outbound calls in `clients/` |
| Contract | `contract/` | The only shared code. The router prompt lives here so training and inference match. |
| Training | `training/` | Never imported by `api/`. The sealed test set is never used for training. |
| Hosting | `render.yaml` | API web service (health check `/health`) and a static site |
