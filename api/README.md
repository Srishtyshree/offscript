# api/

FastAPI backend. It serves `GET /health` and, once built, `POST /api/route`.

```
src/offscript_api/
  main.py      app factory, CORS, routers
  config.py    settings from env (pydantic-settings)
  routes/      HTTP endpoints
  pipeline/    validate, safety, router, fit, card_validation
  handlers/    ai, search, human
  clients/     tinker, serpapi, mock_router
  prompts/     handler prompts
tests/
  api/  unit/  safety/  fakes/
```

Setup: copy `.env.example` to `.env`, then run `make dev-api` from the repo root. Rules: AGENTS.md B3, B4, B8 and B9.
